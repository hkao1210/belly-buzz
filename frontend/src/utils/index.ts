import type { CuisineCategory, FilterCategory } from '../types';

export const FILTER_CATEGORIES: FilterCategory[] = [
  { id: 'all', label: 'All', emoji: '🍽️' },
  { id: 'trending', label: 'Trending', emoji: '🔥' },
  { id: 'ramen', label: 'Ramen', emoji: '🍜' },
  { id: 'thai', label: 'Thai', emoji: '🥘' },
  { id: 'mexican', label: 'Mexican', emoji: '🌮' },
  { id: 'burgers', label: 'Burgers', emoji: '🍔' },
  { id: 'sushi', label: 'Sushi', emoji: '🍣' },
  { id: 'korean', label: 'Korean', emoji: '🥢' },
  { id: 'indian', label: 'Indian', emoji: '🍛' },
  { id: 'italian', label: 'Italian', emoji: '🍝' },
];

export const getCategoryLabel = (id: CuisineCategory): string => {
  return FILTER_CATEGORIES.find(c => c.id === id)?.label ?? id;
};

export const getPriceDisplay = (price: 1 | 2 | 3 | 4): string => {
  return '$'.repeat(price);
};

export const formatDate = (dateStr: string): string => {
  return new Intl.DateTimeFormat('en-CA', {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'America/Toronto',
  }).format(new Date(dateStr));
};

export const formatRelativeTime = (dateStr: string): string => {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(dateStr);
};

export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trim() + '...';
};
