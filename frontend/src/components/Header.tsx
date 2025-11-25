import { useState } from 'react';
import './Header.css';

type HeaderProps = {
  city: string;
  onCityChange: (city: string) => void;
  onSearch: (query: string) => void;
};

const CITIES = ['Toronto', 'Vancouver', 'Montreal', 'Calgary', 'Ottawa'];

export function Header({ city, onCityChange, onSearch }: HeaderProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [showCityDropdown, setShowCityDropdown] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(searchQuery);
  };

  return (
    <header className="header">
      <div className="header__brand">
        <div className="header__logo">
          <span className="header__logo-icon">🔥</span>
          <span className="header__logo-text">Beli Buzz</span>
        </div>
        <div className="header__city-selector">
          <button
            className="header__city-btn"
            onClick={() => setShowCityDropdown(!showCityDropdown)}
          >
            <span className="header__city-icon">📍</span>
            <span>{city}</span>
            <span className="header__chevron">▼</span>
          </button>
          {showCityDropdown && (
            <div className="header__city-dropdown">
              {CITIES.map((c) => (
                <button
                  key={c}
                  className={`header__city-option ${c === city ? 'header__city-option--active' : ''}`}
                  onClick={() => {
                    onCityChange(c);
                    setShowCityDropdown(false);
                  }}
                >
                  {c}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <form className="header__search" onSubmit={handleSearch}>
        <span className="header__search-icon">🔍</span>
        <input
          type="text"
          className="header__search-input"
          placeholder="Search restaurants, cuisines..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </form>

      <div className="header__actions">
        <button className="header__action-btn header__action-btn--ghost">
          <span>📋</span>
          <span>My Lists</span>
        </button>
        <button className="header__action-btn header__action-btn--primary">
          <span>👤</span>
          <span>Sign In</span>
        </button>
      </div>
    </header>
  );
}
