<template>
  <div 
    class="analysis-chart" 
    :style="{ position: 'relative', width: '100%' }"
    role="figure"
    :aria-label="`${metricKey} visualization`"
  >
    <canvas
      ref="chartCanvas"
      :style="{ height: `${height}px` }"
      tabindex="0"
      role="img"
      :aria-label="`${metricKey} chart showing data trends`"
    ></canvas>
    <!-- Accessibility description for screen readers -->
    <div class="visually-hidden" role="note">
      {{ accessibilityDescription }}
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, onBeforeUnmount, watch, ref, computed } from 'vue'; // v3.3.0
import { Chart } from 'chart.js'; // v4.3.0
import { useResizeObserver } from '@vueuse/core'; // v10.1.0

// Internal imports
import { createTimeSeriesChart, createComparisonChart } from '@/utils/charts';
import { ChartType } from '@/types/analysis';
import { CHART_COLORS, getChartColors } from '@/config/charts';

export default defineComponent({
  name: 'AnalysisChart',

  props: {
    chartData: {
      type: Array as () => Array<{ timestamp: Date; value: number }>,
      required: true,
      validator: (data: Array<{ timestamp: Date; value: number }>) => {
        return data.every(point => point.timestamp instanceof Date && typeof point.value === 'number');
      }
    },
    chartType: {
      type: String as () => ChartType,
      required: true,
      validator: (value: string) => ['line', 'bar'].includes(value)
    },
    metricKey: {
      type: String,
      required: true
    },
    height: {
      type: Number,
      default: 300
    },
    accessibilityMode: {
      type: Boolean,
      default: false
    }
  },

  setup(props) {
    const chartInstance = ref<Chart | null>(null);
    const chartCanvas = ref<HTMLCanvasElement | null>(null);
    let resizeObserver: ResizeObserver | null = null;

    // Computed accessibility description
    const accessibilityDescription = computed(() => {
      if (!props.chartData.length) return '';
      
      const startDate = props.chartData[0].timestamp;
      const endDate = props.chartData[props.chartData.length - 1].timestamp;
      const average = props.chartData.reduce((sum, point) => sum + point.value, 0) / props.chartData.length;
      
      return `${props.metricKey} data from ${startDate.toLocaleDateString()} to ${endDate.toLocaleDateString()} with average value of ${average.toFixed(2)}`;
    });

    // Initialize chart with accessibility features
    const initializeChart = () => {
      if (!chartCanvas.value) return;

      const ctx = chartCanvas.value.getContext('2d');
      if (!ctx) return;

      // Get appropriate colors based on accessibility mode
      const colors = getChartColors(props.accessibilityMode);

      // Create chart configuration
      const config = createTimeSeriesChart(
        props.chartData,
        props.metricKey,
        props.chartType,
        {
          options: {
            plugins: {
              accessibility: {
                enabled: true,
                description: accessibilityDescription.value,
                announceDataPoints: true
              }
            }
          }
        }
      );

      // Initialize Chart.js instance
      chartInstance.value = new Chart(ctx, config);

      // Setup keyboard navigation
      setupKeyboardNavigation();
    };

    // Update chart when data changes
    const updateChart = () => {
      if (!chartInstance.value) return;

      chartInstance.value.data.datasets[0].data = props.chartData.map(point => point.value);
      chartInstance.value.data.labels = props.chartData.map(point => 
        point.timestamp.toLocaleDateString()
      );

      chartInstance.value.update('active');
    };

    // Handle responsive resizing
    const handleResize = (entries: ResizeObserverEntry[]) => {
      if (!chartInstance.value || !entries.length) return;

      const { width } = entries[0].contentRect;
      chartInstance.value.resize();
    };

    // Setup keyboard navigation for accessibility
    const setupKeyboardNavigation = () => {
      if (!chartCanvas.value) return;

      chartCanvas.value.addEventListener('keydown', (e: KeyboardEvent) => {
        switch (e.key) {
          case 'ArrowRight':
          case 'ArrowLeft':
            e.preventDefault();
            navigateDataPoints(e.key === 'ArrowRight' ? 1 : -1);
            break;
        }
      });
    };

    // Navigate through data points using keyboard
    const navigateDataPoints = (direction: number) => {
      if (!chartInstance.value) return;

      const activeElements = chartInstance.value.getActiveElements();
      let index = activeElements.length ? activeElements[0].index : -1;
      
      index = Math.max(0, Math.min(props.chartData.length - 1, index + direction));
      
      chartInstance.value.setActiveElements([{
        datasetIndex: 0,
        index
      }]);
      
      chartInstance.value.update();
    };

    // Lifecycle hooks
    onMounted(() => {
      initializeChart();
      
      // Setup resize observer
      if (chartCanvas.value) {
        resizeObserver = useResizeObserver(chartCanvas.value, handleResize);
      }
    });

    onBeforeUnmount(() => {
      // Cleanup
      if (chartInstance.value) {
        chartInstance.value.destroy();
      }
      if (resizeObserver) {
        resizeObserver.disconnect();
      }
    });

    // Watch for data and accessibility changes
    watch(() => props.chartData, updateChart, { deep: true });
    watch(() => props.accessibilityMode, () => {
      if (chartInstance.value) {
        chartInstance.value.destroy();
        initializeChart();
      }
    });

    return {
      chartCanvas,
      accessibilityDescription
    };
  }
});
</script>

<style scoped>
.analysis-chart {
  position: relative;
  width: 100%;
}

/* Hide content visually but keep it available for screen readers */
.visually-hidden {
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