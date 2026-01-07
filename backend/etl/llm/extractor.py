"""
LLM-Powered Restaurant Extraction
=================================
Uses Groq/Llama-3.1-8b to extract restaurant data and sentiment.
Conforms strictly to shared.models.
"""

import os
import json
import re
import time
import logging
from typing import List, Optional, Dict, Tuple

from groq import Groq
from dotenv import load_dotenv

from shared.models import (
    ExtractedRestaurant,
    SentimentAnalysis,
    SentimentLabel,
    ScrapedContent,
    SourceType,
)

load_dotenv()
logger = logging.getLogger(__name__)

# =============================================================================
# PROMPTS (Optimized for Llama 3.1)
# =============================================================================

EXTRACTION_PROMPT = """Extract Toronto restaurants from the text. 

For EACH restaurant, provide:
- name: Official name
- vibe: Short mood description (e.g. "upscale date night", "casual cheap eats")
- cuisine_tags: List of specific cuisines
- recommended_dishes: List of specific dishes mentioned
- price_hint: e.g. "$$", "expensive", "under $15"
- sentiment: "positive", "negative", "neutral", or "mixed"

TEXT:
{content}

Return ONLY a JSON array:
[{{"name": "...", "vibe": "...", "cuisine_tags": [], "recommended_dishes": [], "price_hint": "...", "sentiment": "..."}}]
If none, return []."""

SENTIMENT_PROMPT = """Analyze the overall sentiment of this food review/post.

Return ONLY a JSON object:
{{
  "overall_score": 0.8, 
  "label": "positive", 
  "aspects": {{"food": 0.9, "service": 0.5, "vibe": 0.8}}, 
  "summary": "Short summary here"
}}

TEXT:
{content}"""

# =============================================================================
# EXTRACTOR CLASS
# =============================================================================

class RestaurantExtractor:
    """
    Handles LLM communication to turn raw text into structured restaurant data.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.client = self._init_client()
        self.last_request_time = 0  # Track last API call for rate limiting
        self.min_interval = 3.0  # 30 RPM = 2 sec, but adding 1 sec buffer for retries/429s
    
    def _rate_limit(self):
        """Enforce rate limit: 30 requests/minute = 2 sec between calls."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            logger.info(f"[extractor] Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _init_client(self) -> Optional[Groq]:
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found in environment")
            return None
        return Groq(api_key=self.api_key)
    
    def _clean_json_response(self, text: str) -> str:
        """
        Extremely robust JSON extractor. 
        Handles markdown blocks, conversational filler, and trailing commas.
        """
        if not text:
            return ""
        
        # 1. Try to find the first '[' or '{' and the last ']' or '}'
        # This ignores LLM "Sure, here is your JSON:" chatter
        match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
        if match:
            text = match.group(1)
            
        # 2. Basic Markdown cleanup
        text = text.replace("```json", "").replace("```", "").strip()
        
        return text

    def _call_groq(self, prompt: str, max_tokens: int = 2000, retries: int = 3, force_json: bool = False) -> Optional[str]:
        if not self.client:
            return None
        
        for attempt in range(retries):
            try:
                self._rate_limit()  # Enforce rate limit before each call
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1, # Keep it deterministic for extraction
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"} if force_json or "object" in prompt.lower() else None
                )
                content = response.choices[0].message.content
                if not content or content.strip() == "":
                    if attempt < retries - 1:
                        logger.warning(f"[extractor] Empty response (attempt {attempt+1}/{retries}), retrying...")
                        time.sleep(1)  # Wait before retry
                        continue
                    else:
                        logger.warning(f"[extractor] Empty response after {retries} retries (likely rate limited)")
                return content
                
            except Exception as e:
                if attempt < retries - 1:
                    logger.warning(f"[extractor] API call failed (attempt {attempt+1}/{retries}): {e}")
                    # Sleep longer on retry to avoid hitting rate limits
                    time.sleep(5)
                    continue
                else:
                    logger.error(f"[extractor] Groq API call failed after {retries} retries: {e}")
                    return None
        
        return None

    def extract_restaurants(self, content: ScrapedContent) -> List[ExtractedRestaurant]:
        """Extracts list of restaurants and their attributes."""
        logger.info(f"[extractor] Starting restaurant extraction from: {content.source_url}")
        # Truncate to ~6000 chars to stay safe with context limits and tokens
        prompt = EXTRACTION_PROMPT.format(content=content.raw_text[:6000])
        logger.info(f"[extractor] Calling Groq API for extraction...")
        response = self._call_groq(prompt)
        logger.info(f"[extractor] Groq response received, parsing...")
        
        if not response or response.strip() == "":
            logger.warning(f"[extractor] Empty response from Groq for {content.source_url}")
            return []
        
        cleaned = self._clean_json_response(response)
        if not cleaned or cleaned.strip() == "":
            logger.warning(f"[extractor] Cleaned response was empty after JSON extraction")
            return []
            
        try:
            data = json.loads(cleaned)
            if not isinstance(data, list):
                # Sometimes LLM wraps the list in an object
                if isinstance(data, dict) and "restaurants" in data:
                    data = data["restaurants"]
                else:
                    logger.warning(f"[extractor] Response not a list: {type(data)}")
                    return []

            results = []
            for item in data:
                if not item.get("name"): continue
                
                results.append(ExtractedRestaurant(
                    name=item.get("name"),
                    vibe=item.get("vibe", ""),
                    cuisine_tags=item.get("cuisine_tags", []),
                    recommended_dishes=item.get("recommended_dishes", []),
                    price_hint=item.get("price_hint", ""),
                    sentiment=item.get("sentiment", "neutral")
                ))
            logger.info(f"[extractor] Extracted {len(results)} restaurants")
            return results
        except Exception as e:
            logger.error(f"[extractor] Failed to parse extraction JSON: {e} | cleaned_response: {cleaned[:200]}")
            return []

    def analyze_sentiment(self, content: ScrapedContent) -> Optional[SentimentAnalysis]:
        """Analyzes the overall tone of the post."""
        prompt = SENTIMENT_PROMPT.format(content=content.raw_text[:4000])
        response = self._call_groq(prompt, max_tokens=500)
        
        if not response:
            return None
            
        cleaned = self._clean_json_response(response)
        try:
            data = json.loads(cleaned)
            
            # Map string label to Enum
            label_val = data.get("label", "neutral").lower()
            try:
                label = SentimentLabel(label_val)
            except ValueError:
                label = SentimentLabel.NEUTRAL

            return SentimentAnalysis(
                overall_score=float(data.get("overall_score", 0.0)),
                label=label,
                aspects=data.get("aspects", {}),
                summary=data.get("summary", "")
            )
        except Exception as e:
            logger.error(f"Failed to parse sentiment JSON: {e}")
            return None

    def process_content(self, content: ScrapedContent) -> Tuple[List[ExtractedRestaurant], Optional[SentimentAnalysis]]:
        """
        Coordinates full processing of a single piece of scraped content.
        Used by ingest.py.
        """
        logger.info(f"LLM Processing: {content.source_url}")
        
        restaurants = self.extract_restaurants(content)
        
        # Only run sentiment analysis if we actually found restaurants to avoid wasting tokens
        sentiment = None
        if restaurants:
            sentiment = self.analyze_sentiment(content)
            
        return restaurants, sentiment

# =============================================================================
# SIMPLE TEST
# =============================================================================
if __name__ == "__main__":
    load_dotenv()
    ex = RestaurantExtractor()
    test = ScrapedContent(
        source_type=SourceType.BLOG,
        source_url="http://test.com",
        raw_text="Pai Northern Thai is the best spot for Khao Soi in Toronto. The vibe is super busy and energetic. Also loved the wings at Duff's.",
        title="Best Wings and Thai"
    )
    res, sent = ex.process_content(test)
    print(f"Found {len(res)} restaurants. Sentiment: {sent.label if sent else 'N/A'}")