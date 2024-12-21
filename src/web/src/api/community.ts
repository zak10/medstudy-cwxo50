// @version axios ^1.4.0
import { AxiosInstance } from 'axios';

// Internal imports
import { APIResponse } from './types';
import { Forum, Thread, Comment, Message } from '../types/community';

// Constants
const API_VERSION = '/api/v1';
const DEFAULT_PAGE_SIZE = 20;
const MAX_PAGE_SIZE = 100;
const MIN_PAGE_SIZE = 10;

/**
 * Validates pagination parameters
 * @param page Page number
 * @param pageSize Number of items per page
 * @throws Error if parameters are invalid
 */
const validatePagination = (page: number, pageSize: number): void => {
  if (page < 1) {
    throw new Error('Page number must be greater than 0');
  }
  if (pageSize < MIN_PAGE_SIZE || pageSize > MAX_PAGE_SIZE) {
    throw new Error(`Page size must be between ${MIN_PAGE_SIZE} and ${MAX_PAGE_SIZE}`);
  }
};

/**
 * Retrieves paginated list of forums with optional protocol filter
 * @param protocolId Optional protocol ID to filter forums
 * @param page Page number (1-based)
 * @param pageSize Number of items per page
 * @returns Promise resolving to paginated forum list
 */
export const getForums = async (
  protocolId: string | null = null,
  page = 1,
  pageSize = DEFAULT_PAGE_SIZE
): Promise<APIResponse<Forum[]>> => {
  validatePagination(page, pageSize);

  const params: Record<string, any> = {
    page,
    pageSize
  };

  if (protocolId) {
    params.protocolId = protocolId;
  }

  try {
    const response = await axios.get(`${API_VERSION}/forums`, { params });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to fetch forums: ${error.message}`);
  }
};

/**
 * Retrieves paginated list of threads for a specific forum
 * @param forumId Forum ID
 * @param page Page number (1-based)
 * @param pageSize Number of items per page
 * @returns Promise resolving to paginated thread list
 */
export const getThreads = async (
  forumId: string,
  page = 1,
  pageSize = DEFAULT_PAGE_SIZE
): Promise<APIResponse<Thread[]>> => {
  if (!forumId) {
    throw new Error('Forum ID is required');
  }
  validatePagination(page, pageSize);

  try {
    const response = await axios.get(`${API_VERSION}/forums/${forumId}/threads`, {
      params: { page, pageSize }
    });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to fetch threads: ${error.message}`);
  }
};

/**
 * Retrieves paginated list of comments for a specific thread
 * @param threadId Thread ID
 * @param page Page number (1-based)
 * @param pageSize Number of items per page
 * @returns Promise resolving to paginated comment list
 */
export const getComments = async (
  threadId: string,
  page = 1,
  pageSize = DEFAULT_PAGE_SIZE
): Promise<APIResponse<Comment[]>> => {
  if (!threadId) {
    throw new Error('Thread ID is required');
  }
  validatePagination(page, pageSize);

  try {
    const response = await axios.get(`${API_VERSION}/threads/${threadId}/comments`, {
      params: { page, pageSize }
    });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to fetch comments: ${error.message}`);
  }
};

/**
 * Retrieves paginated list of direct messages for authenticated user
 * @param page Page number (1-based)
 * @param pageSize Number of items per page
 * @returns Promise resolving to paginated message list
 */
export const getMessages = async (
  page = 1,
  pageSize = DEFAULT_PAGE_SIZE
): Promise<APIResponse<Message[]>> => {
  validatePagination(page, pageSize);

  try {
    const response = await axios.get(`${API_VERSION}/messages`, {
      params: { page, pageSize }
    });
    return response.data;
  } catch (error) {
    throw new Error(`Failed to fetch messages: ${error.message}`);
  }
};

// Export constants for external use
export {
  DEFAULT_PAGE_SIZE,
  MAX_PAGE_SIZE,
  MIN_PAGE_SIZE
};