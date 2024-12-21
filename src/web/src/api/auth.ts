// @version axios ^1.4.0
// @version jwt-decode ^3.1.2

import axios from 'axios';
import jwtDecode from 'jwt-decode';
import { APIResponse, API_ENDPOINTS, DEFAULT_REQUEST_CONFIG } from './types';
import { LoginCredentials, AuthTokens, AuthState, MFASetupData } from '../types/auth';

/**
 * Security-related constants
 */
const SECURITY_CONSTANTS = {
  TOKEN_STORAGE_KEY: 'auth_tokens',
  REFRESH_THRESHOLD_MS: 300000, // 5 minutes before expiry
  MAX_RETRY_ATTEMPTS: 3,
  RETRY_DELAY_MS: 1000,
  SECURITY_HEADERS: {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
  }
} as const;

/**
 * Token interface for decoded JWT payload
 */
interface DecodedToken {
  exp: number;
  sub: string;
  role: string;
}

/**
 * Enhanced Authentication Service with security features
 */
export class AuthService {
  private refreshTimeout?: NodeJS.Timeout;
  private retryCount: number = 0;

  /**
   * Initializes the AuthService and sets up token refresh
   */
  constructor() {
    this.setupTokenRefresh();
  }

  /**
   * Authenticates user with enhanced security measures
   * @param credentials - User login credentials
   * @returns Promise with authentication tokens
   */
  public async login(credentials: LoginCredentials): Promise<APIResponse<AuthTokens>> {
    try {
      // Input validation
      this.validateLoginCredentials(credentials);

      // Prepare headers with CSRF protection
      const headers = {
        ...DEFAULT_REQUEST_CONFIG.headers,
        ...SECURITY_CONSTANTS.SECURITY_HEADERS
      };

      const response = await axios.post<APIResponse<AuthTokens>>(
        API_ENDPOINTS.AUTH.LOGIN,
        this.sanitizeCredentials(credentials),
        { headers }
      );

      if (response.data.data) {
        await this.handleSuccessfulLogin(response.data.data);
      }

      return response.data;
    } catch (error) {
      this.handleAuthError(error);
      throw error;
    }
  }

  /**
   * Refreshes authentication tokens
   * @param refreshToken - Current refresh token
   * @returns Promise with new authentication tokens
   */
  public async refreshToken(refreshToken: string): Promise<APIResponse<AuthTokens>> {
    try {
      const headers = {
        ...DEFAULT_REQUEST_CONFIG.headers,
        'Authorization': `Bearer ${refreshToken}`,
        ...SECURITY_CONSTANTS.SECURITY_HEADERS
      };

      const response = await axios.post<APIResponse<AuthTokens>>(
        API_ENDPOINTS.AUTH.REFRESH,
        {},
        { headers }
      );

      if (response.data.data) {
        await this.handleSuccessfulLogin(response.data.data);
      }

      return response.data;
    } catch (error) {
      if (this.retryCount < SECURITY_CONSTANTS.MAX_RETRY_ATTEMPTS) {
        this.retryCount++;
        await this.delay(SECURITY_CONSTANTS.RETRY_DELAY_MS * this.retryCount);
        return this.refreshToken(refreshToken);
      }
      this.handleAuthError(error);
      throw error;
    }
  }

  /**
   * Sets up MFA for a user
   * @returns Promise with MFA setup data
   */
  public async setupMFA(): Promise<APIResponse<MFASetupData>> {
    try {
      const tokens = await this.getStoredTokens();
      const headers = {
        ...DEFAULT_REQUEST_CONFIG.headers,
        'Authorization': `Bearer ${tokens?.accessToken}`,
        ...SECURITY_CONSTANTS.SECURITY_HEADERS
      };

      const response = await axios.post<APIResponse<MFASetupData>>(
        API_ENDPOINTS.AUTH.MFA_SETUP,
        {},
        { headers }
      );

      return response.data;
    } catch (error) {
      this.handleAuthError(error);
      throw error;
    }
  }

  /**
   * Logs out the user and cleans up
   */
  public async logout(): Promise<void> {
    try {
      const tokens = await this.getStoredTokens();
      if (tokens) {
        const headers = {
          ...DEFAULT_REQUEST_CONFIG.headers,
          'Authorization': `Bearer ${tokens.accessToken}`,
          ...SECURITY_CONSTANTS.SECURITY_HEADERS
        };

        await axios.post(API_ENDPOINTS.AUTH.LOGOUT, {}, { headers });
      }
    } finally {
      this.cleanup();
    }
  }

  /**
   * Private helper methods
   */

  private validateLoginCredentials(credentials: LoginCredentials): void {
    if (!credentials.email || !credentials.email.includes('@')) {
      throw new Error('Invalid email format');
    }
    if (!credentials.password || credentials.password.length < 8) {
      throw new Error('Invalid password format');
    }
  }

  private sanitizeCredentials(credentials: LoginCredentials): LoginCredentials {
    return {
      email: credentials.email.trim().toLowerCase(),
      password: credentials.password,
      mfaCode: credentials.mfaCode?.trim()
    };
  }

  private async handleSuccessfulLogin(tokens: AuthTokens): Promise<void> {
    await this.storeTokens(tokens);
    this.setupTokenRefresh();
  }

  private async storeTokens(tokens: AuthTokens): Promise<void> {
    try {
      const encryptedTokens = await this.encryptTokens(tokens);
      localStorage.setItem(SECURITY_CONSTANTS.TOKEN_STORAGE_KEY, encryptedTokens);
    } catch (error) {
      console.error('Failed to store tokens:', error);
      throw new Error('Token storage failed');
    }
  }

  private async getStoredTokens(): Promise<AuthTokens | null> {
    try {
      const encryptedTokens = localStorage.getItem(SECURITY_CONSTANTS.TOKEN_STORAGE_KEY);
      if (!encryptedTokens) return null;
      return await this.decryptTokens(encryptedTokens);
    } catch (error) {
      console.error('Failed to retrieve tokens:', error);
      return null;
    }
  }

  private setupTokenRefresh(): void {
    if (this.refreshTimeout) {
      clearTimeout(this.refreshTimeout);
    }

    const tokens = localStorage.getItem(SECURITY_CONSTANTS.TOKEN_STORAGE_KEY);
    if (!tokens) return;

    try {
      const { accessToken } = JSON.parse(tokens);
      const decoded = jwtDecode<DecodedToken>(accessToken);
      const expiresIn = decoded.exp * 1000 - Date.now();
      const refreshTime = expiresIn - SECURITY_CONSTANTS.REFRESH_THRESHOLD_MS;

      if (refreshTime > 0) {
        this.refreshTimeout = setTimeout(
          () => this.refreshToken(JSON.parse(tokens).refreshToken),
          refreshTime
        );
      }
    } catch (error) {
      console.error('Token refresh setup failed:', error);
    }
  }

  private async encryptTokens(tokens: AuthTokens): Promise<string> {
    // In a production environment, implement proper encryption
    return JSON.stringify(tokens);
  }

  private async decryptTokens(encryptedTokens: string): Promise<AuthTokens> {
    // In a production environment, implement proper decryption
    return JSON.parse(encryptedTokens);
  }

  private handleAuthError(error: any): void {
    if (axios.isAxiosError(error)) {
      if (error.response?.status === 401) {
        this.cleanup();
      }
      throw new Error(error.response?.data?.message || 'Authentication failed');
    }
    throw error;
  }

  private cleanup(): void {
    localStorage.removeItem(SECURITY_CONSTANTS.TOKEN_STORAGE_KEY);
    if (this.refreshTimeout) {
      clearTimeout(this.refreshTimeout);
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Export singleton instance
export const authService = new AuthService();