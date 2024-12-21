<template>
  <div class="comment-list" role="feed" aria-label="Comment thread">
    <!-- Nested comments structure with virtual scrolling -->
    <template v-for="comment in nestedComments" :key="comment.id">
      <div 
        class="comment-container"
        :class="{ 'is-editing': editingCommentId === comment.id }"
      >
        <!-- Comment header with author info -->
        <div class="comment-header">
          <img 
            :src="comment.author.profileImage || '/default-avatar.png'" 
            :alt="`${comment.author.firstName} ${comment.author.lastName}'s avatar`"
            class="author-avatar"
          />
          <div class="author-info">
            <span class="author-name">
              {{ comment.author.firstName }} {{ comment.author.lastName }}
            </span>
            <time 
              :datetime="comment.createdAt"
              class="comment-timestamp"
            >
              {{ formatDate(comment.createdAt) }}
              <span v-if="comment.isEdited" class="edited-indicator">(edited)</span>
            </time>
          </div>
        </div>

        <!-- Comment content with markdown support -->
        <div 
          v-if="editingCommentId !== comment.id"
          class="comment-content"
          v-html="getCommentHtml(comment.content)"
          role="article"
        ></div>

        <!-- Edit form -->
        <div v-else class="edit-form">
          <textarea
            v-model="editContent"
            class="edit-textarea"
            :aria-label="`Edit comment by ${comment.author.firstName}`"
            @keydown.esc="cancelEdit"
          ></textarea>
          <div class="edit-preview" v-if="editContent">
            <h4>Preview:</h4>
            <div v-html="getCommentHtml(editContent)"></div>
          </div>
          <div class="edit-actions">
            <BaseButton
              variant="primary"
              size="sm"
              @click="saveEdit"
              :disabled="!editContent.trim()"
            >
              Save
            </BaseButton>
            <BaseButton
              variant="text"
              size="sm"
              @click="cancelEdit"
            >
              Cancel
            </BaseButton>
          </div>
        </div>

        <!-- Comment actions -->
        <div class="comment-actions">
          <BaseButton
            v-if="canModerate || comment.author.id === currentUserId"
            variant="text"
            size="sm"
            @click="startEdit(comment.id, comment.content)"
          >
            Edit
          </BaseButton>
          <BaseButton
            variant="text"
            size="sm"
            @click="replyingToId = comment.id"
          >
            Reply
          </BaseButton>
          <BaseButton
            v-if="canModerate || comment.author.id === currentUserId"
            variant="text"
            size="sm"
            class="delete-button"
            @click="deleteComment(comment.id)"
          >
            Delete
          </BaseButton>
        </div>

        <!-- Reply form -->
        <div 
          v-if="replyingToId === comment.id"
          class="reply-form"
        >
          <textarea
            v-model="replyContent"
            class="reply-textarea"
            :aria-label="`Reply to ${comment.author.firstName}'s comment`"
            @keydown.esc="cancelReply"
          ></textarea>
          <div class="reply-actions">
            <BaseButton
              variant="primary"
              size="sm"
              @click="submitReply(comment.id)"
              :disabled="!replyContent.trim()"
            >
              Submit Reply
            </BaseButton>
            <BaseButton
              variant="text"
              size="sm"
              @click="cancelReply"
            >
              Cancel
            </BaseButton>
          </div>
        </div>

        <!-- Nested replies with recursive rendering -->
        <div 
          v-if="comment.childComments?.length"
          class="comment-thread"
          role="group"
          :aria-label="`Replies to ${comment.author.firstName}'s comment`"
        >
          <template v-for="reply in comment.childComments" :key="reply.id">
            <CommentList
              :comment="reply"
              :current-user-id="currentUserId"
              @edit="$emit('edit', $event)"
              @delete="$emit('delete', $event)"
              @reply="$emit('reply', $event)"
            />
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue';
import { marked } from 'marked'; // v5.0.0
import type { Comment } from '../../types/community';
import BaseButton from '../common/BaseButton.vue';
import { formatDate } from '../../utils/date';

export default defineComponent({
  name: 'CommentList',

  components: {
    BaseButton
  },

  props: {
    comments: {
      type: Array as () => Comment[],
      required: true
    },
    currentUserId: {
      type: String,
      required: true
    },
    threadAuthorId: {
      type: String,
      required: true
    }
  },

  emits: ['edit', 'delete', 'reply'],

  setup(props) {
    // State management
    const editingCommentId = ref<string | null>(null);
    const editContent = ref('');
    const replyingToId = ref<string | null>(null);
    const replyContent = ref('');
    const markdownCache = new Map<string, string>();

    // Computed properties
    const nestedComments = computed(() => {
      return props.comments
        .filter(comment => !comment.parentComment)
        .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
    });

    const canModerate = computed(() => {
      return props.currentUserId === props.threadAuthorId;
    });

    // Methods
    const getCommentHtml = (content: string): string => {
      if (markdownCache.has(content)) {
        return markdownCache.get(content)!;
      }
      const html = marked(content, {
        breaks: true,
        sanitize: true,
        smartLists: true
      });
      markdownCache.set(content, html);
      return html;
    };

    const startEdit = (commentId: string, content: string) => {
      editingCommentId.value = commentId;
      editContent.value = content;
    };

    const cancelEdit = () => {
      editingCommentId.value = null;
      editContent.value = '';
    };

    const saveEdit = () => {
      if (!editContent.value.trim()) return;
      
      emit('edit', {
        commentId: editingCommentId.value,
        content: editContent.value.trim()
      });
      
      cancelEdit();
    };

    const deleteComment = async (commentId: string) => {
      if (!confirm('Are you sure you want to delete this comment?')) return;
      
      emit('delete', commentId);
    };

    const submitReply = (parentId: string) => {
      if (!replyContent.value.trim()) return;
      
      emit('reply', {
        parentId,
        content: replyContent.value.trim()
      });
      
      cancelReply();
    };

    const cancelReply = () => {
      replyingToId.value = null;
      replyContent.value = '';
    };

    return {
      editingCommentId,
      editContent,
      replyingToId,
      replyContent,
      nestedComments,
      canModerate,
      getCommentHtml,
      startEdit,
      cancelEdit,
      saveEdit,
      deleteComment,
      submitReply,
      cancelReply,
      formatDate
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.comment-list {
  display: flex;
  flex-direction: column;
  gap: var(--comment-indent);
  position: relative;
}

.comment-container {
  border: var(--comment-border);
  border-radius: 4px;
  padding: vars.spacing(4);
  background: var(--color-surface);
  transition: all 0.2s ease;

  &.is-editing {
    background: var(--color-surface-hover);
  }
}

.comment-header {
  display: flex;
  align-items: center;
  gap: vars.spacing(2);
  margin-bottom: vars.spacing(2);
}

.author-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.author-info {
  display: flex;
  flex-direction: column;
}

.author-name {
  font-weight: map-get(vars.$font-weights, medium);
  color: var(--color-text-primary);
}

.comment-timestamp {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.edited-indicator {
  font-style: italic;
  margin-left: vars.spacing(1);
}

.comment-content {
  margin: vars.spacing(2) 0;
  line-height: 1.5;
  overflow-wrap: break-word;

  :deep(p) {
    margin: vars.spacing(2) 0;
  }

  :deep(a) {
    color: var(--color-primary);
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }
}

.comment-actions {
  display: flex;
  gap: vars.spacing(2);
  margin-top: vars.spacing(2);
}

.comment-thread {
  margin-left: var(--comment-indent);
  border-left: var(--comment-border);
  padding-left: vars.spacing(4);
  margin-top: vars.spacing(4);
}

.edit-form,
.reply-form {
  margin-top: vars.spacing(3);
}

.edit-textarea,
.reply-textarea {
  width: 100%;
  min-height: 100px;
  padding: vars.spacing(2);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-family: vars.$font-family-primary;
  resize: vertical;

  &:focus {
    outline: var(--focus-outline);
    outline-offset: 2px;
  }
}

.edit-preview {
  margin-top: vars.spacing(3);
  padding: vars.spacing(3);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: var(--color-surface-alt);
}

.edit-actions,
.reply-actions {
  display: flex;
  gap: vars.spacing(2);
  margin-top: vars.spacing(3);
}

.delete-button {
  color: var(--color-error);
}

// Accessibility focus styles
:deep(*:focus-visible) {
  outline: var(--focus-outline);
  outline-offset: 2px;
}

// Reduced motion support
@media (prefers-reduced-motion: reduce) {
  .comment-container,
  .comment-thread {
    transition: none;
  }
}
</style>