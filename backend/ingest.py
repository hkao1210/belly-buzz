"""
Beli-Buzz Ingestion Script (The "Night Shift")
==============================================
Runs as a GitHub Actions cron job.

Workflow:
1. FIND: Visit Eater.com or Reddit
2. SCRAPE: Crawl4AI extracts Markdown
3. EXTRACT: Groq/Llama extracts restaurant data as JSON
4. ENRICH: Google Places API adds address, coords, price
5. VECTORIZE: Sentence-transformers creates embeddings
6. STORE: Save to Supabase (row + vector)
"""

import os
import json
import logging
from typing import List, Optional
from dataclasses import dataclass

import googlemaps
from groq import Groq
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Try importing crawl4ai (async)
try:
    from crawl4ai import AsyncWebCrawler
    HAS_CRAWL4AI = True
except ImportError:
    HAS_CRAWL4AI = False
    print("Warning: crawl4ai not installed. Run: pip install crawl4ai")

load_dotenv()

# =============================================================================
# CONFIG
# =============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Keys (set these in .env or GitHub Secrets)
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

# Embedding model (runs locally, free)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# =============================================================================
# CLIENTS
# =============================================================================

def get_google_maps_client() -> Optional[googlemaps.Client]:
    if not GOOGLE_MAPS_API_KEY:
        logger.warning("GOOGLE_MAPS_API_KEY not set")
        return None
    return googlemaps.Client(key=GOOGLE_MAPS_API_KEY)


def get_groq_client() -> Optional[Groq]:
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set")
        return None
    return Groq(api_key=GROQ_API_KEY)


def get_supabase_client() -> Optional[Client]:
    if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
        logger.warning("SUPABASE_URL or SUPABASE_SECRET_KEY not set")
        return None
    return create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL)


# =============================================================================
# STEP 1 & 2: SCRAPE (Crawl4AI)
# =============================================================================

async def scrape_url(url: str) -> Optional[str]:
    """Scrape a URL and return Markdown content."""
    if not HAS_CRAWL4AI:
        logger.error("crawl4ai not available")
        return None
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        if result.success:
            return result.markdown
        else:
            logger.error(f"Failed to scrape {url}")
            return None


# =============================================================================
# STEP 3: EXTRACT (Groq LLM)
# =============================================================================

EXTRACTION_PROMPT = """You are a restaurant data extractor. Extract restaurant information from this blog post.

For EACH restaurant mentioned, extract:
- name: The restaurant name
- vibe: A short description of the atmosphere/vibe (e.g., "loud party spot", "romantic date night", "casual family-friendly")
- cuisine_tags: List of cuisine types (e.g., ["Italian", "Pasta", "Wine Bar"])
- recommended_dishes: Specific dishes mentioned positively
- price_hint: Any price mentions (e.g., "affordable", "splurge", "$$$")

Return JSON array. If no restaurants found, return empty array.

BLOG CONTENT:
{content}

Return ONLY valid JSON, no explanation:"""


def extract_restaurants(content: str, groq_client: Groq) -> List[dict]:
    """Use Groq/Llama to extract restaurant data from content."""
    if not groq_client:
        return []
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": EXTRACTION_PROMPT.format(content=content[:8000])}
            ],
            temperature=0.1,
            max_tokens=2000,
        )
        
        result = response.choices[0].message.content.strip()
        
        # Parse JSON (handle markdown code blocks)
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
        
        return json.loads(result)
    
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return []


# =============================================================================
# STEP 4: ENRICH (Google Places API)
# =============================================================================

@dataclass
class PlaceData:
    """Data from Google Places API."""
    place_id: str
    name: str
    address: str
    latitude: float
    longitude: float
    price_level: Optional[int]
    rating: Optional[float]
    google_maps_url: str
    photo_reference: Optional[str] = None


def enrich_with_google_places(
    restaurant_name: str,
    gmaps: googlemaps.Client,
    city: str = "New York"
) -> Optional[PlaceData]:
    """Look up restaurant on Google Places and get official data."""
    if not gmaps:
        return None
    
    try:
        # Find the place
        query = f"{restaurant_name} restaurant {city}"
        result = gmaps.find_place(
            input=query,
            input_type="textquery",
            fields=["place_id", "name", "formatted_address", "geometry", 
                    "price_level", "rating", "photos"]
        )
        
        if not result.get("candidates"):
            logger.warning(f"No Google Places result for: {restaurant_name}")
            return None
        
        place = result["candidates"][0]
        place_id = place["place_id"]
        
        # Get photo URL if available
        photo_ref = None
        if place.get("photos"):
            photo_ref = place["photos"][0].get("photo_reference")
        
        return PlaceData(
            place_id=place_id,
            name=place.get("name", restaurant_name),
            address=place.get("formatted_address", ""),
            latitude=place["geometry"]["location"]["lat"],
            longitude=place["geometry"]["location"]["lng"],
            price_level=place.get("price_level"),
            rating=place.get("rating"),
            google_maps_url=f"https://www.google.com/maps/place/?q=place_id:{place_id}",
            photo_reference=photo_ref,
        )
    
    except Exception as e:
        logger.error(f"Google Places lookup failed for {restaurant_name}: {e}")
        return None


def get_photo_url(photo_reference: str, gmaps: googlemaps.Client, max_width: int = 400) -> str:
    """Generate a Google Places photo URL."""
    if not photo_reference or not GOOGLE_MAPS_API_KEY:
        return ""
    return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photo_reference={photo_reference}&key={GOOGLE_MAPS_API_KEY}"


# =============================================================================
# STEP 5: VECTORIZE (Sentence Transformers)
# =============================================================================

def create_embedding(text: str, model: SentenceTransformer) -> List[float]:
    """Create embedding vector from text."""
    embedding = model.encode(text)
    return embedding.tolist()


def create_restaurant_embedding(
    vibe: str,
    cuisine_tags: List[str],
    dishes: List[str],
    model: SentenceTransformer
) -> List[float]:
    """Create searchable embedding from restaurant attributes."""
    # Combine all searchable text
    text_parts = [vibe] if vibe else []
    text_parts.extend(cuisine_tags)
    text_parts.extend(dishes)
    
    combined_text = " ".join(text_parts)
    return create_embedding(combined_text, model)


# =============================================================================
# STEP 6: STORE (Supabase)
# =============================================================================

def store_restaurant(
    extracted: dict,
    place_data: Optional[PlaceData],
    embedding: List[float],
    source_url: str,
    source_type: str,
    supabase: Client,
    gmaps: Optional[googlemaps.Client] = None
) -> bool:
    """Store restaurant in Supabase with vector embedding."""
    if not supabase:
        logger.error("Supabase client not available")
        return False
    
    try:
        # Build photo URL
        photo_url = None
        if place_data and place_data.photo_reference and gmaps:
            photo_url = get_photo_url(place_data.photo_reference, gmaps)
        
        # Map price hint to tier
        price_tier = 2  # default
        if place_data and place_data.price_level:
            price_tier = place_data.price_level
        elif extracted.get("price_hint"):
            hint = extracted["price_hint"].lower()
            if "cheap" in hint or "affordable" in hint or "$" == hint:
                price_tier = 1
            elif "expensive" in hint or "splurge" in hint or "$$$$" in hint:
                price_tier = 4
            elif "$$$" in hint:
                price_tier = 3
        
        # Prepare row
        row = {
            "name": place_data.name if place_data else extracted["name"],
            "address": place_data.address if place_data else "",
            "latitude": place_data.latitude if place_data else 0,
            "longitude": place_data.longitude if place_data else 0,
            "google_place_id": place_data.place_id if place_data else None,
            "google_maps_url": place_data.google_maps_url if place_data else None,
            "price_tier": price_tier,
            "rating": place_data.rating if place_data else 0,
            "photo_url": photo_url,
            "cuisine_tags": extracted.get("cuisine_tags", []),
            "vibe": extracted.get("vibe", ""),
            "recommended_dishes": extracted.get("recommended_dishes", []),
            "source_url": source_url,
            "source_type": source_type,
            "embedding": embedding,
        }
        
        # Upsert (update if exists based on google_place_id or name)
        result = supabase.table("restaurants").upsert(
            row,
            on_conflict="google_place_id"
        ).execute()
        
        logger.info(f"Stored: {row['name']}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to store restaurant: {e}")
        return False


# =============================================================================
# MAIN PIPELINE
# =============================================================================

async def ingest_url(
    url: str,
    source_type: str = "blog",
    city: str = "New York"
) -> int:
    """Full ingestion pipeline for a single URL."""
    logger.info(f"Ingesting: {url}")
    
    # Initialize clients
    gmaps = get_google_maps_client()
    groq = get_groq_client()
    supabase = get_supabase_client()
    model = get_embedding_model()
    
    # Step 1-2: Scrape
    content = await scrape_url(url)
    if not content:
        logger.error("Scraping failed")
        return 0
    
    # Step 3: Extract
    restaurants = extract_restaurants(content, groq)
    logger.info(f"Extracted {len(restaurants)} restaurants")
    
    stored_count = 0
    for restaurant in restaurants:
        # Step 4: Enrich
        place_data = enrich_with_google_places(restaurant["name"], gmaps, city)
        
        # Step 5: Vectorize
        embedding = create_restaurant_embedding(
            vibe=restaurant.get("vibe", ""),
            cuisine_tags=restaurant.get("cuisine_tags", []),
            dishes=restaurant.get("recommended_dishes", []),
            model=model
        )
        
        # Step 6: Store
        success = store_restaurant(
            extracted=restaurant,
            place_data=place_data,
            embedding=embedding,
            source_url=url,
            source_type=source_type,
            supabase=supabase,
            gmaps=gmaps
        )
        
        if success:
            stored_count += 1
    
    return stored_count


# =============================================================================
# SAMPLE URLS TO INGEST
# =============================================================================

SAMPLE_URLS = [
    ("https://ny.eater.com/maps/best-new-restaurants-nyc", "eater"),
    ("https://ny.eater.com/maps/best-italian-restaurants-nyc", "eater"),
    ("https://ny.eater.com/maps/best-date-night-restaurants-nyc", "eater"),
]


async def run_ingestion():
    """Run ingestion on all sample URLs."""
    total = 0
    for url, source_type in SAMPLE_URLS:
        count = await ingest_url(url, source_type)
        total += count
        logger.info(f"Ingested {count} from {url}")
    
    logger.info(f"Total ingested: {total} restaurants")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_ingestion())
