/**
 * Restaurant types matching backend Pydantic schemas.
 */

export interface Review {
  summary: string;
  recommended_dishes: string[];
  source_url?: string;
  source_type?: string;
}

export interface Restaurant {
  id: string;
  name: string;
  address: string;
  price_tier: 1 | 2 | 3 | 4;
  cuisine_tags: string[];
  rating: number;
  review?: Review;
  latitude: number;
  longitude: number;
  google_place_id?: string;
  google_maps_url?: string;
  photo_url?: string;
  vibe?: string;
}

export interface SearchResponse {
  results: Restaurant[];
  total: number;
  query?: string;
}

export interface SearchParams {
  q?: string;
  price_min?: number;
  price_max?: number;
  cuisine?: string[];
  sort_by?: 'rating' | 'price' | 'name';
  sort_order?: 'asc' | 'desc';
  limit?: number;
}
