/**
 * API Configuration Module
 * @version 1.0.0
 * @package @medical-research-platform/web
 */

import { AxiosRequestConfig } from 'axios'; // ^1.4.0
import { AuthState } from '../types/auth';

/**
 * API version for all endpoints
 */
export const API_VERSION = 'v1';

/**
 * Default request timeout in milliseconds
 */
export const DEFAULT_TIMEOUT = 30000;

/**
 * Maximum number of retry attempts for failed requests
 */
export const MAX_RETRIES = 3;

/**
 * Rate limiting window in milliseconds
 */
export const RATE_LIMIT_WINDOW = 60000;

/**
 * Core API configuration settings
 */
export const API_CONFIG: {
  BASE_URL: string;
  TIMEOUT: number;
  RETRY_ATTEMPTS: number;
  HEADERS: Record<string, string>;
  RATE_LIMIT: {
    MAX_REQUESTS: number;
    WINDOW_MS: number;
    RETRY_AFTER: number;
  };
  SECURITY: {
    CSRF_ENABLED: boolean;
    CONTENT_SECURITY_POLICY: string;
    SANITIZE_REQUESTS: boolean;
  };
  MONITORING: {
    ENABLE_METRICS: boolean;
    LOG_REQUESTS: boolean;
    TRACK_PERFORMANCE: boolean;
  };
} = {
  BASE_URL: process.env.VUE_APP_API_URL || 'http://localhost:8000',
  TIMEOUT: DEFAULT_TIMEOUT,
  RETRY_ATTEMPTS: MAX_RETRIES,
  HEADERS: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-CSRF-Token': 'dynamic',
    'X-Request-ID': 'dynamic'
  },
  RATE_LIMIT: {
    MAX_REQUESTS: 100,
    WINDOW_MS: RATE_LIMIT_WINDOW,
    RETRY_AFTER: 60
  },
  SECURITY: {
    CSRF_ENABLED: true,
    CONTENT_SECURITY_POLICY: "default-src 'self'",
    SANITIZE_REQUESTS: true
  },
  MONITORING: {
    ENABLE_METRICS: true,
    LOG_REQUESTS: true,
    TRACK_PERFORMANCE: true
  }
};

/**
 * API endpoints configuration
 */
export const ENDPOINTS = {
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    REGISTER: '/api/v1/auth/register',
    REFRESH: '/api/v1/auth/refresh',
    LOGOUT: '/api/v1/auth/logout',
    VERIFY_MFA: '/api/v1/auth/verify-mfa',
    SETUP_MFA: '/api/v1/auth/setup-mfa',
    RESET_PASSWORD: '/api/v1/auth/reset-password'
  },
  PROTOCOL: {
    LIST: '/api/v1/protocols',
    DETAIL: '/api/v1/protocols/:id',
    CREATE: '/api/v1/protocols',
    UPDATE: '/api/v1/protocols/:id',
    DELETE: '/api/v1/protocols/:id',
    ENROLL: '/api/v1/protocols/:id/enroll',
    BATCH: '/api/v1/protocols/batch'
  },
  DATA: {
    SUBMIT: '/api/v1/data-points',
    LIST: '/api/v1/data-points',
    DETAIL: '/api/v1/data-points/:id',
    UPLOAD: '/api/v1/data-points/upload',
    VALIDATE: '/api/v1/data-points/validate',
    BATCH: '/api/v1/data-points/batch'
  },
  ANALYSIS: {
    RESULTS: '/api/v1/analysis/results/:protocolId',
    EXPORT: '/api/v1/analysis/export/:protocolId',
    SUMMARY: '/api/v1/analysis/summary/:protocolId',
    BATCH: '/api/v1/analysis/batch'
  },
  COMMUNITY: {
    FORUMS: '/api/v1/community/forums',
    THREADS: '/api/v1/community/threads',
    POSTS: '/api/v1/community/posts',
    MESSAGES: '/api/v1/community/messages'
  },
  HEALTH: {
    PING: '/api/v1/health/ping',
    STATUS: '/api/v1/health/status',
    METRICS: '/api/v1/health/metrics'
  },
  WEBHOOKS: {
    LAB_RESULTS: '/api/v1/webhooks/lab-results',
    NOTIFICATIONS: '/api/v1/webhooks/notifications'
  }
};

/**
 * Generates a complete endpoint URL by replacing path parameters
 * @param endpoint - The endpoint path with parameter placeholders
 * @param params - Object containing parameter values
 * @returns Complete endpoint URL with replaced parameters
 */
export const getEndpointUrl = (
  endpoint: string,
  params?: Record<string, string | number>
): string => {
  if (!endpoint) {
    throw new Error('Endpoint is required');
  }

  let url = endpoint;

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value === undefined || value === null) {
        throw new Error(`Missing required parameter: ${key}`);
      }
      // Sanitize parameter values
      const sanitizedValue = String(value).replace(/[<>'"]/g, '');
      url = url.replace(`:${key}`, sanitizedValue);
    });
  }

  // Validate no unused parameters remain
  if (url.includes(':')) {
    throw new Error('Missing required parameter(s)');
  }

  // Ensure API version prefix
  if (!url.includes(`/api/${API_VERSION}`)) {
    url = `/api/${API_VERSION}${url}`;
  }

  return `${API_CONFIG.BASE_URL}${url}`;
};

/**
 * Manages request retry logic with exponential backoff
 * @param error - The error that triggered the retry
 * @param retryCount - Current retry attempt number
 * @returns Whether to retry the request
 */
export const handleRetry = (error: any, retryCount: number): boolean => {
  // Only retry on network errors or 5xx responses
  const isRetryable = !error.response || (error.response.status >= 500 && error.response.status <= 599);
  
  if (!isRetryable || retryCount >= API_CONFIG.RETRY_ATTEMPTS) {
    return false;
  }

  // Calculate exponential backoff delay
  const backoffDelay = Math.min(1000 * Math.pow(2, retryCount), 10000);

  // Log retry attempt if monitoring is enabled
  if (API_CONFIG.MONITORING.LOG_REQUESTS) {
    console.warn(`Retrying request (attempt ${retryCount + 1}/${API_CONFIG.RETRY_ATTEMPTS}) after ${backoffDelay}ms`);
  }

  return true;
};

/**
 * Default Axios request configuration
 */
export const defaultAxiosConfig: AxiosRequestConfig = {
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.TIMEOUT,
  headers: API_CONFIG.HEADERS,
  validateStatus: (status: number) => status >= 200 && status < 300
};

export default {
  API_CONFIG,
  ENDPOINTS,
  getEndpointUrl,
  handleRetry,
  defaultAxiosConfig
};