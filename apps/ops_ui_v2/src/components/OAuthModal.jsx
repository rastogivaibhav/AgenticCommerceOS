/**
 * OAuthModal Component - Handle OAuth linking with timeout
 * DEF-005: OAuth timeout handling for WhatsApp/Telegram
 */

import { useEffect, useState, useCallback } from 'react';
import { X, AlertCircle, Clock } from 'lucide-react';
import './OAuthModal.css';

const OAUTH_TIMEOUT_MS = 5 * 60 * 1000; // 5 minutes

export default function OAuthModal({
  isOpen,
  channel, // 'whatsapp' or 'telegram'
  onClose,
  onSuccess,
  onError,
}) {
  const [timeRemaining, setTimeRemaining] = useState(Math.ceil(OAUTH_TIMEOUT_MS / 1000));
  const [isTimedOut, setIsTimedOut] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  // Timer effect
  useEffect(() => {
    if (!isOpen) return;

    setTimeRemaining(Math.ceil(OAUTH_TIMEOUT_MS / 1000));
    setIsTimedOut(false);
    setErrorMessage(null);

    const interval = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          setIsTimedOut(true);
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isOpen]);

  const handleClose = useCallback(() => {
    if (isTimedOut) {
      setErrorMessage('OAuth flow expired. Please try again.');
    }
    onClose?.();
  }, [isTimedOut, onClose]);

  const handleRetry = useCallback(() => {
    setTimeRemaining(Math.ceil(OAUTH_TIMEOUT_MS / 1000));
    setIsTimedOut(false);
    setErrorMessage(null);
  }, []);

  if (!isOpen) return null;

  const minutes = Math.floor(timeRemaining / 60);
  const seconds = timeRemaining % 60;
  const displayTime = `${minutes}:${String(seconds).padStart(2, '0')}`;

  const channelName = channel === 'whatsapp' ? 'WhatsApp Business' : 'Telegram Bot';
  const channelIcon = channel === 'whatsapp' ? '💬' : '🤖';
  const oauthUrl = channel === 'whatsapp'
    ? 'https://www.whatsapp.com/business/resources/'
    : 'https://t.me/botfather';

  return (
    <div className="oauth-overlay">
      <div className="oauth-modal">
        {/* Header */}
        <div className="oauth-header">
          <div className="oauth-title">
            <span className="oauth-icon">{channelIcon}</span>
            <h2>Connect {channelName}</h2>
          </div>
          <button
            className="oauth-close"
            onClick={handleClose}
            disabled={isTimedOut && !errorMessage}
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="oauth-content">
          {isTimedOut ? (
            <>
              {/* Timeout state */}
              <div className="oauth-timeout">
                <div className="timeout-icon">⏰</div>
                <h3>OAuth Link Expired</h3>
                <p className="timeout-message">
                  The OAuth flow has timed out after 5 minutes without confirmation.
                </p>
                <p className="timeout-help">
                  Make sure to click <strong>"Confirm"</strong> in the {channelName} app to complete linking.
                </p>
              </div>

              {/* Error message if provided */}
              {errorMessage && (
                <div className="oauth-error">
                  <AlertCircle size={18} />
                  {errorMessage}
                </div>
              )}
            </>
          ) : (
            <>
              {/* Waiting state */}
              <div className="oauth-waiting">
                <div className="oauth-spinner"></div>
                <p className="waiting-text">
                  Waiting for {channelName} confirmation...
                </p>
                <p className="waiting-instructions">
                  {channel === 'whatsapp'
                    ? 'A new window will open. Confirm the request in your WhatsApp Business Account.'
                    : 'A new window will open. Configure your Telegram bot token.'}
                </p>
              </div>

              {/* Timer display */}
              <div className="oauth-timer">
                <Clock size={16} />
                <span>
                  {timeRemaining <= 60 ? (
                    <strong style={{ color: '#dc2626' }}>
                      Expires in {displayTime}
                    </strong>
                  ) : (
                    <>Expires in {displayTime}</>
                  )}
                </span>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="oauth-footer">
          {isTimedOut ? (
            <>
              <button className="oauth-btn oauth-btn-secondary" onClick={handleClose}>
                Cancel
              </button>
              <button className="oauth-btn oauth-btn-primary" onClick={handleRetry}>
                Try Again
              </button>
            </>
          ) : (
            <>
              <button className="oauth-btn oauth-btn-secondary" onClick={handleClose}>
                Cancel Flow
              </button>
              <a
                href={oauthUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="oauth-btn oauth-btn-primary"
              >
                Open {channelName} →
              </a>
            </>
          )}
        </div>

        {/* Help section */}
        {!isTimedOut && (
          <div className="oauth-help">
            <strong>Troubleshooting:</strong>
            <ul>
              <li>Make sure you're logged into your {channelName} account</li>
              <li>Allow pop-ups from this browser</li>
              <li>If you don't see a confirmation, refresh this page</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
