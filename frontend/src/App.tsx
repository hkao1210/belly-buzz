import { APIProvider, Map, AdvancedMarker, Pin } from '@vis.gl/react-google-maps';
import { Header, FilterTabs, RestaurantCard, RestaurantDetail, StatsBar } from './components';
import { useRestaurants } from './hooks';
import { FILTER_CATEGORIES } from './utils';
import './App.css';

const FALLBACK_CENTER = { lat: 43.6532, lng: -79.3832 };

function App() {
  const {
    filteredRestaurants,
    selectedRestaurant,
    isLoading,
    error,
    lastRun,
    totalMentions,
    activeCategory,
    sortBy,
    likedRestaurants,
    savedRestaurants,
    selectRestaurant,
    setActiveCategory,
    setSortBy,
    setSearchQuery,
    toggleLike,
    toggleSave,
    addComment,
  } = useRestaurants();

  return (
    <div className="app">
      <Header
        city="Toronto"
        onCityChange={() => {}}
        onSearch={setSearchQuery}
      />
      
      <div className="app__content">
        <aside className="app__sidebar">
          <StatsBar
            restaurantCount={filteredRestaurants.length}
            totalMentions={totalMentions}
            lastRun={lastRun}
            isLoading={isLoading}
          />

          <FilterTabs
            categories={FILTER_CATEGORIES}
            activeCategory={activeCategory}
            onCategoryChange={setActiveCategory}
            sortBy={sortBy}
            onSortChange={setSortBy}
            totalCount={filteredRestaurants.length}
          />

          {error && <div className="app__alert">{error}</div>}

          <div className="app__restaurant-list">
            {filteredRestaurants.map((restaurant, index) => (
              <RestaurantCard
                key={restaurant.id}
                restaurant={restaurant}
                isSelected={selectedRestaurant?.id === restaurant.id}
                onSelect={() => selectRestaurant(restaurant.id)}
                onLike={() => toggleLike(restaurant.id)}
                onSave={() => toggleSave(restaurant.id)}
                isLiked={likedRestaurants.has(restaurant.id)}
                isSaved={savedRestaurants.has(restaurant.id)}
                rank={activeCategory === 'trending' || activeCategory === 'all' ? index + 1 : undefined}
              />
            ))}
            
            {filteredRestaurants.length === 0 && !isLoading && (
              <div className="app__empty">
                <span className="app__empty-icon">🔍</span>
                <p>No restaurants found matching your criteria.</p>
              </div>
            )}
          </div>
        </aside>

        <main className="app__main">
          <div className="app__map">
            <APIProvider apiKey={import.meta.env.VITE_GOOGLE_MAPS_API_KEY || ''}>
              <Map
                defaultCenter={FALLBACK_CENTER}
                center={selectedRestaurant?.location ?? FALLBACK_CENTER}
                defaultZoom={13}
                mapId="BeliBuzzMap"
                style={{ width: '100%', height: '100%' }}
              >
                {filteredRestaurants.map((r) => (
                  r.location && (
                    <AdvancedMarker key={r.id} position={r.location} onClick={() => selectRestaurant(r.id)}>
                      <Pin
                        background={selectedRestaurant?.id === r.id ? '#ea580c' : '#dc2626'}
                        borderColor={'#fff'}
                        glyphColor={'#fff'}
                      />
                    </AdvancedMarker>
                  )
                ))}
              </Map>
            </APIProvider>
          </div>
          
          {selectedRestaurant ? (
            <div className="app__detail-panel">
              <RestaurantDetail
                restaurant={selectedRestaurant}
                isLiked={likedRestaurants.has(selectedRestaurant.id)}
                isSaved={savedRestaurants.has(selectedRestaurant.id)}
                onLike={() => toggleLike(selectedRestaurant.id)}
                onSave={() => toggleSave(selectedRestaurant.id)}
                onAddComment={(text) => addComment(selectedRestaurant.id, text)}
              />
            </div>
          ) : (
            <div className="app__no-selection">
              <span className="app__no-selection-icon">👆</span>
              <p className="app__no-selection-text">
                Select a restaurant from the list to see details and community discussion
              </p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
