<template>
  <div 
    class="message-composer" 
    role="form" 
    aria-label="Message composition form"
  >
    <form @submit.prevent="sendMessage">
      <BaseInput
        v-model="messageContent"
        :placeholder="placeholder"
        :error="error"
        :disabled="isLoading"
        :maxlength="maxLength"
        aria-label="Message content"
        @validation="handleValidation"
      />
      <BaseButton
        type="submit"
        variant="primary"
        :loading="isLoading"
        :disabled="!isValid || isLoading"
        :aria-busy="isLoading"
      >
        Send
      </BaseButton>
    </form>
  </div>
</template>

<script lang="ts">
import { ref, defineComponent, onMounted, onUnmounted } from 'vue'; // v3.3.0
import { debounce } from 'lodash-es'; // v4.17.21
import BaseInput from '@/components/common/BaseInput';
import BaseButton from '@/components/common/BaseButton';
import useNotification from '@/composables/useNotification';
import type { Message, MessageCreateInput } from '@/types/community';

export default defineComponent({
  name: 'MessageComposer',

  components: {
    BaseInput,
    BaseButton
  },

  props: {
    recipientId: {
      type: String,
      required: true,
      validator: (value: string) => value.trim().length > 0
    },
    placeholder: {
      type: String,
      default: 'Type your message...'
    },
    maxLength: {
      type: Number,
      default: 1000,
      validator: (value: number) => value > 0 && value <= 5000
    }
  },

  emits: {
    messageSent: (message: Message) => !!message,
    validationError: (error: string) => !!error
  },

  setup(props, { emit }) {
    // State management
    const messageContent = ref('');
    const error = ref('');
    const isLoading = ref(false);
    const isValid = ref(false);

    // Composables
    const { showNotification, NotificationType } = useNotification();

    // Validation with debounce for performance
    const validateMessage = debounce(() => {
      error.value = '';
      isValid.value = false;

      // Empty message check
      if (!messageContent.value.trim()) {
        error.value = 'Message cannot be empty';
        return false;
      }

      // Length validation
      if (messageContent.value.length > props.maxLength) {
        error.value = `Message cannot exceed ${props.maxLength} characters`;
        return false;
      }

      // Content validation - prevent spam/invalid patterns
      const invalidPatterns = [
        /^[\s\n]*$/,  // Only whitespace
        /(.)\1{10,}/  // Repeated characters
      ];

      for (const pattern of invalidPatterns) {
        if (pattern.test(messageContent.value)) {
          error.value = 'Message contains invalid content';
          return false;
        }
      }

      isValid.value = true;
      return true;
    }, 300);

    // Handle input validation
    const handleValidation = () => {
      const isValidMessage = validateMessage();
      if (!isValidMessage) {
        emit('validationError', error.value);
      }
    };

    // Send message with loading state and error handling
    const sendMessage = async () => {
      try {
        if (!validateMessage()) {
          emit('validationError', error.value);
          return;
        }

        isLoading.value = true;

        // Create message input with sanitized content
        const messageInput: MessageCreateInput = {
          recipientId: props.recipientId,
          content: messageContent.value.trim()
        };

        // API call would go here
        // const response = await messageService.sendMessage(messageInput);

        // Clear input and show success
        messageContent.value = '';
        showNotification(
          NotificationType.SUCCESS,
          'Message sent successfully'
        );

        // Emit success with message data
        emit('messageSent', {
          id: 'temp-id', // Would come from API
          content: messageInput.content,
          sender: { id: 'current-user' }, // Would come from auth store
          recipient: { id: props.recipientId },
          createdAt: new Date().toISOString()
        } as Message);

      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
        showNotification(NotificationType.ERROR, errorMessage);
        error.value = errorMessage;
        emit('validationError', errorMessage);
      } finally {
        isLoading.value = false;
      }
    };

    // Cleanup on component unmount
    onUnmounted(() => {
      validateMessage.cancel();
    });

    return {
      messageContent,
      error,
      isLoading,
      isValid,
      sendMessage,
      handleValidation
    };
  }
});
</script>

<style lang="scss" scoped>
.message-composer {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  max-width: 100%;

  form {
    display: flex;
    gap: var(--spacing-2);
    align-items: flex-start;
    width: 100%;
  }

  &--error {
    border-color: var(--color-error);
    animation: shake 0.5s;
  }

  // Shake animation for error state
  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-5px); }
    75% { transform: translateX(5px); }
  }

  // Responsive adjustments
  @media (max-width: 768px) {
    form {
      flex-direction: column;
      gap: var(--spacing-3);
    }
  }

  // High contrast mode support
  @media (forced-colors: active) {
    border-color: CanvasText;
    
    &--error {
      border-color: Mark;
    }
  }
}
</style>