# Beli-Buzz 🍜

AI-powered Toronto restaurant discovery based on real conversations from Reddit and food blogs.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OFFLINE ETL PIPELINE                               │
│                        (Runs every X hours via cron)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │   SCRAPE     │───▶│   EXTRACT    │───▶│   ENRICH     │───▶│ VECTORIZE  │ │
│  │ Reddit/Blogs │    │  LLM (Groq)  │    │ Google Maps  │    │ Embeddings │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └────────────┘ │
│         │                   │                   │                   │        │
│         ▼                   ▼                   ▼                   ▼        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │  Raw Posts   │    │ Restaurants  │    │   Address,   │    │  384-dim   │ │
│  │  & Comments  │    │ + Sentiment  │    │   Coords     │    │  Vectors   │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └────────────┘ │
│                                                                      │       │
│                              ┌────────────────────────────────┐      │       │
│                              │         SCORE & STORE          │◀─────┘       │
│                              │   Supabase (PostgreSQL +       │              │
│                              │   pgvector)                    │              │
│                              └────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                          REAL-TIME API PIPELINE                              │
│                       (Handles user requests)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │   Frontend   │───▶│   FastAPI    │───▶│  Embed Query │───▶│  Vector    │ │
│  │   (React)    │    │   Server     │    │              │    │  Search    │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └────────────┘ │
│                              │                                       │       │
│                              ▼                                       ▼       │
│                      ┌──────────────┐                        ┌────────────┐ │
│                      │   Filters &  │                        │  Supabase  │ │
│                      │   Sorting    │                        │  pgvector  │ │
│                      └──────────────┘                        └────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Features

- **Semantic Search**: Find restaurants using natural language ("best date night ramen spot")
- **Buzz Score**: AI-calculated score based on social engagement and sentiment
- **Real Data**: Scraped from Reddit (r/askTO, r/FoodToronto) and food blogs (BlogTO, Eater Toronto)
- **Vector Search**: pgvector-powered similarity search for relevant results
- **Google Maps Integration**: Verified location data and interactive map view

## Tech Stack

### Backend
- **FastAPI** - Modern Python API framework
- **Supabase** - PostgreSQL database with pgvector extension
- **Groq** - LLM API (Llama 3.1) for entity extraction and sentiment analysis
- **Sentence Transformers** - Local embeddings (all-MiniLM-L6-v2)
- **PRAW** - Reddit API wrapper
- **Crawl4AI** - Web scraping for food blogs
- **Google Maps API** - Location enrichment

### Frontend
- **React 19** + **TypeScript**
- **Vite** - Build tool
- **TanStack Query** - Data fetching and caching
- **vis.gl/react-google-maps** - Google Maps integration
- **Tailwind CSS** - Styling with Neobrutalism theme

## Project Structure

```
beli-buzz/
├── backend/
│   ├── main.py              # FastAPI application (Day Shift)
│   ├── ingest.py            # ETL pipeline (Night Shift)
│   ├── models.py            # Pydantic data models
│   ├── schemas.py           # API schemas
│   ├── scoring.py           # Buzz/Viral/Sentiment scoring
│   ├── enrichment.py        # Google Places enrichment
│   ├── database/
│   │   └── schema.sql       # Supabase database schema
│   ├── scrapers/
│   │   ├── reddit.py        # Reddit scraper (PRAW)
│   │   └── blogs.py         # Blog scraper (Crawl4AI)
│   └── llm/
│       ├── extractor.py     # LLM entity extraction
│       └── embeddings.py    # Vector embeddings
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── RestaurantCard.tsx
│   │   │   └── RestaurantMap.tsx
│   │   ├── pages/
│   │   │   ├── Landing.tsx
│   │   │   └── Search.tsx
│   │   ├── hooks/
│   │   │   └── useRestaurants.ts
│   │   └── types/
│   │       └── restaurant.ts
│   └── public/
│       └── data.json        # Static fallback data
└── README.md
```

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- pnpm
- Supabase account
- API Keys: Google Maps, Groq, Reddit

### 1. Database Setup (Supabase)

1. Create a new Supabase project
2. Go to SQL Editor and run the schema:

```sql
-- Run backend/database/schema.sql in Supabase SQL Editor
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Run the API server
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install

# Copy environment file (create .env with these values)
# VITE_API_URL=http://localhost:8000
# VITE_GOOGLE_MAPS_API_KEY=your-key

# Run development server
pnpm dev
```

### 4. Run the Ingestion Pipeline (Optional)

To populate real data from Reddit and blogs:

```bash
cd backend
source venv/bin/activate

# Run full pipeline
python ingest.py

# Or with options
python ingest.py --no-blogs --time-filter week --limit 30
```

## Environment Variables

### Backend (.env)

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEY=your-service-role-key

# Google Maps
GOOGLE_MAPS_API_KEY=your-google-maps-api-key

# Groq (LLM)
GROQ_API_KEY=your-groq-api-key

# Reddit
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret
REDDIT_USER_AGENT=BeliBuzz/1.0

# App
CITY=Toronto
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/search` | Search restaurants with semantic similarity |
| GET | `/restaurants/{id}` | Get single restaurant |
| GET | `/trending` | Get trending restaurants |
| GET | `/trending-queries` | Get popular search queries |
| GET | `/neighborhoods` | List neighborhoods |
| GET | `/cuisines` | List cuisine types |

### Search Parameters

```
GET /search?q=best%20ramen&price_min=1&price_max=3&sort_by=buzz_score&sort_order=desc
```

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Natural language search query |
| `price_min` | 1-4 | Minimum price tier |
| `price_max` | 1-4 | Maximum price tier |
| `cuisine` | string[] | Filter by cuisine tags |
| `neighborhood` | string | Filter by neighborhood |
| `sort_by` | enum | buzz_score, sentiment_score, viral_score, rating, price_tier |
| `sort_order` | enum | asc, desc |

## Scoring System

### Buzz Score (0-20)
Overall score combining:
- 35% Sentiment Score
- 25% Viral Score  
- 20% Mention Count
- 10% Professional Reviews
- 10% Google Rating

### Sentiment Score (0-10)
Average sentiment from LLM analysis of mentions, weighted by source credibility.

### Viral Score (0-10)
Social engagement based on:
- Reddit upvotes (logarithmic)
- Comment count
- Recency (30-day decay)
- Engagement rate

## Development

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
pnpm test
```

### Adding New Sources

1. Create scraper in `backend/scrapers/`
2. Add to `TORONTO_BLOG_URLS` or similar config
3. Implement `scrape_` method returning `ScrapedContent`

## Deployment

### Backend (Railway/Render)
```bash
# Procfile
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Frontend (Vercel/Netlify)
```bash
# Build command
pnpm build

# Output directory
dist
```

## License

MIT
