import './StatsBar.css';

type StatsBarProps = {
  restaurantCount: number;
  totalMentions: number;
  lastRun: string | null;
  isLoading: boolean;
};

export function StatsBar({ restaurantCount, totalMentions, lastRun, isLoading }: StatsBarProps) {
  const formatLastRun = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffHours = Math.floor((now.getTime() - date.getTime()) / 3600000);
    
    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    return new Intl.DateTimeFormat('en-CA', {
      month: 'short',
      day: 'numeric',
    }).format(date);
  };

  return (
    <div className="stats-bar">
      <div className="stats-bar__item">
        <span className="stats-bar__value">{restaurantCount}</span>
        <span className="stats-bar__label">Restaurants</span>
      </div>
      <div className="stats-bar__item">
        <span className="stats-bar__value">{totalMentions}</span>
        <span className="stats-bar__label">Mentions</span>
      </div>
      <div className="stats-bar__item">
        <span className="stats-bar__value">{lastRun ? formatLastRun(lastRun) : '—'}</span>
        <span className="stats-bar__label">Updated</span>
      </div>
      <div className="stats-bar__status">
        <span className={`stats-bar__indicator ${isLoading ? 'stats-bar__indicator--loading' : ''}`} />
        <span className="stats-bar__status-text">{isLoading ? 'Syncing' : 'Live'}</span>
      </div>
    </div>
  );
}
