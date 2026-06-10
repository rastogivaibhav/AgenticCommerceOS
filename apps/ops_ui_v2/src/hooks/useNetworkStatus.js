/**
 * useNetworkStatus Hook - Monitor network status and auto-reconnect
 * DEF-027: Auto-refresh data when network comes back online
 */

import { useEffect, useState, useCallback } from 'react';

/**
 * Monitor network status and trigger reconnection logic
 * @returns {Object} {isOnline, wasOffline, reconnect}
 */
export function useNetworkStatus(onReconnect) {
  const [isOnline, setIsOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true);
  const [wasOffline, setWasOffline] = useState(false);

  // Handle going online
  const handleOnline = useCallback(() => {
    if (!isOnline) {
      setIsOnline(true);
      setWasOffline(true);

      // Call reconnection handler if provided
      if (onReconnect && typeof onReconnect === 'function') {
        // Delay slightly to allow UI to update
        setTimeout(() => {
          try {
            onReconnect();
          } catch (error) {
            console.error('Reconnection handler error:', error);
          }
        }, 500);
      }
    }
  }, [isOnline, onReconnect]);

  // Handle going offline
  const handleOffline = useCallback(() => {
    setIsOnline(false);
  }, []);

  // Set up event listeners
  useEffect(() => {
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [handleOnline, handleOffline]);

  const reconnect = useCallback(() => {
    if (onReconnect && typeof onReconnect === 'function') {
      try {
        onReconnect();
      } catch (error) {
        console.error('Manual reconnection error:', error);
      }
    }
  }, [onReconnect]);

  return {
    isOnline,
    wasOffline,
    reconnect,
  };
}

export default useNetworkStatus;
