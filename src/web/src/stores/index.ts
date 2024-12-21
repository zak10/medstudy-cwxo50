/**
 * Root Pinia Store Configuration
 * @package @medical-research-platform/web
 * @version 1.0.0
 */

// External imports
import { createPinia, type Pinia } from 'pinia'; // v2.1.0
import { markRaw } from 'vue'; // v3.3.0

// Internal store imports
import { useAnalysisStore } from './analysis';
import { useAuthStore } from './auth';
import { useUiStore } from './ui';

// Store version for state management and migrations
const STORE_VERSION = '1.0.0';

/**
 * Creates and configures the root Pinia store instance with all necessary plugins,
 * development tools, and state management features
 */
export function createStore(): Pinia {
  const pinia = createPinia();

  // Configure store with Vue Router for navigation guards
  pinia.use(({ store }) => {
    store.$router = markRaw(router);
  });

  // State hydration/rehydration handling
  pinia.use(({ store }) => {
    // Save initial state for potential reset
    const initialState = JSON.parse(JSON.stringify(store.$state));

    // Add reset capability to all stores
    store.$reset = () => {
      store.$patch(initialState);
    };

    // Version tracking for state migrations
    store.$version = STORE_VERSION;
  });

  // Development tools configuration
  if (process.env.NODE_ENV === 'development') {
    pinia.use(({ store }) => {
      store.$subscribe((mutation, state) => {
        console.log(`[🍍 Pinia] ${mutation.type} on ${mutation.storeId}`, mutation.payload);
      });
    });
  }

  // Error handling and logging
  pinia.use(({ store }) => {
    store.$onError((error) => {
      console.error(`[Store Error] ${store.$id}:`, error);
      useUiStore().notifyError(`Store error: ${error.message}`);
    });
  });

  // Performance optimizations
  pinia.use(({ options, store }) => {
    // Mark non-reactive properties
    if (options.nonReactive) {
      options.nonReactive.forEach((prop) => {
        store[prop] = markRaw(store[prop]);
      });
    }
  });

  return pinia;
}

// Export configured store instance
export const pinia = createStore();

// Export individual store modules
export {
  useAnalysisStore,
  useAuthStore,
  useUiStore
};

// Export store version for external use
export const storeVersion = STORE_VERSION;

// Type definitions for store instance
declare module 'pinia' {
  export interface PiniaCustomProperties {
    $version: string;
    $reset: () => void;
    $router: Router;
  }
}

// Type definitions for store error handling
export interface StoreError extends Error {
  storeId: string;
  actionName?: string;
}

// Export store initialization function for application bootstrap
export function initializeStores() {
  const authStore = useAuthStore();
  const uiStore = useUiStore();

  // Initialize authentication state
  authStore.initializeAuth().catch((error) => {
    console.error('Failed to initialize auth store:', error);
    uiStore.notifyError('Failed to restore authentication state');
  });

  // Initialize UI state (theme, breakpoints)
  uiStore.updateBreakpoint();

  return {
    authStore,
    uiStore
  };
}