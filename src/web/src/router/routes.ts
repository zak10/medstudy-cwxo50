/**
 * Vue Router Route Configurations
 * @version 1.0.0
 * @package @medical-research-platform/web
 */

import type { RouteRecordRaw } from 'vue-router' // ^4.2.0
import { UserRole } from '../types/auth'

/**
 * Enhanced route meta interface for security and verification requirements
 */
interface RouteMeta {
  /** Whether route requires authentication */
  requiresAuth: boolean;
  /** Allowed user roles for access */
  allowedRoles?: UserRole[];
  /** Whether route requires MFA verification */
  requiresMfa?: boolean;
  /** Route title for navigation */
  title: string;
  /** Whether route is restricted to US users */
  restrictToUS?: boolean;
  /** Whether route requires age verification */
  requiresAgeVerification?: boolean;
  /** Whether route requires partner verification */
  requiresPartnerVerification?: boolean;
  /** Whether route handles sensitive data */
  sensitiveData?: boolean;
}

/**
 * Route configurations with enhanced security and access control
 */
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('../layouts/DefaultLayout.vue'),
    children: [
      {
        path: '',
        name: 'dashboard',
        component: () => import('../pages/home/Dashboard.vue'),
        meta: {
          requiresAuth: true,
          title: 'Dashboard',
          restrictToUS: true
        }
      }
    ]
  },
  {
    path: '/auth',
    component: () => import('../layouts/AuthLayout.vue'),
    children: [
      {
        path: 'login',
        name: 'login',
        component: () => import('../pages/auth/Login.vue'),
        meta: {
          requiresAuth: false,
          title: 'Login',
          restrictToUS: true
        }
      },
      {
        path: 'register',
        name: 'register',
        component: () => import('../pages/auth/Register.vue'),
        meta: {
          requiresAuth: false,
          title: 'Register',
          restrictToUS: true,
          requiresAgeVerification: true
        }
      }
    ]
  },
  {
    path: '/protocols',
    component: () => import('../layouts/ProtocolLayout.vue'),
    children: [
      {
        path: 'create',
        name: 'protocolCreate',
        component: () => import('../pages/protocol/Create.vue'),
        meta: {
          requiresAuth: true,
          allowedRoles: [UserRole.PROTOCOL_CREATOR],
          requiresMfa: true,
          title: 'Create Protocol',
          restrictToUS: true
        }
      },
      {
        path: 'manage',
        name: 'protocolManage',
        component: () => import('../pages/protocol/Manage.vue'),
        meta: {
          requiresAuth: true,
          allowedRoles: [UserRole.PROTOCOL_CREATOR, UserRole.PARTNER],
          requiresMfa: true,
          title: 'Manage Protocols',
          restrictToUS: true
        }
      }
    ]
  },
  {
    path: '/data',
    component: () => import('../layouts/DefaultLayout.vue'),
    children: [
      {
        path: 'submission',
        name: 'dataSubmission',
        component: () => import('../pages/data/Submission.vue'),
        meta: {
          requiresAuth: true,
          allowedRoles: [UserRole.PARTICIPANT],
          requiresMfa: true,
          title: 'Submit Data',
          restrictToUS: true,
          sensitiveData: true
        }
      }
    ]
  },
  {
    path: '/partner',
    component: () => import('../layouts/PartnerLayout.vue'),
    children: [
      {
        path: 'dashboard',
        name: 'partnerDashboard',
        component: () => import('../pages/partner/Dashboard.vue'),
        meta: {
          requiresAuth: true,
          allowedRoles: [UserRole.PARTNER],
          requiresPartnerVerification: true,
          requiresMfa: true,
          title: 'Partner Dashboard',
          restrictToUS: true
        }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'notFound',
    component: () => import('../pages/error/NotFound.vue'),
    meta: {
      title: 'Page Not Found'
    }
  }
]

export default routes