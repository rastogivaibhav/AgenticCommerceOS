/**
 * TokenExpiryWarning Component
 * DEF-016: Display warning modal 5 minutes before token expiry
 */

import { useEffect, useState } from 'react';
import './TokenExpiryWarning.css';

export default function TokenExpiryWarning({
  showWarning,
  timeUntilExpiry,
  onDismiss,
  onRefresh,
  onLogout,
}) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState(null);

  if (!showWarning) return null;

  const minutes = Math.floor(timeUntilExpiry / 60);
  const seconds = timeUntilExpiry % 60;

  const handleRefresh = async () => {
    setIsRefreshing(true);
    setRefreshError(null);
    try {
      const success = await onRefresh();
      if (!success) {
        setRefreshError('Failed to refresh token. Try again or log out.');
      }
    } catch (error) {
      setRefreshError('Error refreshing token. Please try again.');
      console.error('Token refresh error:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('ops_token');
    if (onLogout) onLogout();
    window.location.href = '/ui/workflows';
  };

  return (
    <div className="token-expiry-overlay">
      <div className="token-expiry-modal">
        <div className="token-expiry-header">
          <div className="token-expiry-icon">⏰</div>
          <h2>Session Expiring Soon</h2>
        </div>

        <div className="token-expiry-content">
          <p className="token-expiry-message">
            Your session will expire in <strong>{minutes}:{String(seconds).padStart(2, '0')}</strong>
          </p>
          <p className="token-expiry-hint">
            Click "Refresh Session" to continue working, or "Logout" to end your session safely.
          </p>

          {refreshError && (
            <div className="token-expiry-error">
              <span className="error-icon">❌</span>
              {refreshError}
            </div>
          )}
        </div>

        <div className="token-expiry-actions">
          <button
            className="token-expiry-btn token-expiry-btn-primary"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            {isRefreshing ? (
              <>
                <span className="spinner"></span>
                Refreshing...
              </>
            ) : (
              'Refresh Session'
            )}
          </button>
          <button
            className="token-expiry-btn token-expiry-btn-secondary"
            onClick={handleLogout}
            disabled={isRefreshing}
          >
            Logout
          </button>
        </div>

        <div className="token-expiry-footer">
          <button
            className="token-expiry-btn-dismiss"
            onClick={onDismiss}
            title="Dismiss for now (warning will reappear if needed)"
          >
            ✕ Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}
