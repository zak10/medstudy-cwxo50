import { afterEach, beforeEach, vi } from 'vitest';
import { config } from '@vue/test-utils';
import { createVuetify } from 'vuetify';

/**
 * Creates a Vuetify instance configured specifically for testing environment
 * @returns Configured Vuetify instance with testing optimizations
 */
const createTestingVuetify = () => {
  return createVuetify({
    // Test-specific theme configuration
    theme: {
      defaultTheme: 'light',
      themes: {
        light: {
          colors: {
            primary: '#2C3E50',
            secondary: '#3498DB',
            accent: '#E74C3C'
          }
        }
      }
    },
    // Disable transitions for testing
    defaults: {
      global: {
        ripple: false
      },
      VBtn: {
        variant: 'contained'
      }
    }
  });
};

// Create and export Vuetify instance for component tests
export const vuetify = createTestingVuetify();

/**
 * Configures global Vue Test Utils settings with type-safe component stubs
 * and mounting options
 */
export const setupVueTestUtils = (): void => {
  // Configure global component stubs
  config.global.stubs = {
    transition: false,
    'transition-group': false
  };

  // Configure global mounting options
  config.global.provide = {
    vuetify: vuetify
  };

  // Set up global plugins
  config.global.plugins = [vuetify];

  // Configure error handler for component mounting failures
  config.global.config = {
    warnHandler: (msg: string) => {
      // Ignore specific warnings during testing
      if (msg.includes('Unknown custom element')) return;
      console.warn(msg);
    }
  };
};

/**
 * Sets up comprehensive global mocks for browser APIs and utilities
 * with error handling
 */
export const setupGlobalMocks = (): void => {
  // Mock window.matchMedia
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn()
    }))
  });

  // Mock ResizeObserver
  window.ResizeObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn()
  }));

  // Mock IntersectionObserver
  window.IntersectionObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
    root: null,
    rootMargin: '',
    thresholds: []
  }));

  // Mock localStorage with type-safe operations
  const localStorageMock = (() => {
    let store: { [key: string]: string } = {};
    return {
      getItem: vi.fn((key: string): string | null => store[key] || null),
      setItem: vi.fn((key: string, value: string): void => {
        store[key] = value.toString();
      }),
      removeItem: vi.fn((key: string): void => {
        delete store[key];
      }),
      clear: vi.fn((): void => {
        store = {};
      })
    };
  })();
  Object.defineProperty(window, 'localStorage', { value: localStorageMock });

  // Mock sessionStorage
  const sessionStorageMock = (() => {
    let store: { [key: string]: string } = {};
    return {
      getItem: vi.fn((key: string): string | null => store[key] || null),
      setItem: vi.fn((key: string, value: string): void => {
        store[key] = value.toString();
      }),
      removeItem: vi.fn((key: string): void => {
        delete store[key];
      }),
      clear: vi.fn((): void => {
        store = {};
      })
    };
  })();
  Object.defineProperty(window, 'sessionStorage', { value: sessionStorageMock });

  // Clean up mocks after each test
  afterEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
    sessionStorageMock.clear();
  });

  // Set up console mocks with error tracking
  const originalConsole = { ...console };
  beforeEach(() => {
    console.error = vi.fn((...args) => {
      // Log errors during testing but don't fail tests
      originalConsole.error(...args);
    });
    console.warn = vi.fn((...args) => {
      // Log warnings during testing but don't fail tests
      originalConsole.warn(...args);
    });
  });
};

// Initialize test environment
setupVueTestUtils();
setupGlobalMocks();