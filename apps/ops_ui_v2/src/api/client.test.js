import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { getAuthHeaders, getOpsToken } from './client';

describe('client API utility functions', () => {
  beforeEach(() => {
    // Reset any mocks or localStorage before each test
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(),
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe('getOpsToken', () => {
    it('returns the token from localStorage if it exists', () => {
      vi.mocked(localStorage.getItem).mockReturnValue('mocked-token');
      expect(getOpsToken()).toBe('mocked-token');
      expect(localStorage.getItem).toHaveBeenCalledWith('ops_token');
    });

    it('returns an empty string if no token exists in localStorage', () => {
      vi.mocked(localStorage.getItem).mockReturnValue(null);
      expect(getOpsToken()).toBe('');
      expect(localStorage.getItem).toHaveBeenCalledWith('ops_token');
    });
  });

  describe('getAuthHeaders', () => {
    it('returns Authorization header with Bearer token when token is available', () => {
      vi.mocked(localStorage.getItem).mockReturnValue('mocked-token');
      expect(getAuthHeaders()).toEqual({ Authorization: 'Bearer mocked-token' });
    });

    it('returns an empty object when no token is available', () => {
      vi.mocked(localStorage.getItem).mockReturnValue(null);
      expect(getAuthHeaders()).toEqual({});
    });

    it('returns an empty object when token is empty string', () => {
      vi.mocked(localStorage.getItem).mockReturnValue('');
      expect(getAuthHeaders()).toEqual({});
    });
  });
});
