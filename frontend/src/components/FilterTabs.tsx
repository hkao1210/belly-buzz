import type { FilterCategory, CuisineCategory, SortOption } from '../types';
import './FilterTabs.css';

type FilterTabsProps = {
  categories: FilterCategory[];
  activeCategory: CuisineCategory;
  onCategoryChange: (category: CuisineCategory) => void;
  sortBy: SortOption;
  onSortChange: (sort: SortOption) => void;
  totalCount: number;
};

const SORT_OPTIONS: { id: SortOption; label: string }[] = [
  { id: 'buzz', label: 'Buzz Score' },
  { id: 'sentiment', label: 'Rating' },
  { id: 'mentions', label: 'Most Mentioned' },
  { id: 'likes', label: 'Most Liked' },
  { id: 'newest', label: 'Newest' },
];

export function FilterTabs({
  categories,
  activeCategory,
  onCategoryChange,
  sortBy,
  onSortChange,
  totalCount,
}: FilterTabsProps) {
  return (
    <div className="filter-tabs">
      <div className="filter-tabs__categories">
        {categories.map((cat) => (
          <button
            key={cat.id}
            className={`filter-tabs__tab ${activeCategory === cat.id ? 'filter-tabs__tab--active' : ''}`}
            onClick={() => onCategoryChange(cat.id)}
          >
            <span className="filter-tabs__emoji">{cat.emoji}</span>
            <span className="filter-tabs__label">{cat.label}</span>
          </button>
        ))}
      </div>

      <div className="filter-tabs__controls">
        <span className="filter-tabs__count">{totalCount} spots</span>
        <select
          className="filter-tabs__sort"
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value as SortOption)}
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.id} value={opt.id}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
