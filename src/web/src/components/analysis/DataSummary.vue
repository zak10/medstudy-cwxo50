<template>
  <div class="data-summary">
    <!-- Error Boundary -->
    <div v-if="error" class="error-state" role="alert">
      <p>{{ error }}</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-overlay" role="status">
      <LoadingSpinner size="large" color="primary" />
    </div>

    <!-- Basic Statistics Section -->
    <section v-if="currentAnalysis?.statisticalSummary?.basicStats">
      <h3 class="section-title">
        Basic Statistics
        <span class="info-tooltip" title="Statistical measures of central tendency and dispersion">ℹ</span>
      </h3>
      <BaseTable
        :columns="basicStatsColumns"
        :data="basicStatsData"
        :loading="loading"
        emptyText="No basic statistics available"
      />
    </section>

    <!-- Correlations Section -->
    <section v-if="currentAnalysis?.statisticalSummary?.correlations?.length">
      <h3 class="section-title">
        Correlations
        <span class="info-tooltip" title="Relationships between different metrics">ℹ</span>
      </h3>
      <BaseTable
        :columns="correlationColumns"
        :data="correlationData"
        :loading="loading"
        emptyText="No correlations available"
      />
    </section>

    <!-- Time Series Metrics Section -->
    <section v-if="currentAnalysis?.statisticalSummary?.timeSeriesMetrics?.length">
      <h3 class="section-title">
        Time Series Analysis
        <span class="info-tooltip" title="Temporal patterns and trends">ℹ</span>
      </h3>
      <BaseTable
        :columns="timeSeriesColumns"
        :data="timeSeriesData"
        :loading="loading"
        emptyText="No time series metrics available"
      />
    </section>

    <!-- No Data State -->
    <div v-if="!loading && !currentAnalysis" class="no-data" role="status">
      <p>No analysis data available</p>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue'; // v3.3.0
import BaseTable from '../common/BaseTable.vue';
import LoadingSpinner from '../common/LoadingSpinner.vue';
import { useAnalysisStore } from '../../stores/analysis';
import type { StatisticalSummary } from '../../types/analysis';

export default defineComponent({
  name: 'DataSummary',

  components: {
    BaseTable,
    LoadingSpinner
  },

  setup() {
    const analysisStore = useAnalysisStore();
    const { currentAnalysis, loading, error } = analysisStore;

    // Basic Statistics Columns
    const basicStatsColumns = computed(() => [
      {
        key: 'metric',
        title: 'Metric',
        sortable: true,
        width: '25%'
      },
      {
        key: 'mean',
        title: 'Mean',
        sortable: true,
        width: '15%'
      },
      {
        key: 'median',
        title: 'Median',
        sortable: true,
        width: '15%'
      },
      {
        key: 'stdDev',
        title: 'Std Dev',
        sortable: true,
        width: '15%'
      },
      {
        key: 'min',
        title: 'Min',
        sortable: true,
        width: '15%'
      },
      {
        key: 'max',
        title: 'Max',
        sortable: true,
        width: '15%'
      }
    ]);

    // Correlation Columns
    const correlationColumns = computed(() => [
      {
        key: 'metrics',
        title: 'Metric Pair',
        sortable: true,
        width: '40%'
      },
      {
        key: 'coefficient',
        title: 'Correlation',
        sortable: true,
        width: '30%'
      },
      {
        key: 'significance',
        title: 'P-Value',
        sortable: true,
        width: '30%'
      }
    ]);

    // Time Series Columns
    const timeSeriesColumns = computed(() => [
      {
        key: 'metric',
        title: 'Metric',
        sortable: true,
        width: '30%'
      },
      {
        key: 'trend',
        title: 'Trend',
        sortable: true,
        width: '25%'
      },
      {
        key: 'seasonality',
        title: 'Seasonality',
        sortable: true,
        width: '25%'
      },
      {
        key: 'periodicity',
        title: 'Period',
        sortable: true,
        width: '20%'
      }
    ]);

    // Transform data for tables
    const basicStatsData = computed(() => {
      if (!currentAnalysis.value?.statisticalSummary?.basicStats) return [];
      const stats = currentAnalysis.value.statisticalSummary.basicStats;
      return Object.entries(stats).map(([metric, values]) => ({
        metric,
        mean: values.mean.toFixed(2),
        median: values.median.toFixed(2),
        stdDev: values.stdDev.toFixed(2),
        min: values.min.toFixed(2),
        max: values.max.toFixed(2)
      }));
    });

    const correlationData = computed(() => {
      if (!currentAnalysis.value?.statisticalSummary?.correlations) return [];
      return currentAnalysis.value.statisticalSummary.correlations.map(corr => ({
        metrics: `${corr.metric1} vs ${corr.metric2}`,
        coefficient: corr.coefficient.toFixed(3),
        significance: corr.significance.toFixed(4)
      }));
    });

    const timeSeriesData = computed(() => {
      if (!currentAnalysis.value?.statisticalSummary?.timeSeriesMetrics) return [];
      return currentAnalysis.value.statisticalSummary.timeSeriesMetrics.map(ts => ({
        metric: ts.metric,
        trend: ts.trend.charAt(0).toUpperCase() + ts.trend.slice(1),
        seasonality: ts.seasonality ? 'Yes' : 'No',
        periodicity: ts.periodicity ? `${ts.periodicity} days` : 'N/A'
      }));
    });

    return {
      currentAnalysis,
      loading,
      error,
      basicStatsColumns,
      correlationColumns,
      timeSeriesColumns,
      basicStatsData,
      correlationData,
      timeSeriesData
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.data-summary {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
  min-height: 400px;
}

section {
  background-color: var(--color-white);
  border-radius: var(--border-radius-md);
  box-shadow: var(--elevation-2);
  padding: var(--spacing-6);
  position: relative;
}

.section-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  margin-bottom: var(--spacing-4);
  color: var(--color-gray-900);
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.info-tooltip {
  color: var(--color-gray-500);
  cursor: help;
  font-size: 0.875em;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.error-state {
  padding: var(--spacing-4);
  background-color: var(--color-error-50);
  border: 1px solid var(--color-error-200);
  border-radius: var(--border-radius-md);
  color: var(--color-error-700);
}

.no-data {
  text-align: center;
  padding: var(--spacing-8);
  color: var(--color-gray-500);
  font-style: italic;
}

// Responsive adjustments
@media (max-width: map-get(vars.$breakpoints, tablet)) {
  .section-title {
    font-size: var(--font-size-md);
  }

  section {
    padding: var(--spacing-4);
  }
}

// Reduced motion support
@media (prefers-reduced-motion: reduce) {
  .loading-overlay {
    transition: none;
  }
}
</style>