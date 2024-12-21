/**
 * Vue Router Navigation Guards
 * Implements secure route protection with authentication, RBAC, and MFA verification
 * @package @medical-research-platform/web
 * @version 1.0.0
 */

import { NavigationGuard, RouteLocationNormalized } from 'vue-router'; // ^4.2.0
import { useAuthStore } from '../stores/auth';
import { AuthState, UserRole } from '../types/auth';

// Constants for route protection
const PUBLIC_ROUTES = [
  '/auth/login',
  '/auth/register',
  '/auth/reset-password',
  '/auth/oauth/callback',
  '/auth/mfa/verify'
];

// Timeouts for security features (in milliseconds)
const MFA_TIMEOUT = 30 * 60 * 1000; // 30 minutes
const SESSION_TIMEOUT = 24 * 60 * 60 * 1000; // 24 hours

/**
 * Enhanced navigation guard for authentication state verification
 * Handles OAuth flows and session management
 */
export const authGuard: NavigationGuard = async (
  to: RouteLocationNormalized,
  from: RouteLocationNormalized
) => {
  const auth = useAuthStore();
  const lastActivity = Number(sessionStorage.getItem('lastActivityTime')) || 0;
  const currentTime = Date.now();

  // Allow access to public routes
  if (PUBLIC_ROUTES.includes(to.path)) {
    return true;
  }

  // Check for session timeout
  if (currentTime - lastActivity > SESSION_TIMEOUT && auth.isAuthenticated) {
    await auth.logout();
    return {
      name: 'login',
      query: { 
        redirect: to.fullPath,
        reason: 'session_timeout'
      }
    };
  }

  // Update last activity timestamp
  sessionStorage.setItem('lastActivityTime', currentTime.toString());

  // Handle different authentication states
  switch (auth.authState) {
    case AuthState.AUTHENTICATED:
      return true;

    case AuthState.MFA_REQUIRED:
      return {
        name: 'mfa-verify',
        query: { redirect: to.fullPath }
      };

    case AuthState.OAUTH_PENDING:
      return {
        name: 'oauth-callback',
        query: { redirect: to.fullPath }
      };

    default:
      return {
        name: 'login',
        query: { redirect: to.fullPath }
      };
  }
};

/**
 * Enhanced navigation guard for role-based access control
 * Implements strict role validation with audit logging
 */
export const roleGuard: NavigationGuard = (
  to: RouteLocationNormalized,
  from: RouteLocationNormalized
) => {
  const auth = useAuthStore();
  const requiredRoles = to.meta.requiredRoles as UserRole[];

  // Skip role check if no roles are required
  if (!requiredRoles || requiredRoles.length === 0) {
    return true;
  }

  // Verify authentication and role requirements
  if (!auth.isAuthenticated || !auth.user) {
    console.warn(`Access denied: User not authenticated - Route: ${to.path}`);
    return { name: 'login' };
  }

  // Check if user has required role
  const hasRequiredRole = requiredRoles.some(role => auth.hasRole(role));
  
  // Log access attempt for audit
  console.info(`Role access attempt - User: ${auth.user.email}, Route: ${to.path}, Granted: ${hasRequiredRole}`);

  if (!hasRequiredRole) {
    return { name: 'unauthorized' };
  }

  return true;
};

/**
 * Advanced navigation guard for MFA verification
 * Implements enhanced session management and verification flows
 */
export const mfaGuard: NavigationGuard = (
  to: RouteLocationNormalized,
  from: RouteLocationNormalized
) => {
  const auth = useAuthStore();
  const requiresMFA = to.meta.requiresMFA as boolean;
  const lastMFAVerification = Number(sessionStorage.getItem('lastMFAVerification')) || 0;
  const currentTime = Date.now();

  // Skip MFA check if not required for route
  if (!requiresMFA) {
    return true;
  }

  // Verify authentication state
  if (!auth.isAuthenticated) {
    return { name: 'login' };
  }

  // Check if user has MFA enabled
  if (!auth.user?.mfaEnabled) {
    console.warn(`MFA required but not enabled for user: ${auth.user?.email}`);
    return { name: 'mfa-setup' };
  }

  // Verify MFA timeout
  if (currentTime - lastMFAVerification > MFA_TIMEOUT) {
    sessionStorage.removeItem('lastMFAVerification');
    return {
      name: 'mfa-verify',
      query: { redirect: to.fullPath }
    };
  }

  // Update MFA verification timestamp
  sessionStorage.setItem('lastMFAVerification', currentTime.toString());
  return true;
};