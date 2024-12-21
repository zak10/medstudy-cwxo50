/**
 * Authentication Store Test Suite
 * @package @medical-research-platform/web
 * @version 1.0.0
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useAuthStore } from '../../src/stores/auth';
import { AuthState, UserRole } from '../../src/types/auth';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

// Mock setTimeout/clearTimeout
vi.useFakeTimers();

describe('Authentication Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    mockLocalStorage.getItem.mockReset();
    mockLocalStorage.setItem.mockReset();
    mockLocalStorage.removeItem.mockReset();
    mockFetch.mockReset();
    vi.clearAllTimers();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('should start with unauthenticated state', () => {
      const store = useAuthStore();
      expect(store.authState).toBe(AuthState.UNAUTHENTICATED);
      expect(store.user).toBeNull();
      expect(store.isAuthenticated).toBe(false);
      expect(store.requiresMFA).toBe(false);
    });
  });

  describe('Login Flow', () => {
    const mockCredentials = {
      email: 'test@example.com',
      password: 'Test123!@#',
    };

    it('should handle successful login without MFA', async () => {
      const store = useAuthStore();
      const mockResponse = {
        ok: true,
        json: () => Promise.resolve({
          tokens: {
            accessToken: 'mock-access-token',
            refreshToken: 'mock-refresh-token',
            expiresIn: 3600
          },
          user: {
            id: '123',
            email: 'test@example.com',
            role: UserRole.PARTICIPANT
          }
        })
      };

      mockFetch.mockResolvedValueOnce(mockResponse);

      await store.login(mockCredentials);

      expect(store.authState).toBe(AuthState.AUTHENTICATED);
      expect(store.isAuthenticated).toBe(true);
      expect(mockLocalStorage.setItem).toHaveBeenCalled();
    });

    it('should handle MFA requirement', async () => {
      const store = useAuthStore();
      const mockResponse = {
        ok: true,
        json: () => Promise.resolve({ mfaRequired: true })
      };

      mockFetch.mockResolvedValueOnce(mockResponse);

      await store.login(mockCredentials);

      expect(store.authState).toBe(AuthState.MFA_REQUIRED);
      expect(store.requiresMFA).toBe(true);
      expect(store.isAuthenticated).toBe(false);
    });

    it('should enforce rate limiting', async () => {
      const store = useAuthStore();
      const mockErrorResponse = {
        ok: false,
        json: () => Promise.resolve({ message: 'Invalid credentials' })
      };

      mockFetch.mockResolvedValue(mockErrorResponse);

      // Attempt login multiple times
      for (let i = 0; i < 3; i++) {
        await expect(store.login(mockCredentials)).rejects.toThrow();
      }

      // Next attempt should be blocked
      await expect(store.login(mockCredentials)).rejects.toThrow('Too many login attempts');
    });
  });

  describe('MFA Verification', () => {
    it('should handle successful MFA verification', async () => {
      const store = useAuthStore();
      const mockResponse = {
        ok: true,
        json: () => Promise.resolve({
          tokens: {
            accessToken: 'mock-access-token',
            refreshToken: 'mock-refresh-token',
            expiresIn: 3600
          },
          user: {
            id: '123',
            email: 'test@example.com',
            role: UserRole.PARTICIPANT
          }
        })
      };

      mockFetch.mockResolvedValueOnce(mockResponse);
      store.authState = AuthState.MFA_REQUIRED;

      await store.verifyMFA('123456');

      expect(store.authState).toBe(AuthState.AUTHENTICATED);
      expect(store.isAuthenticated).toBe(true);
    });

    it('should handle failed MFA verification', async () => {
      const store = useAuthStore();
      const mockResponse = {
        ok: false,
        json: () => Promise.resolve({ message: 'Invalid MFA code' })
      };

      mockFetch.mockResolvedValueOnce(mockResponse);
      store.authState = AuthState.MFA_REQUIRED;

      await expect(store.verifyMFA('invalid')).rejects.toThrow();
      expect(store.authState).toBe(AuthState.MFA_REQUIRED);
    });
  });

  describe('Token Management', () => {
    it('should schedule token refresh', async () => {
      const store = useAuthStore();
      const mockResponse = {
        ok: true,
        json: () => Promise.resolve({
          tokens: {
            accessToken: 'new-access-token',
            refreshToken: 'new-refresh-token',
            expiresIn: 3600
          }
        })
      };

      mockFetch.mockResolvedValueOnce(mockResponse);

      // Simulate successful login
      await store.login({
        email: 'test@example.com',
        password: 'Test123!@#'
      });

      // Fast-forward to just before token refresh
      vi.advanceTimersByTime(3300000); // 55 minutes

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/auth/refresh',
        expect.any(Object)
      );
    });

    it('should handle failed token refresh', async () => {
      const store = useAuthStore();
      const mockResponse = {
        ok: false,
        json: () => Promise.resolve({ message: 'Invalid refresh token' })
      };

      mockFetch.mockResolvedValueOnce(mockResponse);
      
      await store.refreshAuthToken();

      expect(store.authState).toBe(AuthState.UNAUTHENTICATED);
      expect(mockLocalStorage.removeItem).toHaveBeenCalled();
    });
  });

  describe('Logout', () => {
    it('should clear authentication state on logout', async () => {
      const store = useAuthStore();
      const mockResponse = {
        ok: true,
        json: () => Promise.resolve({})
      };

      mockFetch.mockResolvedValueOnce(mockResponse);

      await store.logout();

      expect(store.authState).toBe(AuthState.UNAUTHENTICATED);
      expect(store.user).toBeNull();
      expect(store.isAuthenticated).toBe(false);
      expect(mockLocalStorage.removeItem).toHaveBeenCalled();
    });

    it('should handle failed logout gracefully', async () => {
      const store = useAuthStore();
      const mockResponse = {
        ok: false,
        json: () => Promise.resolve({ message: 'Server error' })
      };

      mockFetch.mockResolvedValueOnce(mockResponse);

      await store.logout();

      expect(store.authState).toBe(AuthState.UNAUTHENTICATED);
      expect(mockLocalStorage.removeItem).toHaveBeenCalled();
    });
  });

  describe('Role-Based Access', () => {
    it('should correctly check user roles', async () => {
      const store = useAuthStore();
      const mockResponse = {
        ok: true,
        json: () => Promise.resolve({
          tokens: {
            accessToken: 'mock-token',
            refreshToken: 'mock-refresh',
            expiresIn: 3600
          },
          user: {
            id: '123',
            email: 'test@example.com',
            role: UserRole.PROTOCOL_CREATOR
          }
        })
      };

      mockFetch.mockResolvedValueOnce(mockResponse);

      await store.login({
        email: 'test@example.com',
        password: 'Test123!@#'
      });

      expect(store.hasRole(UserRole.PROTOCOL_CREATOR)).toBe(true);
      expect(store.hasRole(UserRole.PARTICIPANT)).toBe(false);
    });
  });

  describe('Authentication Initialization', () => {
    it('should restore authentication state from storage', async () => {
      const store = useAuthStore();
      const mockStoredTokens = {
        accessToken: 'stored-access-token',
        refreshToken: 'stored-refresh-token',
        expiresIn: 3600
      };

      mockLocalStorage.getItem.mockReturnValue(JSON.stringify(mockStoredTokens));
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ tokens: mockStoredTokens })
      });

      await store.initializeAuth();

      expect(store.authState).toBe(AuthState.AUTHENTICATED);
      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/auth/refresh',
        expect.any(Object)
      );
    });

    it('should handle invalid stored tokens', async () => {
      const store = useAuthStore();
      mockLocalStorage.getItem.mockReturnValue('invalid-token-data');

      await store.initializeAuth();

      expect(store.authState).toBe(AuthState.UNAUTHENTICATED);
      expect(mockLocalStorage.removeItem).toHaveBeenCalled();
    });
  });
});