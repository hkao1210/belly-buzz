"""
Blog Scraper using Crawl4AI
===========================
Scrapes Toronto food blogs and publications.
"""

import logging
from typing import List, Optional
from datetime import datetime

from dotenv import load_dotenv

from models import ScrapedContent, SourceType

load_dotenv()

logger = logging.getLogger(__name__)

# Try importing crawl4ai (requires Python 3.10+)
try:
    from crawl4ai import AsyncWebCrawler
    HAS_CRAWL4AI = True
except (ImportError, TypeError):
    AsyncWebCrawler = None
    HAS_CRAWL4AI = False
    logger.warning("crawl4ai not available (requires Python 3.10+)")


# Toronto food blog URLs to scrape
TORONTO_BLOG_URLS = [
    # BlogTO food sections
    ("https://www.blogto.com/toronto/the_best_restaurants_in_toronto/", SourceType.BLOGTO),
    ("https://www.blogto.com/toronto/the_best_ramen_toronto/", SourceType.BLOGTO),
    ("https://www.blogto.com/toronto/the_best_sushi_in_toronto/", SourceType.BLOGTO),
    ("https://www.blogto.com/toronto/the_best_thai_food_in_toronto/", SourceType.BLOGTO),
    ("https://www.blogto.com/toronto/the_best_pizza_in_toronto/", SourceType.BLOGTO),
    ("https://www.blogto.com/toronto/the_best_brunch_in_toronto/", SourceType.BLOGTO),
    ("https://www.blogto.com/toronto/the_best_cheap_eats_in_toronto/", SourceType.BLOGTO),
    ("https://www.blogto.com/toronto/the_best_italian_restaurants_in_toronto/", SourceType.BLOGTO),
    ("https://www.blogto.com/toronto/the_best_indian_restaurants_in_toronto/", SourceType.BLOGTO),
    ("https://www.blogto.com/toronto/the_best_korean_restaurants_in_toronto/", SourceType.BLOGTO),
    
    # Eater Toronto
    ("https://toronto.eater.com/maps/best-new-restaurants-toronto", SourceType.EATER),
    ("https://toronto.eater.com/maps/best-restaurants-toronto", SourceType.EATER),
    
    # Toronto Life food
    ("https://torontolife.com/food/restaurants/", SourceType.TORONTO_LIFE),
]


class BlogScraper:
    """
    Scrapes Toronto food blogs using Crawl4AI.
    """
    
    def __init__(self):
        self.has_crawler = HAS_CRAWL4AI
    
    async def scrape_url(self, url: str) -> Optional[str]:
        """
        Scrape a single URL and return markdown content.
        
        Args:
            url: URL to scrape
            
        Returns:
            Markdown content or None if failed
        """
        if not self.has_crawler:
            logger.error("crawl4ai not available")
            return None
        
        try:
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url)
                if result.success:
                    return result.markdown
                else:
                    logger.error(f"Failed to scrape {url}")
                    return None
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    async def scrape_blog(
        self,
        url: str,
        source_type: SourceType = SourceType.BLOGTO,
    ) -> Optional[ScrapedContent]:
        """
        Scrape a blog URL and return structured content.
        
        Args:
            url: Blog URL
            source_type: Type of source
            
        Returns:
            ScrapedContent or None
        """
        content = await self.scrape_url(url)
        if not content:
            return None
        
        return ScrapedContent(
            source_type=source_type,
            source_url=url,
            title=self._extract_title(content),
            raw_text=content,
            posted_at=datetime.now(),  # Blogs don't always have dates
        )
    
    def _extract_title(self, markdown: str) -> str:
        """Extract title from markdown (first H1)."""
        for line in markdown.split('\n'):
            if line.startswith('# '):
                return line[2:].strip()
        return "Unknown"
    
    async def scrape_all_blogs(self) -> List[ScrapedContent]:
        """
        Scrape all configured Toronto food blogs.
        
        Returns:
            List of scraped content
        """
        results = []
        
        for url, source_type in TORONTO_BLOG_URLS:
            try:
                content = await self.scrape_blog(url, source_type)
                if content:
                    results.append(content)
                    logger.info(f"Scraped: {url}")
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                continue
        
        logger.info(f"Total scraped from blogs: {len(results)}")
        return results


# =============================================================================
# CLI for testing
# =============================================================================
if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        scraper = BlogScraper()
        if scraper.has_crawler:
            content = await scraper.scrape_url("https://www.blogto.com/toronto/the_best_ramen_toronto/")
            if content:
                print(f"Content length: {len(content)}")
                print(f"Preview: {content[:500]}...")
    
    asyncio.run(test())

