// @version axios ^1.4.0
import { AxiosResponse } from 'axios';

// Internal imports
import { StatisticalSummary } from '../types/analysis';
import { Protocol, ProtocolStatus } from '../types/protocol';
import { DataPoint, DataPointType, DataPointStatus } from '../types/data';
import { UserProfile, AuthState, UserRole } from '../types/auth';

/**
 * HTTP Methods supported by the API
 */
export type HTTPMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

/**
 * Generic API Response wrapper interface
 * @template T - Type of the response data
 */
export interface APIResponse<T> {
  data: T;
  status: number;
  message: string;
  timestamp: string;
  requestId: string;
}

/**
 * API Error response interface with detailed error information
 */
export interface APIError {
  code: string;
  message: string;
  details: Record<string, any>;
  timestamp: string;
  requestId: string;
  path: string;
}

/**
 * Generic paginated response interface
 * @template T - Type of items being paginated
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

/**
 * Enhanced interface for API request configuration with security features
 */
export interface RequestConfig {
  headers: {
    'X-CSRF-Token': string;
    'Authorization': string;
    'Content-Type'?: string;
    'Accept'?: string;
    'X-Request-ID'?: string;
  };
  params?: Record<string, any>;
  timeout: number;
  retryConfig: {
    maxRetries: number;
    retryDelay: number;
    retryCondition: (error: any) => boolean;
  };
  securityHeaders: {
    contentSecurityPolicy: string;
    strictTransportSecurity: string;
    xFrameOptions: string;
    xContentTypeOptions: 'nosniff';
    referrerPolicy: string;
  };
}

/**
 * Enhanced interface for secure file upload configuration
 */
export interface UploadConfig {
  contentType: string[];
  maxSize: number;
  allowedTypes: string[];
  virusScan: {
    enabled: boolean;
    provider: string;
    timeout: number;
  };
  encryption: {
    enabled: boolean;
    algorithm: string;
    keySize: number;
  };
  validation: {
    checksumAlgorithm: string;
    validateMimeType: boolean;
    sanitizeFilename: boolean;
  };
}

/**
 * Type guard to check if a response is an API Error
 */
export function isAPIError(response: any): response is APIError {
  return (
    response &&
    typeof response.code === 'string' &&
    typeof response.message === 'string' &&
    typeof response.details === 'object'
  );
}

/**
 * Type guard to check if a response is a successful API Response
 */
export function isAPIResponse<T>(response: any): response is APIResponse<T> {
  return (
    response &&
    response.data !== undefined &&
    typeof response.status === 'number' &&
    typeof response.message === 'string'
  );
}

/**
 * Response type combining successful and error responses
 */
export type ResponseType<T> = APIResponse<T> | APIError;

/**
 * Validation utility to assert valid API response
 */
export function assertValidResponse<T>(
  response: ResponseType<T>
): asserts response is APIResponse<T> {
  if (isAPIError(response)) {
    throw new Error(`API Error: ${response.message} (${response.code})`);
  }
}

// Global constants
export const API_VERSION = 'v1';
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

/**
 * API Endpoints configuration
 */
export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    REGISTER: '/auth/register',
    MFA_SETUP: '/auth/mfa/setup',
    MFA_VERIFY: '/auth/mfa/verify',
  },
  PROTOCOLS: {
    BASE: '/protocols',
    DETAIL: (id: string) => `/protocols/${id}`,
    ENROLL: (id: string) => `/protocols/${id}/enroll`,
    PARTICIPANTS: (id: string) => `/protocols/${id}/participants`,
  },
  DATA_POINTS: {
    BASE: '/data-points',
    DETAIL: (id: string) => `/data-points/${id}`,
    UPLOAD: '/data-points/upload',
    VALIDATE: '/data-points/validate',
  },
  ANALYSIS: {
    BASE: '/analysis',
    PROTOCOL: (id: string) => `/analysis/protocols/${id}`,
    EXPORT: (id: string) => `/analysis/export/${id}`,
  },
} as const;

/**
 * Default request configuration
 */
export const DEFAULT_REQUEST_CONFIG: RequestConfig = {
  headers: {
    'X-CSRF-Token': '',
    'Authorization': '',
  },
  timeout: 30000,
  retryConfig: {
    maxRetries: 3,
    retryDelay: 1000,
    retryCondition: (error: any) => {
      return error.status === 429 || (error.status >= 500 && error.status <= 599);
    },
  },
  securityHeaders: {
    contentSecurityPolicy: "default-src 'self'",
    strictTransportSecurity: 'max-age=31536000; includeSubDomains',
    xFrameOptions: 'DENY',
    xContentTypeOptions: 'nosniff',
    referrerPolicy: 'strict-origin-when-cross-origin',
  },
};

/**
 * Default upload configuration
 */
export const DEFAULT_UPLOAD_CONFIG: UploadConfig = {
  contentType: ['application/json', 'application/pdf', 'image/jpeg', 'image/png'],
  maxSize: MAX_FILE_SIZE,
  allowedTypes: ['.json', '.pdf', '.jpg', '.jpeg', '.png'],
  virusScan: {
    enabled: true,
    provider: 'clamav',
    timeout: 30000,
  },
  encryption: {
    enabled: true,
    algorithm: 'AES-256-GCM',
    keySize: 256,
  },
  validation: {
    checksumAlgorithm: 'SHA-256',
    validateMimeType: true,
    sanitizeFilename: true,
  },
};