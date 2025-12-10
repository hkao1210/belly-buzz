"""
Beli-Buzz FastAPI Backend (The "Day Shift")
============================================
Handles user search requests with vector similarity search.

Workflow:
1. User sends natural language query
2. FastAPI embeds the query using same model as ingestion
3. Supabase does vector similarity search
4. Return matching restaurants
"""

import os
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
from dotenv import load_dotenv

from schemas import Restaurant, Review, SearchResponse

load_dotenv()

# =============================================================================
# CONFIG
# =============================================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Global instances (initialized on startup)
embedding_model: Optional[SentenceTransformer] = None
supabase_client: Optional[Client] = None


# =============================================================================
# STARTUP / SHUTDOWN
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup."""
    global embedding_model, supabase_client
    
    # Load embedding model (takes a few seconds first time)
    print("Loading embedding model...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    print("Embedding model loaded!")
    
    # Initialize Supabase client
    if SUPABASE_URL and SUPABASE_SECRET_KEY:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
        print("Supabase client initialized!")
    else:
        print("Warning: Supabase credentials not set, using mock data")
    
    yield
    
    # Cleanup (if needed)
    print("Shutting down...")


# =============================================================================
# APP
# =============================================================================

app = FastAPI(
    title="Beli-Buzz API",
    description="AI-powered restaurant discovery with semantic search",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# MOCK DATA (used when Supabase not configured)
# =============================================================================

MOCK_RESTAURANTS: List[Restaurant] = [
    Restaurant(
        id="1",
        name="Pasta Paradise",
        address="123 Main St, New York, NY 10001",
        latitude=40.7128,
        longitude=-74.0060,
        google_place_id="ChIJ_mock_1",
        google_maps_url="https://maps.google.com/?q=Pasta+Paradise",
        price_tier=2,
        cuisine_tags=["Italian", "Pasta"],
        rating=4.5,
        vibe="Cozy romantic spot, perfect for date nights",
        review=Review(
            summary="Cozy Italian spot known for handmade pasta. Locals rave about the truffle carbonara.",
            recommended_dishes=["Truffle Carbonara", "Cacio e Pepe", "Tiramisu"],
            source_url="https://eater.com/nyc",
            source_type="eater"
        )
    ),
    Restaurant(
        id="2",
        name="Sushi Zen",
        address="456 Broadway, New York, NY 10012",
        latitude=40.7193,
        longitude=-73.9987,
        google_place_id="ChIJ_mock_2",
        google_maps_url="https://maps.google.com/?q=Sushi+Zen",
        price_tier=4,
        cuisine_tags=["Japanese", "Sushi", "Omakase"],
        rating=4.8,
        vibe="High-end omakase, quiet intimate dining",
        review=Review(
            summary="High-end omakase experience with fish flown in daily from Tokyo.",
            recommended_dishes=["Omakase Course", "Otoro", "Uni"],
            source_url="https://eater.com/nyc",
            source_type="eater"
        )
    ),
    Restaurant(
        id="3",
        name="Taco Libre",
        address="789 Houston St, New York, NY 10014",
        latitude=40.7282,
        longitude=-74.0021,
        google_place_id="ChIJ_mock_3",
        google_maps_url="https://maps.google.com/?q=Taco+Libre",
        price_tier=1,
        cuisine_tags=["Mexican", "Tacos", "Street Food"],
        rating=4.3,
        vibe="Loud party vibes, casual street food",
        review=Review(
            summary="Authentic street-style tacos at unbeatable prices.",
            recommended_dishes=["Al Pastor Tacos", "Carnitas", "Horchata"],
            source_url="https://reddit.com/r/nyc",
            source_type="reddit"
        )
    ),
    Restaurant(
        id="4",
        name="Le Petit Bistro",
        address="234 West Village, New York, NY 10014",
        latitude=40.7359,
        longitude=-74.0036,
        google_place_id="ChIJ_mock_4",
        google_maps_url="https://maps.google.com/?q=Le+Petit+Bistro",
        price_tier=3,
        cuisine_tags=["French", "Bistro", "Wine Bar"],
        rating=4.6,
        vibe="Charming romantic French cafe, candlelit ambiance",
        review=Review(
            summary="Charming French bistro with an extensive wine list.",
            recommended_dishes=["Duck Confit", "Steak Frites", "Crème Brûlée"],
            source_url="https://eater.com/nyc",
            source_type="eater"
        )
    ),
    Restaurant(
        id="5",
        name="Bangkok Express",
        address="567 Chinatown, New York, NY 10013",
        latitude=40.7158,
        longitude=-73.9970,
        google_place_id="ChIJ_mock_5",
        google_maps_url="https://maps.google.com/?q=Bangkok+Express",
        price_tier=1,
        cuisine_tags=["Thai", "Noodles", "Spicy"],
        rating=4.2,
        vibe="No-frills, spicy, quick lunch spot",
        review=Review(
            summary="No-frills Thai joint with explosive flavors.",
            recommended_dishes=["Drunken Noodles", "Green Curry", "Thai Iced Tea"],
            source_url="https://reddit.com/r/nyc",
            source_type="reddit"
        )
    ),
    Restaurant(
        id="6",
        name="The Butcher's Block",
        address="890 Meatpacking District, New York, NY 10014",
        latitude=40.7398,
        longitude=-74.0082,
        google_place_id="ChIJ_mock_6",
        google_maps_url="https://maps.google.com/?q=Butchers+Block",
        price_tier=4,
        cuisine_tags=["Steakhouse", "American", "Fine Dining"],
        rating=4.7,
        vibe="Classic NYC steakhouse, power lunch, business dinner",
        review=Review(
            summary="Classic NYC steakhouse with dry-aged perfection.",
            recommended_dishes=["Porterhouse for Two", "Creamed Spinach", "NY Cheesecake"],
            source_url="https://eater.com/nyc",
            source_type="eater"
        )
    ),
    Restaurant(
        id="7",
        name="Noodle House",
        address="321 East Village, New York, NY 10003",
        latitude=40.7264,
        longitude=-73.9878,
        google_place_id="ChIJ_mock_7",
        google_maps_url="https://maps.google.com/?q=Noodle+House",
        price_tier=2,
        cuisine_tags=["Chinese", "Noodles", "Dumplings"],
        rating=4.4,
        vibe="Casual family-friendly, hand-pulled noodles",
        review=Review(
            summary="Hand-pulled noodles made fresh to order.",
            recommended_dishes=["Hand-Pulled Noodles", "Soup Dumplings", "Cumin Lamb"],
            source_url="https://reddit.com/r/nyc",
            source_type="reddit"
        )
    ),
    Restaurant(
        id="8",
        name="Pizza Underground",
        address="654 Lower East Side, New York, NY 10002",
        latitude=40.7150,
        longitude=-73.9843,
        google_place_id="ChIJ_mock_8",
        google_maps_url="https://maps.google.com/?q=Pizza+Underground",
        price_tier=2,
        cuisine_tags=["Pizza", "Italian", "Late Night"],
        rating=4.5,
        vibe="Late night party spot, quick bites",
        review=Review(
            summary="New York slice perfection. Available until 4am.",
            recommended_dishes=["Vodka Slice", "Pepperoni", "Garlic Knots"],
            source_url="https://reddit.com/r/nyc",
            source_type="reddit"
        )
    ),
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def embed_query(query: str) -> List[float]:
    """Create embedding vector from search query."""
    if not embedding_model:
        raise HTTPException(status_code=500, detail="Embedding model not loaded")
    embedding = embedding_model.encode(query)
    return embedding.tolist()


async def search_supabase(
    query_embedding: List[float],
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
    cuisine: Optional[List[str]] = None,
    limit: int = 20,
) -> List[dict]:
    """Perform vector similarity search in Supabase."""
    if not supabase_client:
        return []
    
    # Call the Supabase RPC function for vector search
    # This assumes you have a function called `search_restaurants` in Supabase
    try:
        result = supabase_client.rpc(
            "search_restaurants",
            {
                "query_embedding": query_embedding,
                "match_count": limit,
                "price_min": price_min,
                "price_max": price_max,
            }
        ).execute()
        
        return result.data or []
    except Exception as e:
        print(f"Supabase search error: {e}")
        return []


def filter_mock_data(
    query: Optional[str],
    price_min: Optional[int],
    price_max: Optional[int],
    cuisine: Optional[List[str]],
) -> List[Restaurant]:
    """Filter mock data (simple text matching, not vector search)."""
    results = MOCK_RESTAURANTS.copy()
    
    # Price filter
    if price_min:
        results = [r for r in results if r.price_tier >= price_min]
    if price_max:
        results = [r for r in results if r.price_tier <= price_max]
    
    # Cuisine filter
    if cuisine:
        cuisine_lower = [c.lower() for c in cuisine]
        results = [
            r for r in results
            if any(tag.lower() in cuisine_lower for tag in r.cuisine_tags)
        ]
    
    # Simple text search
    if query:
        q_lower = query.lower()
        scored = []
        for r in results:
            score = 0
            if q_lower in r.name.lower():
                score += 10
            if r.vibe and q_lower in r.vibe.lower():
                score += 5
            if any(q_lower in tag.lower() for tag in r.cuisine_tags):
                score += 5
            if r.review and q_lower in r.review.summary.lower():
                score += 3
            if score > 0:
                scored.append((score, r))
        
        # Sort by relevance score
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [r for _, r in scored]
    
    return results


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Beli-Buzz API v2.0",
        "supabase_connected": supabase_client is not None,
        "embedding_model_loaded": embedding_model is not None,
    }


@app.get("/search", response_model=SearchResponse)
async def search_restaurants(
    q: Optional[str] = Query(default=None, description="Natural language search query"),
    price_min: Optional[int] = Query(default=None, ge=1, le=4),
    price_max: Optional[int] = Query(default=None, ge=1, le=4),
    cuisine: Optional[List[str]] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
):
    """
    Search restaurants using semantic similarity.
    
    Examples:
    - "romantic Italian date spot"
    - "cheap late night tacos"
    - "upscale sushi omakase"
    """
    # If Supabase is connected, use vector search
    if supabase_client and q:
        # Embed the query
        query_embedding = embed_query(q)
        
        # Search Supabase
        raw_results = await search_supabase(
            query_embedding=query_embedding,
            price_min=price_min,
            price_max=price_max,
            cuisine=cuisine,
            limit=limit,
        )
        
        # Convert to Restaurant objects
        results = []
        for row in raw_results:
            results.append(Restaurant(
                id=str(row["id"]),
                name=row["name"],
                address=row["address"],
                latitude=row["latitude"],
                longitude=row["longitude"],
                google_place_id=row.get("google_place_id"),
                google_maps_url=row.get("google_maps_url"),
                price_tier=row["price_tier"],
                rating=row.get("rating", 0),
                photo_url=row.get("photo_url"),
                cuisine_tags=row.get("cuisine_tags", []),
                vibe=row.get("vibe"),
                review=Review(
                    summary=row.get("vibe", ""),
                    recommended_dishes=row.get("recommended_dishes", []),
                    source_url=row.get("source_url"),
                    source_type=row.get("source_type"),
                ) if row.get("vibe") else None,
            ))
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=q,
        )
    
    # Fallback to mock data
    results = filter_mock_data(q, price_min, price_max, cuisine)
    
    return SearchResponse(
        results=results[:limit],
        total=len(results),
        query=q or "",
    )


@app.get("/restaurants/{restaurant_id}", response_model=Restaurant)
async def get_restaurant(restaurant_id: str):
    """Get a single restaurant by ID."""
    # Try Supabase first
    if supabase_client:
        try:
            result = supabase_client.table("restaurants").select("*").eq("id", restaurant_id).single().execute()
            if result.data:
                row = result.data
                return Restaurant(
                    id=str(row["id"]),
                    name=row["name"],
                    address=row["address"],
                    latitude=row["latitude"],
                    longitude=row["longitude"],
                    google_place_id=row.get("google_place_id"),
                    google_maps_url=row.get("google_maps_url"),
                    price_tier=row["price_tier"],
                    rating=row.get("rating", 0),
                    photo_url=row.get("photo_url"),
                    cuisine_tags=row.get("cuisine_tags", []),
                    vibe=row.get("vibe"),
                    review=Review(
                        summary=row.get("vibe", ""),
                        recommended_dishes=row.get("recommended_dishes", []),
                    ) if row.get("vibe") else None,
                )
        except Exception as e:
            print(f"Supabase fetch error: {e}")
    
    # Fallback to mock data
    for restaurant in MOCK_RESTAURANTS:
        if restaurant.id == restaurant_id:
            return restaurant
    
    raise HTTPException(status_code=404, detail="Restaurant not found")


@app.get("/trending", response_model=List[str])
async def get_trending():
    """Get trending search queries."""
    return [
        "Romantic Italian under $50",
        "Best ramen in NYC",
        "Late night tacos",
        "Rooftop dining",
        "Omakase experience",
        "Spicy food",
    ]
