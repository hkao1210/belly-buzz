import { useState } from 'react';
import type { Restaurant, Comment } from '../types';
import { getPriceDisplay, formatRelativeTime } from '../utils';
import './RestaurantDetail.css';

type RestaurantDetailProps = {
  restaurant: Restaurant;
  isLiked: boolean;
  isSaved: boolean;
  onLike: () => void;
  onSave: () => void;
  onAddComment: (text: string) => void;
};

export function RestaurantDetail({
  restaurant,
  isLiked,
  isSaved,
  onLike,
  onSave,
  onAddComment,
}: RestaurantDetailProps) {
  const [newComment, setNewComment] = useState('');
  const [showAllComments, setShowAllComments] = useState(false);

  const handleSubmitComment = (e: React.FormEvent) => {
    e.preventDefault();
    if (newComment.trim()) {
      onAddComment(newComment.trim());
      setNewComment('');
    }
  };

  const displayedComments = showAllComments
    ? restaurant.comments
    : restaurant.comments.slice(0, 3);

  const heroImage = restaurant.photos?.[0];

  return (
    <div className="restaurant-detail">
      {heroImage && (
        <div className="restaurant-detail__hero">
          <img 
            src={heroImage} 
            alt={restaurant.name} 
            className="restaurant-detail__hero-image"
          />
          <div className="restaurant-detail__hero-overlay" />
        </div>
      )}
      
      <div className="restaurant-detail__content">
        <div className="restaurant-detail__header">
          <div className="restaurant-detail__badge">🔥 Trending Now</div>
          <h2 className="restaurant-detail__name">{restaurant.name}</h2>
          <p className="restaurant-detail__summary">{restaurant.summary}</p>
          
          <div className="restaurant-detail__meta">
            <span className="restaurant-detail__cuisine">🍽️ {restaurant.cuisine_type}</span>
            <span className="restaurant-detail__separator">•</span>
            <span className="restaurant-detail__price">{getPriceDisplay(restaurant.price_range)}</span>
            {restaurant.hours && (
              <>
                <span className="restaurant-detail__separator">•</span>
                <span className="restaurant-detail__hours">
                  🕐 {restaurant.hours.open} - {restaurant.hours.close}
                </span>
              </>
            )}
          </div>
        </div>

        <div className="restaurant-detail__scores">
          <div className="restaurant-detail__score">
            <span className="restaurant-detail__score-icon">🔥</span>
            <div className="restaurant-detail__score-info">
              <span className="restaurant-detail__score-value">{restaurant.buzz_score.toFixed(1)}</span>
              <span className="restaurant-detail__score-label">Buzz</span>
            </div>
          </div>
          <div className="restaurant-detail__score">
            <span className="restaurant-detail__score-icon">❤️</span>
            <div className="restaurant-detail__score-info">
              <span className="restaurant-detail__score-value">{restaurant.sentiment.toFixed(1)}</span>
              <span className="restaurant-detail__score-label">Rating</span>
            </div>
          </div>
          <div className="restaurant-detail__score">
            <span className="restaurant-detail__score-icon">💬</span>
            <div className="restaurant-detail__score-info">
              <span className="restaurant-detail__score-value">{restaurant.mentions}</span>
              <span className="restaurant-detail__score-label">Mentions</span>
            </div>
          </div>
        </div>

        {restaurant.location?.address && (
          <div className="restaurant-detail__location">
            <span className="restaurant-detail__location-icon">📍</span>
            <span>{restaurant.location.address}</span>
          </div>
        )}

        {restaurant.sources && restaurant.sources.length > 0 && (
          <div className="restaurant-detail__sources">
            <span className="restaurant-detail__sources-label">Mentioned on:</span>
            {restaurant.sources.map((src, i) => (
              <span key={i} className="restaurant-detail__source-tag">{src}</span>
            ))}
          </div>
        )}

        <div className="restaurant-detail__actions">
          <button
            className={`restaurant-detail__action ${isLiked ? 'restaurant-detail__action--liked' : ''}`}
            onClick={onLike}
          >
            <span>{isLiked ? '❤️' : '🤍'}</span>
            <span>{isLiked ? 'Liked' : 'Like'}</span>
            <span className="restaurant-detail__action-count">{restaurant.user_likes}</span>
          </button>
          <button
            className={`restaurant-detail__action ${isSaved ? 'restaurant-detail__action--saved' : ''}`}
            onClick={onSave}
          >
            <span>{isSaved ? '🔖' : '📌'}</span>
            <span>{isSaved ? 'Saved' : 'Save'}</span>
            <span className="restaurant-detail__action-count">{restaurant.user_saves}</span>
          </button>
          <a
            className="restaurant-detail__action"
            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(restaurant.name + ' ' + (restaurant.location?.address || ''))}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            <span>🗺️</span>
            <span>Directions</span>
          </a>
        </div>

        <div className="restaurant-detail__comments">
          <h3 className="restaurant-detail__comments-title">
            💬 Community Discussion
            <span className="restaurant-detail__comments-count">{restaurant.comments.length}</span>
          </h3>
          
          <form className="restaurant-detail__comment-form" onSubmit={handleSubmitComment}>
            <input
              type="text"
              className="restaurant-detail__comment-input"
              placeholder="Share your thoughts..."
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
            />
            <button
              type="submit"
              className="restaurant-detail__comment-submit"
              disabled={!newComment.trim()}
            >
              Post
            </button>
          </form>

          <div className="restaurant-detail__comments-list">
            {displayedComments.map((comment) => (
              <CommentItem key={comment.id} comment={comment} />
            ))}
          </div>

          {restaurant.comments.length > 3 && (
            <button
              className="restaurant-detail__comments-toggle"
              onClick={() => setShowAllComments(!showAllComments)}
            >
              {showAllComments ? 'Show less' : `View all ${restaurant.comments.length} comments`}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function CommentItem({ comment }: { comment: Comment }) {
  return (
    <div className="comment">
      <div className="comment__avatar">
        {comment.userAvatar ? (
          <img src={comment.userAvatar} alt={comment.userName} />
        ) : (
          <span>{comment.userName[0].toUpperCase()}</span>
        )}
      </div>
      <div className="comment__content">
        <div className="comment__header">
          <span className="comment__author">{comment.userName}</span>
          <span className="comment__time">{formatRelativeTime(comment.timestamp)}</span>
        </div>
        <p className="comment__text">{comment.text}</p>
        <div className="comment__actions">
          <button className="comment__action">
            <span>❤️</span>
            <span>{comment.likes}</span>
          </button>
          <button className="comment__action">Reply</button>
        </div>
      </div>
    </div>
  );
}
