import { RouteRecordRaw } from 'vue-router'; // ^4.2.0
import { defineAsyncComponent } from 'vue'; // ^3.3.0

/**
 * Route path constants for the Medical Research Platform
 * @constant
 */
export const ROUTE_PATHS = {
  HOME: '/',
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  RESET_PASSWORD: '/auth/reset-password',
  PROTOCOLS: '/protocols',
  PROTOCOL_DETAILS: '/protocols/:id',
  PROTOCOL_CREATE: '/protocols/create',
  PROTOCOL_EDIT: '/protocols/:id/edit',
  DATA_COLLECTION: '/data/collection/:protocolId',
  DATA_SUBMISSION: '/data/submission/:protocolId',
  DATA_HISTORY: '/data/history/:protocolId',
  ANALYSIS: '/analysis/:protocolId',
  ANALYSIS_EXPORT: '/analysis/:protocolId/export',
  COMMUNITY: '/community',
  COMMUNITY_TOPIC: '/community/topic/:topicId',
  MESSAGES: '/messages',
  MESSAGE_THREAD: '/messages/:threadId',
  PROFILE: '/profile',
  SETTINGS: '/settings'
} as const;

/**
 * Route name constants for type-safe routing
 * @constant
 */
export const ROUTE_NAMES = {
  HOME: 'home',
  LOGIN: 'login',
  REGISTER: 'register',
  RESET_PASSWORD: 'reset-password',
  PROTOCOLS: 'protocols',
  PROTOCOL_DETAILS: 'protocol-details',
  PROTOCOL_CREATE: 'protocol-create',
  PROTOCOL_EDIT: 'protocol-edit',
  DATA_COLLECTION: 'data-collection',
  DATA_SUBMISSION: 'data-submission',
  DATA_HISTORY: 'data-history',
  ANALYSIS: 'analysis',
  ANALYSIS_EXPORT: 'analysis-export',
  COMMUNITY: 'community',
  COMMUNITY_TOPIC: 'community-topic',
  MESSAGES: 'messages',
  MESSAGE_THREAD: 'message-thread',
  PROFILE: 'profile',
  SETTINGS: 'settings'
} as const;

/**
 * Layout types for different sections of the application
 * @constant
 */
export const LAYOUT_TYPES = {
  AUTH: 'auth',
  DEFAULT: 'default',
  PROTOCOL: 'protocol',
  COMMUNITY: 'community',
  ANALYSIS: 'analysis'
} as const;

// Type definitions for better type safety
type RoutePath = typeof ROUTE_PATHS[keyof typeof ROUTE_PATHS];
type RouteName = typeof ROUTE_NAMES[keyof typeof ROUTE_NAMES];
type LayoutType = typeof LAYOUT_TYPES[keyof typeof LAYOUT_TYPES];

/**
 * Gets the route path by route name with type checking
 * @param {RouteName} name - Route name from ROUTE_NAMES
 * @returns {RoutePath} Corresponding route path
 * @throws {Error} If route name is not found
 */
export const getRoutePath = (name: RouteName): RoutePath => {
  const paths = Object.entries(ROUTE_PATHS);
  const matchingPath = paths.find(([key]) => ROUTE_NAMES[key as keyof typeof ROUTE_NAMES] === name);
  
  if (!matchingPath) {
    const availableRoutes = Object.values(ROUTE_NAMES).join(', ');
    throw new Error(`Route name "${name}" not found. Available routes: ${availableRoutes}`);
  }
  
  return matchingPath[1];
};

/**
 * Gets the route name by route path with type checking
 * @param {RoutePath} path - Route path from ROUTE_PATHS
 * @returns {RouteName} Corresponding route name
 * @throws {Error} If route path is not found
 */
export const getRouteName = (path: RoutePath): RouteName => {
  const names = Object.entries(ROUTE_NAMES);
  const matchingName = names.find(([key]) => ROUTE_PATHS[key as keyof typeof ROUTE_PATHS] === path);
  
  if (!matchingName) {
    const availablePaths = Object.values(ROUTE_PATHS).join(', ');
    throw new Error(`Route path "${path}" not found. Available paths: ${availablePaths}`);
  }
  
  return matchingName[1] as RouteName;
};

/**
 * Gets the layout component by layout type using dynamic import
 * @param {LayoutType} layoutType - Layout type from LAYOUT_TYPES
 * @returns {Promise<Component>} Dynamically imported layout component
 * @throws {Error} If layout type is invalid
 */
export const getLayoutComponent = (layoutType: LayoutType) => {
  if (!Object.values(LAYOUT_TYPES).includes(layoutType)) {
    const availableLayouts = Object.values(LAYOUT_TYPES).join(', ');
    throw new Error(`Invalid layout type "${layoutType}". Available layouts: ${availableLayouts}`);
  }

  return defineAsyncComponent({
    loader: () => import(`@/layouts/${layoutType}Layout.vue`),
    loadingComponent: () => import('@/components/common/LoadingSpinner.vue'),
    errorComponent: () => import('@/components/common/ErrorMessage.vue'),
    delay: 200,
    timeout: 5000,
    suspensible: true,
    onError(error, retry, fail) {
      if (error.message.includes('Failed to fetch')) {
        // Retry on network errors
        retry();
      } else {
        // Log error and fail on other errors
        console.error(`Failed to load layout component: ${error}`);
        fail();
      }
    }
  });
};

// Export type definitions for use in other files
export type { RoutePath, RouteName, LayoutType };