<template>
  <div 
    class="data-point-list"
    role="region"
    aria-label="Protocol Data Points"
  >
    <!-- Error Display -->
    <div 
      v-if="error"
      class="error-container"
      role="alert"
    >
      <p>{{ error.message }}</p>
      <BaseButton
        variant="secondary"
        size="sm"
        @click="handleRetry"
      >
        Retry
      </BaseButton>
    </div>

    <!-- Data Points Table -->
    <BaseTable
      :columns="tableColumns"
      :data="filteredDataPoints"
      :loading="dataStore.loading"
      :error="error"
      sortable
      paginated
      :items-per-page="itemsPerPage"
      @sort="handleSort"
      @page-change="handlePageChange"
      @row-click="handleRowClick"
      aria-label="Protocol Data Points"
      role="grid"
    >
      <!-- Type Column -->
      <template #cell-type="{ value }">
        {{ formatDataType(value) }}
      </template>

      <!-- Date Column -->
      <template #cell-recordedAt="{ value }">
        {{ format(new Date(value), 'MMM dd, yyyy HH:mm') }}
      </template>

      <!-- Status Column -->
      <template #cell-status="{ value }">
        <span 
          class="status-badge"
          :class="`status-${value.toLowerCase()}`"
          :aria-label="`Status: ${value}`"
        >
          {{ formatStatus(value) }}
        </span>
      </template>

      <!-- Details Column -->
      <template #cell-details="{ row }">
        <div class="data-details">
          {{ formatDataDetails(row.data) }}
          <span 
            v-if="row.validationErrors.length > 0"
            class="validation-errors"
            role="alert"
          >
            ({{ row.validationErrors.length }} validation issues)
          </span>
        </div>
      </template>
    </BaseTable>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted, onErrorCaptured } from 'vue'; // v3.3.0
import { format } from 'date-fns'; // v2.30.0
import BaseTable from '../common/BaseTable.vue';
import BaseButton from '../common/BaseButton.vue';
import useDataStore from '../../stores/data';
import type { DataPoint } from '../../types/data';

export default defineComponent({
  name: 'DataPointList',

  components: {
    BaseTable,
    BaseButton
  },

  props: {
    protocolId: {
      type: String,
      required: true,
      validator: (value: string) => /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(value)
    },
    type: {
      type: String,
      required: false,
      validator: (value: string) => ['BLOOD_WORK', 'CHECK_IN', 'BIOMETRIC'].includes(value)
    }
  },

  emits: {
    'row-click': (dataPoint: DataPoint) => !!dataPoint,
    'error': (error: Error) => error instanceof Error
  },

  setup(props, { emit }) {
    const dataStore = useDataStore();
    const currentPage = ref(1);
    const itemsPerPage = ref(10);
    const sortColumn = ref('recordedAt');
    const sortDirection = ref('desc');
    const error = ref<Error | null>(null);

    // Table column definitions with accessibility
    const tableColumns = computed(() => [
      {
        title: 'Type',
        key: 'type',
        sortable: true,
        'aria-sort': sortColumn.value === 'type' ? sortDirection.value : 'none',
        width: '20%'
      },
      {
        title: 'Date',
        key: 'recordedAt',
        sortable: true,
        'aria-sort': sortColumn.value === 'recordedAt' ? sortDirection.value : 'none',
        width: '25%'
      },
      {
        title: 'Status',
        key: 'status',
        sortable: true,
        'aria-sort': sortColumn.value === 'status' ? sortDirection.value : 'none',
        width: '15%'
      },
      {
        title: 'Details',
        key: 'details',
        sortable: false,
        width: '40%'
      }
    ]);

    // Filtered and sorted data points
    const filteredDataPoints = computed(() => {
      let points = [...dataStore.dataPoints];
      
      // Apply type filter if specified
      if (props.type) {
        points = points.filter(point => point.type === props.type);
      }

      // Apply sorting
      points.sort((a, b) => {
        const aVal = a[sortColumn.value as keyof DataPoint];
        const bVal = b[sortColumn.value as keyof DataPoint];
        const modifier = sortDirection.value === 'asc' ? 1 : -1;
        return aVal < bVal ? -modifier : aVal > bVal ? modifier : 0;
      });

      return points;
    });

    // Format data type for display
    const formatDataType = (type: string): string => {
      return type.replace('_', ' ').toLowerCase()
        .replace(/\b\w/g, l => l.toUpperCase());
    };

    // Format status for display
    const formatStatus = (status: string): string => {
      return status.toLowerCase()
        .replace(/\b\w/g, l => l.toUpperCase());
    };

    // Format data details for display
    const formatDataDetails = (data: Record<string, any>): string => {
      const details = [];
      if (data.markers) {
        details.push(`${Object.keys(data.markers).length} markers recorded`);
      }
      if (data.energyLevel) {
        details.push(`Energy Level: ${data.energyLevel}/5`);
      }
      if (data.sleepQuality) {
        details.push(`Sleep Quality: ${data.sleepQuality}/5`);
      }
      return details.join(' | ');
    };

    // Event handlers
    const handleSort = (column: string, direction: string) => {
      sortColumn.value = column;
      sortDirection.value = direction;
      // Announce sort change to screen readers
      const announcer = document.createElement('div');
      announcer.setAttribute('role', 'status');
      announcer.setAttribute('aria-live', 'polite');
      announcer.textContent = `Table sorted by ${column} ${direction}ending`;
      document.body.appendChild(announcer);
      setTimeout(() => announcer.remove(), 1000);
    };

    const handlePageChange = async (page: number) => {
      currentPage.value = page;
      try {
        await dataStore.fetchDataPoints({
          protocolId: props.protocolId,
          page: currentPage.value,
          pageSize: itemsPerPage.value
        });
      } catch (err) {
        handleError(err as Error);
      }
    };

    const handleRowClick = (dataPoint: DataPoint) => {
      emit('row-click', dataPoint);
    };

    const handleError = (err: Error) => {
      error.value = err;
      emit('error', err);
      console.error('DataPointList Error:', err);
    };

    const handleRetry = async () => {
      error.value = null;
      try {
        await dataStore.fetchDataPoints({
          protocolId: props.protocolId,
          page: currentPage.value,
          pageSize: itemsPerPage.value
        });
      } catch (err) {
        handleError(err as Error);
      }
    };

    // Lifecycle hooks
    onMounted(async () => {
      try {
        await dataStore.fetchDataPoints({
          protocolId: props.protocolId,
          page: currentPage.value,
          pageSize: itemsPerPage.value
        });
      } catch (err) {
        handleError(err as Error);
      }
    });

    onErrorCaptured((err) => {
      handleError(err);
      return false;
    });

    return {
      dataStore,
      tableColumns,
      filteredDataPoints,
      currentPage,
      itemsPerPage,
      error,
      format,
      formatDataType,
      formatStatus,
      formatDataDetails,
      handleSort,
      handlePageChange,
      handleRowClick,
      handleRetry
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;

.data-point-list {
  width: 100%;
  margin-top: var(--spacing-4);
  position: relative;
}

.status-badge {
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-sm);
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
}

.status-validated {
  background-color: var(--color-success-50);
  color: var(--color-success-700);
  border: 1px solid var(--color-success-200);
}

.status-pending {
  background-color: var(--color-warning-50);
  color: var(--color-warning-700);
  border: 1px solid var(--color-warning-200);
}

.status-rejected {
  background-color: var(--color-error-50);
  color: var(--color-error-700);
  border: 1px solid var(--color-error-200);
}

.error-container {
  padding: var(--spacing-4);
  background-color: var(--color-error-50);
  border: 1px solid var(--color-error-200);
  border-radius: var(--border-radius-md);
  margin-bottom: var(--spacing-4);
}

.data-details {
  .validation-errors {
    color: var(--color-error-700);
    font-size: var(--font-size-sm);
    margin-left: var(--spacing-2);
  }
}
</style>