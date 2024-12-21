/**
 * Test Suite for useAuth Composable
 * @package @medical-research-platform/web
 * @version 1.0.0
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useAuth } from '../../src/composables/useAuth';
import { AuthState, UserRole } from '../../src/types/auth';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value.toString();
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    })
  };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mock fetch API
global.fetch = vi.fn();

// Test constants
const MOCK_USER = {
  id: 'test-user-id',
  email: 'test@example.com',
  firstName: 'Test',
  lastName: 'User',
  role: UserRole.PARTICIPANT,
  mfaEnabled: false,
  profileImage: null
};

const MOCK_TOKENS = {
  accessToken: 'mock-access-token',
  refreshToken: 'mock-refresh-token',
  expiresIn: 3600
};

describe('useAuth', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    localStorageMock.clear();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
  });

  describe('Initial State', () => {
    it('should initialize with unauthenticated state', () => {
      const { isAuthenticated, authState, user, error } = useAuth();
      
      expect(isAuthenticated.value).toBe(false);
      expect(authState.value).toBe(AuthState.UNAUTHENTICATED);
      expect(user.value).toBeNull();
      expect(error.value).toBeNull();
    });

    it('should attempt to restore session from localStorage on mount', async () => {
      const mockEncryptedTokens = 'encrypted-tokens';
      localStorageMock.setItem('mrs_auth_tokens', mockEncryptedTokens);
      
      const { isLoading } = useAuth();
      
      expect(isLoading.value).toBe(true);
      await vi.runAllTimersAsync();
      expect(isLoading.value).toBe(false);
    });
  });

  describe('Authentication Flows', () => {
    it('should handle successful login', async () => {
      const { handleLogin, isAuthenticated, user, error } = useAuth();

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ user: MOCK_USER, tokens: MOCK_TOKENS })
      });

      const credentials = {
        email: 'test@example.com',
        password: 'SecurePass123!'
      };

      const success = await handleLogin(credentials);

      expect(success).toBe(true);
      expect(isAuthenticated.value).toBe(true);
      expect(user.value).toEqual(MOCK_USER);
      expect(error.value).toBeNull();
    });

    it('should handle MFA challenge', async () => {
      const { handleLogin, authState, error } = useAuth();

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ mfaRequired: true })
      });

      const credentials = {
        email: 'test@example.com',
        password: 'SecurePass123!'
      };

      const success = await handleLogin(credentials);

      expect(success).toBe(false);
      expect(authState.value).toBe(AuthState.MFA_REQUIRED);
      expect(error.value).toBeNull();
    });

    it('should handle failed login attempts', async () => {
      const { handleLogin, isAuthenticated, error } = useAuth();

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ message: 'Invalid credentials' })
      });

      const credentials = {
        email: 'test@example.com',
        password: 'WrongPassword123!'
      };

      const success = await handleLogin(credentials);

      expect(success).toBe(false);
      expect(isAuthenticated.value).toBe(false);
      expect(error.value).toBe('Invalid credentials');
    });

    it('should enforce rate limiting after multiple failed attempts', async () => {
      const { handleLogin } = useAuth();
      const credentials = {
        email: 'test@example.com',
        password: 'WrongPassword123!'
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        json: () => Promise.resolve({ message: 'Invalid credentials' })
      });

      // Simulate multiple failed attempts
      for (let i = 0; i < 3; i++) {
        await handleLogin(credentials);
      }

      // Next attempt should be rate limited
      const success = await handleLogin(credentials);
      expect(success).toBe(false);
      expect(global.fetch).not.toHaveBeenCalledTimes(4);
    });
  });

  describe('Security Controls', () => {
    it('should securely handle token refresh', async () => {
      const { handleLogin } = useAuth();

      // Mock successful login
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ user: MOCK_USER, tokens: MOCK_TOKENS })
      });

      await handleLogin({
        email: 'test@example.com',
        password: 'SecurePass123!'
      });

      // Advance timer to trigger token refresh
      vi.advanceTimersByTime(3300000); // 55 minutes

      // Verify refresh token call
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v1/auth/refresh',
        expect.any(Object)
      );
    });

    it('should properly clean up on logout', async () => {
      const { handleLogin, handleLogout, isAuthenticated, user } = useAuth();

      // Setup authenticated session
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ user: MOCK_USER, tokens: MOCK_TOKENS })
      });

      await handleLogin({
        email: 'test@example.com',
        password: 'SecurePass123!'
      });

      // Mock logout request
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({})
      });

      await handleLogout();

      expect(isAuthenticated.value).toBe(false);
      expect(user.value).toBeNull();
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('mrs_auth_tokens');
    });

    it('should validate email format', async () => {
      const { handleLogin, error } = useAuth();

      const success = await handleLogin({
        email: 'invalid-email',
        password: 'SecurePass123!'
      });

      expect(success).toBe(false);
      expect(error.value).toBe('Invalid email format');
      expect(global.fetch).not.toHaveBeenCalled();
    });
  });

  describe('HIPAA Compliance', () => {
    it('should enforce session timeout', async () => {
      const { handleLogin, isAuthenticated } = useAuth();

      // Mock successful login
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ user: MOCK_USER, tokens: MOCK_TOKENS })
      });

      await handleLogin({
        email: 'test@example.com',
        password: 'SecurePass123!'
      });

      // Simulate session timeout
      vi.advanceTimersByTime(3600000); // 1 hour

      expect(isAuthenticated.value).toBe(false);
    });

    it('should handle MFA timeout', async () => {
      const { handleLogin, error } = useAuth();

      // Mock MFA required response
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ mfaRequired: true })
      });

      await handleLogin({
        email: 'test@example.com',
        password: 'SecurePass123!'
      });

      // Simulate MFA timeout
      vi.advanceTimersByTime(300000); // 5 minutes

      const mfaSuccess = await handleLogin({
        email: 'test@example.com',
        password: 'SecurePass123!',
        mfaCode: '123456'
      });

      expect(mfaSuccess).toBe(false);
      expect(error.value).toBe('MFA verification timeout. Please try again');
    });
  });
});