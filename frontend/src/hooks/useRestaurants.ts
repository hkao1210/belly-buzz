import { useEffect, useState, useMemo, useCallback } from 'react';
import axios from 'axios';
import type { Restaurant, CuisineCategory, SortOption, DataResponse, Comment } from '../types';

const DATA_SOURCE = import.meta.env.VITE_TRENDING_DATA_URL ?? '/data.json';

type UseRestaurantsReturn = {
  restaurants: Restaurant[];
  filteredRestaurants: Restaurant[];
  selectedRestaurant: Restaurant | null;
  isLoading: boolean;
  error: string | null;
  lastRun: string | null;
  totalMentions: number;
  activeCategory: CuisineCategory;
  sortBy: SortOption;
  searchQuery: string;
  likedRestaurants: Set<string>;
  savedRestaurants: Set<string>;
  selectRestaurant: (id: string) => void;
  setActiveCategory: (category: CuisineCategory) => void;
  setSortBy: (sort: SortOption) => void;
  setSearchQuery: (query: string) => void;
  toggleLike: (id: string) => void;
  toggleSave: (id: string) => void;
  addComment: (restaurantId: string, text: string) => void;
};

export function useRestaurants(): UseRestaurantsReturn {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [lastRun, setLastRun] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState<CuisineCategory>('all');
  const [sortBy, setSortBy] = useState<SortOption>('buzz');
  const [searchQuery, setSearchQuery] = useState('');
  const [likedRestaurants, setLikedRestaurants] = useState<Set<string>>(() => {
    const saved = localStorage.getItem('beli-buzz-liked');
    return saved ? new Set(JSON.parse(saved)) : new Set();
  });
  const [savedRestaurants, setSavedRestaurants] = useState<Set<string>>(() => {
    const saved = localStorage.getItem('beli-buzz-saved');
    return saved ? new Set(JSON.parse(saved)) : new Set();
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const response = await axios.get<DataResponse>(DATA_SOURCE, {
          headers: { 'Cache-Control': 'no-cache' },
        });
        
        // Add trending rank
        const sorted = [...response.data.restaurants]
          .sort((a, b) => b.buzz_score - a.buzz_score)
          .map((r, i) => ({ ...r, trending_rank: i + 1 }));
        
        setRestaurants(sorted);
        setLastRun(response.data.date);
        setSelectedId(sorted[0]?.id ?? null);
        setError(null);
      } catch (err) {
        console.error(err);
        setError('Unable to fetch the latest buzz. Showing the last cached version.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  // Persist likes/saves to localStorage
  useEffect(() => {
    localStorage.setItem('beli-buzz-liked', JSON.stringify([...likedRestaurants]));
  }, [likedRestaurants]);

  useEffect(() => {
    localStorage.setItem('beli-buzz-saved', JSON.stringify([...savedRestaurants]));
  }, [savedRestaurants]);

  const filteredRestaurants = useMemo(() => {
    let result = [...restaurants];

    // Filter by category
    if (activeCategory === 'trending') {
      result = result.slice(0, 10);
    } else if (activeCategory !== 'all') {
      result = result.filter(r => 
        r.category.includes(activeCategory) || 
        r.cuisine_type.toLowerCase() === activeCategory
      );
    }

    // Filter by search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(r =>
        r.name.toLowerCase().includes(query) ||
        r.summary.toLowerCase().includes(query) ||
        r.cuisine_type.toLowerCase().includes(query)
      );
    }

    // Sort
    switch (sortBy) {
      case 'sentiment':
        result.sort((a, b) => b.sentiment - a.sentiment);
        break;
      case 'mentions':
        result.sort((a, b) => b.mentions - a.mentions);
        break;
      case 'likes':
        result.sort((a, b) => b.user_likes - a.user_likes);
        break;
      case 'newest':
        result.sort((a, b) => (b.is_new ? 1 : 0) - (a.is_new ? 1 : 0));
        break;
      case 'buzz':
      default:
        result.sort((a, b) => b.buzz_score - a.buzz_score);
    }

    return result;
  }, [restaurants, activeCategory, sortBy, searchQuery]);

  const selectedRestaurant = useMemo(() => 
    restaurants.find(r => r.id === selectedId) ?? restaurants[0] ?? null,
    [restaurants, selectedId]
  );

  const totalMentions = useMemo(() => 
    restaurants.reduce((sum, r) => sum + r.mentions, 0),
    [restaurants]
  );

  const selectRestaurant = useCallback((id: string) => {
    setSelectedId(id);
  }, []);

  const toggleLike = useCallback((id: string) => {
    setLikedRestaurants(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
        // Decrement like count in restaurant
        setRestaurants(rs => rs.map(r => 
          r.id === id ? { ...r, user_likes: Math.max(0, r.user_likes - 1) } : r
        ));
      } else {
        next.add(id);
        // Increment like count in restaurant
        setRestaurants(rs => rs.map(r => 
          r.id === id ? { ...r, user_likes: r.user_likes + 1 } : r
        ));
      }
      return next;
    });
  }, []);

  const toggleSave = useCallback((id: string) => {
    setSavedRestaurants(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
        setRestaurants(rs => rs.map(r => 
          r.id === id ? { ...r, user_saves: Math.max(0, r.user_saves - 1) } : r
        ));
      } else {
        next.add(id);
        setRestaurants(rs => rs.map(r => 
          r.id === id ? { ...r, user_saves: r.user_saves + 1 } : r
        ));
      }
      return next;
    });
  }, []);

  const addComment = useCallback((restaurantId: string, text: string) => {
    const newComment: Comment = {
      id: `comment-${Date.now()}`,
      userId: 'guest',
      userName: 'Guest User',
      text,
      timestamp: new Date().toISOString(),
      likes: 0,
    };
    
    setRestaurants(rs => rs.map(r => 
      r.id === restaurantId 
        ? { ...r, comments: [newComment, ...r.comments] }
        : r
    ));
  }, []);

  return {
    restaurants,
    filteredRestaurants,
    selectedRestaurant,
    isLoading,
    error,
    lastRun,
    totalMentions,
    activeCategory,
    sortBy,
    searchQuery,
    likedRestaurants,
    savedRestaurants,
    selectRestaurant,
    setActiveCategory,
    setSortBy,
    setSearchQuery,
    toggleLike,
    toggleSave,
    addComment,
  };
}
