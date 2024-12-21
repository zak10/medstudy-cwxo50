// @version axios ^1.4.0
import axios, { AxiosError } from 'axios';

// Internal imports
import { APIResponse } from './types';
import { StatisticalSummary, AnalysisRequest, AnalysisResult } from '../types/analysis';
import { ENDPOINTS } from '../config/api';

// Constants for analysis configuration
const ANALYSIS_FORMATS = ['csv', 'json', 'pdf', 'xlsx'] as const;
const DEFAULT_CONFIDENCE_THRESHOLD = 0.95;
const MAX_RETRY_ATTEMPTS = 3;
const RETRY_DELAY_MS = 1000;

type AnalysisFormat = typeof ANALYSIS_FORMATS[number];

/**
 * Validates protocol ID format
 * @param protocolId - Protocol identifier to validate
 * @throws Error if protocol ID is invalid
 */
const validateProtocolId = (protocolId: string): void => {
  if (!protocolId || !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(protocolId)) {
    throw new Error('Invalid protocol ID format');
  }
};

/**
 * Validates analysis export format
 * @param format - Format to validate
 * @throws Error if format is invalid
 */
const validateExportFormat = (format: string): asserts format is AnalysisFormat => {
  if (!ANALYSIS_FORMATS.includes(format as AnalysisFormat)) {
    throw new Error(`Invalid export format. Supported formats: ${ANALYSIS_FORMATS.join(', ')}`);
  }
};

/**
 * Implements exponential backoff retry logic
 * @param attempt - Current retry attempt number
 * @returns Delay in milliseconds before next retry
 */
const getRetryDelay = (attempt: number): number => {
  return Math.min(RETRY_DELAY_MS * Math.pow(2, attempt), 10000);
};

/**
 * Retrieves analysis results for a specific protocol with enhanced error handling
 * @param protocolId - Unique identifier of the protocol
 * @returns Promise resolving to analysis results
 */
export const getProtocolResults = async (
  protocolId: string
): Promise<APIResponse<AnalysisResult>> => {
  validateProtocolId(protocolId);

  let attempt = 0;
  while (attempt < MAX_RETRY_ATTEMPTS) {
    try {
      const response = await axios.get<APIResponse<AnalysisResult>>(
        ENDPOINTS.ANALYSIS.RESULTS.replace(':protocolId', protocolId),
        {
          headers: {
            'Accept': 'application/json',
            'X-Request-ID': crypto.randomUUID()
          }
        }
      );

      // Validate response data integrity
      if (!response.data.data || !response.data.data.statisticalSummary) {
        throw new Error('Invalid analysis results format');
      }

      return response.data;
    } catch (error) {
      if (attempt === MAX_RETRY_ATTEMPTS - 1 || (error as AxiosError).response?.status === 404) {
        throw error;
      }
      await new Promise(resolve => setTimeout(resolve, getRetryDelay(attempt)));
      attempt++;
    }
  }
  throw new Error('Maximum retry attempts exceeded');
};

/**
 * Exports analysis results in specified format with format validation
 * @param protocolId - Unique identifier of the protocol
 * @param format - Export format (csv, json, pdf, xlsx)
 * @returns Promise resolving to file blob
 */
export const exportAnalysis = async (
  protocolId: string,
  format: string
): Promise<Blob> => {
  validateProtocolId(protocolId);
  validateExportFormat(format);

  try {
    const response = await axios.get(
      ENDPOINTS.ANALYSIS.EXPORT.replace(':protocolId', protocolId),
      {
        params: { format },
        responseType: 'blob',
        headers: {
          'Accept': `application/${format}`,
          'X-Request-ID': crypto.randomUUID()
        }
      }
    );

    // Validate response content type
    const contentType = response.headers['content-type'];
    if (!contentType?.includes(format)) {
      throw new Error('Invalid response content type');
    }

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(`Export failed: ${error.response?.data?.message || error.message}`);
    }
    throw error;
  }
};

/**
 * Retrieves statistical summary with confidence intervals
 * @param protocolId - Unique identifier of the protocol
 * @returns Promise resolving to statistical summary
 */
export const getStatisticalSummary = async (
  protocolId: string
): Promise<APIResponse<StatisticalSummary>> => {
  validateProtocolId(protocolId);

  try {
    const response = await axios.get<APIResponse<StatisticalSummary>>(
      ENDPOINTS.ANALYSIS.SUMMARY.replace(':protocolId', protocolId),
      {
        headers: {
          'Accept': 'application/json',
          'X-Request-ID': crypto.randomUUID()
        }
      }
    );

    // Validate statistical significance
    const summary = response.data.data;
    if (summary.basicStats.confidenceInterval.lower >= summary.basicStats.confidenceInterval.upper) {
      throw new Error('Invalid confidence interval in statistical summary');
    }

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(`Failed to retrieve statistical summary: ${error.response?.data?.message || error.message}`);
    }
    throw error;
  }
};

/**
 * Triggers analysis computation with enhanced validation
 * @param request - Analysis request parameters
 * @returns Promise resolving to analysis results
 */
export const runAnalysis = async (
  request: AnalysisRequest
): Promise<APIResponse<AnalysisResult>> => {
  validateProtocolId(request.protocolId);

  // Validate confidence threshold
  if (request.confidenceThreshold < DEFAULT_CONFIDENCE_THRESHOLD) {
    throw new Error(`Confidence threshold must be >= ${DEFAULT_CONFIDENCE_THRESHOLD}`);
  }

  // Validate data points completeness
  if (!request.dataPoints?.length) {
    throw new Error('Analysis requires at least one data point');
  }

  try {
    const response = await axios.post<APIResponse<AnalysisResult>>(
      ENDPOINTS.ANALYSIS.BASE,
      request,
      {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-Request-ID': crypto.randomUUID()
        }
      }
    );

    // Validate analysis results
    const result = response.data.data;
    if (!result.metadata.dataQualityScore || result.metadata.dataQualityScore < 0.8) {
      throw new Error('Insufficient data quality for reliable analysis');
    }

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(`Analysis computation failed: ${error.response?.data?.message || error.message}`);
    }
    throw error;
  }
};