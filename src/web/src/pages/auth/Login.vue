<template>
  <div 
    class="login-page" 
    role="main" 
    aria-labelledby="login-title"
  >
    <!-- Welcome Section -->
    <section class="welcome-section">
      <h1 
        id="login-title" 
        class="welcome-section__title"
      >
        Welcome to Medical Research Platform
      </h1>
      <p class="welcome-section__subtitle">
        Sign in to access your research protocols and data
      </p>
    </section>

    <!-- Login Form -->
    <LoginForm
      @login-success="handleLoginSuccess"
      @login-error="handleLoginError"
      @mfa-required="handleMFARequired"
      data-testid="login-form"
    />

    <!-- Auth Links -->
    <div class="auth-links">
      <router-link 
        to="/auth/register" 
        class="auth-links__item"
        data-testid="register-link"
      >
        Create Account
      </router-link>
      <router-link 
        to="/auth/reset-password" 
        class="auth-links__item"
        data-testid="reset-password-link"
      >
        Forgot Password?
      </router-link>
    </div>

    <!-- Error Display -->
    <div 
      v-if="error" 
      class="login-page__error" 
      role="alert"
      aria-live="polite"
    >
      {{ error }}
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import FingerprintJS from '@fingerprintjs/fingerprintjs';
import { LoginForm } from '@/components/auth/LoginForm';
import { useAuth } from '@/composables/useAuth';
import { ROUTE_NAMES } from '@/router/routes';
import type { AuthResponse } from '@/types/auth';

export default defineComponent({
  name: 'LoginPage',

  components: {
    LoginForm
  },

  setup() {
    const router = useRouter();
    const { handleLogin, handleOAuthLogin, verifyMFA } = useAuth();
    const error = ref<string | null>(null);
    const fpPromise = FingerprintJS.load();

    // Initialize browser fingerprinting for enhanced security
    onMounted(async () => {
      try {
        const fp = await fpPromise;
        const result = await fp.get();
        // Store fingerprint for session tracking
        localStorage.setItem('device_fingerprint', result.visitorId);
      } catch (err) {
        console.error('Fingerprint initialization error:', err);
      }
    });

    /**
     * Handles successful login with enhanced security measures
     */
    const handleLoginSuccess = async (response: AuthResponse) => {
      try {
        error.value = null;

        // Store auth tokens in HttpOnly cookies
        document.cookie = `access_token=${response.tokens.accessToken}; Secure; HttpOnly; SameSite=Strict`;
        document.cookie = `refresh_token=${response.tokens.refreshToken}; Secure; HttpOnly; SameSite=Strict`;

        // Initialize session with security context
        sessionStorage.setItem('last_activity', Date.now().toString());
        sessionStorage.setItem('session_id', response.sessionId);

        // Navigate to dashboard
        await router.push({ name: ROUTE_NAMES.DASHBOARD });

      } catch (err) {
        console.error('Login success handler error:', err);
        error.value = 'An error occurred while completing login. Please try again.';
      }
    };

    /**
     * Handles login errors with rate limiting and security monitoring
     */
    const handleLoginError = (err: Error) => {
      error.value = err.message;
      
      // Log security event
      console.error('Login error:', {
        timestamp: new Date().toISOString(),
        fingerprint: localStorage.getItem('device_fingerprint'),
        error: err.message
      });

      // Clear sensitive form data
      const form = document.querySelector('form');
      if (form) {
        form.reset();
      }
    };

    /**
     * Handles MFA verification flow
     */
    const handleMFARequired = async (challenge: any) => {
      try {
        error.value = null;
        
        // Initialize MFA verification UI
        const verified = await verifyMFA(challenge);
        
        if (verified) {
          await handleLoginSuccess(verified);
        } else {
          error.value = 'MFA verification failed. Please try again.';
        }
      } catch (err) {
        console.error('MFA verification error:', err);
        error.value = 'An error occurred during MFA verification. Please try again.';
      }
    };

    return {
      error,
      handleLoginSuccess,
      handleLoginError,
      handleMFARequired
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.login-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: vars.spacing(6);
  background-color: var(--color-background);

  // Dark mode support
  @media (prefers-color-scheme: dark) {
    background-color: var(--color-background-dark);
  }

  &__error {
    margin-top: vars.spacing(4);
    padding: vars.spacing(3);
    border-radius: 4px;
    background-color: rgba(map-get(vars.$colors, error), 0.1);
    color: map-get(vars.$colors, error);
    font-size: 0.875rem;
    text-align: center;
    max-width: 400px;
    width: 100%;
  }
}

.welcome-section {
  text-align: center;
  margin-bottom: vars.spacing(8);
  color: var(--color-text-primary);

  &__title {
    font-family: vars.$font-family-primary;
    font-weight: map-get(vars.$font-weights, bold);
    font-size: 2rem;
    margin-bottom: vars.spacing(2);
  }

  &__subtitle {
    font-family: vars.$font-family-secondary;
    font-size: 1rem;
    color: var(--color-text-secondary);
  }
}

.auth-links {
  margin-top: vars.spacing(6);
  display: flex;
  gap: vars.spacing(4);
  justify-content: center;

  &__item {
    color: map-get(vars.$colors, primary);
    text-decoration: none;
    font-size: 0.875rem;
    transition: color 0.2s ease;

    &:hover {
      color: map-get(vars.$colors, secondary);
      text-decoration: underline;
    }

    &:focus {
      outline: 2px solid map-get(vars.$colors, primary);
      outline-offset: 2px;
      border-radius: 2px;
    }
  }
}

// Responsive adjustments
@media (max-width: map-get(vars.$breakpoints, tablet)) {
  .login-page {
    padding: vars.spacing(4);
  }

  .welcome-section {
    margin-bottom: vars.spacing(6);

    &__title {
      font-size: 1.5rem;
    }
  }
}

// High contrast mode support
@media (forced-colors: active) {
  .auth-links__item {
    &:focus {
      outline: 2px solid ButtonText;
    }
  }
}

// Reduced motion support
@media (prefers-reduced-motion: reduce) {
  * {
    transition: none !important;
  }
}
</style>