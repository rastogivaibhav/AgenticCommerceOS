/**
 * useAuth Hook - Token monitoring and expiry management
 * DEF-016: Monitor token expiry and warn user before logout
 */

import { useEffect, useState, useCallback } from 'react';
import { getOpsToken } from '../api/client';

// Decode JWT without verification (for client-side expiry checking only)
function decodeToken(token) {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;

    const payload = JSON.parse(atob(parts[1]));
    return payload;
  } catch {
    return null;
  }
}

/**
 * Monitor token expiry and emit warnings
 * @returns {Object} {isExpired, timeUntilExpiry, showWarning, dismissWarning, refreshToken}
 */
export function useAuth() {
  const [tokenClaims, setTokenClaims] = useState(null);
  const [isExpired, setIsExpired] = useState(false);
  const [showWarning, setShowWarning] = useState(false);
  const [timeUntilExpiry, setTimeUntilExpiry] = useState(null);
  const [lastCheckTime, setLastCheckTime] = useState(Date.now());

  // Check token and update state
  const checkToken = useCallback(() => {
    const token = getOpsToken();
    if (!token) {
      setTokenClaims(null);
      setIsExpired(false);
      return;
    }

    const claims = decodeToken(token);
    if (!claims || !claims.exp) {
      setTokenClaims(null);
      return;
    }

    setTokenClaims(claims);
    const now = Math.floor(Date.now() / 1000);
    const expiresIn = claims.exp - now;

    // Token already expired
    if (expiresIn <= 0) {
      setIsExpired(true);
      setShowWarning(false);
      localStorage.removeItem('ops_token');
      return;
    }

    setIsExpired(false);
    setTimeUntilExpiry(expiresIn);

    // Show warning 5 minutes before expiry (300 seconds)
    if (expiresIn <= 300 && expiresIn > 0 && !showWarning) {
      setShowWarning(true);
    }
  }, [showWarning]);

  // Set up interval to check token every 30 seconds
  useEffect(() => {
    checkToken();
    const interval = setInterval(checkToken, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, [checkToken]);

  // Update time display every second when warning is shown
  useEffect(() => {
    if (!showWarning || !tokenClaims) return;

    const displayInterval = setInterval(() => {
      const token = getOpsToken();
      const claims = decodeToken(token);
      if (claims && claims.exp) {
        const now = Math.floor(Date.now() / 1000);
        const expiresIn = claims.exp - now;
        setTimeUntilExpiry(expiresIn);

        // Auto-logout when expired
        if (expiresIn <= 0) {
          setIsExpired(true);
          setShowWarning(false);
          localStorage.removeItem('ops_token');
        }
      }
    }, 1000);

    return () => clearInterval(displayInterval);
  }, [showWarning, tokenClaims]);

  const dismissWarning = useCallback(() => {
    setShowWarning(false);
  }, []);

  const refreshToken = useCallback(async () => {
    // Get the current role from token claims
    if (!tokenClaims || !tokenClaims.role) {
      console.error('Cannot refresh token: no role found');
      return false;
    }

    try {
      const role = tokenClaims.role;
      const response = await fetch(
        `/dev/auth/bootstrap/${role}?redirect=%2Fui%2Fworkflows`,
        { method: 'GET' }
      );

      const html = await response.text();
      const tokenMatch = html.match(/setItem\("ops_token",\s*"([^"]+)"/);

      if (tokenMatch && tokenMatch[1]) {
        localStorage.setItem('ops_token', tokenMatch[1]);
        setShowWarning(false);
        checkToken(); // Re-check token
        return true;
      }
    } catch (error) {
      console.error('Failed to refresh token:', error);
    }

    return false;
  }, [tokenClaims, checkToken]);

  return {
    isExpired,
    timeUntilExpiry,
    showWarning,
    dismissWarning,
    refreshToken,
    tokenClaims,
  };
}

export default useAuth;
