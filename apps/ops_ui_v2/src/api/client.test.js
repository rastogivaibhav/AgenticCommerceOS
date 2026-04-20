import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { getOpsToken, getAuthHeaders, buildApiUrl, ApiError, apiFetch, apiJson } from './client.js';

describe('client API', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    // Reset mocks if any were added to localStorage
    vi.restoreAllMocks();
  });

  describe('getOpsToken', () => {
    it('should return empty string when localStorage has no ops_token', () => {
      expect(getOpsToken()).toBe('');
    });

    it('should return token when ops_token exists in localStorage', () => {
      localStorage.setItem('ops_token', 'test-token-123');
      expect(getOpsToken()).toBe('test-token-123');
    });

    it('should handle mock localStorage gracefully', () => {
      const getItemMock = vi.spyOn(Storage.prototype, 'getItem').mockReturnValue('mocked-token');
      expect(getOpsToken()).toBe('mocked-token');
      expect(getItemMock).toHaveBeenCalledWith('ops_token');
    });
  });

  describe('getAuthHeaders', () => {
    it('should return empty object when no token exists', () => {
      expect(getAuthHeaders()).toEqual({});
    });

    it('should return Authorization header when token exists', () => {
      localStorage.setItem('ops_token', 'test-token-123');
      expect(getAuthHeaders()).toEqual({ Authorization: 'Bearer test-token-123' });
    });
  });

  describe('buildApiUrl', () => {
    it('should return full URL when path starts with http://', () => {
      expect(buildApiUrl('http://example.com/api')).toBe('http://example.com/api');
    });

    it('should return full URL when path starts with https://', () => {
      expect(buildApiUrl('https://example.com/api')).toBe('https://example.com/api');
    });

    it('should append path to API_BASE when path starts with /', () => {
      // In tests without API_BASE env, API_BASE is resolved to '' or window.location.origin which jsdom mocks as http://localhost:3000
      expect(buildApiUrl('/test-path')).toContain('/test-path');
    });

    it('should prepend / and append to API_BASE when path does not start with /', () => {
      expect(buildApiUrl('test-path')).toContain('/test-path');
    });
  });
});
