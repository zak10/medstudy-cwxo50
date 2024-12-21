// @version crypto ^1.0.0
import { UUID } from 'crypto';

/**
 * Enum representing all supported data point types in the system
 * Used for type-safe data point classification
 */
export enum DataPointType {
    BLOOD_WORK = 'blood_work',
    CHECK_IN = 'check_in',
    BIOMETRIC = 'biometric'
}

/**
 * Constants for data point status tracking
 */
export const DATA_POINT_STATUS = {
    PENDING: 'pending',
    VALIDATED: 'validated',
    REJECTED: 'rejected',
    ENCRYPTED: 'encrypted'
} as const;

export type DataPointStatus = typeof DATA_POINT_STATUS[keyof typeof DATA_POINT_STATUS];

/**
 * Constants for rating scale validation
 */
export const RATING_SCALE = {
    MIN: 1,
    MAX: 5,
    STEP: 1
} as const;

/**
 * Constants for validation severity levels
 */
export const VALIDATION_SEVERITY = {
    ERROR: 'error',
    WARNING: 'warning',
    INFO: 'info'
} as const;

export type ValidationSeverity = typeof VALIDATION_SEVERITY[keyof typeof VALIDATION_SEVERITY];

/**
 * Interface for encryption metadata attached to sensitive data
 */
export interface EncryptionMetadata {
    algorithm: string;
    keyId: string;
    encryptedAt: Date;
    version: string;
}

/**
 * Interface for data validation schema
 */
export interface ValidationSchema {
    rules: Record<string, any>;
    required: string[];
    customValidators?: Record<string, (value: any) => boolean>;
}

/**
 * Enhanced interface for data validation errors with severity levels
 */
export interface DataValidationError {
    field: string;
    message: string;
    code: string;
    severity: ValidationSeverity;
    context: Record<string, any>;
}

/**
 * Core interface for all data points with enhanced security and validation
 */
export interface DataPoint {
    id: UUID;
    protocolId: UUID;
    participantId: UUID;
    type: DataPointType;
    data: Record<string, any>;
    recordedAt: Date;
    status: DataPointStatus;
    encryptedFields: string[];
    validationErrors: DataValidationError[];
}

/**
 * Interface for blood work data with encryption and validation metadata
 */
export interface BloodWorkData {
    markers: Record<string, number>;
    testDate: Date;
    labName: string;
    fileHash: string;
    reportFileUrl: string;
    encryptionMetadata: EncryptionMetadata;
    validationSchema: ValidationSchema;
}

/**
 * Interface for weekly check-in data with enhanced validation
 */
export interface CheckInData {
    energyLevel: number;
    sleepQuality: number;
    sideEffects: string[];
    additionalNotes: Record<string, any>;
    mood: number;
    compliance: boolean;
    validationSchema: ValidationSchema;
}

/**
 * Type guard to check if a data point is blood work
 */
export function isBloodWorkData(data: any): data is BloodWorkData {
    return (
        data &&
        typeof data.markers === 'object' &&
        data.testDate instanceof Date &&
        typeof data.labName === 'string'
    );
}

/**
 * Type guard to check if a data point is a check-in
 */
export function isCheckInData(data: any): data is CheckInData {
    return (
        data &&
        typeof data.energyLevel === 'number' &&
        typeof data.sleepQuality === 'number' &&
        Array.isArray(data.sideEffects)
    );
}

/**
 * Utility type for creating type-safe data point builders
 */
export type DataPointBuilder<T> = {
    build(): DataPoint & { data: T };
    withData(data: T): DataPointBuilder<T>;
    withValidation(schema: ValidationSchema): DataPointBuilder<T>;
    withEncryption(fields: string[]): DataPointBuilder<T>;
};