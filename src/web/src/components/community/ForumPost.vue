<template>
  <article 
    class="forum-post"
    :data-thread-id="thread.id"
    :aria-labelledby="`post-title-${thread.id}`"
  >
    <!-- Post Header -->
    <header class="post-header">
      <div class="author-info">
        <img 
          v-if="thread.author.profileImage"
          :src="thread.author.profileImage"
          :alt="`${authorDisplayName}'s profile picture`"
          class="author-avatar"
        />
        <div class="author-details">
          <h3 
            :id="`post-title-${thread.id}`"
            class="post-title"
          >
            {{ thread.title }}
          </h3>
          <div class="post-metadata">
            <span class="author-name">{{ authorDisplayName }}</span>
            <time 
              :datetime="thread.createdAt"
              class="timestamp"
            >
              {{ formattedDate }}
            </time>
          </div>
        </div>
      </div>

      <!-- Moderation Badge -->
      <div 
        v-if="thread.isModerated"
        class="moderation-badge"
        role="status"
        aria-live="polite"
      >
        <span class="sr-only">This post has been moderated</span>
        <span aria-hidden="true">Moderated</span>
      </div>
    </header>

    <!-- Post Content -->
    <div 
      class="post-content"
      v-html="sanitizedContent"
    ></div>

    <!-- Post Actions -->
    <div 
      v-if="showActions"
      class="post-actions"
      role="group"
      :aria-label="`Actions for post ${thread.title}`"
    >
      <BaseButton
        variant="secondary"
        size="sm"
        :aria-label="'Reply to post'"
        @click="handleReply"
      >
        Reply
      </BaseButton>

      <BaseButton
        variant="text"
        size="sm"
        :aria-label="'Share post'"
        @click="handleShare"
      >
        Share
      </BaseButton>

      <!-- Moderation Controls -->
      <div 
        v-if="moderationEnabled"
        class="moderation-controls"
      >
        <BaseButton
          variant="accent"
          size="sm"
          :aria-label="'Moderate post'"
          @click="handleModeration('flag')"
        >
          Flag
        </BaseButton>
        <BaseButton
          v-if="isAuthor"
          variant="text"
          size="sm"
          :aria-label="'Delete post'"
          @click="handleModeration('delete')"
        >
          Delete
        </BaseButton>
      </div>
    </div>
  </article>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue' // v3.3.0
import { format } from 'date-fns' // v2.30.0
import DOMPurify from 'dompurify' // v3.0.0

// Internal imports
import type { Thread } from '@/types/community'
import BaseButton from '@/components/common/BaseButton.vue'
import { useAnalytics } from '@/composables/useAnalytics'

export default defineComponent({
  name: 'ForumPost',

  components: {
    BaseButton
  },

  props: {
    thread: {
      type: Object as () => Thread,
      required: true
    },
    showActions: {
      type: Boolean,
      default: true
    },
    moderationEnabled: {
      type: Boolean,
      default: false
    }
  },

  emits: {
    reply: (threadId: string) => !!threadId,
    share: (threadId: string) => !!threadId,
    moderate: (threadId: string, action: string) => !!threadId && !!action
  },

  setup(props, { emit }) {
    const { trackEvent } = useAnalytics()

    // Computed properties
    const formattedDate = computed(() => {
      return format(new Date(props.thread.createdAt), 'MMM d, yyyy h:mm a')
    })

    const authorDisplayName = computed(() => {
      const { firstName, lastName } = props.thread.author
      return firstName && lastName 
        ? `${firstName} ${lastName}`
        : props.thread.author.email
    })

    const sanitizedContent = computed(() => {
      return DOMPurify.sanitize(props.thread.content, {
        ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li'],
        ALLOWED_ATTR: []
      })
    })

    const isAuthor = computed(() => {
      // Implementation would check against current user ID
      return false // Placeholder
    })

    // Event handlers
    const handleReply = () => {
      trackEvent('forum_post_reply', {
        threadId: props.thread.id,
        authorId: props.thread.author.id
      })
      emit('reply', props.thread.id)
    }

    const handleShare = () => {
      trackEvent('forum_post_share', {
        threadId: props.thread.id
      })
      emit('share', props.thread.id)
    }

    const handleModeration = (action: string) => {
      trackEvent('forum_post_moderation', {
        threadId: props.thread.id,
        action,
        moderatorId: 'current-user-id' // Placeholder
      })
      emit('moderate', props.thread.id, action)
    }

    return {
      formattedDate,
      authorDisplayName,
      sanitizedContent,
      isAuthor,
      handleReply,
      handleShare,
      handleModeration
    }
  }
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;

.forum-post {
  background-color: #FFFFFF;
  border-radius: 8px;
  box-shadow: map-get(vars.$elevation-levels, 1);
  padding: vars.spacing(4);
  margin-bottom: vars.spacing(4);
  transition: box-shadow 0.2s ease-in-out;

  &:hover {
    box-shadow: map-get(vars.$elevation-levels, 2);
  }
}

.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: vars.spacing(4);
}

.author-info {
  display: flex;
  align-items: center;
  gap: vars.spacing(3);
}

.author-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.author-details {
  display: flex;
  flex-direction: column;
  gap: vars.spacing(1);
}

.post-title {
  font-family: vars.$font-family-primary;
  font-weight: map-get(vars.$font-weights, semibold);
  font-size: 1.125rem;
  color: map-get(vars.$colors, primary);
  margin: 0;
}

.post-metadata {
  display: flex;
  align-items: center;
  gap: vars.spacing(2);
  font-size: 0.875rem;
  color: map-get(vars.$colors, gray, 600);
}

.post-content {
  font-family: vars.$font-family-secondary;
  line-height: 1.6;
  color: map-get(vars.$colors, gray, 800);
  margin-bottom: vars.spacing(4);

  ::v-deep(p) {
    margin-bottom: vars.spacing(3);
  }
}

.post-actions {
  display: flex;
  align-items: center;
  gap: vars.spacing(3);
  padding-top: vars.spacing(3);
  border-top: 1px solid map-get(vars.$colors, gray, 200);
}

.moderation-controls {
  display: flex;
  gap: vars.spacing(2);
  margin-left: auto;
}

.moderation-badge {
  background-color: map-get(vars.$colors, warning);
  color: #000000;
  font-size: 0.75rem;
  padding: vars.spacing(1) vars.spacing(2);
  border-radius: 4px;
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

// Responsive styles
@media (max-width: map-get(vars.$breakpoints, tablet)) {
  .forum-post {
    padding: vars.spacing(3);
  }

  .post-actions {
    flex-wrap: wrap;
    gap: vars.spacing(2);
  }

  .moderation-controls {
    width: 100%;
    margin-left: 0;
    margin-top: vars.spacing(2);
  }
}
</style>