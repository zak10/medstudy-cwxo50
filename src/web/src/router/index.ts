/**
 * Vue Router Configuration
 * Implements secure routing with authentication, RBAC, and geographic restrictions
 * @package @medical-research-platform/web
 * @version 1.0.0
 */

import { createRouter, createWebHistory, Router, RouteLocationNormalized } from 'vue-router'; // ^4.2.0
import routes from './routes';
import { authGuard, roleGuard, mfaGuard } from './guards';

// Constants for navigation configuration
const DEFAULT_TITLE = 'Medical Research Platform';
const ALLOWED_COUNTRY = 'US';

/**
 * Enhanced route meta interface for security and verification requirements
 */
interface RouteMeta {
  /** Whether route requires authentication */
  requiresAuth: boolean;
  /** Allowed user roles for access */
  allowedRoles?: string[];
  /** Whether route requires MFA verification */
  requiresMfa?: boolean;
  /** Route title for navigation */
  title: string;
}

/**
 * Create router instance with HTML5 history mode
 */
const router: Router = createRouter({
  history: createWebHistory(),
  routes,
  // Restore scroll position for navigation
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    }
    return { top: 0 };
  }
});

/**
 * Configure global navigation guards with enhanced security
 * @param router Vue Router instance
 */
function setupNavigationGuards(router: Router): void {
  // Geographic restriction check
  router.beforeEach(async (to: RouteLocationNormalized) => {
    if (to.meta.restrictToUS) {
      try {
        const response = await fetch('https://api.ipstack.com/check?access_key=YOUR_API_KEY');
        const data = await response.json();
        if (data.country_code !== ALLOWED_COUNTRY) {
          return {
            name: 'geographicRestriction',
            query: { redirect: to.fullPath }
          };
        }
      } catch (error) {
        console.error('Geographic check failed:', error);
        return false;
      }
    }
    return true;
  });

  // Authentication guard
  router.beforeEach(authGuard);

  // Role-based access control
  router.beforeEach(roleGuard);

  // MFA verification
  router.beforeEach(mfaGuard);

  // Route meta validation
  router.beforeEach((to: RouteLocationNormalized) => {
    if (to.meta.requiresAuth === undefined) {
      console.warn(`Route ${to.path} is missing requiresAuth meta property`);
    }
    return true;
  });

  // Navigation event logging
  router.afterEach((to: RouteLocationNormalized) => {
    console.info(`Navigation to: ${to.path}`, {
      name: to.name,
      params: to.params,
      query: to.query,
      meta: to.meta
    });
  });

  // Document title updates
  router.afterEach((to: RouteLocationNormalized) => {
    document.title = to.meta.title 
      ? `${to.meta.title} | ${DEFAULT_TITLE}`
      : DEFAULT_TITLE;
  });

  // Navigation error handling
  router.onError((error: Error, to: RouteLocationNormalized, from: RouteLocationNormalized) => {
    handleNavigationError(error, to, from);
  });
}

/**
 * Handle navigation failures and security violations
 * @param error Navigation error
 * @param to Target route
 * @param from Source route
 */
function handleNavigationError(
  error: Error,
  to: RouteLocationNormalized,
  from: RouteLocationNormalized
): void {
  console.error('Navigation error:', {
    error: error.message,
    from: from.path,
    to: to.path,
    meta: to.meta
  });

  // Handle specific navigation failures
  if (error.message.includes('authentication')) {
    router.push({
      name: 'login',
      query: { redirect: to.fullPath }
    });
  } else if (error.message.includes('authorization')) {
    router.push({ name: 'unauthorized' });
  } else if (error.message.includes('geographic')) {
    router.push({ name: 'geographicRestriction' });
  } else if (error.message.includes('mfa')) {
    router.push({
      name: 'mfa-verify',
      query: { redirect: to.fullPath }
    });
  } else {
    router.push({ name: 'error' });
  }
}

// Initialize navigation guards
setupNavigationGuards(router);

export { router };