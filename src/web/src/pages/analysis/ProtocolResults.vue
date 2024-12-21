<template>
  <div 
    class="protocol-results"
    role="main"
    aria-busy="isLoading"
  >
    <!-- Loading State -->
    <div 
      v-if="isLoading" 
      class="loading-overlay"
      role="status"
    >
      <LoadingSpinner size="large" color="primary" />
      <span class="sr-only">Loading analysis results</span>
    </div>

    <!-- Error State -->
    <div 
      v-else-if="error" 
      class="error-state" 
      role="alert"
    >
      <p>{{ error }}</p>
      <BaseButton 
        variant="primary" 
        @click="loadAnalysisData"
      >
        Retry Loading
      </BaseButton>
    </div>

    <!-- Results Content -->
    <template v-else-if="hasAnalysisData">
      <header class="results-header">
        <h1>Protocol Analysis Results</h1>
        <ResultsExport
          :protocol-id="protocolId"
          @export-complete="handleExportComplete"
          @export-error="handleExportError"
        />
      </header>

      <!-- Data Quality Indicator -->
      <div 
        class="data-quality"
        role="status"
        :aria-label="`Data quality score: ${currentAnalysis?.metadata?.dataQualityScore || 0}%`"
      >
        <span class="quality-label">Data Quality:</span>
        <div class="quality-bar">
          <div 
            class="quality-fill"
            :style="{ width: `${currentAnalysis?.metadata?.dataQualityScore || 0}%` }"
            :class="{ 'high': qualityScore >= 95, 'medium': qualityScore >= 80 && qualityScore < 95, 'low': qualityScore < 80 }"
          ></div>
        </div>
        <span class="quality-score">{{ qualityScore }}%</span>
      </div>

      <!-- Visualization Section -->
      <section class="visualization-section" aria-labelledby="viz-heading">
        <h2 id="viz-heading">Data Visualization</h2>
        <div class="chart-container">
          <AnalysisChart
            v-for="metric in selectedMetrics"
            :key="metric.key"
            :chart-data="getChartData(metric)"
            :chart-type="metric.chartType"
            :metric-key="metric.key"
            class="analysis-chart"
          />
        </div>
      </section>

      <!-- Statistical Summary -->
      <section class="summary-section" aria-labelledby="summary-heading">
        <h2 id="summary-heading">Statistical Summary</h2>
        <DataSummary
          :protocol-id="protocolId"
          :loading="isLoading"
        />
      </section>

      <!-- Pattern Detection -->
      <section 
        v-if="significantPatterns.length"
        class="patterns-section"
        aria-labelledby="patterns-heading"
      >
        <h2 id="patterns-heading">Detected Patterns</h2>
        <ul class="pattern-list">
          <li 
            v-for="pattern in significantPatterns"
            :key="pattern.pattern"
            class="pattern-item"
          >
            <div class="pattern-header">
              <h3>{{ pattern.pattern }}</h3>
              <span class="confidence-score">
                {{ (pattern.confidenceScore * 100).toFixed(1) }}% confidence
              </span>
            </div>
            <p>{{ pattern.metadata.description }}</p>
          </li>
        </ul>
      </section>
    </template>

    <!-- No Data State -->
    <div 
      v-else 
      class="no-data-state"
      role="status"
    >
      <p>No analysis data available for this protocol.</p>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, ref, computed } from 'vue';
import { useRoute } from 'vue-router';
import AnalysisChart from '@/components/analysis/AnalysisChart.vue';
import DataSummary from '@/components/analysis/DataSummary.vue';
import ResultsExport from '@/components/analysis/ResultsExport.vue';
import LoadingSpinner from '@/components/common/LoadingSpinner.vue';
import BaseButton from '@/components/common/BaseButton.vue';
import { useAnalysisStore } from '@/stores/analysis';
import type { ChartType } from '@/types/analysis';

export default defineComponent({
  name: 'ProtocolResults',

  components: {
    AnalysisChart,
    DataSummary,
    ResultsExport,
    LoadingSpinner,
    BaseButton
  },

  setup() {
    const route = useRoute();
    const analysisStore = useAnalysisStore();
    const error = ref<string | null>(null);
    const selectedMetrics = ref<Array<{ key: string; chartType: ChartType }>>([]);

    // Computed properties
    const protocolId = computed(() => route.params.id as string);
    
    const hasAnalysisData = computed(() => 
      analysisStore.currentAnalysis !== null && 
      analysisStore.hasValidAnalysis
    );

    const qualityScore = computed(() => 
      Math.round(analysisStore.currentAnalysis?.metadata?.dataQualityScore || 0)
    );

    const significantPatterns = computed(() => 
      analysisStore.significantPatterns || []
    );

    // Methods
    const loadAnalysisData = async () => {
      try {
        error.value = null;
        await analysisStore.fetchAnalysisResults(protocolId.value);
        initializeMetrics();
      } catch (err) {
        error.value = err instanceof Error ? err.message : 'Failed to load analysis results';
      }
    };

    const initializeMetrics = () => {
      if (!analysisStore.currentAnalysis?.statisticalSummary) return;
      
      selectedMetrics.value = Object.keys(analysisStore.currentAnalysis.statisticalSummary.basicStats)
        .map(key => ({
          key,
          chartType: determineChartType(key)
        }));
    };

    const determineChartType = (metricKey: string): ChartType => {
      // Determine appropriate chart type based on metric characteristics
      const timeSeriesMetric = analysisStore.currentAnalysis?.statisticalSummary?.timeSeriesMetrics
        ?.find(m => m.metric === metricKey);
      
      return timeSeriesMetric?.seasonality ? 'line' : 'bar';
    };

    const getChartData = (metric: { key: string; chartType: ChartType }) => {
      if (!analysisStore.currentAnalysis?.statisticalSummary) return [];
      
      // Transform data into chart-compatible format
      return analysisStore.currentAnalysis.statisticalSummary.timeSeriesMetrics
        ?.find(m => m.metric === metric.key)
        ?.forecast?.values.map((value, index) => ({
          timestamp: new Date(analysisStore.currentAnalysis!.statisticalSummary!.timeSeriesMetrics![0].forecast!.timestamps[index]),
          value
        })) || [];
    };

    const handleExportComplete = (format: string) => {
      // Handle successful export
      analysisStore.notifySuccess(`Analysis results exported successfully as ${format.toUpperCase()}`);
    };

    const handleExportError = (error: Error) => {
      // Handle export error
      analysisStore.notifyError(`Export failed: ${error.message}`);
    };

    // Lifecycle hooks
    onMounted(loadAnalysisData);

    return {
      protocolId,
      hasAnalysisData,
      qualityScore,
      significantPatterns,
      selectedMetrics,
      error,
      isLoading: computed(() => analysisStore.loading),
      currentAnalysis: computed(() => analysisStore.currentAnalysis),
      loadAnalysisData,
      getChartData,
      handleExportComplete,
      handleExportError
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.protocol-results {
  display: flex;
  flex-direction: column;
  gap: vars.spacing(6);
  padding: vars.spacing(6);
  min-height: 400px;
  position: relative;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.9);
  z-index: 10;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: vars.spacing(4);

  h1 {
    font-size: vars.typography.scale.levels.h1;
    color: vars.color(text, primary);
    margin: 0;
  }
}

.data-quality {
  display: flex;
  align-items: center;
  gap: vars.spacing(3);
  padding: vars.spacing(4);
  background-color: white;
  border-radius: 8px;
  box-shadow: vars.elevation.levels.level1.shadow;

  .quality-bar {
    flex: 1;
    height: 8px;
    background-color: vars.color(gray, 200);
    border-radius: 4px;
    overflow: hidden;
  }

  .quality-fill {
    height: 100%;
    transition: width 0.3s ease-in-out;

    &.high { background-color: vars.color(semantic, success); }
    &.medium { background-color: vars.color(semantic, warning); }
    &.low { background-color: vars.color(semantic, error); }
  }
}

.visualization-section,
.summary-section,
.patterns-section {
  background-color: white;
  border-radius: 8px;
  padding: vars.spacing(6);
  box-shadow: vars.elevation.levels.level1.shadow;

  h2 {
    font-size: vars.typography.scale.levels.h2;
    color: vars.color(text, primary);
    margin-bottom: vars.spacing(4);
  }
}

.chart-container {
  display: grid;
  gap: vars.spacing(4);
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

.pattern-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: vars.spacing(4);
}

.pattern-item {
  padding: vars.spacing(4);
  border: 1px solid vars.color(gray, 200);
  border-radius: 4px;

  .pattern-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: vars.spacing(2);
  }

  .confidence-score {
    font-size: 0.875rem;
    color: vars.color(text, secondary);
  }
}

.error-state,
.no-data-state {
  text-align: center;
  padding: vars.spacing(8);
  background-color: white;
  border-radius: 8px;
  box-shadow: vars.elevation.levels.level1.shadow;
}

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

// Responsive adjustments
@media (max-width: map-get(vars.$breakpoints, tablet)) {
  .protocol-results {
    padding: vars.spacing(4);
  }

  .results-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .chart-container {
    grid-template-columns: 1fr;
  }
}

// Reduced motion support
@media (prefers-reduced-motion: reduce) {
  .quality-fill {
    transition: none;
  }
}
</style>