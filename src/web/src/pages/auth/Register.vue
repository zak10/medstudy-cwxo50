<template>
  <AuthLayout>
    <div 
      class="register-page"
      role="main"
      aria-labelledby="register-title"
    >
      <h1 
        id="register-title"
        class="page-title"
      >
        Create Your Account
      </h1>

      <p class="page-description">
        Join the Medical Research Platform to participate in or create community-driven observational studies.
      </p>

      <!-- Registration Form -->
      <RegisterForm
        @registration-success="handleRegistrationSuccess"
        @registration-error="handleRegistrationError"
        @validation-error="handleValidationError"
      />

      <!-- Login Link -->
      <router-link 
        :to="{ name: ROUTE_NAMES.LOGIN }"
        class="login-link"
      >
        Already have an account? Sign in
      </router-link>

      <!-- Error Message Region -->
      <div 
        v-if="error"
        class="error-message"
        role="alert"
        aria-live="assertive"
      >
        {{ error }}
      </div>

      <!-- Success Message Region -->
      <div
        v-if="success"
        class="success-message"
        role="status"
        aria-live="polite"
      >
        {{ success }}
      </div>
    </div>
  </AuthLayout>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'; // v3.3.0
import AuthLayout from '@/layouts/AuthLayout.vue';
import RegisterForm from '@/components/auth/RegisterForm.vue';
import { useRouter } from 'vue-router';
import { ROUTE_NAMES } from '@/router/routes';
import useNotification from '@/composables/useNotification';
import { UserProfile } from '@/types/auth';

export default defineComponent({
  name: 'RegisterPage',

  components: {
    AuthLayout,
    RegisterForm
  },

  setup() {
    const router = useRouter();
    const notification = useNotification();
    const error = ref<string | null>(null);
    const success = ref<string | null>(null);

    /**
     * Handles successful registration
     * @param user Registered user profile
     */
    const handleRegistrationSuccess = async (user: UserProfile) => {
      try {
        success.value = 'Registration successful! Redirecting to dashboard...';
        notification.showNotification('success', 'Welcome to the Medical Research Platform!');
        
        // Allow time for success message before redirect
        await new Promise(resolve => setTimeout(resolve, 1500));
        await router.push({ name: ROUTE_NAMES.DASHBOARD });
      } catch (err) {
        console.error('Navigation error:', err);
        error.value = 'Error during redirect. Please try logging in.';
      }
    };

    /**
     * Handles registration errors with appropriate user feedback
     * @param err Registration error
     */
    const handleRegistrationError = (err: Error) => {
      error.value = err.message;
      notification.showNotification('error', 'Registration failed. Please try again.');
      console.error('Registration error:', err);
    };

    /**
     * Handles form validation errors
     * @param validationError Validation error details
     */
    const handleValidationError = (validationError: any) => {
      error.value = validationError.message;
      // Focus first invalid field for accessibility
      const firstInvalidField = document.querySelector('[aria-invalid="true"]');
      if (firstInvalidField instanceof HTMLElement) {
        firstInvalidField.focus();
      }
    };

    /**
     * Verifies geographic location on component mount
     */
    onMounted(async () => {
      try {
        const response = await fetch('https://api.ipstack.com/check');
        const data = await response.json();
        
        if (data.country_code !== 'US') {
          error.value = 'Registration is currently only available in the United States.';
          notification.showNotification('error', 'Geographic restriction: US only');
        }
      } catch (err) {
        console.error('Location verification error:', err);
      }
    });

    return {
      error,
      success,
      ROUTE_NAMES,
      handleRegistrationSuccess,
      handleRegistrationError,
      handleValidationError
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;

.register-page {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
  text-align: center;
  min-height: 100vh;
  padding: var(--spacing-4);
}

.page-title {
  font-family: var(--font-heading);
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-4);
  line-height: 1.2;
}

.page-description {
  font-family: var(--font-body);
  font-size: var(--text-base);
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-8);
  max-width: 600px;
  margin-inline: auto;
}

.login-link {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: var(--font-medium);
  margin-top: var(--spacing-4);
  display: inline-block;
  padding: var(--spacing-2);

  &:hover {
    text-decoration: underline;
  }

  &:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
    border-radius: var(--radius-sm);
  }
}

.error-message,
.success-message {
  padding: var(--spacing-3);
  border-radius: var(--radius-md);
  margin-top: var(--spacing-4);
  font-weight: var(--font-medium);
}

.error-message {
  background-color: var(--color-error-light);
  color: var(--color-error);
  border: 1px solid var(--color-error);
}

.success-message {
  background-color: var(--color-success-light);
  color: var(--color-success);
  border: 1px solid var(--color-success);
}

// Responsive breakpoints
@media (max-width: vars.$breakpoints(mobile)) {
  .register-page {
    padding: var(--spacing-2);
  }

  .page-title {
    font-size: var(--text-xl);
  }

  .page-description {
    font-size: var(--text-sm);
  }
}

// High contrast mode support
@media (forced-colors: active) {
  .login-link:focus {
    outline: 2px solid ButtonText;
  }
}

// Reduced motion support
@media (prefers-reduced-motion: reduce) {
  * {
    transition: none !important;
  }
}
</style>