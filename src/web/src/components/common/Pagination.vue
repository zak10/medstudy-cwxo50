<template>
  <nav 
    class="pagination" 
    role="navigation" 
    :dir="dir"
    aria-label="Pagination navigation"
  >
    <!-- Page size selector -->
    <div v-if="showPageSize" class="page-size-selector">
      <label :for="pageSizeId" class="sr-only">Items per page</label>
      <select 
        :id="pageSizeId"
        :value="pageSize"
        @change="handlePageSizeChange($event.target.value)"
        class="page-size-select"
        :aria-controls="pageSizeId"
      >
        <option v-for="size in pageSizeOptions" :key="size" :value="size">
          {{ size }} per page
        </option>
      </select>
    </div>

    <!-- Pagination controls -->
    <div class="page-controls">
      <!-- Previous button -->
      <BaseButton
        v-if="showPrevious"
        variant="text"
        size="sm"
        :disabled="currentPage === 1"
        :aria-label="'Go to previous page'"
        @click="handlePageChange(currentPage - 1)"
      >
        <template #prefix>
          <span class="pagination-arrow" aria-hidden="true">&lsaquo;</span>
        </template>
        Previous
      </BaseButton>

      <!-- Page numbers -->
      <div class="page-numbers" role="group" aria-label="Page numbers">
        <BaseButton
          v-for="page in visiblePages"
          :key="page"
          variant="text"
          size="sm"
          :class="{ 'active': page === currentPage }"
          :aria-current="page === currentPage ? 'page' : undefined"
          :aria-label="`Go to page ${page}`"
          @click="handlePageChange(page)"
          v-if="page !== '...'"
        >
          {{ page }}
        </BaseButton>
        <span v-else class="ellipsis" aria-hidden="true">...</span>
      </div>

      <!-- Next button -->
      <BaseButton
        v-if="showNext"
        variant="text"
        size="sm"
        :disabled="currentPage === totalPages"
        :aria-label="'Go to next page'"
        @click="handlePageChange(currentPage + 1)"
      >
        Next
        <template #suffix>
          <span class="pagination-arrow" aria-hidden="true">&rsaquo;</span>
        </template>
      </BaseButton>
    </div>

    <!-- Live region for screen reader announcements -->
    <div class="sr-only" aria-live="polite" role="status">
      Page {{ currentPage }} of {{ totalPages }}
    </div>
  </nav>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue'; // v3.3.0
import { debounce } from 'lodash'; // v4.17.21
import type { Theme } from '@/types/ui';
import BaseButton from '@/components/common/BaseButton.vue';

export default defineComponent({
  name: 'Pagination',

  components: {
    BaseButton
  },

  props: {
    currentPage: {
      type: Number,
      required: true,
      validator: (value: number) => value > 0 && Number.isInteger(value)
    },
    totalPages: {
      type: Number,
      required: true,
      validator: (value: number) => value >= 0 && Number.isInteger(value)
    },
    pageSize: {
      type: Number,
      default: 10,
      validator: (value: number) => [10, 25, 50, 100].includes(value)
    },
    showPageSize: {
      type: Boolean,
      default: true
    },
    maxVisiblePages: {
      type: Number,
      default: 5,
      validator: (value: number) => value > 0 && value <= 10
    },
    dir: {
      type: String,
      default: 'ltr',
      validator: (value: string) => ['ltr', 'rtl'].includes(value)
    }
  },

  emits: {
    pageChange: (page: number) => Number.isInteger(page) && page > 0,
    pageSizeChange: (size: number) => [10, 25, 50, 100].includes(size)
  },

  setup(props, { emit }) {
    // Generate unique ID for page size selector
    const pageSizeId = `page-size-${Math.random().toString(36).substr(2, 9)}`;

    // Available page size options
    const pageSizeOptions = computed(() => [10, 25, 50, 100]);

    // Compute visible page numbers with ellipsis
    const visiblePages = computed(() => {
      const pages: (number | string)[] = [];
      const halfVisible = Math.floor(props.maxVisiblePages / 2);
      
      let start = Math.max(1, props.currentPage - halfVisible);
      let end = Math.min(props.totalPages, start + props.maxVisiblePages - 1);
      
      if (end - start + 1 < props.maxVisiblePages) {
        start = Math.max(1, end - props.maxVisiblePages + 1);
      }

      // Add first page
      if (start > 1) {
        pages.push(1);
        if (start > 2) pages.push('...');
      }

      // Add visible pages
      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      // Add last page
      if (end < props.totalPages) {
        if (end < props.totalPages - 1) pages.push('...');
        pages.push(props.totalPages);
      }

      return pages;
    });

    // Navigation button visibility
    const showPrevious = computed(() => props.currentPage > 1);
    const showNext = computed(() => props.currentPage < props.totalPages);

    // Debounced page change handler
    const debouncedPageChange = debounce((page: number) => {
      emit('pageChange', page);
    }, 300);

    // Page change handler with validation
    const handlePageChange = (page: number) => {
      if (page < 1 || page > props.totalPages) return;
      debouncedPageChange(page);
    };

    // Page size change handler
    const handlePageSizeChange = (size: string) => {
      const newSize = parseInt(size, 10);
      if (!pageSizeOptions.value.includes(newSize)) return;
      
      // Calculate new current page to maintain approximate scroll position
      const currentItem = (props.currentPage - 1) * props.pageSize;
      const newPage = Math.floor(currentItem / newSize) + 1;
      
      emit('pageSizeChange', newSize);
      if (newPage !== props.currentPage) {
        handlePageChange(newPage);
      }
    };

    return {
      pageSizeId,
      pageSizeOptions,
      visiblePages,
      showPrevious,
      showNext,
      handlePageChange,
      handlePageSizeChange
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;

.pagination {
  display: flex;
  flex-direction: column;
  gap: vars.spacing(4);
  align-items: center;
  
  @media (min-width: map-get(vars.$breakpoints, tablet)) {
    flex-direction: row;
    justify-content: space-between;
  }
}

.page-size-selector {
  display: flex;
  align-items: center;
  gap: vars.spacing(2);

  .page-size-select {
    padding: vars.spacing(1) vars.spacing(2);
    border: 1px solid color(gray, 300);
    border-radius: 4px;
    background-color: white;
    font-family: vars.$font-family-primary;
    font-size: 0.875rem;
    cursor: pointer;

    &:focus {
      outline: 2px solid color(primary);
      outline-offset: 2px;
    }
  }
}

.page-controls {
  display: flex;
  align-items: center;
  gap: vars.spacing(1);
}

.page-numbers {
  display: flex;
  align-items: center;
  gap: vars.spacing(1);
}

.ellipsis {
  padding: vars.spacing(1) vars.spacing(2);
  color: color(gray, 500);
}

.pagination-arrow {
  font-size: 1.2em;
  line-height: 1;
}

// RTL Support
[dir="rtl"] {
  .pagination-arrow {
    transform: scaleX(-1);
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
</style>