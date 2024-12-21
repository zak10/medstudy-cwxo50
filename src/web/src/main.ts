/**
 * Main Application Entry Point
 * @package @medical-research-platform/web
 * @version 1.0.0
 */

import { createApp } from 'vue'; // ^3.3.0
import { createVuetify } from 'vuetify'; // ^3.3.0
import VueAxios from 'vue-axios'; // ^3.5.0
import axios from 'axios'; // ^1.4.0
import * as Sentry from '@sentry/vue'; // ^7.0.0
import VueGtag from 'vue-gtag'; // ^2.0.0

// Internal imports
import App from './App.vue';
import { router } from './router';
import { pinia, initializeStores } from './stores';
import { theme } from './config/theme';
import { API_CONFIG } from './config/api';

/**
 * Configures global Axios instance with security and performance settings
 */
function configureAxios() {
  const instance = axios.create({
    baseURL: API_CONFIG.BASE_URL,
    timeout: API_CONFIG.TIMEOUT,
    headers: API_CONFIG.HEADERS,
    withCredentials: true
  });

  // Request interceptor for authentication
  instance.interceptors.request.use(
    (config) => {
      // Add CSRF token
      const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
      if (token) {
        config.headers['X-CSRF-Token'] = token;
      }

      // Add request ID for tracing
      config.headers['X-Request-ID'] = crypto.randomUUID();

      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor for error handling
  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      if (error.response?.status === 401) {
        router.push({ name: 'login' });
      }
      return Promise.reject(error);
    }
  );

  return instance;
}

/**
 * Configures Vuetify with theme and responsive settings
 */
function setupVuetify() {
  return createVuetify({
    theme: {
      defaultTheme: 'light',
      themes: {
        light: theme.colors,
      }
    },
    defaults: {
      global: {
        ripple: false,
      },
      VBtn: {
        variant: 'elevated',
      }
    }
  });
}

/**
 * Configures Sentry for error tracking and performance monitoring
 */
function configureSentry(app: any) {
  if (process.env.VUE_APP_SENTRY_DSN) {
    Sentry.init({
      app,
      dsn: process.env.VUE_APP_SENTRY_DSN,
      integrations: [
        new Sentry.BrowserTracing({
          routingInstrumentation: Sentry.vueRouterInstrumentation(router),
          tracingOrigins: ['localhost', process.env.VUE_APP_API_URL],
        }),
      ],
      tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.2 : 1.0,
      environment: process.env.NODE_ENV,
      beforeSend(event) {
        // Sanitize sensitive data
        if (event.request?.headers) {
          delete event.request.headers['Authorization'];
        }
        return event;
      },
    });
  }
}

// Create and configure Vue application
const app = createApp(App);

// Configure global properties and plugins
app.use(pinia);
app.use(router);
app.use(setupVuetify());
app.use(VueAxios, configureAxios());

// Configure analytics in production
if (process.env.NODE_ENV === 'production' && process.env.VUE_APP_GA_ID) {
  app.use(VueGtag, {
    config: { id: process.env.VUE_APP_GA_ID },
    appName: 'Medical Research Platform',
    pageTrackerScreenviewEnabled: true,
    router
  });
}

// Configure error tracking
configureSentry(app);

// Initialize stores
initializeStores();

// Mount application
app.mount('#app');

// Export app instance for testing
export { app };