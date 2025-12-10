"""
Pydantic schemas for Beli-Buzz API.
Matches Supabase database schema.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# DATABASE MODELS (matching Supabase schema)
# =============================================================================

class Review(BaseModel):
    """AI-extracted review data from blogs/Reddit."""
    summary: str = Field(..., description="AI-generated vibe/sentiment summary")
    recommended_dishes: List[str] = Field(
        default_factory=list,
        description="Dishes mentioned positively"
    )
    source_url: Optional[str] = Field(default=None, description="Original blog/Reddit URL")
    source_type: Optional[str] = Field(default=None, description="eater, reddit, etc.")


class Restaurant(BaseModel):
    """Restaurant entity - combines scraped data + Google Places enrichment."""
    id: str = Field(..., description="Unique identifier (UUID)")
    name: str = Field(..., description="Restaurant name")
    
    # From Google Places API
    address: str = Field(..., description="Full formatted address")
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    google_place_id: Optional[str] = Field(default=None, description="Google Place ID")
    google_maps_url: Optional[str] = Field(default=None, description="Google Maps link")
    
    # From Google Places or scraped
    price_tier: int = Field(
        ..., 
        ge=1, 
        le=4, 
        description="Price level from 1 ($) to 4 ($$$$)"
    )
    rating: float = Field(
        default=0.0, 
        ge=0, 
        le=5, 
        description="Google rating out of 5"
    )
    photo_url: Optional[str] = Field(default=None, description="Photo URL")
    
    # AI-extracted data
    cuisine_tags: List[str] = Field(
        default_factory=list,
        description="Cuisine types extracted by LLM"
    )
    vibe: Optional[str] = Field(
        default=None,
        description="Vibe/atmosphere description (used for embedding)"
    )
    review: Optional[Review] = Field(
        default=None,
        description="AI-generated review summary"
    )
    
    # Note: embedding vector is stored in Supabase but NOT returned to frontend


class RestaurantCreate(BaseModel):
    """Schema for creating a restaurant during ingestion."""
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    google_place_id: Optional[str] = None
    google_maps_url: Optional[str] = None
    price_tier: Optional[int] = None
    rating: Optional[float] = None
    photo_url: Optional[str] = None
    cuisine_tags: List[str] = Field(default_factory=list)
    vibe: Optional[str] = None
    recommended_dishes: List[str] = Field(default_factory=list)
    source_url: Optional[str] = None
    source_type: Optional[str] = None


# =============================================================================
# API REQUEST/RESPONSE MODELS
# =============================================================================

class SearchQuery(BaseModel):
    """Semantic search request."""
    q: str = Field(..., description="Natural language query (e.g., 'romantic Italian date spot')")
    price_min: Optional[int] = Field(default=None, ge=1, le=4)
    price_max: Optional[int] = Field(default=None, ge=1, le=4)
    cuisine: Optional[List[str]] = Field(default=None)
    limit: int = Field(default=20, ge=1, le=100)


class SearchResponse(BaseModel):
    """Search response with results and metadata."""
    results: List[Restaurant]
    total: int
    query: str


# =============================================================================
# LLM EXTRACTION SCHEMAS (for Groq output)
# =============================================================================

class ExtractedRestaurant(BaseModel):
    """What we ask Groq to extract from blog content."""
    name: str = Field(..., description="Restaurant name")
    vibe: str = Field(..., description="Atmosphere/vibe description (e.g., 'loud, party, date night')")
    cuisine_tags: List[str] = Field(default_factory=list, description="Cuisine types")
    recommended_dishes: List[str] = Field(default_factory=list, description="Specific dishes mentioned")
    price_hint: Optional[str] = Field(default=None, description="Price mentions (e.g., 'affordable', 'splurge')")


class ExtractionResult(BaseModel):
    """Full extraction result from a single blog/article."""
    restaurants: List[ExtractedRestaurant]
    source_url: str
    source_type: str
