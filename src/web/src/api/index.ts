// @version axios ^1.4.0
// @version axios-retry ^3.5.0

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import axiosRetry from 'axios-retry';

// Internal imports
import { APIResponse, APIError, isAPIError } from './types';
import { API_CONFIG, ENDPOINTS, handleRetry } from '../config/api';

/**
 * Error codes for API error handling
 */
const ERROR_CODES = {
  NETWORK: 'NETWORK_ERROR',
  AUTH: 'AUTH_ERROR',
  VALIDATION: 'VALIDATION_ERROR',
  RATE_LIMIT: 'RATE_LIMIT_ERROR',
  SERVER: 'SERVER_ERROR',
  UNKNOWN: 'UNKNOWN_ERROR'
} as const;

/**
 * Custom API error class with enhanced error details
 */
export class ApiError extends Error {
  constructor(
    public code: keyof typeof ERROR_CODES,
    public status: number,
    public details: Record<string, any>,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Creates and configures the API client instance with security and monitoring features
 */
function createApiClient(): AxiosInstance {
  const client = axios.create({
    baseURL: API_CONFIG.BASE_URL,
    timeout: API_CONFIG.TIMEOUT,
    headers: {
      ...API_CONFIG.HEADERS,
      'X-Request-ID': crypto.randomUUID()
    },
    validateStatus: (status) => status >= 200 && status < 300
  });

  // Configure retry mechanism with exponential backoff
  axiosRetry(client, {
    retries: API_CONFIG.RETRY_ATTEMPTS,
    retryDelay: (retryCount) => {
      return Math.min(1000 * Math.pow(2, retryCount), 10000);
    },
    retryCondition: (error) => handleRetry(error, axiosRetry.getRequestCount(error))
  });

  // Request interceptor for authentication and security
  client.interceptors.request.use(
    (config) => {
      // Add security headers
      if (API_CONFIG.SECURITY.CSRF_ENABLED) {
        config.headers['X-CSRF-Token'] = localStorage.getItem('csrf_token');
      }
      
      // Add auth token if available
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }

      // Add security headers
      config.headers['Content-Security-Policy'] = API_CONFIG.SECURITY.CONTENT_SECURITY_POLICY;
      
      // Track request timing if enabled
      if (API_CONFIG.MONITORING.TRACK_PERFORMANCE) {
        config.metadata = { startTime: Date.now() };
      }

      return config;
    },
    (error) => Promise.reject(handleApiError(error))
  );

  // Response interceptor for error handling and monitoring
  client.interceptors.response.use(
    (response) => {
      // Log performance metrics if enabled
      if (API_CONFIG.MONITORING.TRACK_PERFORMANCE && response.config.metadata) {
        const duration = Date.now() - response.config.metadata.startTime;
        console.debug(`Request to ${response.config.url} completed in ${duration}ms`);
      }

      return response;
    },
    (error) => Promise.reject(handleApiError(error))
  );

  return client;
}

/**
 * Handles API errors and transforms them into standardized error responses
 */
function handleApiError(error: AxiosError): ApiError {
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    const data = error.response.data as APIError;

    if (status === 401) {
      return new ApiError('AUTH', status, data, 'Authentication failed');
    }
    if (status === 422) {
      return new ApiError('VALIDATION', status, data, 'Validation failed');
    }
    if (status === 429) {
      return new ApiError('RATE_LIMIT', status, data, 'Rate limit exceeded');
    }
    if (status >= 500) {
      return new ApiError('SERVER', status, data, 'Server error occurred');
    }
  } else if (error.request) {
    // Network error
    return new ApiError('NETWORK', 0, {}, 'Network error occurred');
  }

  // Unknown error
  return new ApiError('UNKNOWN', 0, {}, error.message);
}

// Create singleton API client instance
export const apiClient = createApiClient();

/**
 * Retrieves protocol analysis results
 */
export async function getProtocolResults(protocolId: string): Promise<APIResponse<any>> {
  const url = ENDPOINTS.ANALYSIS.RESULTS.replace(':protocolId', protocolId);
  const response = await apiClient.get(url);
  return response.data;
}

/**
 * Exports protocol analysis data
 */
export async function exportAnalysis(protocolId: string, format: 'csv' | 'json' = 'json'): Promise<APIResponse<any>> {
  const url = ENDPOINTS.ANALYSIS.EXPORT.replace(':protocolId', protocolId);
  const response = await apiClient.get(url, { params: { format } });
  return response.data;
}

/**
 * Retrieves statistical summary for a protocol
 */
export async function getStatisticalSummary(protocolId: string): Promise<APIResponse<any>> {
  const url = ENDPOINTS.ANALYSIS.SUMMARY.replace(':protocolId', protocolId);
  const response = await apiClient.get(url);
  return response.data;
}

export {
  ApiError,
  ERROR_CODES
};