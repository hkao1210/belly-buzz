#!/usr/bin/env python3
"""
For scraping 1 single link
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import logging
import asyncio
from etl.scrapers.content import ContentScraper, FeedConfig
from etl.db import get_supabase
from etl.llm.extractor import RestaurantExtractor
from etl.enrichment import GooglePlacesEnricher
from shared.embeddings.embeddings import get_embedding_service
from etl.scoring import calculate_metrics
from etl.ingest import price_hint_to_tier
from shared.models import Restaurant, RestaurantMetrics, SocialMention, SourceType

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

REDDIT_URLS = [
    "https://www.reddit.com/r/FoodToronto/comments/1pyzj19/the_best_foods_you_ate_in_toronto_in_2025/",
    # "https://www.reddit.com/r/FoodToronto/comments/ya0auo/what_restaurants_are_you_most_loyal_to_how/",
    # "https://www.reddit.com/r/FoodToronto/comments/1f0yxsr/local_restaurants_recommendations_for_visitor/",
    # "https://www.reddit.com/r/FoodToronto/comments/1781s5z/what_are_you_having_for_dinner_tonight/",
    # "https://www.reddit.com/r/FoodToronto/comments/1l8vj76/what_would_your_final_meal_in_the_city_be/",
    # "https://www.reddit.com/r/FoodToronto/comments/1krhl6o/whats_a_toronto_restaurant_that_100_lived_up_to/",
    # "https://www.reddit.com/r/FoodToronto/comments/1dsrkki/what_are_some_restaurants_that_you_feel_have_done/",
    # "https://www.reddit.com/r/FoodToronto/comments/1pnaf36/visiting_from_dallas_please_help_w_recs_if_you_can/",
    # "https://www.reddit.com/r/FoodToronto/comments/1p55tiq/i_tried_25_butter_tarts_in_toronto/",
    # "https://www.reddit.com/r/FoodToronto/comments/1nsrbdd/had_such_a_delicious_meal_at_louf/",
    # "https://www.reddit.com/r/FoodToronto/comments/1j79pf5/i_took_my_groomsmen_on_a_pizza_crawl_to_get/",
    # "https://www.reddit.com/r/FoodToronto/comments/1lqowxd/first_time_visiting_i_love_your_city/",
]

async def main():
    """Scrape ONLY the custom Reddit URLs and insert into DB."""
    scraper = ContentScraper()
    supabase = get_supabase()
    extractor = RestaurantExtractor()
    enricher = GooglePlacesEnricher()
    embedder = get_embedding_service()
    embedder.load()
    
    # Convert to RSS URLs and scrape
    rss_urls = [url.rstrip('/') + '.rss' for url in REDDIT_URLS]
    logger.info(f"Processing {len(rss_urls)} Reddit post(s)...")
    
    all_content = []
    for i, rss_url in enumerate(rss_urls):
        try:
            config = FeedConfig(name=f"Reddit Post {i+1}", feed_url=rss_url)
            content = scraper.scrape_feed(config, SourceType.SOCIAL, limit=999)
            all_content.extend(content)
            logger.info(f"Scraped {len(content)} items from {rss_url}")
        except Exception as e:
            logger.error(f"Failed to scrape {rss_url}: {e}", exc_info=True)
    
    logger.info(f"Total items scraped: {len(all_content)}")
    
    queue = {}
    for idx, item in enumerate(all_content):
        logger.info(f"[{idx+1}/{len(all_content)}] Processing: {item.source_url[:80]}...")
        extracted_list, sentiment = extractor.process_content(item)
        for ext in extracted_list:
            place = enricher.find_place(ext.name)
            key = place.place_id if place else ext.name
            
            if key in queue:
                queue[key]["mentions"].append(SocialMention(
                    restaurant_name=ext.name,
                    source_type=item.source_type,
                    source_url=item.source_url,
                    title=item.title,
                    raw_text=item.raw_text[:3000],
                    reddit_score=item.reddit_score,
                    reddit_num_comments=item.reddit_num_comments,
                    posted_at=item.posted_at,
                    sentiment_score=sentiment.overall_score if sentiment else 0.0,
                    sentiment_label=sentiment.label if sentiment else None,
                    aspects=sentiment.aspects if sentiment else None,
                    summary=sentiment.summary if sentiment else None,
                    vibe_extracted=ext.vibe,
                    dishes_mentioned=ext.recommended_dishes or [],
                    price_mentioned=ext.price_hint,
                ))
            else:
                queue[key] = {
                    "ext": ext,
                    "place": place,
                    "mentions": [SocialMention(
                        restaurant_name=ext.name,
                        source_type=item.source_type,
                        source_url=item.source_url,
                        title=item.title,
                        raw_text=item.raw_text[:3000],
                        reddit_score=item.reddit_score,
                        reddit_num_comments=item.reddit_num_comments,
                        posted_at=item.posted_at,
                        sentiment_score=sentiment.overall_score if sentiment else 0.0,
                        sentiment_label=sentiment.label if sentiment else None,
                        aspects=sentiment.aspects if sentiment else None,
                        summary=sentiment.summary if sentiment else None,
                        vibe_extracted=ext.vibe,
                        dishes_mentioned=ext.recommended_dishes or [],
                        price_mentioned=ext.price_hint,
                    )]
                }
    
    logger.info(f"Processing {len(queue)} unique restaurant(s)")
    
    # Insert to DB
    inserted = 0
    for key, data in queue.items():
        ext, place, mentions = data["ext"], data["place"], data["mentions"]
        buzz, sentiment_score = calculate_metrics(mentions)
        restaurant_name = place.name if place else ext.name
        
        # Check if restaurant is new and filter for positive sentiment for embedding
        embedding = None
        if sentiment_score > 0.3:  # Only embed if positive sentiment
            try:
                existing = supabase.table("restaurants").select("id,embedding").eq("google_place_id", place.place_id if place else None).execute()
                is_new = not existing.data or not existing.data[0].get("embedding")
                if is_new:
                    embedding = embedder.embed_text(f"{ext.name} {ext.vibe}")
                    logger.info(f"[{restaurant_name}] Generated embedding for new positive restaurant")
                else:
                    logger.info(f"[{restaurant_name}] Skipped embedding (already exists)")
            except Exception as e:
                logger.warning(f"[{restaurant_name}] Embedding check failed: {e}")
        else:
            logger.info(f"[{restaurant_name}] Skipped embedding (negative/neutral sentiment)")
        
        # Upsert restaurant
        try:
            restaurant = Restaurant(
                name=restaurant_name,
                slug=ext.name.lower().replace(" ", "-").replace("'", ""),
                address=place.address if place else "Toronto",
                latitude=place.latitude if place else 0.0,
                longitude=place.longitude if place else 0.0,
                price_tier=price_hint_to_tier(ext.price_hint, None),
                google_place_id=place.place_id if place else None,
                google_maps_url=place.google_maps_url if place else None,
                vibe=ext.vibe,
                cuisine_tags=ext.cuisine_tags,
                embedding=embedding,
            )
            
            res = supabase.table("restaurants").upsert(
                restaurant.model_dump(exclude={"id"}),
                on_conflict="google_place_id"
            ).execute()
            
            if not res.data:
                logger.error(f"[{restaurant_name}] Restaurant upsert returned no data")
                continue
                
            res_id = res.data[0]["id"]
            logger.info(f"✓ [{restaurant_name}] Inserted/Updated (ID: {res_id})")
        except Exception as e:
            logger.error(f"✗ [{restaurant_name}] Failed to upsert restaurant: {e}", exc_info=True)
            continue
        
        # Upsert metrics
        try:
            metrics_data = RestaurantMetrics(
                restaurant_id=res_id,
                buzz_score=buzz,
                sentiment_score=sentiment_score,
                total_mentions=len(mentions),
                is_trending=(len(mentions) >= 2),
            ).model_dump(mode='json')
            
            supabase.table("restaurant_metrics").upsert(
                metrics_data,
                on_conflict="restaurant_id"
            ).execute()
            logger.info(f"✓ [{restaurant_name}] Metrics upserted")
        except Exception as e:
            logger.error(f"✗ [{restaurant_name}] Failed to upsert metrics: {e}", exc_info=True)
        
        # Upsert mentions
        mention_count = 0
        for m in mentions:
            try:
                m_data = m.model_dump(mode='json')
                m_data["restaurant_id"] = res_id
                supabase.table("social_mentions").upsert(
                    m_data,
                    on_conflict="source_url"
                ).execute()
                mention_count += 1
            except Exception as e:
                logger.error(f"✗ [{restaurant_name}] Failed to upsert mention {m.source_url}: {e}", exc_info=True)
        
        logger.info(f"✓ [{restaurant_name}] Inserted {mention_count}/{len(mentions)} mentions")
        inserted += 1
    
    logger.info(f"\n✓ Done! Inserted {inserted} restaurants")

if __name__ == "__main__":
    asyncio.run(main())
