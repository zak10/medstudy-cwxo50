// @version pinia ^2.1.0
// @version axios ^1.4.0
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { UUID } from 'crypto';

// Internal imports
import { DataPoint, BloodWorkData, CheckInData, DataPointType, DataPointStatus } from '../types/data';
import { validateBloodWorkData } from '../utils/validation';
import { submitDataPoint, uploadBloodWork } from '../api/data';
import { APIResponse, isAPIError } from '../api/types';
import { ENDPOINTS } from '../config/api';

// Types for store state
interface ValidationError {
  field: string;
  message: string;
  code: string;
  severity: 'error' | 'warning' | 'info';
}

interface SecurityContext {
  isEncrypted: boolean;
  lastValidated: Date | null;
  securityLevel: 'public' | 'confidential' | 'restricted';
}

interface DataState {
  dataPoints: DataPoint[];
  currentPage: number;
  pageSize: number;
  totalItems: number;
  loading: boolean;
  error: Error | null;
  encryptionStatus: 'pending' | 'encrypted' | 'failed';
  validationErrors: ValidationError[];
  uploadProgress: number;
  securityContext: SecurityContext;
}

/**
 * Pinia store for managing secure data collection state and operations
 */
export const useDataStore = defineStore('data', {
  state: (): DataState => ({
    dataPoints: [],
    currentPage: 1,
    pageSize: 10,
    totalItems: 0,
    loading: false,
    error: null,
    encryptionStatus: 'pending',
    validationErrors: [],
    uploadProgress: 0,
    securityContext: {
      isEncrypted: false,
      lastValidated: null,
      securityLevel: 'restricted'
    }
  }),

  getters: {
    /**
     * Returns paginated data points
     */
    paginatedDataPoints: (state): DataPoint[] => {
      const start = (state.currentPage - 1) * state.pageSize;
      return state.dataPoints.slice(start, start + state.pageSize);
    },

    /**
     * Returns total number of pages
     */
    totalPages: (state): number => {
      return Math.ceil(state.totalItems / state.pageSize);
    },

    /**
     * Returns data points grouped by type
     */
    dataPointsByType: (state) => (type: DataPointType): DataPoint[] => {
      return state.dataPoints.filter(dp => dp.type === type);
    },

    /**
     * Returns validation status
     */
    hasValidationErrors: (state): boolean => {
      return state.validationErrors.some(error => error.severity === 'error');
    }
  },

  actions: {
    /**
     * Securely submits blood work data with file upload
     */
    async submitBloodWork(data: BloodWorkData, file: File): Promise<void> {
      try {
        this.loading = true;
        this.error = null;
        this.encryptionStatus = 'pending';
        this.uploadProgress = 0;

        // Validate blood work data
        const validationErrors = await validateBloodWorkData(data);
        if (validationErrors.length > 0) {
          this.validationErrors = validationErrors;
          throw new Error('Blood work data validation failed');
        }

        // Upload file and data
        const response = await uploadBloodWork(file, data, {
          onProgress: (progress) => {
            this.uploadProgress = progress;
          }
        });

        if (isAPIError(response)) {
          throw new Error(response.message);
        }

        // Update store state
        this.dataPoints.push(response.data);
        this.totalItems++;
        this.encryptionStatus = 'encrypted';
        this.securityContext.lastValidated = new Date();
        this.securityContext.isEncrypted = true;

      } catch (error) {
        this.error = error as Error;
        this.encryptionStatus = 'failed';
        throw error;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Securely submits weekly check-in data
     */
    async submitCheckIn(data: CheckInData): Promise<void> {
      try {
        this.loading = true;
        this.error = null;

        const dataPoint: DataPoint = {
          id: crypto.randomUUID() as UUID,
          type: DataPointType.CHECK_IN,
          data,
          status: DataPointStatus.PENDING,
          recordedAt: new Date(),
          encryptedFields: ['sideEffects', 'additionalNotes'],
          validationErrors: []
        };

        const response = await submitDataPoint(dataPoint);

        if (isAPIError(response)) {
          throw new Error(response.message);
        }

        // Update store state
        this.dataPoints.push(response.data);
        this.totalItems++;
        this.securityContext.lastValidated = new Date();

      } catch (error) {
        this.error = error as Error;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Fetches paginated data points with filtering
     */
    async fetchDataPoints(filters?: Record<string, any>): Promise<void> {
      try {
        this.loading = true;
        this.error = null;

        const params = {
          page: this.currentPage,
          pageSize: this.pageSize,
          ...filters
        };

        const response = await axios.get<APIResponse<DataPoint[]>>(
          ENDPOINTS.DATA.LIST,
          { params }
        );

        if (isAPIError(response)) {
          throw new Error(response.message);
        }

        // Update store state
        this.dataPoints = response.data.data;
        this.totalItems = response.data.total;
        this.securityContext.lastValidated = new Date();

      } catch (error) {
        this.error = error as Error;
        throw error;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Updates pagination settings
     */
    setPagination(page: number, pageSize: number): void {
      this.currentPage = page;
      this.pageSize = pageSize;
    },

    /**
     * Clears all validation errors
     */
    clearValidationErrors(): void {
      this.validationErrors = [];
    },

    /**
     * Resets store state
     */
    resetState(): void {
      this.dataPoints = [];
      this.currentPage = 1;
      this.totalItems = 0;
      this.loading = false;
      this.error = null;
      this.encryptionStatus = 'pending';
      this.validationErrors = [];
      this.uploadProgress = 0;
      this.securityContext = {
        isEncrypted: false,
        lastValidated: null,
        securityLevel: 'restricted'
      };
    }
  }
});