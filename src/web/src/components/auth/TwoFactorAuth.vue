<template>
  <form 
    class="two-factor-auth"
    @submit.prevent="handleMFASubmit"
    aria-labelledby="mfa-title"
  >
    <h2 id="mfa-title" class="two-factor-auth__title">
      Two-Factor Authentication
    </h2>

    <div class="two-factor-auth__content">
      <BaseInput
        v-model="mfaCode"
        type="text"
        label="Enter Authentication Code"
        placeholder="Enter 6-digit code"
        :error="validationError"
        :disabled="isVerifying"
        required
        inputmode="numeric"
        pattern="[0-9]*"
        maxlength="6"
        aria-describedby="mfa-help-text"
        @blur="validateMFACode(mfaCode)"
      />

      <p 
        id="mfa-help-text" 
        class="two-factor-auth__help-text"
      >
        Enter the 6-digit code from your authenticator app
      </p>

      <div 
        v-if="remainingAttempts < 3" 
        class="two-factor-auth__attempts"
        role="alert"
      >
        {{ remainingAttempts }} attempts remaining
      </div>

      <BaseButton
        type="submit"
        variant="primary"
        :loading="isVerifying"
        :disabled="!isValidCode || isVerifying || isRateLimited"
        aria-label="Verify authentication code"
      >
        {{ isVerifying ? 'Verifying...' : 'Verify Code' }}
      </BaseButton>
    </div>
  </form>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue'; // v3.3.0
import { useRateLimiter } from '@vueuse/core'; // v10.0.0
import { useAuth } from '../../composables/useAuth';
import BaseInput from '../common/BaseInput.vue';
import BaseButton from '../common/BaseButton.vue';
import { AuthState } from '../../types/auth';

// Constants for MFA validation and security
const MFA_CODE_LENGTH = 6;
const MAX_ATTEMPTS = 3;
const RATE_LIMIT_DURATION = 300000; // 5 minutes in milliseconds
const SEQUENTIAL_DIGITS_PATTERN = /(012|123|234|345|456|567|678|789|987|876|765|654|543|432|321|210)/;
const REPEATED_DIGITS_PATTERN = /(.)\1{2,}/;

export default defineComponent({
  name: 'TwoFactorAuth',

  components: {
    BaseInput,
    BaseButton
  },

  props: {
    loginCredentials: {
      type: Object,
      required: true
    }
  },

  emits: ['mfaVerified', 'mfaFailed'],

  setup(props, { emit }) {
    const { verifyMFACode, authState } = useAuth();
    const mfaCode = ref('');
    const validationError = ref('');
    const attempts = ref(0);
    const isVerifying = ref(false);

    // Rate limiting setup
    const { isRateLimited, increment: incrementRateLimit } = useRateLimiter(3, RATE_LIMIT_DURATION);

    // Computed properties
    const remainingAttempts = computed(() => MAX_ATTEMPTS - attempts.value);
    const isValidCode = computed(() => validateMFACode(mfaCode.value));

    /**
     * Validates MFA code format and security requirements
     * @param code - The MFA code to validate
     * @returns boolean indicating if code is valid
     */
    const validateMFACode = (code: string): boolean => {
      // Reset validation error
      validationError.value = '';

      // Check code length
      if (!code || code.length !== MFA_CODE_LENGTH) {
        validationError.value = 'Please enter a 6-digit code';
        return false;
      }

      // Check if code contains only numbers
      if (!/^\d+$/.test(code)) {
        validationError.value = 'Code must contain only numbers';
        return false;
      }

      // Check for sequential digits
      if (SEQUENTIAL_DIGITS_PATTERN.test(code)) {
        validationError.value = 'Code cannot contain sequential numbers';
        return false;
      }

      // Check for repeated digits
      if (REPEATED_DIGITS_PATTERN.test(code)) {
        validationError.value = 'Code cannot contain repeated numbers';
        return false;
      }

      return true;
    };

    /**
     * Handles MFA code submission with rate limiting and security checks
     */
    const handleMFASubmit = async () => {
      try {
        // Check rate limiting
        if (isRateLimited.value) {
          validationError.value = 'Too many attempts. Please try again later.';
          return;
        }

        // Validate code format
        if (!validateMFACode(mfaCode.value)) {
          return;
        }

        // Track attempt
        attempts.value++;
        incrementRateLimit();

        // Set loading state
        isVerifying.value = true;

        // Attempt verification
        const success = await verifyMFACode({
          ...props.loginCredentials,
          mfaCode: mfaCode.value
        });

        if (success && authState.value === AuthState.AUTHENTICATED) {
          emit('mfaVerified');
          mfaCode.value = ''; // Clear code after successful verification
        } else {
          throw new Error('MFA verification failed');
        }

      } catch (error) {
        console.error('MFA verification error:', error);
        validationError.value = 'Invalid verification code';
        emit('mfaFailed', {
          error: 'Invalid verification code',
          attempts: attempts.value
        });

      } finally {
        isVerifying.value = false;
      }
    };

    return {
      mfaCode,
      validationError,
      isVerifying,
      isRateLimited,
      remainingAttempts,
      isValidCode,
      handleMFASubmit,
      validateMFACode
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.two-factor-auth {
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
  padding: vars.spacing(4);

  &__title {
    font-family: vars.$font-family-primary;
    font-weight: map-get(vars.$font-weights, semibold);
    font-size: 1.5rem;
    color: color(gray, 900);
    margin-bottom: vars.spacing(4);
    text-align: center;
  }

  &__content {
    display: flex;
    flex-direction: column;
    gap: vars.spacing(3);
  }

  &__help-text {
    font-family: vars.$font-family-primary;
    font-size: 0.875rem;
    color: color(gray, 600);
    margin-top: vars.spacing(1);
  }

  &__attempts {
    font-family: vars.$font-family-primary;
    font-size: 0.875rem;
    color: color(error);
    text-align: center;
    @include animations.fade-in(0.3s);
  }

  // Dark mode support
  @media (prefers-color-scheme: dark) {
    &__title {
      color: color(gray, 100);
    }

    &__help-text {
      color: color(gray, 400);
    }
  }

  // Responsive adjustments
  @media screen and (max-width: map-get(vars.$breakpoints, mobile)) {
    padding: vars.spacing(3);
  }
}
</style>