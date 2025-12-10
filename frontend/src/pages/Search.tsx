import { useNavigate } from 'react-router-dom';
import {
  Search as SearchIcon,
  Map as MapIcon,
  List,
  Filter,
  X,
  ArrowLeft,
  Loader2,
  Flame,
  Star,
  TrendingUp,
  MessageCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { RestaurantCard } from '@/components/RestaurantCard';
import { RestaurantMap } from '@/components/RestaurantMap';
import { useRestaurants, useSearchFilters } from '@/hooks';
import { useState } from 'react';
import type { Restaurant, SearchParams } from '@/types';

type SortOption = {
  value: SearchParams['sort_by'];
  label: string;
  icon: React.ReactNode;
};

const SORT_OPTIONS: SortOption[] = [
  { value: 'buzz_score', label: 'Buzz', icon: <Flame className="h-3 w-3" /> },
  { value: 'rating', label: 'Rating', icon: <Star className="h-3 w-3" /> },
  { value: 'viral_score', label: 'Viral', icon: <TrendingUp className="h-3 w-3" /> },
  { value: 'total_mentions', label: 'Mentions', icon: <MessageCircle className="h-3 w-3" /> },
];

/**
 * Search results page with split view layout.
 * Left: scrollable restaurant list
 * Right: Google Maps with markers
 * Mobile: list only with floating "Show Map" button
 */
export function Search() {
  const navigate = useNavigate();
  const { data, isLoading, error } = useRestaurants();
  const { params, updateParams, clearParams } = useSearchFilters();
  const [showMobileMap, setShowMobileMap] = useState(false);
  const [localQuery, setLocalQuery] = useState(params.q || '');
  const [selectedRestaurantId, setSelectedRestaurantId] = useState<string | undefined>();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    updateParams({ q: localQuery });
  };

  const handlePriceFilter = (tier: number) => {
    if (params.price_max === tier && params.price_min === tier) {
      updateParams({ price_min: undefined, price_max: undefined });
    } else {
      updateParams({ price_min: tier, price_max: tier });
    }
  };

  const handleSortChange = (sortBy: SearchParams['sort_by']) => {
    // Toggle sort order if same field, otherwise default to desc
    const newOrder = params.sort_by === sortBy && params.sort_order === 'desc' ? 'asc' : 'desc';
    updateParams({ sort_by: sortBy, sort_order: newOrder });
  };

  const handleRestaurantClick = (restaurant: Restaurant) => {
    setSelectedRestaurantId(restaurant.id);
  };

  const activeFiltersCount =
    (params.price_min ? 1 : 0) +
    (params.cuisine?.length || 0);

  const restaurants = data?.results || [];

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b-2 border-border bg-background px-4 py-3">
        <div className="mx-auto flex max-w-7xl items-center gap-4">
          {/* Back Button */}
          <Button
            variant="neutral"
            size="icon"
            onClick={() => navigate('/')}
            className="flex-shrink-0"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>

          {/* Search Bar */}
          <form onSubmit={handleSearch} className="flex flex-1 gap-2">
            <div className="relative flex-1">
              <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Best ramen in Toronto..."
                value={localQuery}
                onChange={(e) => setLocalQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button type="submit">Search</Button>
          </form>

          {/* Filter Toggle */}
          <Button variant="neutral" className="relative flex-shrink-0">
            <Filter className="mr-2 h-4 w-4" />
            Filters
            {activeFiltersCount > 0 && (
              <Badge className="ml-2">{activeFiltersCount}</Badge>
            )}
          </Button>
        </div>

        {/* Filter Bar */}
        <div className="mx-auto mt-3 flex max-w-7xl items-center gap-2 overflow-x-auto pb-1">
          {/* Sort Options */}
          <span className="text-xs font-medium text-muted-foreground mr-1">Sort:</span>
          {SORT_OPTIONS.map((option) => (
            <Badge
              key={option.value}
              variant={params.sort_by === option.value ? 'default' : 'neutral'}
              className="cursor-pointer whitespace-nowrap gap-1"
              onClick={() => handleSortChange(option.value)}
            >
              {option.icon}
              {option.label}
              {params.sort_by === option.value && (
                <span className="text-[10px]">
                  {params.sort_order === 'desc' ? '↓' : '↑'}
                </span>
              )}
            </Badge>
          ))}

          <div className="w-px h-5 bg-border mx-1" />

          {/* Price Filters */}
          <span className="text-xs font-medium text-muted-foreground mr-1">Price:</span>
          {[1, 2, 3, 4].map((tier) => (
            <Badge
              key={tier}
              variant={params.price_min === tier ? 'default' : 'neutral'}
              className="cursor-pointer whitespace-nowrap"
              onClick={() => handlePriceFilter(tier)}
            >
              {'$'.repeat(tier)}
            </Badge>
          ))}

          {/* Clear Filters */}
          {activeFiltersCount > 0 && (
            <Badge
              variant="neutral"
              className="cursor-pointer whitespace-nowrap ml-2"
              onClick={clearParams}
            >
              <X className="mr-1 h-3 w-3" />
              Clear
            </Badge>
          )}
        </div>
      </header>

      {/* Main Content - Split View */}
      <main className="flex flex-1 overflow-hidden">
        {/* Left Panel - Restaurant List */}
        <div
          className={`flex-1 overflow-y-auto p-4 ${
            showMobileMap ? 'hidden md:block' : ''
          }`}
        >
          {/* Results Count */}
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-heading text-lg font-bold">
              {isLoading ? (
                'Searching...'
              ) : (
                <>
                  {data?.total || 0} results
                  {params.q && (
                    <span className="font-normal text-muted-foreground">
                      {' '}
                      for "{params.q}"
                    </span>
                  )}
                </>
              )}
            </h2>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="rounded-base border-2 border-border bg-red-50 p-4 text-center">
              <p className="text-sm text-red-600">
                Failed to load restaurants. Please try again.
              </p>
              <Button
                variant="neutral"
                size="sm"
                className="mt-2"
                onClick={() => window.location.reload()}
              >
                Retry
              </Button>
            </div>
          )}

          {/* Restaurant Cards */}
          {!isLoading && !error && (
            <div className="space-y-4">
              {restaurants.map((restaurant) => (
                <RestaurantCard
                  key={restaurant.id}
                  restaurant={restaurant}
                  onClick={() => handleRestaurantClick(restaurant)}
                />
              ))}
              {restaurants.length === 0 && (
                <div className="py-12 text-center">
                  <p className="text-lg font-medium">No restaurants found</p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Try adjusting your search or filters
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Panel - Google Map */}
        <div
          className={`hidden w-1/2 border-l-2 border-border lg:block ${
            showMobileMap ? '!block w-full lg:w-1/2' : ''
          }`}
        >
          <RestaurantMap
            restaurants={restaurants}
            selectedId={selectedRestaurantId}
            onMarkerClick={handleRestaurantClick}
            className="h-full w-full"
          />
        </div>
      </main>

      {/* Mobile Map Toggle Button */}
      <div className="fixed bottom-4 left-1/2 z-50 -translate-x-1/2 lg:hidden">
        <Button
          onClick={() => setShowMobileMap(!showMobileMap)}
          className="shadow-lg"
        >
          {showMobileMap ? (
            <>
              <List className="mr-2 h-4 w-4" />
              Show List
            </>
          ) : (
            <>
              <MapIcon className="mr-2 h-4 w-4" />
              Show Map
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
