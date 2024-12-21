// External imports
import { UUID } from 'crypto'; // v1.0.0 - Type definition for UUID strings

// Chart Types
export type ChartType = 'line' | 'bar' | 'scatter' | 'histogram' | 'boxplot' | 'heatmap' | 'radar' | 'pie';

// Analysis Metrics
export type AnalysisMetric = 'basic_stats' | 'correlations' | 'time_series' | 'patterns' | 'outliers' | 'clusters';

// Trend Types
export type TrendType = 'increasing' | 'decreasing' | 'stable' | 'cyclic' | 'irregular';

// Correlation Types
export type CorrelationType = 'pearson' | 'spearman' | 'kendall';

// Pattern Types and Metadata
export type PatternType = 'trend' | 'cycle' | 'seasonality' | 'outlier' | 'cluster';

// Basic Statistical Metrics Interface
export interface BasicStats {
    mean: number;
    median: number;
    stdDev: number;
    min: number;
    max: number;
    sampleSize: number;
    variance: number;
    confidenceInterval: {
        lower: number;
        upper: number;
    };
}

// Correlation Interface
export interface Correlation {
    metric1: string;
    metric2: string;
    coefficient: number;
    significance: number;
    sampleSize: number;
    correlationType: CorrelationType;
}

// Time Series Forecast Interface
export interface TimeSeriesForecast {
    values: number[];
    confidenceIntervals: Array<{
        lower: number;
        upper: number;
    }>;
    timestamps: Date[];
}

// Time Series Metric Interface
export interface TimeSeriesMetric {
    metric: string;
    trend: TrendType;
    seasonality: boolean;
    periodicity: number | null;
    forecast: TimeSeriesForecast | null;
    confidence: number;
}

// Chart Configuration Interfaces
export interface ChartConfig {
    responsive: boolean;
    displayModeBar: boolean;
    showLegend: boolean;
    showGrid: boolean;
    animations: boolean;
}

export interface ChartData {
    x: (number | string | Date)[];
    y: number[];
    type: ChartType;
    name: string;
    error_y?: {
        array: number[];
        visible: boolean;
    };
}

export interface ChartLayout {
    title: string;
    xaxis: {
        title: string;
        type: string;
    };
    yaxis: {
        title: string;
        type: string;
    };
    margin: {
        l: number;
        r: number;
        t: number;
        b: number;
    };
}

// Pattern Metadata Interface
export interface PatternMetadata {
    description: string;
    significance: number;
    affectedMetrics: string[];
    timeRange?: {
        start: Date;
        end: Date;
    };
}

// Analysis Options Interface
export interface AnalysisOptions {
    metrics: AnalysisMetric[];
    timeRange?: {
        start: Date;
        end: Date;
    };
    groupBy?: string[];
    filters?: Record<string, unknown>;
}

// Analysis Metadata Interface
export interface AnalysisMetadata {
    version: string;
    executionTime: number;
    dataQualityScore: number;
    warnings: string[];
    completeness: number;
}

// Main Exported Interfaces
export interface StatisticalSummary {
    basicStats: BasicStats;
    correlations: Correlation[];
    timeSeriesMetrics: TimeSeriesMetric[];
    computedAt: Date;
}

export interface PatternDetection {
    pattern: PatternType;
    confidenceScore: number;
    detectedAt: Date;
    metadata: PatternMetadata;
}

export interface VisualizationConfig {
    chartType: ChartType;
    config: ChartConfig;
    data: ChartData;
    layout: ChartLayout;
}

export interface AnalysisRequest {
    protocolId: UUID;
    dataPoints: DataPoint[];
    confidenceThreshold: number;
    analysisOptions: AnalysisOptions;
}

export interface AnalysisResult {
    statisticalSummary: StatisticalSummary;
    patterns: PatternDetection[];
    visualizations: VisualizationConfig[];
    metadata: AnalysisMetadata;
}

// DataPoint interface (referenced but not defined in imports)
export interface DataPoint {
    id: UUID;
    value: number;
    timestamp: Date;
    metric: string;
    metadata?: Record<string, unknown>;
}