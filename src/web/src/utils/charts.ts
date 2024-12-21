// External imports
import { Chart, ChartConfiguration } from 'chart.js'; // v4.3.0
import { format } from 'date-fns'; // v2.30.0

// Internal imports
import { ChartType } from '../types/analysis';
import { CHART_COLORS, DEFAULT_CHART_OPTIONS } from '../config/charts';

/**
 * Interface for time series data point
 */
interface TimeSeriesDataPoint {
  timestamp: Date;
  value: number;
  label?: string;
}

/**
 * Interface for comparison dataset
 */
interface ComparisonDataset {
  label: string;
  data: number[];
  description?: string;
}

/**
 * Creates an accessible time series chart configuration with WCAG compliance
 * @param data - Array of time series data points
 * @param metricKey - Key identifier for the metric being visualized
 * @param chartType - Type of chart to create (line or bar)
 * @param options - Optional Chart.js configuration overrides
 * @returns ChartConfiguration object with accessibility features
 */
export const createTimeSeriesChart = (
  data: TimeSeriesDataPoint[],
  metricKey: string,
  chartType: ChartType,
  options: Partial<ChartConfiguration> = {}
): ChartConfiguration => {
  // Validate input data
  if (!data?.length) {
    throw new Error('Time series data is required');
  }

  // Format timestamps for x-axis
  const labels = data.map(point => format(point.timestamp, 'MMM d, yyyy'));
  const values = data.map(point => point.value);

  // Create accessible dataset configuration
  const dataset = {
    label: metricKey,
    data: values,
    backgroundColor: CHART_COLORS.primary,
    borderColor: CHART_COLORS.primary,
    fill: false,
    tension: 0.4,
    pointRadius: 4,
    pointHoverRadius: 6,
    // Add ARIA description for screen readers
    description: `Time series data for ${metricKey} from ${format(data[0].timestamp, 'MMM d, yyyy')} to ${format(data[data.length - 1].timestamp, 'MMM d, yyyy')}`,
  };

  // Merge with default options and add accessibility features
  return {
    type: chartType,
    data: {
      labels,
      datasets: [dataset],
    },
    options: {
      ...DEFAULT_CHART_OPTIONS,
      ...options,
      plugins: {
        ...DEFAULT_CHART_OPTIONS.plugins,
        ...options.plugins,
        // Enhanced accessibility configuration
        accessibility: {
          enabled: true,
          description: `Chart showing ${metricKey} over time`,
          announceDataPoints: true,
        },
      },
      scales: {
        x: {
          ...DEFAULT_CHART_OPTIONS.scales?.x,
          title: {
            display: true,
            text: 'Date',
          },
        },
        y: {
          ...DEFAULT_CHART_OPTIONS.scales?.y,
          title: {
            display: true,
            text: metricKey,
          },
        },
      },
    },
  };
};

/**
 * Creates an accessible comparison chart for multiple metrics
 * @param datasets - Array of comparison datasets
 * @param labels - Array of labels for x-axis
 * @param chartType - Type of chart to create
 * @param options - Optional Chart.js configuration overrides
 * @returns ChartConfiguration object with accessibility features
 */
export const createComparisonChart = (
  datasets: ComparisonDataset[],
  labels: string[],
  chartType: ChartType,
  options: Partial<ChartConfiguration> = {}
): ChartConfiguration => {
  // Validate inputs
  if (!datasets?.length || !labels?.length) {
    throw new Error('Datasets and labels are required');
  }

  // Format datasets with accessibility features
  const formattedDatasets = datasets.map((dataset, index) => ({
    label: dataset.label,
    data: dataset.data,
    backgroundColor: index === 0 ? CHART_COLORS.primary : CHART_COLORS.secondary,
    borderColor: index === 0 ? CHART_COLORS.primary : CHART_COLORS.secondary,
    fill: false,
    // Add ARIA description for screen readers
    description: dataset.description || `Data series for ${dataset.label}`,
  }));

  return {
    type: chartType,
    data: {
      labels,
      datasets: formattedDatasets,
    },
    options: {
      ...DEFAULT_CHART_OPTIONS,
      ...options,
      plugins: {
        ...DEFAULT_CHART_OPTIONS.plugins,
        ...options.plugins,
        // Enhanced accessibility configuration
        accessibility: {
          enabled: true,
          description: `Comparison chart with ${datasets.length} metrics`,
          announceDataPoints: true,
        },
      },
    },
  };
};

/**
 * Formats raw data into Chart.js compatible format with accessibility metadata
 * @param data - Array of raw data records
 * @param xKey - Key for x-axis values
 * @param yKey - Key for y-axis values
 * @param options - Optional formatting options
 * @returns Formatted data object for Chart.js
 */
export const formatChartData = (
  data: Array<Record<string, any>>,
  xKey: string,
  yKey: string,
  options: { description?: string; ariaLabel?: string } = {}
) => {
  // Validate input data
  if (!data?.length || !xKey || !yKey) {
    throw new Error('Data and key names are required');
  }

  const formattedData = {
    labels: data.map(item => item[xKey]),
    datasets: [{
      data: data.map(item => item[yKey]),
      label: options.ariaLabel || yKey,
      description: options.description || `Data series showing ${yKey} values`,
    }],
  };

  return formattedData;
};

/**
 * Generates accessible chart options based on metric type
 * @param metricKey - Key identifier for the metric
 * @param chartType - Type of chart
 * @param accessibility - Accessibility options
 * @param responsive - Whether to enable responsive features
 * @returns Chart options configuration
 */
export const getChartOptions = (
  metricKey: string,
  chartType: ChartType,
  accessibility: { description?: string; ariaLabel?: string } = {},
  responsive: boolean = true
): ChartConfiguration['options'] => {
  return {
    ...DEFAULT_CHART_OPTIONS,
    responsive,
    plugins: {
      ...DEFAULT_CHART_OPTIONS.plugins,
      // Enhanced accessibility configuration
      accessibility: {
        enabled: true,
        description: accessibility.description || `Chart showing ${metricKey} data`,
        announceDataPoints: true,
        labels: {
          aria: accessibility.ariaLabel || `${metricKey} chart`,
        },
      },
      // Enhanced tooltip configuration for accessibility
      tooltip: {
        ...DEFAULT_CHART_OPTIONS.plugins?.tooltip,
        callbacks: {
          label: (context: any) => {
            return `${context.dataset.label}: ${context.formattedValue}`;
          },
        },
      },
    },
    // Keyboard navigation support
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false,
      includeInvisible: true,
    },
  };
};