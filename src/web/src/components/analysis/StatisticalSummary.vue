<template>
  <div 
    class="statistical-summary" 
    role="region" 
    aria-label="Statistical Analysis Results"
  >
    <!-- Basic Statistics Section -->
    <BaseCard 
      elevation="2"
      padding="4"
      class="statistics-section"
    >
      <template #header>
        <h2 class="section-title">Basic Statistics</h2>
      </template>
      
      <BaseTable
        :columns="basicStatsColumns"
        :data="basicStats"
        :loading="loading"
        :sortable="true"
        @row-click="handleMetricClick"
      >
        <template #cell-value="{ value }">
          <span class="metric-value">
            {{ formatValue(value.value, value.precision, value.unit) }}
          </span>
        </template>
        <template #cell-confidence="{ value }">
          <span 
            class="confidence-indicator"
            :class="{ 'high': value >= 0.95, 'medium': value >= 0.8 && value < 0.95, 'low': value < 0.8 }"
          >
            {{ (value * 100).toFixed(1) }}%
          </span>
        </template>
      </BaseTable>
    </BaseCard>

    <!-- Correlations Section -->
    <BaseCard 
      elevation="2"
      padding="4"
      class="statistics-section"
    >
      <template #header>
        <h2 class="section-title">Correlations</h2>
      </template>

      <BaseTable
        :columns="correlationColumns"
        :data="correlations"
        :loading="loading"
        :sortable="true"
        @row-click="handleMetricClick"
      >
        <template #cell-coefficient="{ value }">
          <span 
            class="correlation-value"
            :class="getCorrelationClass(value)"
          >
            {{ value.toFixed(3) }}
          </span>
        </template>
        <template #cell-significance="{ value }">
          <span class="significance-value">
            p = {{ value < 0.001 ? '< 0.001' : value.toFixed(3) }}
          </span>
        </template>
      </BaseTable>
    </BaseCard>

    <!-- Time Series Metrics Section -->
    <BaseCard 
      elevation="2"
      padding="4"
      class="statistics-section"
    >
      <template #header>
        <h2 class="section-title">Time Series Analysis</h2>
      </template>

      <BaseTable
        :columns="timeSeriesColumns"
        :data="timeSeriesMetrics"
        :loading="loading"
        :sortable="true"
        @row-click="handleMetricClick"
      >
        <template #cell-trend="{ value }">
          <span 
            class="trend-indicator"
            :class="value.toLowerCase()"
          >
            {{ value }}
          </span>
        </template>
        <template #cell-seasonality="{ value }">
          <span class="seasonality-indicator">
            {{ value ? 'Yes' : 'No' }}
          </span>
        </template>
      </BaseTable>
    </BaseCard>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue'; // v3.3.0
import { useI18n } from 'vue-i18n'; // v9.2.0
import BaseTable from '@/components/common/BaseTable.vue';
import BaseCard from '@/components/common/BaseCard.vue';
import type { StatisticalSummary } from '@/types/analysis';

export default defineComponent({
  name: 'StatisticalSummary',

  components: {
    BaseTable,
    BaseCard
  },

  props: {
    statisticalSummary: {
      type: Object as () => StatisticalSummary,
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    }
  },

  emits: ['metric-click'],

  setup(props, { emit }) {
    const { t } = useI18n();

    // Column definitions for basic statistics table
    const basicStatsColumns = computed(() => [
      {
        key: 'metric',
        title: t('analysis.metric'),
        sortable: true,
        width: '30%'
      },
      {
        key: 'value',
        title: t('analysis.value'),
        sortable: true,
        width: '25%'
      },
      {
        key: 'confidence',
        title: t('analysis.confidence'),
        sortable: true,
        width: '25%'
      },
      {
        key: 'sampleSize',
        title: t('analysis.sampleSize'),
        sortable: true,
        width: '20%'
      }
    ]);

    // Column definitions for correlations table
    const correlationColumns = computed(() => [
      {
        key: 'metrics',
        title: t('analysis.metricPair'),
        sortable: true,
        width: '35%'
      },
      {
        key: 'coefficient',
        title: t('analysis.correlation'),
        sortable: true,
        width: '25%'
      },
      {
        key: 'significance',
        title: t('analysis.significance'),
        sortable: true,
        width: '20%'
      },
      {
        key: 'type',
        title: t('analysis.correlationType'),
        sortable: true,
        width: '20%'
      }
    ]);

    // Column definitions for time series metrics table
    const timeSeriesColumns = computed(() => [
      {
        key: 'metric',
        title: t('analysis.metric'),
        sortable: true,
        width: '30%'
      },
      {
        key: 'trend',
        title: t('analysis.trend'),
        sortable: true,
        width: '25%'
      },
      {
        key: 'seasonality',
        title: t('analysis.seasonality'),
        sortable: true,
        width: '25%'
      },
      {
        key: 'confidence',
        title: t('analysis.confidence'),
        sortable: true,
        width: '20%'
      }
    ]);

    // Format numeric values with appropriate precision and units
    const formatValue = (value: number, precision = 2, unit = '') => {
      if (value === null || value === undefined) return '-';
      const formattedValue = Number.isInteger(value) ? 
        value.toString() : 
        value.toFixed(precision);
      return unit ? `${formattedValue} ${unit}` : formattedValue;
    };

    // Get correlation strength class
    const getCorrelationClass = (value: number) => {
      const abs = Math.abs(value);
      if (abs >= 0.7) return 'strong';
      if (abs >= 0.4) return 'moderate';
      return 'weak';
    };

    // Handle metric row click
    const handleMetricClick = (metricData: any) => {
      if (!metricData) return;
      
      // Enhance metric data with confidence intervals and validation status
      const enhancedData = {
        ...metricData,
        confidenceInterval: props.statisticalSummary.basicStats.confidenceInterval,
        timestamp: new Date().toISOString()
      };

      emit('metric-click', enhancedData);
    };

    return {
      basicStatsColumns,
      correlationColumns,
      timeSeriesColumns,
      formatValue,
      getCorrelationClass,
      handleMetricClick
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;

.statistical-summary {
  display: grid;
  gap: var(--spacing-6);
  margin-bottom: var(--spacing-8);
  min-height: 0;
  max-height: 100vh;
  overflow-y: auto;
}

.statistics-section {
  background-color: var(--color-white);
  border-radius: var(--border-radius-md);
}

.section-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--spacing-4);
  color: var(--color-text-primary);
}

.metric-value {
  font-family: var(--font-family-mono);
  font-weight: var(--font-weight-medium);
  transition: background-color 0.2s ease;
  cursor: pointer;

  &:hover {
    background-color: var(--color-gray-100);
  }
}

.correlation-value {
  font-weight: var(--font-weight-medium);

  &.strong { color: var(--color-success); }
  &.moderate { color: var(--color-warning); }
  &.weak { color: var(--color-error); }
}

.confidence-indicator {
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--border-radius-sm);
  font-size: var(--font-size-sm);

  &.high { background-color: var(--color-success-light); }
  &.medium { background-color: var(--color-warning-light); }
  &.low { background-color: var(--color-error-light); }
}

.trend-indicator {
  text-transform: capitalize;
  font-weight: var(--font-weight-medium);

  &.increasing { color: var(--color-success); }
  &.decreasing { color: var(--color-error); }
  &.stable { color: var(--color-info); }
  &.cyclic { color: var(--color-warning); }
}

// Print styles
@media print {
  .statistical-summary {
    overflow: visible;
    max-height: none;
  }

  .statistics-section {
    break-inside: avoid;
    margin-bottom: var(--spacing-8);
  }
}

// Reduced motion
@media (prefers-reduced-motion: reduce) {
  .metric-value {
    transition: none;
  }
}
</style>