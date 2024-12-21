<template>
  <div class="thread-list" role="region" aria-label="Forum threads">
    <!-- Loading State -->
    <div v-if="loading" class="loading-overlay" role="alert" aria-busy="true">
      <LoadingSpinner size="large" color="primary" />
    </div>

    <!-- Thread Table -->
    <BaseTable
      :columns="tableColumns"
      :data="threads"
      :loading="loading"
      :sortable="true"
      :paginated="true"
      :items-per-page="20"
      empty-text="No threads found"
      @row-click="handleThreadClick"
      @sort="handleSort"
      @page-change="handlePageChange"
    >
      <!-- Custom Title Cell -->
      <template #cell-title="{ value, row }">
        <div class="thread-title" :title="value">
          <span v-if="row.isPinned" class="pin-indicator" aria-label="Pinned thread">📌</span>
          {{ value }}
        </div>
      </template>

      <!-- Custom Author Cell -->
      <template #cell-author="{ value }">
        {{ value.firstName }} {{ value.lastName }}
      </template>

      <!-- Custom Created Date Cell -->
      <template #cell-createdAt="{ value }">
        {{ formatDate(value) }}
      </template>
    </BaseTable>

    <!-- Error State -->
    <div 
      v-if="error" 
      class="error-message" 
      role="alert"
      aria-live="polite"
    >
      {{ error }}
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted } from 'vue'; // v3.3.0
import { debounce } from 'lodash'; // v4.17.21
import BaseTable from '@/components/common/BaseTable.vue';
import LoadingSpinner from '@/components/common/LoadingSpinner.vue';
import { getThreads } from '@/api/community';
import type { Thread } from '@/types/community';

export default defineComponent({
  name: 'ThreadList',

  components: {
    BaseTable,
    LoadingSpinner
  },

  props: {
    forumId: {
      type: String,
      required: true
    }
  },

  emits: ['thread-click', 'error'],

  setup(props, { emit }) {
    // State
    const threads = ref<Thread[]>([]);
    const loading = ref(false);
    const error = ref<string | null>(null);
    const currentPage = ref(1);
    const totalThreads = ref(0);

    // Table column configuration
    const tableColumns = computed(() => [
      {
        title: 'Title',
        key: 'title',
        sortable: true,
        width: '40%'
      },
      {
        title: 'Author',
        key: 'author',
        sortable: true,
        width: '20%'
      },
      {
        title: 'Created',
        key: 'createdAt',
        sortable: true,
        width: '20%'
      },
      {
        title: 'Views',
        key: 'viewCount',
        sortable: true,
        width: '20%'
      }
    ]);

    // Load threads with error handling
    const loadThreads = async () => {
      loading.value = true;
      error.value = null;

      try {
        const response = await getThreads(
          props.forumId,
          currentPage.value,
          20
        );

        threads.value = response.data;
        totalThreads.value = response.total;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load threads';
        error.value = errorMessage;
        emit('error', errorMessage);
      } finally {
        loading.value = false;
      }
    };

    // Debounced page change handler
    const handlePageChange = debounce((newPage: number) => {
      currentPage.value = newPage;
      loadThreads();
    }, 300);

    // Thread click handler with accessibility
    const handleThreadClick = (thread: Thread) => {
      emit('thread-click', thread.id);
    };

    // Sort handler
    const handleSort = (key: string, direction: 'asc' | 'desc') => {
      // Implement sorting logic here if needed
      // For now, we'll let the API handle sorting
    };

    // Date formatter
    const formatDate = (date: string) => {
      return new Date(date).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    };

    // Load initial data
    onMounted(() => {
      loadThreads();
    });

    return {
      threads,
      loading,
      error,
      tableColumns,
      handlePageChange,
      handleThreadClick,
      handleSort,
      formatDate
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.thread-list {
  width: 100%;
  background-color: var(--color-white);
  border-radius: var(--border-radius-md);
  box-shadow: var(--elevation-2);
  position: relative;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.thread-title {
  color: var(--color-primary);
  font-weight: 500;
  cursor: pointer;
  transition: color 0.2s ease;

  &:hover {
    color: var(--color-primary-dark);
  }

  .pin-indicator {
    margin-right: vars.spacing(2);
  }
}

.error-message {
  text-align: center;
  padding: vars.spacing(4);
  color: var(--color-error);
  background-color: var(--color-error-light);
  border-radius: var(--border-radius-sm);
  margin: vars.spacing(4);
}

// Reduced motion support
@media (prefers-reduced-motion: reduce) {
  .thread-title {
    transition: none;
  }
}
</style>