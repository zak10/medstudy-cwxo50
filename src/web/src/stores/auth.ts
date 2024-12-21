/**
 * Authentication Store Module
 * @package @medical-research-platform/web
 * @version 1.0.0
 */

import { defineStore } from 'pinia';
import CryptoJS from 'crypto-js';
import { 
  AuthState, 
  LoginCredentials, 
  UserProfile, 
  AuthTokens,
  UserRole 
} from '../types/auth';
import { ref, computed } from 'vue';

// Constants for authentication configuration
const TOKEN_STORAGE_KEY = 'mrs_auth_tokens';
const REFRESH_TOKEN_THRESHOLD = 300000; // 5 minutes in milliseconds
const MAX_AUTH_ATTEMPTS = 3;
const AUTH_ATTEMPT_TIMEOUT = 300000; // 5 minutes in milliseconds
const ENCRYPTION_KEY = process.env.VITE_TOKEN_ENCRYPTION_KEY || 'default-key';

/**
 * Interface for tracking authentication attempts
 */
interface AuthAttemptTracker {
  count: number;
  lastAttempt: number;
}

/**
 * Authentication store for managing user sessions and tokens
 */
export const useAuthStore = defineStore('auth', () => {
  // State
  const authState = ref<AuthState>(AuthState.UNAUTHENTICATED);
  const user = ref<UserProfile | null>(null);
  const authAttempts = ref<AuthAttemptTracker>({ count: 0, lastAttempt: 0 });
  const refreshTimer = ref<number | null>(null);
  const tokens = ref<AuthTokens | null>(null);

  // Computed properties
  const isAuthenticated = computed(() => authState.value === AuthState.AUTHENTICATED);
  const requiresMFA = computed(() => authState.value === AuthState.MFA_REQUIRED);

  /**
   * Encrypts sensitive token data for storage
   * @param tokens Authentication tokens to encrypt
   * @returns Encrypted token string
   */
  const encryptTokens = (tokens: AuthTokens): string => {
    return CryptoJS.AES.encrypt(
      JSON.stringify(tokens),
      ENCRYPTION_KEY
    ).toString();
  };

  /**
   * Decrypts stored token data
   * @param encryptedTokens Encrypted token string
   * @returns Decrypted AuthTokens object
   */
  const decryptTokens = (encryptedTokens: string): AuthTokens => {
    const decrypted = CryptoJS.AES.decrypt(encryptedTokens, ENCRYPTION_KEY);
    return JSON.parse(decrypted.toString(CryptoJS.enc.Utf8));
  };

  /**
   * Validates and tracks login attempts to prevent brute force attacks
   * @throws Error if too many attempts or timeout not expired
   */
  const validateLoginAttempts = (): void => {
    const now = Date.now();
    if (authAttempts.value.count >= MAX_AUTH_ATTEMPTS) {
      if (now - authAttempts.value.lastAttempt < AUTH_ATTEMPT_TIMEOUT) {
        throw new Error('Too many login attempts. Please try again later.');
      }
      authAttempts.value = { count: 0, lastAttempt: now };
    }
  };

  /**
   * Authenticates user with provided credentials
   * @param credentials User login credentials
   * @returns Promise resolving to authentication result
   */
  const login = async (credentials: LoginCredentials): Promise<boolean> => {
    try {
      validateLoginAttempts();

      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });

      const data = await response.json();

      if (!response.ok) {
        authAttempts.value.count++;
        authAttempts.value.lastAttempt = Date.now();
        throw new Error(data.message);
      }

      if (data.mfaRequired) {
        authState.value = AuthState.MFA_REQUIRED;
        return false;
      }

      await handleAuthenticationSuccess(data);
      return true;

    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  /**
   * Handles successful authentication by storing tokens and user data
   * @param data Authentication response data
   */
  const handleAuthenticationSuccess = async (data: any): Promise<void> => {
    tokens.value = data.tokens;
    localStorage.setItem(TOKEN_STORAGE_KEY, encryptTokens(data.tokens));
    
    user.value = data.user;
    authState.value = AuthState.AUTHENTICATED;
    authAttempts.value = { count: 0, lastAttempt: 0 };
    
    scheduleTokenRefresh();
  };

  /**
   * Schedules automatic token refresh before expiration
   */
  const scheduleTokenRefresh = (): void => {
    if (refreshTimer.value) {
      clearTimeout(refreshTimer.value);
    }

    const timeUntilRefresh = (tokens.value?.expiresIn || 0) * 1000 - REFRESH_TOKEN_THRESHOLD;
    refreshTimer.value = window.setTimeout(refreshAuthToken, timeUntilRefresh);
  };

  /**
   * Refreshes authentication tokens
   * @returns Promise resolving when tokens are refreshed
   */
  const refreshAuthToken = async (): Promise<void> => {
    try {
      if (!tokens.value?.refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken: tokens.value.refreshToken })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message);
      }

      tokens.value = data.tokens;
      localStorage.setItem(TOKEN_STORAGE_KEY, encryptTokens(data.tokens));
      scheduleTokenRefresh();

    } catch (error) {
      console.error('Token refresh error:', error);
      await logout();
    }
  };

  /**
   * Completes MFA verification process
   * @param mfaCode MFA verification code
   * @returns Promise resolving to verification result
   */
  const verifyMFA = async (mfaCode: string): Promise<boolean> => {
    try {
      const response = await fetch('/api/v1/auth/mfa/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mfaCode })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message);
      }

      await handleAuthenticationSuccess(data);
      return true;

    } catch (error) {
      console.error('MFA verification error:', error);
      throw error;
    }
  };

  /**
   * Checks if user has specific role
   * @param role Role to check
   * @returns Boolean indicating if user has role
   */
  const hasRole = (role: UserRole): boolean => {
    return user.value?.role === role;
  };

  /**
   * Logs out user and clears authentication state
   */
  const logout = async (): Promise<void> => {
    try {
      if (tokens.value?.refreshToken) {
        await fetch('/api/v1/auth/logout', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refreshToken: tokens.value.refreshToken })
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      if (refreshTimer.value) {
        clearTimeout(refreshTimer.value);
      }
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      tokens.value = null;
      user.value = null;
      authState.value = AuthState.UNAUTHENTICATED;
    }
  };

  /**
   * Initializes authentication state from stored tokens
   */
  const initializeAuth = async (): Promise<void> => {
    const storedTokens = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (storedTokens) {
      try {
        tokens.value = decryptTokens(storedTokens);
        await refreshAuthToken();
      } catch (error) {
        console.error('Auth initialization error:', error);
        await logout();
      }
    }
  };

  return {
    // State
    authState,
    user,
    
    // Computed
    isAuthenticated,
    requiresMFA,
    
    // Actions
    login,
    logout,
    verifyMFA,
    hasRole,
    initializeAuth
  };
});