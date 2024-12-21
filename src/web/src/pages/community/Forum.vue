<template>
  <div 
    class="forum-page" 
    role="main" 
    :aria-busy="loading"
    :aria-labelledby="'forum-title'"
  >
    <ErrorBoundary @error="handleError">
      <!-- Page Header -->
      <header class="page-header">
        <h1 id="forum-title" class="forum-title">
          {{ pageTitle }}
        </h1>
        <div class="header-actions" v-if="canModerate">
          <BaseButton
            variant="primary"
            size="md"
            :aria-label="'Create new thread'"
            @click="handleNewThread"
          >
            New Thread
          </BaseButton>
        </div>
      </header>

      <!-- Loading State -->
      <div 
        v-if="loading" 
        class="loading-container"
        role="status"
        aria-live="polite"
      >
        <LoadingSpinner size="large" color="primary" />
        <span class="sr-only">Loading forum content</span>
      </div>

      <!-- Thread List -->
      <ThreadList
        v-else-if="!error"
        :forum-id="protocolId"
        :page-size="20"
        :sort-order="sortOrder"
        :moderation-enabled="canModerate"
        @thread-click="handleThreadClick"
        @moderate="handleModeration"
      />

      <!-- Error State -->
      <div 
        v-if="error"
        class="error-message"
        role="alert"
        aria-live="assertive"
      >
        <p>{{ error }}</p>
        <BaseButton
          variant="secondary"
          size="sm"
          @click="loadForumData"
        >
          Retry
        </BaseButton>
      </div>

      <!-- Real-time Update Indicator -->
      <div 
        v-if="websocketConnected"
        class="real-time-indicator"
        role="status"
        aria-live="polite"
      >
        <span class="sr-only">Real-time updates active</span>
        <span class="indicator-dot" aria-hidden="true"></span>
      </div>
    </ErrorBoundary>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAnalytics } from '@/composables/analytics'

// Internal imports
import ThreadList from '@/components/community/ThreadList.vue'
import ForumPost from '@/components/community/ForumPost.vue'
import ErrorBoundary from '@/components/common/ErrorBoundary.vue'
import { useCommunityStore } from '@/stores/community'
import type { Thread } from '@/types/community'

export default defineComponent({
  name: 'ForumPage',

  components: {
    ThreadList,
    ForumPost,
    ErrorBoundary
  },

  setup() {
    const route = useRoute()
    const router = useRouter()
    const { trackEvent } = useAnalytics()
    const communityStore = useCommunityStore()

    // State
    const loading = ref(false)
    const error = ref<string | null>(null)
    const sortOrder = ref<'newest' | 'oldest'>('newest')
    const websocketConnected = computed(() => communityStore.wsStatus === 'OPEN')

    // Computed
    const protocolId = computed(() => {
      const id = route.params.protocolId as string
      if (!id) throw new Error('Protocol ID is required')
      return id
    })

    const pageTitle = computed(() => {
      const forum = communityStore.forums.value.find(f => f.protocolId === protocolId.value)
      return forum ? `${forum.name} Discussion` : 'Protocol Forum'
    })

    const canModerate = computed(() => {
      const forum = communityStore.forums.value.find(f => f.protocolId === protocolId.value)
      return forum?.moderators.some(m => m.id === 'current-user-id') || false // Replace with actual user ID
    })

    // Methods
    const loadForumData = async () => {
      loading.value = true
      error.value = null

      try {
        await communityStore.fetchForums(protocolId.value)
        trackEvent('forum_view', { protocolId: protocolId.value })
      } catch (err) {
        error.value = err instanceof Error ? err.message : 'Failed to load forum'
        trackEvent('forum_error', { 
          protocolId: protocolId.value,
          error: error.value
        })
      } finally {
        loading.value = false
      }
    }

    const handleThreadClick = (threadId: string) => {
      trackEvent('thread_click', { threadId })
      router.push({
        name: 'thread-detail',
        params: { threadId }
      })
    }

    const handleNewThread = () => {
      trackEvent('new_thread_click', { protocolId: protocolId.value })
      router.push({
        name: 'new-thread',
        params: { protocolId: protocolId.value }
      })
    }

    const handleModeration = async (threadId: string, action: string) => {
      try {
        // Implement moderation action
        await communityStore.moderateThread(threadId, action)
        trackEvent('thread_moderation', {
          threadId,
          action,
          moderatorId: 'current-user-id' // Replace with actual user ID
        })
      } catch (err) {
        error.value = err instanceof Error ? err.message : 'Moderation failed'
      }
    }

    const handleError = (err: Error) => {
      error.value = `An error occurred: ${err.message}`
      trackEvent('forum_error', {
        protocolId: protocolId.value,
        error: err.message
      })
    }

    // Lifecycle hooks
    onMounted(() => {
      loadForumData()
    })

    onUnmounted(() => {
      communityStore.cleanup()
    })

    return {
      loading,
      error,
      sortOrder,
      websocketConnected,
      protocolId,
      pageTitle,
      canModerate,
      handleThreadClick,
      handleNewThread,
      handleModeration,
      handleError,
      loadForumData
    }
  }
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.forum-page {
  padding: vars.spacing(6);
  max-width: var(--content-width-lg);
  margin: 0 auto;
  min-height: 100vh;
}

.page-header {
  margin-bottom: vars.spacing(6);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.forum-title {
  font-family: vars.$font-family-primary;
  font-weight: map-get(vars.$font-weights, bold);
  font-size: 2rem;
  color: map-get(vars.$colors, primary);
  margin: 0;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.error-message {
  text-align: center;
  padding: vars.spacing(4);
  background-color: var(--color-error-bg);
  border-radius: var(--radius-md);
  color: var(--color-error);
  margin: vars.spacing(4) 0;
}

.real-time-indicator {
  position: fixed;
  bottom: vars.spacing(4);
  right: vars.spacing(4);
  background: var(--color-success);
  border-radius: 50%;
  width: 12px;
  height: 12px;
  
  .indicator-dot {
    display: block;
    width: 100%;
    height: 100%;
    border-radius: 50%;
    background: currentColor;
    animation: pulse 2s infinite;
  }
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
  .forum-page {
    padding: vars.spacing(4);
  }

  .page-header {
    flex-direction: column;
    gap: vars.spacing(3);
    align-items: flex-start;
  }
}

// Reduced motion support
@media (prefers-reduced-motion: reduce) {
  .indicator-dot {
    animation: none;
  }
}
</style>