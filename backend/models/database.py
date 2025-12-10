"""Database models for persistence."""

from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

from .enums import SourceType, SentimentLabel


class SocialMention(BaseModel):
    """Social mention record for database."""
    id: Optional[str] = None
    restaurant_id: Optional[str] = None
    restaurant_name: str

    source_type: SourceType
    source_url: str
    source_id: Optional[str] = None

    title: Optional[str] = None
    raw_text: str

    # Reddit-specific
    subreddit: Optional[str] = None
    reddit_score: int = 0
    reddit_num_comments: int = 0
    author: Optional[str] = None

    # AI-extracted
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[SentimentLabel] = None
    aspects: Optional[Dict[str, float]] = None
    dishes_mentioned: List[str] = Field(default_factory=list)
    price_mentioned: Optional[str] = None
    vibe_extracted: Optional[str] = None

    engagement_score: float = 0.0
    posted_at: Optional[datetime] = None
    scraped_at: Optional[datetime] = None


class Restaurant(BaseModel):
    """Full restaurant record for database."""
    id: Optional[str] = None
    name: str
    slug: Optional[str] = None

    # Location
    address: str = ""
    neighborhood: Optional[str] = None
    city: str = "Toronto"
    latitude: float = 0.0
    longitude: float = 0.0

    # Google Places
    google_place_id: Optional[str] = None
    google_maps_url: Optional[str] = None
    google_rating: Optional[float] = None
    google_reviews_count: int = 0

    # Details
    price_tier: int = Field(2, ge=1, le=4)
    photo_url: Optional[str] = None
    cuisine_tags: List[str] = Field(default_factory=list)
    vibe: Optional[str] = None
    recommended_dishes: List[str] = Field(default_factory=list)

    # Scores
    buzz_score: float = 0.0
    sentiment_score: float = 0.0
    viral_score: float = 0.0
    pro_score: float = 0.0

    # Engagement
    total_mentions: int = 0
    user_likes: int = 0
    user_saves: int = 0

    # Flags
    is_new: bool = False
    is_trending: bool = False
    hours: Optional[Dict[str, str]] = None

    # Sources
    sources: List[str] = Field(default_factory=list)
    source_urls: List[str] = Field(default_factory=list)

    # Vector (stored separately, not returned to API)
    embedding: Optional[List[float]] = None

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_scraped_at: Optional[datetime] = None
