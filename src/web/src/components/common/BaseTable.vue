<template>
  <div 
    class="base-table-wrapper"
    :class="{ 'loading': loading }"
    :aria-busy="loading"
  >
    <!-- Loading State -->
    <LoadingSpinner
      v-if="loading"
      size="large"
      color="primary"
      class="table-loader"
    />

    <!-- Table Element -->
    <table
      role="grid"
      :aria-label="'Data table'"
      class="base-table"
    >
      <thead>
        <tr role="row">
          <th
            v-for="column in columns"
            :key="column.key"
            role="columnheader"
            :class="{
              'sortable': column.sortable && sortable,
              'sorted': currentSort.key === column.key
            }"
            :style="{ width: column.width }"
            :aria-sort="getSortAriaLabel(column)"
            @click="column.sortable && sortable ? handleSort(column) : null"
            @keydown.enter="column.sortable && sortable ? handleSort(column) : null"
            :tabindex="column.sortable && sortable ? 0 : -1"
          >
            <div class="th-content">
              {{ column.title }}
              <span 
                v-if="column.sortable && sortable"
                class="sort-indicator"
                aria-hidden="true"
              >
                {{ getSortIcon(column) }}
              </span>
            </div>
          </th>
        </tr>
      </thead>

      <tbody>
        <tr
          v-for="(row, index) in displayData"
          :key="index"
          role="row"
          class="table-row"
          :class="{ 'clickable': $listeners['row-click'] }"
          @click="handleRowClick(row)"
          :tabindex="$listeners['row-click'] ? 0 : -1"
          @keydown.enter="$listeners['row-click'] ? handleRowClick(row) : null"
        >
          <td
            v-for="column in columns"
            :key="column.key"
            role="gridcell"
          >
            <slot
              :name="`cell-${column.key}`"
              :value="getCellValue(row, column.key)"
              :row="row"
            >
              {{ getCellValue(row, column.key) }}
            </slot>
          </td>
        </tr>

        <!-- Empty State -->
        <tr v-if="!loading && (!data || data.length === 0)">
          <td
            :colspan="columns.length"
            class="empty-state"
            role="cell"
          >
            {{ emptyText }}
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Pagination -->
    <Pagination
      v-if="paginated && data.length > 0"
      :current-page="currentPage"
      :total-pages="totalPages"
      :page-size="itemsPerPage"
      @page-change="handlePageChange"
    />

    <!-- Live Region for Announcements -->
    <div 
      class="sr-only" 
      role="status" 
      aria-live="polite"
      ref="announcer"
    >
      {{ announcement }}
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue'; // v3.3.0
import { debounce } from 'lodash'; // v4.17.21
import Pagination from './Pagination.vue';
import LoadingSpinner from './LoadingSpinner.vue';

export default defineComponent({
  name: 'BaseTable',

  components: {
    Pagination,
    LoadingSpinner
  },

  props: {
    columns: {
      type: Array,
      required: true,
      validator: (value: any[]) => value.every(col => 
        col.title && col.key && typeof col.sortable === 'boolean'
      )
    },
    data: {
      type: Array,
      required: true
    },
    sortable: {
      type: Boolean,
      default: false
    },
    paginated: {
      type: Boolean,
      default: false
    },
    itemsPerPage: {
      type: Number,
      default: 10,
      validator: (value: number) => value > 0
    },
    loading: {
      type: Boolean,
      default: false
    },
    emptyText: {
      type: String,
      default: 'No data available'
    }
  },

  setup(props, { emit }) {
    const currentPage = ref(1);
    const currentSort = ref({ key: '', direction: '' });
    const announcement = ref('');
    const announcer = ref<HTMLElement | null>(null);

    // Computed Properties
    const displayData = computed(() => {
      let processedData = [...props.data];

      // Apply sorting
      if (currentSort.value.key && currentSort.value.direction) {
        processedData.sort((a, b) => {
          const aVal = getCellValue(a, currentSort.value.key);
          const bVal = getCellValue(b, currentSort.value.key);
          
          const modifier = currentSort.value.direction === 'asc' ? 1 : -1;
          
          if (typeof aVal === 'string' && typeof bVal === 'string') {
            return aVal.localeCompare(bVal) * modifier;
          }
          return (aVal < bVal ? -1 : aVal > bVal ? 1 : 0) * modifier;
        });
      }

      // Apply pagination
      if (props.paginated) {
        const start = (currentPage.value - 1) * props.itemsPerPage;
        const end = start + props.itemsPerPage;
        return processedData.slice(start, end);
      }

      return processedData;
    });

    const totalPages = computed(() => {
      return Math.ceil(props.data.length / props.itemsPerPage);
    });

    // Methods
    const getCellValue = (row: any, key: string) => {
      return key.split('.').reduce((obj, key) => obj?.[key], row);
    };

    const getSortAriaLabel = (column: any) => {
      if (!column.sortable || !props.sortable) return undefined;
      if (currentSort.value.key !== column.key) return 'none';
      return currentSort.value.direction === 'asc' ? 'ascending' : 'descending';
    };

    const getSortIcon = (column: any) => {
      if (!column.sortable || !props.sortable) return '';
      if (currentSort.value.key !== column.key) return '↕';
      return currentSort.value.direction === 'asc' ? '↑' : '↓';
    };

    const announce = (message: string) => {
      announcement.value = message;
      setTimeout(() => {
        announcement.value = '';
      }, 1000);
    };

    const handleSort = debounce((column: any) => {
      if (!column.sortable || !props.sortable) return;

      const direction = 
        currentSort.value.key === column.key && currentSort.value.direction === 'asc'
          ? 'desc'
          : 'asc';

      currentSort.value = { key: column.key, direction };
      
      emit('sort', column.key, direction);
      announce(`Table sorted by ${column.title} ${direction === 'asc' ? 'ascending' : 'descending'}`);
    }, 300);

    const handlePageChange = (page: number) => {
      if (page < 1 || page > totalPages.value) return;
      
      currentPage.value = page;
      emit('page-change', page);
      announce(`Showing page ${page} of ${totalPages.value}`);
    };

    const handleRowClick = (row: any) => {
      emit('row-click', row);
    };

    return {
      currentPage,
      currentSort,
      announcement,
      announcer,
      displayData,
      totalPages,
      getCellValue,
      getSortAriaLabel,
      getSortIcon,
      handleSort,
      handlePageChange,
      handleRowClick
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.base-table-wrapper {
  width: 100%;
  overflow-x: auto;
  background-color: var(--color-white);
  border-radius: var(--border-radius-md);
  box-shadow: var(--elevation-2);
  position: relative;

  &.loading {
    min-height: 200px;
  }
}

.table-loader {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.base-table {
  width: 100%;
  border-collapse: collapse;
  font-family: vars.$font-family-primary;
  direction: inherit;

  th, td {
    padding: vars.spacing(4);
    text-align: start;
    border-bottom: 1px solid color(gray, 200);
  }

  th {
    font-weight: map-get(vars.$font-weights, semibold);
    background-color: color(gray, 50);
    position: sticky;
    top: 0;
    z-index: 1;

    &.sortable {
      cursor: pointer;
      user-select: none;
      padding-inline-end: vars.spacing(6);

      &:hover {
        background-color: color(gray, 100);
      }

      &:focus-visible {
        outline: 2px solid color(primary);
        outline-offset: -2px;
      }
    }
  }

  .th-content {
    display: flex;
    align-items: center;
    gap: vars.spacing(2);
  }

  .sort-indicator {
    font-size: 0.875em;
    color: color(gray, 500);
  }

  .table-row {
    &:hover {
      background-color: color(gray, 50);
    }

    &.clickable {
      cursor: pointer;

      &:focus-visible {
        outline: 2px solid color(primary);
        outline-offset: -2px;
      }
    }
  }

  .empty-state {
    text-align: center;
    padding: vars.spacing(8);
    color: color(gray, 500);
    font-style: italic;
  }
}

// RTL Support
[dir="rtl"] {
  .sort-indicator {
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

// Reduced motion support
@media (prefers-reduced-motion: reduce) {
  .sort-indicator {
    transition: none;
  }
}
</style>