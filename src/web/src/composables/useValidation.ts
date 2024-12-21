/**
 * Vue 3 composable providing reactive form validation capabilities
 * with enhanced performance optimization and error tracking
 * @version 1.0.0
 * @package @medical-research-platform/web
 */

import { ref, computed } from 'vue'; // v3.3.0
import {
  validateLoginCredentials,
  validateRegistrationData,
  validateBloodWorkData
} from '../utils/validation';
import type {
  LoginCredentials,
  RegisterCredentials
} from '../types/auth';
import type { DataValidationError } from '../types/data';

// Validation state interface
interface ValidationState {
  errors: DataValidationError[];
  isValid: boolean;
  isDirty: boolean;
  isSubmitting: boolean;
  validationHistory: ValidationHistoryEntry[];
}

// Cache entry interface for validation results
interface CachedValidation {
  timestamp: number;
  errors: DataValidationError[];
  value: any;
}

// Validation history entry for tracking
interface ValidationHistoryEntry {
  fieldName: string;
  timestamp: number;
  wasValid: boolean;
  errors: DataValidationError[];
}

// Constants
const DEBOUNCE_DELAY = 300; // ms
const CACHE_DURATION = 5000; // ms

/**
 * Vue composable providing reactive form validation capabilities
 * with performance optimization and detailed error tracking
 */
export default function useValidation() {
  // Initialize validation state
  const validationState = ref<ValidationState>({
    errors: [],
    isValid: true,
    isDirty: false,
    isSubmitting: false,
    validationHistory: []
  });

  // Validation cache for performance optimization
  const validationCache = new Map<string, CachedValidation>();

  /**
   * Cleans expired entries from validation cache
   */
  const cleanValidationCache = () => {
    const now = Date.now();
    for (const [key, value] of validationCache.entries()) {
      if (now - value.timestamp > CACHE_DURATION) {
        validationCache.delete(key);
      }
    }
  };

  /**
   * Debounced validation function
   */
  const debouncedValidate = (() => {
    let timeout: NodeJS.Timeout;
    return (callback: () => void) => {
      clearTimeout(timeout);
      timeout = setTimeout(callback, DEBOUNCE_DELAY);
    };
  })();

  /**
   * Validates login credentials with caching
   * @param credentials LoginCredentials object
   */
  const validateLogin = async (credentials: LoginCredentials) => {
    const cacheKey = `login:${JSON.stringify(credentials)}`;
    const cached = validationCache.get(cacheKey);

    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      validationState.value.errors = cached.errors;
      return cached.errors;
    }

    validationState.value.isSubmitting = true;
    const errors = validateLoginCredentials(credentials);

    // Cache results
    validationCache.set(cacheKey, {
      timestamp: Date.now(),
      errors,
      value: credentials
    });

    validationState.value.errors = errors;
    validationState.value.isValid = errors.length === 0;
    validationState.value.isSubmitting = false;

    return errors;
  };

  /**
   * Validates registration data with enhanced error tracking
   * @param data RegisterCredentials object
   */
  const validateRegistration = async (data: RegisterCredentials) => {
    const cacheKey = `registration:${JSON.stringify(data)}`;
    const cached = validationCache.get(cacheKey);

    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      validationState.value.errors = cached.errors;
      return cached.errors;
    }

    validationState.value.isSubmitting = true;
    const errors = validateRegistrationData(data);

    // Cache results
    validationCache.set(cacheKey, {
      timestamp: Date.now(),
      errors,
      value: data
    });

    validationState.value.errors = errors;
    validationState.value.isValid = errors.length === 0;
    validationState.value.isSubmitting = false;

    // Track validation history
    validationState.value.validationHistory.push({
      fieldName: 'registration',
      timestamp: Date.now(),
      wasValid: errors.length === 0,
      errors
    });

    return errors;
  };

  /**
   * Validates a single field with debouncing
   * @param fieldName Field identifier
   * @param value Field value
   */
  const validateField = async (fieldName: string, value: any) => {
    const cacheKey = `field:${fieldName}:${JSON.stringify(value)}`;
    const cached = validationCache.get(cacheKey);

    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      return cached.errors;
    }

    return new Promise<DataValidationError[]>((resolve) => {
      debouncedValidate(async () => {
        let errors: DataValidationError[] = [];

        // Field-specific validation logic
        switch (fieldName) {
          case 'email':
            if (value && typeof value === 'string') {
              errors = validateLoginCredentials({ email: value, password: '' })
                .filter(error => error.field === 'email');
            }
            break;
          case 'password':
            if (value && typeof value === 'string') {
              errors = validateLoginCredentials({ email: '', password: value })
                .filter(error => error.field === 'password');
            }
            break;
          // Add other field validations as needed
        }

        // Cache results
        validationCache.set(cacheKey, {
          timestamp: Date.now(),
          errors,
          value
        });

        // Update validation state
        validationState.value.isDirty = true;
        validationState.value.validationHistory.push({
          fieldName,
          timestamp: Date.now(),
          wasValid: errors.length === 0,
          errors
        });

        resolve(errors);
      });
    });
  };

  /**
   * Resets validation state and clears cache
   */
  const resetValidation = () => {
    validationState.value = {
      errors: [],
      isValid: true,
      isDirty: false,
      isSubmitting: false,
      validationHistory: []
    };
    validationCache.clear();
  };

  /**
   * Retrieves validation errors for a specific field
   * @param fieldName Field identifier
   */
  const getFieldErrors = (fieldName: string): DataValidationError[] => {
    return validationState.value.errors.filter(error => error.field === fieldName);
  };

  // Computed properties for validation state
  const hasErrors = computed(() => validationState.value.errors.length > 0);
  const isValid = computed(() => validationState.value.isValid);
  const isDirty = computed(() => validationState.value.isDirty);
  const isSubmitting = computed(() => validationState.value.isSubmitting);

  // Clean validation cache periodically
  setInterval(cleanValidationCache, CACHE_DURATION);

  return {
    // State
    errors: computed(() => validationState.value.errors),
    hasErrors,
    isValid,
    isDirty,
    isSubmitting,
    validationHistory: computed(() => validationState.value.validationHistory),

    // Methods
    validateLogin,
    validateRegistration,
    validateField,
    resetValidation,
    getFieldErrors
  };
}