// numeral v2.0.6 - Number formatting library
import numeral from 'numeral';
import { DataPoint, DataPointType, isBloodWorkData, isCheckInData } from '../types/data';
import { formatDate } from './date';

/**
 * Constants for blood work marker units with proper typing
 */
const BLOOD_WORK_UNITS: Readonly<Record<string, string>> = {
  vitamin_d: 'ng/mL',
  omega_3: 'mg/dL',
  vitamin_b12: 'pg/mL',
  iron: 'μg/dL',
  magnesium: 'mg/dL',
  zinc: 'μg/dL'
} as const;

/**
 * Constants for number formatting patterns
 */
const NUMBER_FORMATS: Readonly<Record<string, string>> = {
  DEFAULT: '0,0.00',
  PERCENTAGE: '0.0%',
  INTEGER: '0,0',
  PRECISE: '0,0.000',
  COMPACT: '0a'
} as const;

/**
 * Marker-specific precision settings
 */
const MARKER_PRECISION: Readonly<Record<string, number>> = {
  vitamin_d: 1,
  omega_3: 0,
  vitamin_b12: 0,
  iron: 0,
  magnesium: 1,
  zinc: 0
} as const;

/**
 * Custom error class for formatting operations
 */
class FormatError extends Error {
  constructor(message: string) {
    super(`Format Error: ${message}`);
    this.name = 'FormatError';
  }
}

/**
 * Formats numeric values with specified precision and validation
 * @param value - Number to format
 * @param format - Optional format pattern from NUMBER_FORMATS
 * @returns Formatted number string
 * @throws {FormatError} If value is invalid or format is unsupported
 */
export const formatNumber = (value: number, format: string = NUMBER_FORMATS.DEFAULT): string => {
  try {
    // Validate input number
    if (!Number.isFinite(value)) {
      throw new FormatError('Invalid number provided');
    }

    // Validate format string
    if (!Object.values(NUMBER_FORMATS).includes(format)) {
      throw new FormatError('Unsupported number format');
    }

    // Format number using numeral
    const formatted = numeral(value).format(format);

    // Validate output
    if (formatted === 'NaN') {
      throw new FormatError('Failed to format number');
    }

    return formatted;
  } catch (error) {
    if (error instanceof FormatError) {
      throw error;
    }
    throw new FormatError(`Failed to format number: ${error.message}`);
  }
};

/**
 * Formats blood work values with appropriate units and precision
 * @param value - Blood work measurement value
 * @param marker - Blood work marker type
 * @returns Formatted value with units
 * @throws {FormatError} If marker is invalid or value is out of range
 */
export const formatBloodWorkValue = (value: number, marker: string): string => {
  try {
    // Validate marker exists
    if (!BLOOD_WORK_UNITS[marker]) {
      throw new FormatError(`Unsupported blood work marker: ${marker}`);
    }

    // Validate value
    if (!Number.isFinite(value) || value < 0) {
      throw new FormatError('Invalid blood work value');
    }

    // Get marker-specific precision
    const precision = MARKER_PRECISION[marker] ?? 1;

    // Format number with proper precision
    const formatted = formatNumber(value, `0,0.${Array(precision).fill('0').join('')}`);

    // Return formatted value with units
    return `${formatted} ${BLOOD_WORK_UNITS[marker]}`;
  } catch (error) {
    if (error instanceof FormatError) {
      throw error;
    }
    throw new FormatError(`Failed to format blood work value: ${error.message}`);
  }
};

/**
 * Formats protocol duration with proper pluralization
 * @param weeks - Number of weeks
 * @returns Formatted duration string
 * @throws {FormatError} If weeks value is invalid
 */
export const formatProtocolDuration = (weeks: number): string => {
  try {
    // Validate weeks is positive integer
    if (!Number.isInteger(weeks) || weeks < 0) {
      throw new FormatError('Invalid number of weeks');
    }

    // Format with proper pluralization
    return weeks === 1 ? '1 week' : `${formatNumber(weeks, NUMBER_FORMATS.INTEGER)} weeks`;
  } catch (error) {
    if (error instanceof FormatError) {
      throw error;
    }
    throw new FormatError(`Failed to format protocol duration: ${error.message}`);
  }
};

/**
 * Formats participant count with proper pluralization
 * @param count - Number of participants
 * @returns Formatted count string
 * @throws {FormatError} If count is invalid
 */
export const formatParticipantCount = (count: number): string => {
  try {
    // Validate count is non-negative integer
    if (!Number.isInteger(count) || count < 0) {
      throw new FormatError('Invalid participant count');
    }

    // Handle special cases
    if (count === 0) return 'No participants';
    if (count === 1) return '1 participant';

    // Format plural case
    return `${formatNumber(count, NUMBER_FORMATS.INTEGER)} participants`;
  } catch (error) {
    if (error instanceof FormatError) {
      throw error;
    }
    throw new FormatError(`Failed to format participant count: ${error.message}`);
  }
};

/**
 * Formats data point values based on their type with comprehensive validation
 * @param dataPoint - Data point object to format
 * @returns Formatted data point value with appropriate units
 * @throws {FormatError} If data point is invalid or formatting fails
 */
export const formatDataPointValue = (dataPoint: DataPoint): string => {
  try {
    // Validate data point structure
    if (!dataPoint?.type || !dataPoint.data) {
      throw new FormatError('Invalid data point structure');
    }

    // Format based on data point type
    switch (dataPoint.type) {
      case DataPointType.BLOOD_WORK:
        if (!isBloodWorkData(dataPoint.data)) {
          throw new FormatError('Invalid blood work data structure');
        }
        const marker = Object.keys(dataPoint.data.markers)[0];
        return formatBloodWorkValue(dataPoint.data.markers[marker], marker);

      case DataPointType.CHECK_IN:
        if (!isCheckInData(dataPoint.data)) {
          throw new FormatError('Invalid check-in data structure');
        }
        return `Energy: ${dataPoint.data.energyLevel}/5, Sleep: ${dataPoint.data.sleepQuality}/5`;

      case DataPointType.BIOMETRIC:
        return formatNumber(dataPoint.data.value, NUMBER_FORMATS.PRECISE);

      default:
        throw new FormatError(`Unsupported data point type: ${dataPoint.type}`);
    }
  } catch (error) {
    if (error instanceof FormatError) {
      throw error;
    }
    throw new FormatError(`Failed to format data point: ${error.message}`);
  }
};