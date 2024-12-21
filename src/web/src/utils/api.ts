/**
 * Core API Utility Module
 * @version 1.0.0
 * @package @medical-research-platform/web
 */

import axios, { 
  AxiosInstance, 
  AxiosRequestConfig, 
  AxiosResponse, 
  AxiosError 
} from 'axios'; // ^1.4.0

import { 
  API_CONFIG, 
  ENDPOINTS, 
  defaultAxiosConfig, 
  handleRetry 
} from '../config/api';

import { AuthState, AuthTokens } from '../types/auth';

/**
 * Security event logging levels
 */
const SECURITY_LOG_LEVELS = {
  ERROR: 'error',
  WARN: 'warn',
  INFO: 'info'
} as const;

/**
 * Custom API error interface with security context
 */
interface ApiError extends Error {
  status?: number;
  code?: string;
  securityContext?: {
    requestId: string;
    timestamp: string;
    severity: typeof SECURITY_LOG_LEVELS[keyof typeof SECURITY_LOG_LEVELS];
  };
}

/**
 * Performance metrics tracking interface
 */
interface RequestMetrics {
  requestId: string;
  endpoint: string;
  method: string;
  startTime: number;
  duration?: number;
  status?: number;
  error?: string;
}

/**
 * Creates and configures an Axios instance with security and monitoring features
 */
const createApiClient = (): AxiosInstance => {
  const instance = axios.create(defaultAxiosConfig);

  // Request interceptor for authentication and security
  instance.interceptors.request.use(
    (config) => {
      // Add security headers
      config.headers = {
        ...config.headers,
        'X-Request-ID': crypto.randomUUID(),
        'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
      };

      // Add authentication token if available
      const token = localStorage.getItem('accessToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      // Start performance tracking
      if (API_CONFIG.MONITORING.TRACK_PERFORMANCE) {
        (config as any).metrics = {
          requestId: config.headers['X-Request-ID'],
          endpoint: config.url,
          method: config.method,
          startTime: Date.now()
        } as RequestMetrics;
      }

      return config;
    },
    (error) => {
      return Promise.reject(handleApiError(error));
    }
  );

  // Response interceptor for error handling and monitoring
  instance.interceptors.response.use(
    (response) => {
      // Complete performance tracking
      if (API_CONFIG.MONITORING.TRACK_PERFORMANCE && (response.config as any).metrics) {
        const metrics = (response.config as any).metrics as RequestMetrics;
        metrics.duration = Date.now() - metrics.startTime;
        metrics.status = response.status;
        logPerformanceMetrics(metrics);
      }

      return response;
    },
    async (error) => {
      // Handle token refresh
      if (error.response?.status === 401 && error.config && !error.config.__isRetryRequest) {
        try {
          const newToken = await refreshAuthToken();
          error.config.headers.Authorization = `Bearer ${newToken}`;
          error.config.__isRetryRequest = true;
          return instance(error.config);
        } catch (refreshError) {
          return Promise.reject(handleApiError(refreshError));
        }
      }

      return Promise.reject(handleApiError(error));
    }
  );

  return instance;
};

/**
 * Enhanced error handling with security logging and monitoring
 */
export const handleApiError = (error: AxiosError): ApiError => {
  const apiError: ApiError = new Error(error.message);
  
  apiError.securityContext = {
    requestId: error.config?.headers?.['X-Request-ID'] as string || crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    severity: SECURITY_LOG_LEVELS.ERROR
  };

  if (error.response) {
    apiError.status = error.response.status;
    apiError.code = error.response.data?.code;

    // Log security events
    if (error.response.status === 401 || error.response.status === 403) {
      logSecurityEvent({
        type: 'AUTH_FAILURE',
        severity: SECURITY_LOG_LEVELS.WARN,
        details: {
          status: error.response.status,
          path: error.config?.url,
          requestId: apiError.securityContext.requestId
        }
      });
    }
  }

  // Track error metrics if monitoring enabled
  if (API_CONFIG.MONITORING.ENABLE_METRICS) {
    trackErrorMetrics(apiError);
  }

  return apiError;
};

/**
 * Handles JWT token refresh with security logging
 */
export const refreshAuthToken = async (): Promise<string> => {
  try {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await apiClient.post<AuthTokens>(
      ENDPOINTS.AUTH.REFRESH,
      { refreshToken }
    );

    // Update stored tokens
    localStorage.setItem('accessToken', response.data.accessToken);
    localStorage.setItem('refreshToken', response.data.refreshToken);

    // Log successful token refresh
    logSecurityEvent({
      type: 'TOKEN_REFRESH',
      severity: SECURITY_LOG_LEVELS.INFO,
      details: {
        timestamp: new Date().toISOString()
      }
    });

    return response.data.accessToken;
  } catch (error) {
    // Clear tokens on refresh failure
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    
    throw error;
  }
};

/**
 * Logs security events for monitoring
 */
const logSecurityEvent = (event: {
  type: string;
  severity: typeof SECURITY_LOG_LEVELS[keyof typeof SECURITY_LOG_LEVELS];
  details: Record<string, any>;
}): void => {
  if (API_CONFIG.MONITORING.LOG_REQUESTS) {
    console.log('[Security Event]', {
      ...event,
      timestamp: new Date().toISOString()
    });
  }
};

/**
 * Tracks request performance metrics
 */
const logPerformanceMetrics = (metrics: RequestMetrics): void => {
  if (API_CONFIG.MONITORING.LOG_REQUESTS) {
    console.log('[Performance Metrics]', metrics);
  }
};

/**
 * Tracks error metrics for monitoring
 */
const trackErrorMetrics = (error: ApiError): void => {
  if (API_CONFIG.MONITORING.LOG_REQUESTS) {
    console.error('[Error Metrics]', {
      status: error.status,
      code: error.code,
      securityContext: error.securityContext
    });
  }
};

// Create and export configured API client instance
export const apiClient = createApiClient();

export default {
  apiClient,
  handleApiError,
  refreshAuthToken
};