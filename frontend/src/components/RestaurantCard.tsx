import { Star, MapPin, DollarSign, ChefHat, TrendingUp, MessageCircle, Flame } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Restaurant } from '@/types';

interface RestaurantCardProps {
  restaurant: Restaurant;
  onClick?: () => void;
}

/**
 * Price tier display component.
 */
function PriceTier({ tier }: { tier: number }) {
  return (
    <span className="flex items-center gap-0.5 text-sm font-bold">
      {Array.from({ length: 4 }).map((_, i) => (
        <DollarSign
          key={i}
          className={`h-3.5 w-3.5 ${
            i < tier ? 'text-foreground' : 'text-muted-foreground/30'
          }`}
        />
      ))}
    </span>
  );
}

/**
 * Star rating display component.
 */
function Rating({ rating }: { rating?: number }) {
  if (!rating) return null;
  
  return (
    <div className="flex items-center gap-1.5">
      <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
      <span className="font-bold">{rating.toFixed(1)}</span>
    </div>
  );
}

/**
 * Buzz score display component with fire icon.
 */
function BuzzScore({ score }: { score: number }) {
  // Color based on score (0-20 range)
  const getScoreColor = () => {
    if (score >= 12) return 'text-orange-500';
    if (score >= 8) return 'text-amber-500';
    return 'text-muted-foreground';
  };
  
  return (
    <div className={`flex items-center gap-1 ${getScoreColor()}`}>
      <Flame className="h-4 w-4" />
      <span className="font-bold">{score.toFixed(1)}</span>
    </div>
  );
}

/**
 * Sentiment score badge component.
 */
function SentimentBadge({ score }: { score: number }) {
  const getColor = () => {
    if (score >= 0.7) return 'bg-green-500';
    if (score >= 0.4) return 'bg-yellow-500';
    return 'bg-red-500';
  };
  
  const getLabel = () => {
    if (score >= 0.7) return '😊';
    if (score >= 0.4) return '😐';
    return '😞';
  };
  
  return (
    <Badge className={`${getColor()} text-white border-0`}>
      {getLabel()} {(score * 100).toFixed(0)}%
    </Badge>
  );
}

/**
 * Restaurant card component with Neobrutalism styling.
 * Displays restaurant info in a bold, eye-catching card format.
 */
export function RestaurantCard({ restaurant, onClick }: RestaurantCardProps) {
  return (
    <Card
      className="cursor-pointer transition-transform hover:translate-x-1 hover:-translate-y-1"
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <CardTitle className="text-lg leading-tight truncate">{restaurant.name}</CardTitle>
              {restaurant.is_trending && (
                <Badge variant="default" className="flex-shrink-0 bg-orange-500 text-white">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  Hot
                </Badge>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3 flex-shrink-0">
            <BuzzScore score={restaurant.buzz_score} />
            <SentimentBadge score={restaurant.sentiment_score} />
          </div>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <MapPin className="h-3.5 w-3.5 flex-shrink-0" />
          <span className="truncate">
            {restaurant.address}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Cuisine Tags */}
        {restaurant.cuisine_tags && restaurant.cuisine_tags.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {restaurant.cuisine_tags.slice(0, 4).map((tag) => (
              <Badge key={tag} variant="default" className="text-xs">
                {tag}
              </Badge>
            ))}
            {restaurant.cuisine_tags.length > 4 && (
              <Badge variant="neutral" className="text-xs">
                +{restaurant.cuisine_tags.length - 4}
              </Badge>
            )}
          </div>
        )}

        {/* Price & Metrics Row */}
        <div className="flex items-center justify-between">
          <PriceTier tier={restaurant.price_tier} />
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <div className="flex items-center gap-1" title="Mentions">
              <MessageCircle className="h-3.5 w-3.5" />
              <span>{restaurant.total_mentions}</span>
            </div>
          </div>
        </div>

        {/* Vibe / Review Summary */}
        {(restaurant.vibe || restaurant.review?.summary) && (
          <p className="text-sm leading-relaxed text-muted-foreground line-clamp-2">
            {restaurant.review?.summary || restaurant.vibe}
          </p>
        )}

        {/* Recommended Dishes */}
        {restaurant.review?.recommended_dishes && restaurant.review.recommended_dishes.length > 0 && (
          <div className="flex items-start gap-2 pt-1">
            <ChefHat className="h-4 w-4 flex-shrink-0 text-muted-foreground mt-0.5" />
            <p className="text-sm text-muted-foreground">
              <span className="font-medium text-foreground">Try:</span>{' '}
              {restaurant.review.recommended_dishes.slice(0, 3).join(', ')}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
