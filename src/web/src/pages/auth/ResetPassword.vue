<template>
  <AuthLayout>
    <div 
      class="reset-password-page"
      role="main"
      aria-labelledby="reset-password-title"
    >
      <h1 
        id="reset-password-title" 
        class="page-title"
      >
        Reset Your Password
      </h1>

      <ResetPassword
        ref="resetFormRef"
        @reset-success="handleResetSuccess"
        @reset-error="handleResetError"
        aria-live="polite"
        role="form"
      />

      <!-- Accessibility status updates -->
      <div 
        class="sr-only" 
        role="status" 
        aria-live="polite"
        ref="statusRef"
      >
        {{ statusMessage }}
      </div>
    </div>
  </AuthLayout>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import ResetPassword from '../../components/auth/ResetPassword.vue';
import AuthLayout from '../../layouts/AuthLayout.vue';
import { useAuth } from '../../composables/useAuth';
import { useNotification } from '../../composables/useNotification';

// Constants
const PAGE_TITLE = 'Reset Password - Medical Research Platform';
const SUCCESS_MESSAGE = 'Password reset successful. Please login with your new password.';
const ERROR_MESSAGES = {
  INVALID_TOKEN: 'Invalid or expired reset token. Please request a new one.',
  RATE_LIMIT: 'Too many attempts. Please try again in 15 minutes.',
  SYSTEM_ERROR: 'System error occurred. Please try again later.'
};

export default defineComponent({
  name: 'ResetPasswordPage',

  components: {
    ResetPassword,
    AuthLayout
  },

  setup() {
    // Composables
    const router = useRouter();
    const { validateResetToken } = useAuth();
    const { showSuccess, showError } = useNotification();

    // Template refs
    const resetFormRef = ref<InstanceType<typeof ResetPassword> | null>(null);
    const statusRef = ref<HTMLDivElement | null>(null);
    const statusMessage = ref('');

    /**
     * Updates the accessibility status message
     * @param message Message to display/announce
     */
    const updateStatus = (message: string) => {
      statusMessage.value = message;
      // Ensure screen readers announce the new message
      if (statusRef.value) {
        statusRef.value.textContent = '';
        setTimeout(() => {
          statusRef.value!.textContent = message;
        }, 100);
      }
    };

    /**
     * Handles successful password reset
     */
    const handleResetSuccess = async () => {
      try {
        // Update UI and accessibility
        updateStatus(SUCCESS_MESSAGE);
        showSuccess(SUCCESS_MESSAGE);

        // Clear sensitive data
        if (resetFormRef.value) {
          resetFormRef.value.$el.reset();
        }

        // Redirect to login after brief delay
        setTimeout(async () => {
          await router.push({
            name: 'login',
            query: { reset: 'success' }
          });
        }, 2000);

      } catch (error) {
        console.error('Reset success handler error:', error);
        handleResetError(new Error(ERROR_MESSAGES.SYSTEM_ERROR));
      }
    };

    /**
     * Handles password reset errors
     * @param error Error object
     */
    const handleResetError = (error: Error) => {
      // Clear sensitive data
      if (resetFormRef.value) {
        resetFormRef.value.$el.reset();
      }

      // Determine error message
      let errorMessage = ERROR_MESSAGES.SYSTEM_ERROR;
      if (error.message.includes('rate limit')) {
        errorMessage = ERROR_MESSAGES.RATE_LIMIT;
      } else if (error.message.includes('invalid token')) {
        errorMessage = ERROR_MESSAGES.INVALID_TOKEN;
      }

      // Update UI and accessibility
      updateStatus(errorMessage);
      showError(errorMessage);

      // Log error for monitoring
      console.error('Password reset error:', {
        message: error.message,
        timestamp: new Date().toISOString()
      });
    };

    /**
     * Validates reset token on component mount
     */
    onMounted(async () => {
      try {
        const token = router.currentRoute.value.query.token as string;
        
        if (!token) {
          throw new Error(ERROR_MESSAGES.INVALID_TOKEN);
        }

        const isValid = await validateResetToken(token);
        if (!isValid) {
          throw new Error(ERROR_MESSAGES.INVALID_TOKEN);
        }

      } catch (error) {
        handleResetError(error as Error);
        // Redirect to login after error
        await router.push({ name: 'login' });
      }
    });

    // Update document title
    document.title = PAGE_TITLE;

    return {
      resetFormRef,
      statusRef,
      statusMessage,
      handleResetSuccess,
      handleResetError
    };
  }
});
</script>

<style lang="scss" scoped>
.reset-password-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
}

.page-title {
  font-family: v-bind('theme.typography.fontFamily.primary');
  font-weight: 600;
  font-size: 24px;
  color: v-bind('theme.colors.text.primary');
  margin-bottom: 24px;
  text-align: center;
}

// Screen reader only class
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
</style>