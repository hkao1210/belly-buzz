"""API response models for frontend."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Review(BaseModel):
    """Review summary for API response."""
    summary: str
    recommended_dishes: List[str] = Field(default_factory=list)
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    sentiment_score: Optional[float] = None


class RestaurantResponse(BaseModel):
    """Restaurant response for frontend API."""
    id: str
    name: str
    slug: Optional[str] = None

    address: str
    neighborhood: Optional[str] = None
    latitude: float
    longitude: float
    google_place_id: Optional[str] = None
    google_maps_url: Optional[str] = None

    price_tier: int = Field(..., ge=1, le=4)
    rating: float = 0.0
    photo_url: Optional[str] = None

    cuisine_tags: List[str] = Field(default_factory=list)
    vibe: Optional[str] = None
    review: Optional[Review] = None

    # Scores
    buzz_score: float = 0.0
    sentiment_score: float = 0.0
    viral_score: float = 0.0
    total_mentions: int = 0
    sources: List[str] = Field(default_factory=list)

    is_new: bool = False
    is_trending: bool = False


class SearchResponse(BaseModel):
    """Search API response."""
    results: List[RestaurantResponse]
    total: int
    query: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
