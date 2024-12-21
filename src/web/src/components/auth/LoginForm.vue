<template>
  <form 
    class="login-form" 
    role="form" 
    aria-label="Login Form"
    @submit.prevent="handleSubmit"
  >
    <!-- Email Input -->
    <BaseInput
      v-model="formData.email"
      type="email"
      label="Email"
      :error="errors.email"
      :validation-rules="emailRules"
      required
      autocomplete="email"
      aria-label="Email Input"
      data-testid="email-input"
    />

    <!-- Password Input -->
    <BaseInput
      v-model="formData.password"
      type="password"
      label="Password"
      :error="errors.password"
      :validation-rules="passwordRules"
      required
      autocomplete="current-password"
      aria-label="Password Input"
      data-testid="password-input"
    />

    <!-- MFA Code Input (conditionally rendered) -->
    <BaseInput
      v-if="requiresMFA"
      v-model="formData.mfaCode"
      type="text"
      label="MFA Code"
      :error="errors.mfaCode"
      :validation-rules="mfaRules"
      required
      inputmode="numeric"
      pattern="[0-9]*"
      maxlength="6"
      aria-label="MFA Code Input"
      data-testid="mfa-input"
    />

    <!-- Error Message Display -->
    <div 
      v-if="globalError"
      class="login-form__error"
      role="alert"
      aria-live="polite"
    >
      {{ globalError }}
    </div>

    <!-- Submit Button -->
    <BaseButton
      type="submit"
      variant="primary"
      :loading="isLoading"
      :disabled="isLoading || !isFormValid"
      aria-label="Submit Login"
      data-testid="submit-button"
    >
      {{ submitButtonText }}
    </BaseButton>

    <!-- OAuth Section -->
    <div class="login-form__oauth">
      <div class="login-form__divider">
        <span>{{ t('auth.or_continue_with') }}</span>
      </div>

      <BaseButton
        variant="secondary"
        :disabled="isLoading"
        @click="handleOAuthLogin('google')"
        aria-label="Login with Google"
        data-testid="google-login"
      >
        <template #prefix>
          <GoogleIcon class="oauth-icon" />
        </template>
        {{ t('auth.continue_with_google') }}
      </BaseButton>
    </div>
  </form>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue'; // v3.3.0
import { useI18n } from 'vue-i18n'; // v9.2.0
import { useAuth } from '@/composables/useAuth';
import BaseInput from '@/components/common/BaseInput.vue';
import BaseButton from '@/components/common/BaseButton.vue';
import GoogleIcon from '@/components/icons/GoogleIcon.vue';
import { PASSWORD_REGEX } from '@/types/auth';
import type { LoginCredentials } from '@/types/auth';

// Rate limiting configuration
const RATE_LIMIT = {
  MAX_ATTEMPTS: 3,
  TIMEOUT: 300000, // 5 minutes
};

export default defineComponent({
  name: 'LoginForm',

  components: {
    BaseInput,
    BaseButton,
    GoogleIcon,
  },

  emits: ['login-success', 'login-error'],

  setup(_, { emit }) {
    const { t } = useI18n();
    const { handleLogin, authState, isLoading } = useAuth();

    // Form state
    const formData = ref<LoginCredentials>({
      email: '',
      password: '',
      mfaCode: '',
    });

    const errors = ref({
      email: '',
      password: '',
      mfaCode: '',
    });

    const globalError = ref('');
    const attemptCount = ref(0);
    const lastAttemptTime = ref(0);

    // Computed properties
    const requiresMFA = computed(() => authState.value === 'MFA_REQUIRED');

    const isFormValid = computed(() => {
      const hasRequiredFields = formData.value.email && formData.value.password;
      const hasMFAIfRequired = !requiresMFA.value || formData.value.mfaCode;
      return hasRequiredFields && hasMFAIfRequired && !Object.values(errors.value).some(Boolean);
    });

    const submitButtonText = computed(() => {
      if (isLoading.value) return t('auth.logging_in');
      return requiresMFA.value ? t('auth.verify_mfa') : t('auth.login');
    });

    // Validation rules
    const emailRules = [
      {
        validate: (value: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
        message: t('auth.invalid_email'),
      },
    ];

    const passwordRules = [
      {
        validate: (value: string) => new RegExp(PASSWORD_REGEX).test(value),
        message: t('auth.invalid_password'),
      },
    ];

    const mfaRules = [
      {
        validate: (value: string) => /^\d{6}$/.test(value),
        message: t('auth.invalid_mfa'),
      },
    ];

    // Rate limiting check
    const checkRateLimit = (): boolean => {
      const now = Date.now();
      if (attemptCount.value >= RATE_LIMIT.MAX_ATTEMPTS) {
        const timeElapsed = now - lastAttemptTime.value;
        if (timeElapsed < RATE_LIMIT.TIMEOUT) {
          const remainingTime = Math.ceil((RATE_LIMIT.TIMEOUT - timeElapsed) / 1000);
          globalError.value = t('auth.rate_limit_exceeded', { seconds: remainingTime });
          return false;
        }
        attemptCount.value = 0;
      }
      return true;
    };

    // Form submission handler
    const handleSubmit = async () => {
      try {
        if (!checkRateLimit()) return;

        globalError.value = '';
        errors.value = { email: '', password: '', mfaCode: '' };

        const success = await handleLogin(formData.value);

        if (success) {
          emit('login-success');
        } else {
          attemptCount.value++;
          lastAttemptTime.value = Date.now();
          globalError.value = t('auth.login_failed');
          emit('login-error', { message: 'Login failed' });
        }
      } catch (error) {
        console.error('Login error:', error);
        globalError.value = t('auth.system_error');
        emit('login-error', { error });
      }
    };

    // OAuth login handler
    const handleOAuthLogin = async (provider: string) => {
      try {
        globalError.value = '';
        const success = await handleLogin({ provider });
        
        if (success) {
          emit('login-success');
        } else {
          globalError.value = t('auth.oauth_failed');
          emit('login-error', { message: 'OAuth login failed' });
        }
      } catch (error) {
        console.error('OAuth login error:', error);
        globalError.value = t('auth.system_error');
        emit('login-error', { error });
      }
    };

    return {
      formData,
      errors,
      globalError,
      isLoading,
      requiresMFA,
      isFormValid,
      submitButtonText,
      emailRules,
      passwordRules,
      mfaRules,
      handleSubmit,
      handleOAuthLogin,
      t,
    };
  },
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.login-form {
  display: flex;
  flex-direction: column;
  gap: vars.spacing(4);
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
  padding: vars.spacing(6);
  background: var(--color-background);
  border-radius: 8px;
  box-shadow: map-get(vars.$elevation-levels, 2);

  &__error {
    color: map-get(vars.$colors, error);
    font-size: 0.875rem;
    text-align: center;
    padding: vars.spacing(2);
    border-radius: 4px;
    background-color: rgba(map-get(vars.$colors, error), 0.1);
  }

  &__oauth {
    margin-top: vars.spacing(4);
  }

  &__divider {
    position: relative;
    text-align: center;
    margin: vars.spacing(4) 0;

    &::before,
    &::after {
      content: '';
      position: absolute;
      top: 50%;
      width: calc(50% - 1rem);
      height: 1px;
      background-color: map-get(vars.$colors, gray, 200);
    }

    &::before {
      left: 0;
    }

    &::after {
      right: 0;
    }

    span {
      padding: 0 vars.spacing(2);
      background-color: var(--color-background);
      color: map-get(vars.$colors, gray, 500);
      font-size: 0.875rem;
    }
  }
}

.oauth-icon {
  width: 20px;
  height: 20px;
}

// Responsive adjustments
@media (max-width: map-get(vars.$breakpoints, tablet)) {
  .login-form {
    padding: vars.spacing(4);
    margin: vars.spacing(4);
  }
}

// High contrast mode support
@media (forced-colors: active) {
  .login-form {
    border: 1px solid CanvasText;
  }
}

// Reduced motion support
@media (prefers-reduced-motion: reduce) {
  .login-form {
    * {
      transition: none !important;
    }
  }
}
</style>