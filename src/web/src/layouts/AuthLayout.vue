<template>
  <div 
    class="auth-layout" 
    role="main" 
    aria-live="polite"
  >
    <!-- Logo and Branding Section -->
    <div class="auth-branding">
      <img 
        src="@/assets/logo.svg" 
        alt="Medical Research Platform Logo" 
        class="auth-logo"
        width="180" 
        height="48"
      />
    </div>

    <!-- Main Authentication Content Area -->
    <main class="auth-content" aria-label="Authentication Form">
      <!-- Loading Overlay -->
      <div 
        v-if="authLoading" 
        class="auth-loading" 
        role="alert" 
        aria-busy="true"
      >
        <span class="sr-only">Loading authentication...</span>
        <div class="loading-spinner" aria-hidden="true"></div>
      </div>

      <!-- Router View for Auth Components -->
      <router-view v-slot="{ Component }">
        <transition 
          name="fade" 
          mode="out-in"
          @enter="handleTransitionEnter"
          @leave="handleTransitionLeave"
        >
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- Footer Section -->
    <footer class="auth-footer">
      <nav aria-label="Legal Links">
        <ul class="footer-links">
          <li>
            <a 
              href="/privacy" 
              class="footer-link"
              target="_blank"
              rel="noopener noreferrer"
            >
              Privacy Policy
            </a>
          </li>
          <li>
            <a 
              href="/terms" 
              class="footer-link"
              target="_blank"
              rel="noopener noreferrer"
            >
              Terms of Service
            </a>
          </li>
          <li>
            <a 
              href="/help" 
              class="footer-link"
              target="_blank"
              rel="noopener noreferrer"
            >
              Help Center
            </a>
          </li>
        </ul>
      </nav>
    </footer>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, watchEffect } from 'vue'; // ^3.3.0
import { useRouter } from 'vue-router'; // ^4.2.0
import { useAuthStore } from '@/stores/auth';
import { ROUTE_NAMES } from '@/router/routes';

export default defineComponent({
  name: 'AuthLayout',

  setup() {
    const router = useRouter();
    const authStore = useAuthStore();
    const { isAuthenticated, authLoading } = authStore;

    /**
     * Checks authentication state and handles secure redirects
     */
    const checkAuthState = async (): Promise<void> => {
      try {
        // Redirect authenticated users to dashboard
        if (isAuthenticated.value) {
          await router.push({ name: ROUTE_NAMES.DASHBOARD });
        }
      } catch (error) {
        console.error('Auth state check error:', error);
      }
    };

    // Watch for authentication state changes
    watchEffect(() => {
      if (!authLoading.value) {
        checkAuthState();
      }
    });

    // Initialize auth check on mount
    onMounted(() => {
      checkAuthState();
    });

    /**
     * Handles enter transition accessibility
     */
    const handleTransitionEnter = (el: Element): void => {
      el.setAttribute('aria-hidden', 'false');
    };

    /**
     * Handles leave transition accessibility
     */
    const handleTransitionLeave = (el: Element): void => {
      el.setAttribute('aria-hidden', 'true');
    };

    return {
      authLoading,
      handleTransitionEnter,
      handleTransitionLeave
    };
  }
});
</script>

<style scoped>
.auth-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-6);
  background-color: var(--color-background);
  color: var(--color-text);
  position: relative;
}

.auth-branding {
  margin-bottom: var(--spacing-8);
  text-align: center;
}

.auth-logo {
  max-width: 180px;
  height: auto;
}

.auth-content {
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
  padding: var(--spacing-8);
  background-color: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  position: relative;
}

.auth-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--color-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-overlay);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--color-primary);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.auth-footer {
  margin-top: var(--spacing-8);
  text-align: center;
}

.footer-links {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  gap: var(--spacing-4);
  justify-content: center;
}

.footer-link {
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: 0.875rem;
  transition: color 0.2s ease;
}

.footer-link:hover,
.footer-link:focus {
  color: var(--color-primary);
  text-decoration: underline;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Responsive Breakpoints */
@media (max-width: 767px) {
  .auth-content {
    padding: var(--spacing-6);
  }

  .footer-links {
    flex-direction: column;
    gap: var(--spacing-2);
  }
}

@media (min-width: 768px) and (max-width: 1023px) {
  .auth-content {
    max-width: 480px;
  }
}

@media (min-width: 1024px) {
  .auth-content {
    max-width: 400px;
  }
}
</style>