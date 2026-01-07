import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import type { SearchResponse, SearchParams, Restaurant } from '@/types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Fetch restaurants from the API with search params.
 */
async function fetchRestaurants(params: SearchParams): Promise<SearchResponse> {
  const url = new URL(`${API_BASE}/search`);
  
  if (params.q) url.searchParams.set('q', params.q);
  if (params.price_min) url.searchParams.set('price_min', params.price_min.toString());
  if (params.price_max) url.searchParams.set('price_max', params.price_max.toString());
  if (params.cuisine?.length) {
    params.cuisine.forEach(c => url.searchParams.append('cuisine', c));
  }
  if (params.sort_by) url.searchParams.set('sort_by', params.sort_by);
  if (params.sort_order) url.searchParams.set('sort_order', params.sort_order);
  if (params.limit) url.searchParams.set('limit', params.limit.toString());
  
  const urlString = url.toString();
  console.log("API_BASE:", API_BASE);
  console.log("Full URL:", urlString);
  console.log("About to fetch:", urlString);

  const response = await fetch(urlString);
  console.log("Response URL:", response.url);
  console.log("Response status:", response.status);
  if (!response.ok) {
    throw new Error('Failed to fetch restaurants');
  }
  return response.json();
}

/**
 * Fetch trending search queries.
 */
async function fetchTrending(): Promise<string[]> {
  const response = await fetch(`${API_BASE}/trending-queries`);
  if (!response.ok) {
    // Fallback to old endpoint
    const fallbackResponse = await fetch(`${API_BASE}/trending`);
    if (!fallbackResponse.ok) {
      throw new Error('Failed to fetch trending');
    }
    return fallbackResponse.json();
  }
  return response.json();
}

/**
 * Fetch trending restaurants.
 */
async function fetchTrendingRestaurants(limit: number = 10): Promise<Restaurant[]> {
  const response = await fetch(`${API_BASE}/trending?limit=${limit}`);
  if (!response.ok) {
    throw new Error('Failed to fetch trending restaurants');
  }
  return response.json();
}

/**
 * Fetch available cuisines.
 */
async function fetchCuisines(): Promise<string[]> {
  const response = await fetch(`${API_BASE}/cuisines`);
  if (!response.ok) {
    throw new Error('Failed to fetch cuisines');
  }
  return response.json();
}

/**
 * Parse URL search params into SearchParams object.
 */
function parseSearchParams(searchParams: URLSearchParams): SearchParams {
  return {
    q: searchParams.get('q') || undefined,
    price_min: searchParams.get('price_min') ? Number(searchParams.get('price_min')) : undefined,
    price_max: searchParams.get('price_max') ? Number(searchParams.get('price_max')) : undefined,
    cuisine: searchParams.getAll('cuisine').length > 0 ? searchParams.getAll('cuisine') : undefined,
    sort_by: (searchParams.get('sort_by') as SearchParams['sort_by']) || 'buzz_score',
    sort_order: (searchParams.get('sort_order') as SearchParams['sort_order']) || 'desc',
  };
}

/**
 * Hook to fetch restaurants based on URL search params.
 * Uses TanStack Query for caching and state management.
 */
export function useRestaurants() {
  const [searchParams] = useSearchParams();
  const params = parseSearchParams(searchParams);

  return useQuery({
    queryKey: ['restaurants', params],
    queryFn: () => fetchRestaurants(params),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Hook to update search params in URL.
 * Returns a function to update params while preserving existing ones.
 */
export function useSearchFilters() {
  const [searchParams, setSearchParams] = useSearchParams();
  
  const updateParams = (updates: Partial<SearchParams>) => {
    const newParams = new URLSearchParams(searchParams);
    
    Object.entries(updates).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') {
        newParams.delete(key);
      } else if (Array.isArray(value)) {
        newParams.delete(key);
        value.forEach(v => newParams.append(key, v));
      } else {
        newParams.set(key, String(value));
      }
    });
    
    setSearchParams(newParams);
  };

  const clearParams = () => {
    setSearchParams(new URLSearchParams());
  };

  return {
    params: parseSearchParams(searchParams),
    updateParams,
    clearParams,
  };
}

/**
 * Hook to fetch trending search queries.
 */
export function useTrending() {
  return useQuery({
    queryKey: ['trending'],
    queryFn: fetchTrending,
    staleTime: 1000 * 60 * 30, // 30 minutes
  });
}

/**
 * Hook to fetch trending restaurants.
 */
export function useTrendingRestaurants(limit: number = 10) {
  return useQuery({
    queryKey: ['trending-restaurants', limit],
    queryFn: () => fetchTrendingRestaurants(limit),
    staleTime: 1000 * 60 * 10, // 10 minutes
  });
}

/**
 * Hook to fetch cuisines.
 */
export function useCuisines() {
  return useQuery({
    queryKey: ['cuisines'],
    queryFn: fetchCuisines,
    staleTime: 1000 * 60 * 60, // 1 hour
  });
}
