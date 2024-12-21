// date-fns v2.30.0 - Date manipulation utilities
import { format, parseISO, addDays, differenceInDays } from 'date-fns';

/**
 * Custom error class for date-related operations
 */
class DateUtilError extends Error {
  constructor(message: string) {
    super(`DateUtil Error: ${message}`);
    this.name = 'DateUtilError';
  }
}

/**
 * Supported date format strings
 */
export const DATE_FORMATS = {
  DISPLAY: 'MMM d, yyyy',
  INPUT: 'yyyy-MM-dd',
  TIMESTAMP: 'yyyy-MM-dd HH:mm:ss'
} as const;

export const DEFAULT_DATE_FORMAT = DATE_FORMATS.INPUT;

/**
 * Cache for memoizing frequently used date formats
 */
const formatCache = new Map<string, string>();

/**
 * Validates if a value is a valid Date object
 * @param date - Value to validate
 * @returns True if value is a valid Date
 */
const isValidDate = (date: Date): boolean => {
  return date instanceof Date && !isNaN(date.getTime());
};

/**
 * Formats a date using the specified format string or default format
 * @param date - Date to format (Date object or ISO string)
 * @param formatStr - Optional format string (defaults to yyyy-MM-dd)
 * @returns Formatted date string
 * @throws {DateUtilError} If date is invalid or format string is unsupported
 */
export const formatDate = (date: Date | string, formatStr: string = DEFAULT_DATE_FORMAT): string => {
  try {
    // Convert string dates to Date objects
    const dateObj = typeof date === 'string' ? parseISO(date) : date;

    // Validate date object
    if (!isValidDate(dateObj)) {
      throw new DateUtilError('Invalid date provided');
    }

    // Validate format string is supported
    if (!Object.values(DATE_FORMATS).includes(formatStr as any) && formatStr !== DEFAULT_DATE_FORMAT) {
      throw new DateUtilError('Unsupported date format');
    }

    // Check cache for frequently used formats
    const cacheKey = `${dateObj.getTime()}-${formatStr}`;
    if (formatCache.has(cacheKey)) {
      return formatCache.get(cacheKey)!;
    }

    // Format date and cache result
    const formatted = format(dateObj, formatStr);
    formatCache.set(cacheKey, formatted);
    return formatted;
  } catch (error) {
    if (error instanceof DateUtilError) {
      throw error;
    }
    throw new DateUtilError(`Failed to format date: ${error.message}`);
  }
};

/**
 * Parses a date string into a Date object with validation
 * @param dateStr - ISO format date string
 * @returns Parsed Date object
 * @throws {DateUtilError} If date string is invalid or out of acceptable range
 */
export const parseDate = (dateStr: string): Date => {
  try {
    // Validate input string
    if (!dateStr?.trim()) {
      throw new DateUtilError('Empty or invalid date string');
    }

    // Parse ISO date string
    const parsed = parseISO(dateStr);
    
    // Validate parsed date
    if (!isValidDate(parsed)) {
      throw new DateUtilError('Failed to parse date string');
    }

    // Validate date is within acceptable range (1900-2100)
    const year = parsed.getFullYear();
    if (year < 1900 || year > 2100) {
      throw new DateUtilError('Date is outside acceptable range (1900-2100)');
    }

    return parsed;
  } catch (error) {
    if (error instanceof DateUtilError) {
      throw error;
    }
    throw new DateUtilError(`Failed to parse date: ${error.message}`);
  }
};

/**
 * Calculates the duration between two dates in days
 * @param startDate - Protocol start date
 * @param endDate - Protocol end date
 * @returns Number of days between dates
 * @throws {DateUtilError} If dates are invalid or in wrong order
 */
export const calculateProtocolDuration = (startDate: Date, endDate: Date): number => {
  try {
    // Validate input dates
    if (!isValidDate(startDate) || !isValidDate(endDate)) {
      throw new DateUtilError('Invalid date object provided');
    }

    // Validate date order
    if (startDate > endDate) {
      throw new DateUtilError('Start date cannot be after end date');
    }

    // Calculate duration using date-fns
    const duration = differenceInDays(endDate, startDate);

    // Validate result
    if (duration < 0) {
      throw new DateUtilError('Invalid duration calculation');
    }

    return duration;
  } catch (error) {
    if (error instanceof DateUtilError) {
      throw error;
    }
    throw new DateUtilError(`Failed to calculate duration: ${error.message}`);
  }
};

/**
 * Calculates the current week number in a protocol timeline
 * @param startDate - Protocol start date
 * @param currentDate - Current date to compare against
 * @returns Current week number (1-based)
 * @throws {DateUtilError} If dates are invalid or in wrong order
 */
export const getWeekNumber = (startDate: Date, currentDate: Date): number => {
  try {
    // Validate input dates
    if (!isValidDate(startDate) || !isValidDate(currentDate)) {
      throw new DateUtilError('Invalid date object provided');
    }

    // Validate date order
    if (startDate > currentDate) {
      throw new DateUtilError('Start date cannot be after current date');
    }

    // Calculate days elapsed
    const daysElapsed = differenceInDays(currentDate, startDate);

    // Validate result
    if (daysElapsed < 0) {
      throw new DateUtilError('Invalid days elapsed calculation');
    }

    // Calculate week number (1-based)
    return Math.floor(daysElapsed / 7) + 1;
  } catch (error) {
    if (error instanceof DateUtilError) {
      throw error;
    }
    throw new DateUtilError(`Failed to calculate week number: ${error.message}`);
  }
};