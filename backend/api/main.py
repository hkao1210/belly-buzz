"""
Belly-Buzz FastAPI Backend
==========================
Refactored for Normalized Schema: No mock data, JOIN-based queries.
"""

import os
import logging
from typing import List, Optional, Any, Mapping
from contextlib import asynccontextmanager
from enum import Enum

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv

from .schemas import RestaurantResponse, SearchResponse, Review
from shared.embeddings.embeddings import get_embedding_service
from .db import get_supabase, set_supabase_client

load_dotenv()
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIG
# =============================================================================

CITY = os.getenv("CITY", "Toronto")
embedding_service = get_embedding_service()

class SortBy(str, Enum):
    BUZZ = "buzz_score"
    SENTIMENT = "sentiment_score"
    PRICE = "price_tier"

# =============================================================================
# LIFESPAN & APP
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm up services on startup."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SECRET_KEY")
    if supabase_url and supabase_key:
        client = create_client(supabase_url, supabase_key)
        set_supabase_client(client)
        logger.info("Supabase client initialized")
    else:
        logger.warning("Supabase credentials not found in environment")
    
    embedding_service.load()
    logger.info("Belly-Buzz API ready!")
    yield

app = FastAPI(
    title="Belly-Buzz API",
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Tighten this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# HELPERS
# =============================================================================

def db_row_to_response(row: Mapping[str, Any]) -> RestaurantResponse:
    """
    Maps a database row (including joined metrics) to the API response.
    Handles both flattened RPC results and nested table joins.
    """
    # Extract metrics from join if nested, otherwise look for top-level (RPC)
    metrics = row.get("restaurant_metrics")
    if isinstance(metrics, list):
        metrics = metrics[0] if metrics else {}
    if metrics is None:
        metrics = {}

    buzz = metrics.get("buzz_score") if isinstance(metrics, dict) else None
    buzz = buzz or row.get("buzz_score", 0)
    sentiment = metrics.get("sentiment_score") if isinstance(metrics, dict) else None
    sentiment = sentiment or row.get("sentiment_score", 0)

    # Parse cuisine_tags if it's a string, otherwise default to empty list
    cuisine_tags = row.get("cuisine_tags", [])
    if isinstance(cuisine_tags, str):
        cuisine_tags = [tag.strip() for tag in cuisine_tags.split(",")] if cuisine_tags else []
    
    return RestaurantResponse(
        id=str(row["id"]),
        name=row["name"],
        slug=row.get("slug"),
        address=row.get("address", ""),
        latitude=row.get("latitude", 0),
        longitude=row.get("longitude", 0),
        google_maps_url=row.get("google_maps_url"),
        price_tier=row.get("price_tier", 2),
        vibe=row.get("vibe"),
        cuisine_tags=cuisine_tags,
        buzz_score=buzz,
        sentiment_score=sentiment,
        total_mentions=metrics.get("total_mentions") or row.get("total_mentions", 0),
        is_trending=metrics.get("is_trending") or row.get("is_trending", False),
        # Review summary maps to vibe for now
        review=Review(
            summary=row.get("vibe", ""),
            recommended_dishes=[] # Can be populated from restaurant_tags join if needed
        ) if row.get("vibe") else None
    )

# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/search", response_model=SearchResponse)
async def search(
    q: Optional[str] = Query(None),
    price_min: Optional[int] = Query(None, ge=1, le=4),
    price_max: Optional[int] = Query(None, ge=1, le=4),
    limit: int = Query(20, ge=1, le=100)
):
    """Semantic search using pgvector RPC."""
    supabase: Optional[Client] = get_supabase()
    if not supabase:
        logger.error("Supabase client not available")
        raise HTTPException(status_code=500, detail="Search engine not configured")

    try:
        if q:
            # 1. Semantic Search (Uses the JOIN-based SQL Function)
            vector = embedding_service.embed_query(q)
            res = supabase.rpc("search_restaurants", {
                "query_embedding": vector,
                "match_count": limit,
                "price_min": price_min,
                "price_max": price_max
            }).execute()
        else:
            # 2. Standard Discovery (Highest Buzz)
            query = supabase.table("restaurants").select("*, restaurant_metrics!inner(*)").eq("city", CITY)
            if price_min: query = query.gte("price_tier", price_min)
            if price_max: query = query.lte("price_tier", price_max)
            res = query.order("restaurant_metrics(buzz_score)", desc=True).limit(limit).execute()

        rows = getattr(res, "data", []) or []
        results = [db_row_to_response(dict(row)) for row in rows]
        return SearchResponse(results=results, total=len(results), query=q or "")

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search engine error")

@app.get("/restaurants/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(restaurant_id: str):
    """Fetch restaurant + metrics by ID or Slug."""
    supabase: Optional[Client] = get_supabase()
    if not supabase:
        logger.error("Supabase client not available")
        raise HTTPException(status_code=500, detail="Database not configured")

    query = supabase.table("restaurants").select("*, restaurant_metrics(*)").eq("id", restaurant_id)
    res = query.execute()
    rows = getattr(res, "data", []) or []

    if not rows:
        # Fallback to Slug search
        res = supabase.table("restaurants").select("*, restaurant_metrics(*)").eq("slug", restaurant_id).execute()
        rows = getattr(res, "data", []) or []

    if not rows:
        raise HTTPException(status_code=404, detail="Restaurant not found")
        
    return db_row_to_response(dict(rows[0]))

@app.get("/trending", response_model=List[RestaurantResponse])
async def trending(limit: int = 10):
    """Fetch top spots from the metrics table."""
    supabase: Optional[Client] = get_supabase()
    if not supabase:
        logger.error("Supabase client not available")
        raise HTTPException(status_code=500, detail="Database not configured")

    res = supabase.table("restaurants").select("*, restaurant_metrics!inner(*)").order("restaurant_metrics(buzz_score)", desc=True).limit(limit).execute()
    rows = getattr(res, "data", []) or []
    return [db_row_to_response(dict(row)) for row in rows]


@app.get("/cuisines", response_model=List[str])
async def get_cuisines():
    """Get all unique cuisine tags from restaurants."""
    supabase: Optional[Client] = get_supabase()
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        res = supabase.table("restaurants").select("cuisine_tags").execute()
        rows = getattr(res, "data", []) or []
        
        # Flatten and deduplicate cuisine tags
        all_tags = set()
        for row in rows:
            tags = row.get("cuisine_tags", [])
            if tags:
                if isinstance(tags, list):
                    all_tags.update(tags)
                elif isinstance(tags, str):
                    all_tags.update(tags.split(','))
        
        return sorted(list(all_tags))
    except Exception as e:
        logger.error(f"Failed to fetch cuisines: {e}")
        return []

@app.get("/trending-queries", response_model=List[str])
async def get_trending_queries():
    """Get trending search queries (placeholder - returns popular cuisines for now)."""
    # TODO: Track actual user searches and return trending queries
    return [
        "best ramen",
        "date night restaurants", 
        "cheap eats",
        "italian pasta",
        "vegan options",
        "brunch spots",
        "sushi"
    ]
    return [db_row_to_response(dict(row)) for row in rows]
