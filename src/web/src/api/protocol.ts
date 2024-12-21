// @version axios ^1.4.0
import axios, { AxiosError } from 'axios';

// Internal imports
import { APIResponse, APIError, PaginatedResponse, isAPIError } from './types';
import { Protocol, ProtocolStatus, ProtocolSchema } from '../types/protocol';
import { ENDPOINTS, API_CONFIG, getEndpointUrl, handleRetry } from '../config/api';

/**
 * Default pagination size for protocol listing
 */
const DEFAULT_PAGE_SIZE = 20;

/**
 * Request timeout in milliseconds
 */
const REQUEST_TIMEOUT_MS = 5000;

/**
 * Maximum number of retry attempts
 */
const MAX_RETRIES = 3;

/**
 * Interface for protocol filtering options
 */
interface ProtocolFilters {
  title?: string;
  duration?: number;
  status?: ProtocolStatus;
  participantCount?: number;
}

/**
 * Interface for protocol enrollment data
 */
interface EnrollmentData {
  consent: boolean;
  initialData: Record<string, any>;
}

/**
 * Interface for protocol participation response
 */
interface ProtocolParticipation {
  id: string;
  protocolId: string;
  userId: string;
  status: 'ACTIVE' | 'COMPLETED' | 'WITHDRAWN';
  enrolledAt: string;
  completedAt?: string;
}

/**
 * Fetches a paginated list of available protocols
 * @param params - Pagination and filtering parameters
 * @returns Promise with paginated protocol list
 */
export async function getProtocols(params?: {
  page?: number;
  pageSize?: number;
  status?: ProtocolStatus;
  filters?: ProtocolFilters;
}): Promise<APIResponse<PaginatedResponse<Protocol>>> {
  try {
    const queryParams = {
      page: params?.page || 1,
      pageSize: params?.pageSize || DEFAULT_PAGE_SIZE,
      status: params?.status,
      ...params?.filters
    };

    const response = await axios.get<APIResponse<PaginatedResponse<Protocol>>>(
      getEndpointUrl(ENDPOINTS.PROTOCOL.LIST),
      {
        params: queryParams,
        headers: {
          ...API_CONFIG.HEADERS,
          'X-Request-ID': crypto.randomUUID()
        },
        timeout: REQUEST_TIMEOUT_MS,
        validateStatus: (status) => status === 200
      }
    );

    // Validate response data against schema
    response.data.data.items.forEach(protocol => {
      const validation = ProtocolSchema.safeParse(protocol);
      if (!validation.success) {
        throw new Error('Invalid protocol data received from server');
      }
    });

    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw {
        code: error.response?.status?.toString() || '500',
        message: error.response?.data?.message || 'Failed to fetch protocols',
        details: error.response?.data
      } as APIError;
    }
    throw error;
  }
}

/**
 * Fetches detailed information for a specific protocol
 * @param id - Protocol identifier
 * @returns Promise with protocol details
 */
export async function getProtocolById(id: string): Promise<APIResponse<Protocol>> {
  try {
    if (!id || typeof id !== 'string') {
      throw new Error('Invalid protocol ID');
    }

    const response = await axios.get<APIResponse<Protocol>>(
      getEndpointUrl(ENDPOINTS.PROTOCOL.DETAIL, { id }),
      {
        headers: {
          ...API_CONFIG.HEADERS,
          'X-Request-ID': crypto.randomUUID()
        },
        timeout: REQUEST_TIMEOUT_MS,
        validateStatus: (status) => status === 200
      }
    );

    // Validate response data
    const validation = ProtocolSchema.safeParse(response.data.data);
    if (!validation.success) {
      throw new Error('Invalid protocol data received from server');
    }

    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw {
        code: error.response?.status?.toString() || '500',
        message: error.response?.data?.message || 'Failed to fetch protocol details',
        details: error.response?.data
      } as APIError;
    }
    throw error;
  }
}

/**
 * Enrolls the authenticated user in a protocol
 * @param protocolId - Protocol identifier
 * @param enrollmentData - Enrollment data including consent and initial measurements
 * @returns Promise with enrollment confirmation
 */
export async function enrollInProtocol(
  protocolId: string,
  enrollmentData: EnrollmentData
): Promise<APIResponse<ProtocolParticipation>> {
  try {
    if (!protocolId || typeof protocolId !== 'string') {
      throw new Error('Invalid protocol ID');
    }

    if (!enrollmentData.consent) {
      throw new Error('User consent is required for enrollment');
    }

    const response = await axios.post<APIResponse<ProtocolParticipation>>(
      getEndpointUrl(ENDPOINTS.PROTOCOL.ENROLL, { id: protocolId }),
      enrollmentData,
      {
        headers: {
          ...API_CONFIG.HEADERS,
          'X-Request-ID': crypto.randomUUID(),
          'Content-Type': 'application/json'
        },
        timeout: REQUEST_TIMEOUT_MS,
        validateStatus: (status) => status === 201,
        retry: MAX_RETRIES,
        retryCondition: (error: AxiosError) => handleRetry(error, error.config?.retry || 0)
      }
    );

    return response.data;
  } catch (error) {
    if (error instanceof AxiosError) {
      throw {
        code: error.response?.status?.toString() || '500',
        message: error.response?.data?.message || 'Failed to enroll in protocol',
        details: error.response?.data
      } as APIError;
    }
    throw error;
  }
}