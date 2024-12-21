/**
 * Core validation utility module for the Medical Research Platform
 * Provides comprehensive validation for form inputs and data submissions
 * @version 1.0.0
 * @package @medical-research-platform/web
 */

import validator from 'validator';  // v13.9.0
import zxcvbn from 'zxcvbn';      // v4.4.2
import { LoginCredentials, RegisterCredentials } from '../types/auth';
import { 
  DataValidationError, 
  BloodWorkData,
  ValidationSeverity,
  VALIDATION_SEVERITY 
} from '../types/data';

// Validation Constants
export const PASSWORD_MIN_LENGTH = 12;
export const PASSWORD_PATTERN = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]{12,}$/;

// Validation Error Messages
export const VALIDATION_ERRORS = {
  INVALID_EMAIL: 'Please enter a valid email address',
  INVALID_PASSWORD: 'Password must be at least 12 characters with uppercase, lowercase, numbers, and special characters',
  PASSWORD_MISMATCH: 'Passwords do not match',
  WEAK_PASSWORD: 'Password is too weak. Please choose a stronger password',
  INVALID_MARKER_VALUE: 'Marker value is outside valid range',
  INVALID_TEST_DATE: 'Test date must be within the last 30 days',
  REQUIRED_FIELD: 'This field is required',
  INVALID_ENCRYPTION: 'Invalid encryption metadata',
  INVALID_LAB: 'Laboratory not in approved list'
};

// Approved laboratories list
export const APPROVED_LABS = [
  'LabCorp',
  'Quest Diagnostics',
  'Mayo Clinic Laboratories'
];

// Blood work marker reference ranges
export const MARKER_RANGES: Record<string, { min: number; max: number; unit: string }> = {
  vitamin_d: { min: 20, max: 80, unit: 'ng/mL' },
  b12: { min: 200, max: 900, unit: 'pg/mL' }
};

/**
 * Creates a validation error object with enhanced context
 */
const createValidationError = (
  field: string,
  message: string,
  code: string,
  severity: ValidationSeverity = VALIDATION_SEVERITY.ERROR,
  context: Record<string, unknown> = {}
): DataValidationError => ({
  field,
  message,
  code,
  severity,
  context
});

/**
 * Validates login credentials with enhanced security checks
 * @param credentials LoginCredentials object containing email and password
 * @returns Array of validation errors
 */
export const validateLoginCredentials = (credentials: LoginCredentials): DataValidationError[] => {
  const errors: DataValidationError[] = [];

  // Email validation
  const normalizedEmail = validator.normalizeEmail(credentials.email, {
    all_lowercase: true,
    gmail_remove_dots: false
  });

  if (!normalizedEmail || !validator.isEmail(normalizedEmail, { allow_utf8_local_part: false })) {
    errors.push(createValidationError(
      'email',
      VALIDATION_ERRORS.INVALID_EMAIL,
      'INVALID_EMAIL_FORMAT'
    ));
  }

  // Password validation
  if (!credentials.password) {
    errors.push(createValidationError(
      'password',
      VALIDATION_ERRORS.REQUIRED_FIELD,
      'MISSING_PASSWORD'
    ));
  } else if (!PASSWORD_PATTERN.test(credentials.password)) {
    errors.push(createValidationError(
      'password',
      VALIDATION_ERRORS.INVALID_PASSWORD,
      'INVALID_PASSWORD_FORMAT'
    ));
  }

  return errors;
};

/**
 * Validates registration data with advanced password strength validation
 * @param data RegisterCredentials object
 * @returns Array of validation errors
 */
export const validateRegistrationData = (data: RegisterCredentials): DataValidationError[] => {
  const errors: DataValidationError[] = [];

  // Email validation
  const normalizedEmail = validator.normalizeEmail(data.email, {
    all_lowercase: true,
    gmail_remove_dots: false
  });

  if (!normalizedEmail || !validator.isEmail(normalizedEmail, { allow_utf8_local_part: false })) {
    errors.push(createValidationError(
      'email',
      VALIDATION_ERRORS.INVALID_EMAIL,
      'INVALID_EMAIL_FORMAT'
    ));
  }

  // Password strength validation
  const passwordStrength = zxcvbn(data.password);
  if (passwordStrength.score < 3) {
    errors.push(createValidationError(
      'password',
      VALIDATION_ERRORS.WEAK_PASSWORD,
      'WEAK_PASSWORD',
      VALIDATION_SEVERITY.ERROR,
      { suggestions: passwordStrength.feedback.suggestions }
    ));
  }

  // Password format validation
  if (!PASSWORD_PATTERN.test(data.password)) {
    errors.push(createValidationError(
      'password',
      VALIDATION_ERRORS.INVALID_PASSWORD,
      'INVALID_PASSWORD_FORMAT'
    ));
  }

  // Password confirmation validation
  if (data.password !== data.confirmPassword) {
    errors.push(createValidationError(
      'confirmPassword',
      VALIDATION_ERRORS.PASSWORD_MISMATCH,
      'PASSWORD_MISMATCH'
    ));
  }

  return errors;
};

/**
 * Validates blood work data with encryption validation and marker checks
 * @param data BloodWorkData object containing test results and metadata
 * @returns Array of validation errors
 */
export const validateBloodWorkData = (data: BloodWorkData): DataValidationError[] => {
  const errors: DataValidationError[] = [];

  // Encryption metadata validation
  if (!data.encryptionMetadata || !data.encryptionMetadata.algorithm || !data.encryptionMetadata.keyId) {
    errors.push(createValidationError(
      'encryption',
      VALIDATION_ERRORS.INVALID_ENCRYPTION,
      'MISSING_ENCRYPTION_METADATA',
      VALIDATION_SEVERITY.ERROR,
      { metadata: data.encryptionMetadata }
    ));
  }

  // Lab validation
  if (!APPROVED_LABS.includes(data.labName)) {
    errors.push(createValidationError(
      'labName',
      VALIDATION_ERRORS.INVALID_LAB,
      'UNAPPROVED_LAB',
      VALIDATION_SEVERITY.ERROR,
      { approvedLabs: APPROVED_LABS }
    ));
  }

  // Test date validation
  const testDate = new Date(data.testDate);
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

  if (testDate < thirtyDaysAgo || testDate > new Date()) {
    errors.push(createValidationError(
      'testDate',
      VALIDATION_ERRORS.INVALID_TEST_DATE,
      'INVALID_TEST_DATE',
      VALIDATION_SEVERITY.ERROR,
      { testDate, validRange: { min: thirtyDaysAgo, max: new Date() } }
    ));
  }

  // Marker validation
  Object.entries(data.markers).forEach(([marker, value]) => {
    const range = MARKER_RANGES[marker];
    if (range) {
      if (value < range.min || value > range.max) {
        errors.push(createValidationError(
          `markers.${marker}`,
          VALIDATION_ERRORS.INVALID_MARKER_VALUE,
          'INVALID_MARKER_VALUE',
          VALIDATION_SEVERITY.WARNING,
          { value, range, unit: range.unit }
        ));
      }
    }
  });

  // Validation schema checks
  if (data.validationSchema) {
    const { rules, required, customValidators } = data.validationSchema;
    
    // Check required fields
    required.forEach(field => {
      if (!data.markers[field]) {
        errors.push(createValidationError(
          `markers.${field}`,
          VALIDATION_ERRORS.REQUIRED_FIELD,
          'MISSING_REQUIRED_MARKER',
          VALIDATION_SEVERITY.ERROR,
          { field }
        ));
      }
    });

    // Run custom validators
    if (customValidators) {
      Object.entries(customValidators).forEach(([field, validator]) => {
        if (data.markers[field] && !validator(data.markers[field])) {
          errors.push(createValidationError(
            `markers.${field}`,
            'Custom validation failed',
            'CUSTOM_VALIDATION_FAILED',
            VALIDATION_SEVERITY.ERROR,
            { field, value: data.markers[field] }
          ));
        }
      });
    }
  }

  return errors;
};