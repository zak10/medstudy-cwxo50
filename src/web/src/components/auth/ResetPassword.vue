<template>
  <form 
    class="reset-password-form"
    @submit.prevent="handleSubmit"
    aria-labelledby="reset-password-title"
    novalidate
  >
    <h1 id="reset-password-title" class="form-title">Reset Password</h1>

    <BaseInput
      v-model="email"
      type="email"
      label="Email Address"
      :error="errors.email"
      required
      aria-required="true"
      autocomplete="email"
      data-testid="email-input"
    />

    <BaseInput
      v-model="token"
      type="text"
      label="Reset Token"
      :error="errors.token"
      required
      aria-required="true"
      data-testid="token-input"
      :maxlength="VALIDATION_RULES.TOKEN_LENGTH"
    />

    <BaseInput
      v-model="newPassword"
      type="password"
      label="New Password"
      :error="errors.password"
      required
      aria-required="true"
      autocomplete="new-password"
      data-testid="new-password-input"
    />

    <BaseInput
      v-model="confirmPassword"
      type="password"
      label="Confirm Password"
      :error="errors.confirmPassword"
      required
      aria-required="true"
      autocomplete="new-password"
      data-testid="confirm-password-input"
    />

    <div class="password-requirements" aria-live="polite">
      <p class="requirements-title">Password must:</p>
      <ul>
        <li>Be at least {{ VALIDATION_RULES.MIN_PASSWORD_LENGTH }} characters long</li>
        <li>Include uppercase and lowercase letters</li>
        <li>Include at least one number</li>
        <li>Include at least one special character (!@#$%^&*)</li>
      </ul>
    </div>

    <BaseButton
      type="submit"
      variant="primary"
      :loading="isLoading"
      :disabled="isLoading"
      :aria-busy="isLoading"
      data-testid="submit-button"
    >
      Reset Password
    </BaseButton>
  </form>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'; // v3.3.0
import { useRouter } from 'vue-router'; // v4.2.0
import { useAuth } from '../../composables/useAuth';
import { validatePassword } from '../../utils/validation';
import BaseInput from '../common/BaseInput.vue';
import BaseButton from '../common/BaseButton.vue';

// Validation constants
const VALIDATION_RULES = {
  TOKEN_LENGTH: 32,
  MIN_PASSWORD_LENGTH: 12,
  RATE_LIMIT_ATTEMPTS: 3,
  TOKEN_EXPIRY_HOURS: 24
};

// Error messages
const ERROR_MESSAGES = {
  INVALID_TOKEN: 'Invalid or expired reset token. Please request a new one.',
  PASSWORD_MISMATCH: 'Passwords do not match. Please try again.',
  RESET_FAILED: 'Password reset failed. Please try again later.',
  RATE_LIMIT: 'Too many attempts. Please wait before trying again.',
  INVALID_PASSWORD: 'Password must meet all security requirements.',
  INVALID_EMAIL: 'Please enter a valid email address.'
};

export default defineComponent({
  name: 'ResetPassword',

  components: {
    BaseInput,
    BaseButton
  },

  setup() {
    const router = useRouter();
    const { handleResetPassword, validateResetToken } = useAuth();

    // Form state
    const email = ref('');
    const token = ref('');
    const newPassword = ref('');
    const confirmPassword = ref('');
    const isLoading = ref(false);
    const attemptCount = ref(0);
    const errors = ref({
      email: '',
      token: '',
      password: '',
      confirmPassword: '',
      general: ''
    });

    // Validate form inputs
    const validateForm = (): boolean => {
      let isValid = true;
      errors.value = {
        email: '',
        token: '',
        password: '',
        confirmPassword: '',
        general: ''
      };

      // Email validation
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email.value)) {
        errors.value.email = ERROR_MESSAGES.INVALID_EMAIL;
        isValid = false;
      }

      // Token validation
      if (!token.value || token.value.length !== VALIDATION_RULES.TOKEN_LENGTH) {
        errors.value.token = ERROR_MESSAGES.INVALID_TOKEN;
        isValid = false;
      }

      // Password validation
      if (!validatePassword(newPassword.value)) {
        errors.value.password = ERROR_MESSAGES.INVALID_PASSWORD;
        isValid = false;
      }

      // Password confirmation
      if (newPassword.value !== confirmPassword.value) {
        errors.value.confirmPassword = ERROR_MESSAGES.PASSWORD_MISMATCH;
        isValid = false;
      }

      // Rate limiting check
      if (attemptCount.value >= VALIDATION_RULES.RATE_LIMIT_ATTEMPTS) {
        errors.value.general = ERROR_MESSAGES.RATE_LIMIT;
        isValid = false;
      }

      return isValid;
    };

    // Handle form submission
    const handleSubmit = async () => {
      try {
        if (!validateForm()) {
          return;
        }

        isLoading.value = true;
        attemptCount.value++;

        // Validate token first
        const isTokenValid = await validateResetToken(token.value);
        if (!isTokenValid) {
          errors.value.token = ERROR_MESSAGES.INVALID_TOKEN;
          return;
        }

        // Attempt password reset
        const success = await handleResetPassword({
          email: email.value,
          token: token.value,
          newPassword: newPassword.value
        });

        if (success) {
          // Navigate to login on success
          router.push({ name: 'login', query: { reset: 'success' }});
        } else {
          errors.value.general = ERROR_MESSAGES.RESET_FAILED;
        }

      } catch (error) {
        console.error('Password reset error:', error);
        errors.value.general = ERROR_MESSAGES.RESET_FAILED;
      } finally {
        isLoading.value = false;
      }
    };

    return {
      // Template refs
      email,
      token,
      newPassword,
      confirmPassword,
      isLoading,
      errors,

      // Methods
      handleSubmit,

      // Constants
      VALIDATION_RULES,
      ERROR_MESSAGES
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;

.reset-password-form {
  max-width: 400px;
  margin: 0 auto;
  padding: vars.spacing(4);
  display: flex;
  flex-direction: column;
  gap: vars.spacing(4);

  .form-title {
    font-family: vars.$font-family-primary;
    font-weight: map-get(vars.$font-weights, bold);
    color: vars.color(primary);
    text-align: center;
    margin-bottom: vars.spacing(4);
  }

  .password-requirements {
    background-color: vars.color(gray, 50);
    padding: vars.spacing(3);
    border-radius: 4px;
    margin: vars.spacing(2) 0;

    .requirements-title {
      font-weight: map-get(vars.$font-weights, medium);
      margin-bottom: vars.spacing(2);
    }

    ul {
      list-style-type: none;
      padding-left: vars.spacing(2);

      li {
        font-size: 0.875rem;
        color: vars.color(gray, 600);
        margin-bottom: vars.spacing(1);
        
        &::before {
          content: "•";
          color: vars.color(primary);
          margin-right: vars.spacing(2);
        }
      }
    }
  }
}
</style>