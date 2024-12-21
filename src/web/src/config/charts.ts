import { ChartConfiguration } from 'chart.js'; // v4.3.0
import { ChartType } from '../types/analysis';

/**
 * WCAG 2.1 AA compliant color palette for data visualizations
 * All colors meet minimum contrast ratio requirements of 4.5:1
 */
export const CHART_COLORS = {
  // Primary brand colors
  primary: '#2C3E50', // Dark blue - main data series
  secondary: '#3498DB', // Light blue - secondary data series
  accent: '#E74C3C', // Red - highlights and alerts
  
  // Background and structural colors
  background: '#FFFFFF', // White - chart background
  grid: '#EEEEEE', // Light grey - grid lines
  text: '#2C3E50', // Dark blue - text elements
  
  // UI element colors
  tooltipBackground: '#FFFFFF',
  tooltipBorder: '#EEEEEE',
  
  // High contrast mode colors for accessibility
  highContrast: {
    primary: '#000000', // Black
    secondary: '#0066CC', // High contrast blue
    accent: '#CC0000', // High contrast red
  }
} as const;

/**
 * Typography configuration for chart elements
 * Using system font stack with Inter as primary font
 */
export const CHART_FONTS = {
  family: 'Inter, system-ui, -apple-system, sans-serif',
  size: {
    title: '16px',
    label: '14px',
    tick: '12px',
    legend: '12px',
    tooltip: '13px',
    // Responsive font sizes for different breakpoints
    responsive: {
      mobile: {
        title: '14px',
        label: '12px',
        tick: '10px',
      }
    }
  },
  weight: {
    normal: '400',
    medium: '500',
    bold: '600'
  }
} as const;

/**
 * Default chart configuration with accessibility and responsive features
 * Implements Chart.js best practices for enterprise applications
 */
export const DEFAULT_CHART_OPTIONS: ChartConfiguration['options'] = {
  // Enable responsive behavior
  responsive: true,
  maintainAspectRatio: false,

  // Plugin configurations
  plugins: {
    // Legend configuration
    legend: {
      position: 'bottom',
      align: 'start',
      labels: {
        font: {
          family: CHART_FONTS.family,
          size: CHART_FONTS.size.legend,
          weight: CHART_FONTS.weight.normal,
        },
        color: CHART_COLORS.text,
        padding: 20,
        usePointStyle: true,
      }
    },

    // Tooltip configuration
    tooltip: {
      enabled: true,
      mode: 'index',
      intersect: false,
      backgroundColor: CHART_COLORS.tooltipBackground,
      titleColor: CHART_COLORS.text,
      bodyColor: CHART_COLORS.text,
      borderColor: CHART_COLORS.tooltipBorder,
      borderWidth: 1,
      padding: 12,
      cornerRadius: 4,
      titleFont: {
        family: CHART_FONTS.family,
        size: CHART_FONTS.size.tooltip,
        weight: CHART_FONTS.weight.medium,
      },
      bodyFont: {
        family: CHART_FONTS.family,
        size: CHART_FONTS.size.tooltip,
        weight: CHART_FONTS.weight.normal,
      }
    }
  },

  // Scales configuration
  scales: {
    x: {
      grid: {
        color: CHART_COLORS.grid,
        drawBorder: false,
        tickLength: 8,
      },
      ticks: {
        font: {
          family: CHART_FONTS.family,
          size: CHART_FONTS.size.tick,
          weight: CHART_FONTS.weight.normal,
        },
        color: CHART_COLORS.text,
        padding: 8,
      },
      title: {
        display: true,
        font: {
          family: CHART_FONTS.family,
          size: CHART_FONTS.size.label,
          weight: CHART_FONTS.weight.medium,
        }
      }
    },
    y: {
      grid: {
        color: CHART_COLORS.grid,
        drawBorder: false,
      },
      ticks: {
        font: {
          family: CHART_FONTS.family,
          size: CHART_FONTS.size.tick,
          weight: CHART_FONTS.weight.normal,
        },
        color: CHART_COLORS.text,
        padding: 8,
      },
      title: {
        display: true,
        font: {
          family: CHART_FONTS.family,
          size: CHART_FONTS.size.label,
          weight: CHART_FONTS.weight.medium,
        }
      }
    }
  },

  // Animation configuration
  animation: {
    duration: 750,
    easing: 'easeInOutQuart',
  },

  // Interaction configuration
  interaction: {
    mode: 'nearest',
    axis: 'x',
    intersect: false,
  },

  // Element styling
  elements: {
    line: {
      tension: 0.4, // Smooth curves for line charts
      borderWidth: 2,
    },
    point: {
      radius: 4,
      hitRadius: 8,
      hoverRadius: 6,
    }
  }
} as const;

/**
 * Helper function to get chart colors with high contrast if needed
 * @param {boolean} highContrast - Whether to use high contrast colors
 * @returns {Record<string, string>} Color object with appropriate contrast
 */
export const getChartColors = (highContrast: boolean = false): Record<string, string> => {
  return highContrast ? CHART_COLORS.highContrast : {
    primary: CHART_COLORS.primary,
    secondary: CHART_COLORS.secondary,
    accent: CHART_COLORS.accent,
  };
};

/**
 * Helper function to get responsive font sizes based on viewport
 * @param {number} viewportWidth - Current viewport width
 * @returns {Record<string, string>} Font sizes object for current viewport
 */
export const getResponsiveFontSizes = (viewportWidth: number): Record<string, string> => {
  return viewportWidth < 768 ? CHART_FONTS.size.responsive.mobile : {
    title: CHART_FONTS.size.title,
    label: CHART_FONTS.size.label,
    tick: CHART_FONTS.size.tick,
  };
};