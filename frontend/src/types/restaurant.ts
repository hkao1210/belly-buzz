/**
 * Restaurant types matching backend Pydantic schemas.
 */

export interface Review {
  summary: string;
  recommended_dishes: string[];
  source_url?: string;
  source_type?: string;
  sentiment_score?: number;
}

export interface Restaurant {
  id: string;
  name: string;
  slug?: string;
  address: string;
  price_tier: 1 | 2 | 3 | 4;
  cuisine_tags: string[];
  review?: Review;
  latitude: number;
  longitude: number;
  google_maps_url?: string;
  vibe?: string;
  
  // Scores
  buzz_score: number;
  sentiment_score: number;
  total_mentions: number;
  
  // Flags
  is_trending: boolean;
}

export interface SearchResponse {
  results: Restaurant[];
  total: number;
  query?: string;
  filters?: SearchFilters;
}

export interface SearchFilters {
  price_min?: number;
  price_max?: number;
  cuisine?: string[];
  sort_by?: string;
  sort_order?: string;
}

export interface SearchParams {
  q?: string;
  price_min?: number;
  price_max?: number;
  cuisine?: string[];
  sort_by?: 'buzz_score' | 'sentiment_score' | 'total_mentions';
  sort_order?: 'asc' | 'desc';
  limit?: number;
}
