<template>
  <div 
    class="messages-page" 
    role="main" 
    aria-label="Messages"
  >
    <!-- Header Section -->
    <header class="messages-header">
      <h1>Messages</h1>
      <div class="messages-actions">
        <BaseButton
          v-if="selectedMessage"
          variant="text"
          @click="clearSelection"
          aria-label="Return to message list"
        >
          Back to Messages
        </BaseButton>
      </div>
    </header>

    <!-- Loading State -->
    <LoadingSpinner
      v-if="loading"
      size="large"
      color="primary"
      label="Loading messages"
    />

    <!-- Messages Container -->
    <div 
      v-else
      class="messages-container"
      role="log"
      aria-live="polite"
    >
      <!-- Message List -->
      <div 
        v-if="!selectedMessage"
        class="message-list"
        role="list"
      >
        <div
          v-for="message in messages"
          :key="message.id"
          class="message-item"
          :class="{ 'message-item--unread': !message.isRead }"
          role="listitem"
          @click="selectMessage(message)"
        >
          <div class="message-item__avatar">
            <img 
              :src="message.sender.profileImage || '/default-avatar.png'"
              :alt="`${message.sender.firstName} ${message.sender.lastName}`"
              class="avatar-image"
            />
          </div>
          <div class="message-item__content">
            <div class="message-item__header">
              <span class="message-item__sender">
                {{ message.sender.firstName }} {{ message.sender.lastName }}
              </span>
              <time 
                :datetime="message.createdAt"
                class="message-item__time"
              >
                {{ formatMessageTime(message.createdAt) }}
              </time>
            </div>
            <p 
              class="message-item__preview"
              :class="{ 'message-item__preview--moderated': message.isModerated }"
            >
              {{ message.isModerated ? message.moderationReason : message.content }}
            </p>
          </div>
        </div>

        <!-- Empty State -->
        <div 
          v-if="messages.length === 0" 
          class="messages-empty"
          role="status"
        >
          No messages yet
        </div>

        <!-- Load More -->
        <BaseButton
          v-if="hasMoreMessages"
          variant="text"
          :loading="loadingMore"
          @click="loadMoreMessages"
          class="load-more-button"
        >
          Load More Messages
        </BaseButton>
      </div>

      <!-- Message Detail View -->
      <div 
        v-else 
        class="message-detail"
        role="article"
      >
        <div class="message-detail__header">
          <h2>
            {{ selectedMessage.sender.firstName }} {{ selectedMessage.sender.lastName }}
          </h2>
          <time :datetime="selectedMessage.createdAt">
            {{ formatMessageTime(selectedMessage.createdAt) }}
          </time>
        </div>
        
        <div 
          class="message-detail__content"
          :class="{ 'message-detail__content--moderated': selectedMessage.isModerated }"
        >
          {{ selectedMessage.isModerated ? selectedMessage.moderationReason : selectedMessage.content }}
        </div>

        <!-- Message Composer -->
        <MessageComposer
          :recipient-id="selectedMessage.sender.id"
          :placeholder="'Write a reply...'"
          @message-sent="handleMessageSent"
          @validation-error="handleValidationError"
        />
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { ref, computed, onMounted, defineComponent, onErrorCaptured } from 'vue'; // v3.3.0
import { storeToRefs } from 'pinia'; // v2.1.0
import sanitizeHtml from 'sanitize-html'; // v2.11.0
import MessageComposer from '@/components/community/MessageComposer.vue';
import BaseButton from '@/components/common/BaseButton.vue';
import LoadingSpinner from '@/components/common/LoadingSpinner.vue';
import useNotification from '@/composables/useNotification';
import type { Message } from '@/types/community';

export default defineComponent({
  name: 'MessagesPage',

  components: {
    MessageComposer,
    BaseButton,
    LoadingSpinner
  },

  setup() {
    // State
    const messages = ref<Message[]>([]);
    const selectedMessage = ref<Message | null>(null);
    const loading = ref(true);
    const loadingMore = ref(false);
    const currentPage = ref(1);
    const hasMoreMessages = ref(true);
    const PAGE_SIZE = 20;

    // Composables
    const { showNotification } = useNotification();

    // Load messages with error handling
    const loadMessages = async (page: number = 1, pageSize: number = PAGE_SIZE) => {
      try {
        loading.value = true;
        // API call would go here
        // const response = await messageService.getMessages(page, pageSize);
        // messages.value = response.data;
        // hasMoreMessages.value = response.hasMore;

        // Temporary mock data
        messages.value = [
          {
            id: '1',
            sender: { id: 'sender1', firstName: 'John', lastName: 'Doe' },
            recipient: { id: 'current-user', firstName: 'Current', lastName: 'User' },
            content: 'Hello, this is a test message',
            isRead: false,
            isModerated: false,
            createdAt: new Date().toISOString()
          }
        ];
        
      } catch (error) {
        showNotification('error', 'Failed to load messages');
        console.error('Error loading messages:', error);
      } finally {
        loading.value = false;
      }
    };

    // Load more messages
    const loadMoreMessages = async () => {
      if (loadingMore.value || !hasMoreMessages.value) return;
      
      try {
        loadingMore.value = true;
        currentPage.value++;
        await loadMessages(currentPage.value);
      } finally {
        loadingMore.value = false;
      }
    };

    // Message selection
    const selectMessage = async (message: Message) => {
      selectedMessage.value = message;
      if (!message.isRead) {
        // Mark as read
        // await messageService.markAsRead(message.id);
        message.isRead = true;
      }
    };

    const clearSelection = () => {
      selectedMessage.value = null;
    };

    // Message handling
    const handleMessageSent = async (message: Message) => {
      try {
        // Sanitize content
        const sanitizedContent = sanitizeHtml(message.content, {
          allowedTags: [],
          allowedAttributes: {}
        });

        // Validate content length
        if (sanitizedContent.length > 1000) {
          throw new Error('Message is too long');
        }

        // Add message to list
        messages.value.unshift({
          ...message,
          content: sanitizedContent,
          createdAt: new Date().toISOString()
        });

        showNotification('success', 'Message sent successfully');
      } catch (error) {
        showNotification('error', 'Failed to send message');
        console.error('Error sending message:', error);
      }
    };

    const handleValidationError = (error: string) => {
      showNotification('error', error);
    };

    // Time formatting
    const formatMessageTime = (timestamp: string): string => {
      const date = new Date(timestamp);
      const now = new Date();
      const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

      if (diffInHours < 24) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      } else if (diffInHours < 48) {
        return 'Yesterday';
      } else {
        return date.toLocaleDateString();
      }
    };

    // Error handling
    onErrorCaptured((error) => {
      showNotification('error', 'An error occurred');
      console.error('Error in MessagesPage:', error);
      return false;
    });

    // Initial load
    onMounted(() => {
      loadMessages();
    });

    return {
      messages,
      selectedMessage,
      loading,
      loadingMore,
      hasMoreMessages,
      selectMessage,
      clearSelection,
      loadMoreMessages,
      handleMessageSent,
      handleValidationError,
      formatMessageTime
    };
  }
});
</script>

<style lang="scss" scoped>
.messages-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: var(--spacing-4);
  background-color: var(--color-background-primary);

  .messages-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-4);

    h1 {
      font-family: var(--font-family-primary);
      font-size: var(--font-size-h2);
      color: var(--color-text-primary);
      margin: 0;
    }
  }

  .messages-container {
    flex: 1;
    overflow-y: auto;
    border-radius: var(--border-radius-lg);
    background-color: var(--color-background-secondary);
    box-shadow: var(--elevation-level1);
  }

  .message-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2);
  }

  .message-item {
    display: flex;
    padding: var(--spacing-3);
    gap: var(--spacing-3);
    cursor: pointer;
    transition: background-color 0.2s ease;
    border-bottom: 1px solid var(--color-border);

    &:hover {
      background-color: var(--color-background-hover);
    }

    &--unread {
      background-color: var(--color-background-unread);
      font-weight: var(--font-weight-medium);
    }

    &__avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      overflow: hidden;

      img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
    }

    &__content {
      flex: 1;
      min-width: 0;
    }

    &__header {
      display: flex;
      justify-content: space-between;
      margin-bottom: var(--spacing-1);
    }

    &__sender {
      font-weight: var(--font-weight-medium);
      color: var(--color-text-primary);
    }

    &__time {
      color: var(--color-text-secondary);
      font-size: var(--font-size-sm);
    }

    &__preview {
      color: var(--color-text-secondary);
      font-size: var(--font-size-sm);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;

      &--moderated {
        color: var(--color-text-error);
        font-style: italic;
      }
    }
  }

  .message-detail {
    padding: var(--spacing-4);

    &__header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: var(--spacing-4);
    }

    &__content {
      margin-bottom: var(--spacing-4);
      white-space: pre-wrap;

      &--moderated {
        color: var(--color-text-error);
        font-style: italic;
      }
    }
  }

  .messages-empty {
    text-align: center;
    padding: var(--spacing-8);
    color: var(--color-text-secondary);
  }

  .load-more-button {
    margin: var(--spacing-4) auto;
  }

  // Responsive adjustments
  @media (max-width: 768px) {
    padding: var(--spacing-2);

    .message-item {
      padding: var(--spacing-2);
    }

    .message-detail {
      padding: var(--spacing-2);
    }
  }

  // High contrast mode support
  @media (forced-colors: active) {
    .message-item {
      border: 1px solid CanvasText;
    }

    .message-item--unread {
      border: 2px solid CanvasText;
    }
  }
}
</style>