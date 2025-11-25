export type Location = {
  lat: number;
  lng: number;
  address?: string;
};

export type Comment = {
  id: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  text: string;
  timestamp: string;
  likes: number;
};

export type Restaurant = {
  id: string;
  name: string;
  buzz_score: number;
  sentiment: number;
  mentions: number;
  summary: string;
  location: Location | null;
  sources?: string[];
  // New fields
  cuisine_type: string;
  category: string[];
  price_range: 1 | 2 | 3 | 4;
  photos?: string[];
  user_likes: number;
  user_saves: number;
  comments: Comment[];
  trending_rank?: number;
  is_new?: boolean;
  hours?: {
    open: string;
    close: string;
  };
};

export type CuisineCategory = 
  | 'all'
  | 'trending'
  | 'ramen'
  | 'thai'
  | 'mexican'
  | 'burgers'
  | 'pizza'
  | 'sushi'
  | 'korean'
  | 'indian'
  | 'italian'
  | 'chinese'
  | 'vietnamese'
  | 'seafood'
  | 'vegetarian';

export type FilterCategory = {
  id: CuisineCategory;
  label: string;
  emoji: string;
};

export type SortOption = 'buzz' | 'sentiment' | 'mentions' | 'likes' | 'newest';

export type DataResponse = {
  date: string;
  restaurants: Restaurant[];
  categories: FilterCategory[];
};

export type User = {
  id: string;
  name: string;
  avatar?: string;
  savedRestaurants: string[];
  likedRestaurants: string[];
};
