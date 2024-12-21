<template>
  <div 
    class="chart-container"
    :style="{ height, width }"
    role="group"
    :aria-label="description || 'Data visualization chart'"
  >
    <canvas
      ref="chartCanvas"
      role="img"
      :aria-label="description"
      tabindex="0"
      @keydown="handleKeyboardNavigation"
    ></canvas>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onUnmounted, watch, PropType } from 'vue';
import { Chart, ChartConfiguration } from 'chart.js'; // v4.3.0

// Internal imports
import { createTimeSeriesChart, createComparisonChart } from '@/utils/charts';
import { CHART_COLORS, DEFAULT_CHART_OPTIONS } from '@/config/charts';
import { ChartType } from '@/types/analysis';

export default defineComponent({
  name: 'BaseChart',

  props: {
    chartType: {
      type: String as PropType<ChartType>,
      required: true,
      validator: (value: string) => ['line', 'bar', 'scatter', 'histogram', 'boxplot', 'heatmap', 'radar', 'pie'].includes(value)
    },
    data: {
      type: Array as PropType<Array<Record<string, any>>>,
      required: true,
      validator: (value: Array<any>) => value.length > 0
    },
    options: {
      type: Object as PropType<Partial<ChartConfiguration>>,
      default: () => DEFAULT_CHART_OPTIONS
    },
    height: {
      type: String,
      default: '300px'
    },
    width: {
      type: String,
      default: '100%'
    },
    highContrast: {
      type: Boolean,
      default: false
    },
    description: {
      type: String,
      default: ''
    }
  },

  emits: ['chartClick', 'chartHover', 'accessibilityAction'],

  setup(props, { emit }) {
    const chartCanvas = ref<HTMLCanvasElement | null>(null);
    const chartInstance = ref<Chart | null>(null);
    let keyboardFocusIndex = ref(0);

    // Initialize chart with accessibility features
    const initializeChart = () => {
      if (!chartCanvas.value) return;

      const ctx = chartCanvas.value.getContext('2d');
      if (!ctx) return;

      // Apply high contrast colors if enabled
      const colors = props.highContrast ? CHART_COLORS.highContrast : {
        backgroundColor: CHART_COLORS.primary,
        borderColor: CHART_COLORS.primary
      };

      // Merge default options with custom options and accessibility features
      const mergedOptions: ChartConfiguration = {
        ...props.options,
        plugins: {
          ...DEFAULT_CHART_OPTIONS.plugins,
          ...props.options.plugins,
          accessibility: {
            enabled: true,
            description: props.description,
            announceDataPoints: true,
            labels: {
              aria: props.description
            }
          }
        }
      };

      // Create chart instance with accessibility support
      chartInstance.value = new Chart(ctx, {
        type: props.chartType,
        data: {
          labels: props.data.map(d => d.label),
          datasets: [{
            ...colors,
            data: props.data.map(d => d.value)
          }]
        },
        options: mergedOptions
      });

      // Set up event listeners
      chartInstance.value.canvas.addEventListener('click', handleChartClick);
      chartInstance.value.canvas.addEventListener('mousemove', handleChartHover);
    };

    // Update chart while maintaining accessibility
    const updateChart = () => {
      if (!chartInstance.value) return;

      chartInstance.value.data.labels = props.data.map(d => d.label);
      chartInstance.value.data.datasets[0].data = props.data.map(d => d.value);

      if (props.highContrast) {
        chartInstance.value.data.datasets[0].backgroundColor = CHART_COLORS.highContrast.primary;
        chartInstance.value.data.datasets[0].borderColor = CHART_COLORS.highContrast.primary;
      }

      chartInstance.value.options = {
        ...chartInstance.value.options,
        plugins: {
          ...chartInstance.value.options.plugins,
          accessibility: {
            enabled: true,
            description: props.description,
            announceDataPoints: true
          }
        }
      };

      chartInstance.value.update();
    };

    // Handle keyboard navigation for accessibility
    const handleKeyboardNavigation = (event: KeyboardEvent) => {
      if (!chartInstance.value) return;

      const dataLength = chartInstance.value.data.datasets[0].data.length;

      switch (event.key) {
        case 'ArrowRight':
        case 'ArrowDown':
          keyboardFocusIndex.value = (keyboardFocusIndex.value + 1) % dataLength;
          break;
        case 'ArrowLeft':
        case 'ArrowUp':
          keyboardFocusIndex.value = (keyboardFocusIndex.value - 1 + dataLength) % dataLength;
          break;
        case 'Enter':
        case ' ':
          const element = chartInstance.value.getDatasetMeta(0).data[keyboardFocusIndex.value];
          emit('accessibilityAction', 'select', {
            index: keyboardFocusIndex.value,
            value: props.data[keyboardFocusIndex.value]
          });
          break;
        default:
          return;
      }

      event.preventDefault();
      announceSelectedDataPoint();
    };

    // Announce selected data point for screen readers
    const announceSelectedDataPoint = () => {
      if (!chartInstance.value) return;
      
      const data = props.data[keyboardFocusIndex.value];
      const announcement = `Selected data point: ${data.label}, value: ${data.value}`;
      
      emit('accessibilityAction', 'announce', { message: announcement });
    };

    // Event handlers
    const handleChartClick = (event: MouseEvent) => {
      if (!chartInstance.value) return;
      
      const elements = chartInstance.value.getElementsAtEventForMode(
        event,
        'nearest',
        { intersect: true },
        false
      );
      
      emit('chartClick', event, elements);
    };

    const handleChartHover = (event: MouseEvent) => {
      if (!chartInstance.value) return;
      
      const elements = chartInstance.value.getElementsAtEventForMode(
        event,
        'nearest',
        { intersect: true },
        false
      );
      
      emit('chartHover', event, elements);
    };

    // Cleanup
    const destroyChart = () => {
      if (chartInstance.value) {
        chartInstance.value.canvas.removeEventListener('click', handleChartClick);
        chartInstance.value.canvas.removeEventListener('mousemove', handleChartHover);
        chartInstance.value.destroy();
        chartInstance.value = null;
      }
    };

    // Lifecycle hooks
    onMounted(() => {
      initializeChart();
    });

    onUnmounted(() => {
      destroyChart();
    });

    // Watch for changes
    watch(() => props.data, updateChart, { deep: true });
    watch(() => props.options, updateChart, { deep: true });
    watch(() => props.highContrast, updateChart);

    return {
      chartCanvas,
      handleKeyboardNavigation
    };
  }
});
</script>

<style scoped>
.chart-container {
  position: relative;
  margin: 0 auto;
  min-height: 200px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .chart-container {
    min-height: 150px;
  }
}

/* Focus styles for keyboard navigation */
.chart-container:focus-within {
  outline: 2px solid var(--focus-color, #3498DB);
  outline-offset: 2px;
}

/* High contrast mode styles */
:deep(.high-contrast) {
  filter: contrast(1.5);
}
</style>