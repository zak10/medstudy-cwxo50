import { z } from 'zod'; // v3.22.0
import * as t from 'io-ts'; // v2.2.20

/**
 * Branded type for protocol IDs to prevent mixing with other ID types
 */
export type ProtocolId = string & { readonly __brand: unique symbol };

/**
 * Type for ISO 8601 date strings with validation
 */
export type ISODateString = string & { readonly __brand: 'ISODateString' };

/**
 * Enum representing possible protocol statuses
 */
export enum ProtocolStatus {
  DRAFT = 'DRAFT',
  ACTIVE = 'ACTIVE',
  PAUSED = 'PAUSED',
  COMPLETED = 'COMPLETED',
  CANCELLED = 'CANCELLED'
}

/**
 * Interface defining data collection requirements for a protocol
 */
export interface DataRequirement {
  readonly id: string;
  readonly type: 'BLOOD_WORK' | 'BIOMETRIC' | 'CHECK_IN' | 'EXPERIENCE';
  readonly frequency: 'ONCE' | 'DAILY' | 'WEEKLY' | 'MONTHLY';
  readonly required: boolean;
  readonly validationRules?: Record<string, unknown>;
  readonly metadata?: Record<string, unknown>;
}

/**
 * Interface defining safety parameters for protocol monitoring
 */
export interface SafetyParameter {
  readonly id: string;
  readonly metric: string;
  readonly minValue?: number;
  readonly maxValue?: number;
  readonly unit: string;
  readonly criticalThreshold?: number;
  readonly warningThreshold?: number;
  readonly metadata?: Record<string, unknown>;
}

/**
 * Main protocol interface definition with strict type safety
 */
export interface Protocol {
  readonly id: ProtocolId;
  readonly title: string;
  readonly description: string;
  readonly requirements: readonly DataRequirement[];
  readonly safetyParams: readonly SafetyParameter[];
  readonly duration: number; // in weeks
  readonly status: ProtocolStatus;
  readonly participantCount: number;
  readonly createdAt: ISODateString;
  readonly updatedAt: ISODateString;
  readonly metadata: Record<string, unknown>;
}

/**
 * Zod schema for runtime validation of Protocol data
 */
export const ProtocolSchema = z.object({
  id: z.string(),
  title: z.string().min(1).max(200),
  description: z.string().min(1),
  requirements: z.array(z.object({
    id: z.string(),
    type: z.enum(['BLOOD_WORK', 'BIOMETRIC', 'CHECK_IN', 'EXPERIENCE']),
    frequency: z.enum(['ONCE', 'DAILY', 'WEEKLY', 'MONTHLY']),
    required: z.boolean(),
    validationRules: z.record(z.unknown()).optional(),
    metadata: z.record(z.unknown()).optional()
  })),
  safetyParams: z.array(z.object({
    id: z.string(),
    metric: z.string(),
    minValue: z.number().optional(),
    maxValue: z.number().optional(),
    unit: z.string(),
    criticalThreshold: z.number().optional(),
    warningThreshold: z.number().optional(),
    metadata: z.record(z.unknown()).optional()
  })),
  duration: z.number().positive(),
  status: z.nativeEnum(ProtocolStatus),
  participantCount: z.number().nonnegative(),
  createdAt: z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$/),
  updatedAt: z.string().regex(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$/),
  metadata: z.record(z.unknown())
});

/**
 * io-ts codec for Protocol validation
 */
export const ProtocolCodec = t.type({
  id: t.string,
  title: t.string,
  description: t.string,
  requirements: t.readonlyArray(t.type({
    id: t.string,
    type: t.keyof({
      BLOOD_WORK: null,
      BIOMETRIC: null,
      CHECK_IN: null,
      EXPERIENCE: null
    }),
    frequency: t.keyof({
      ONCE: null,
      DAILY: null,
      WEEKLY: null,
      MONTHLY: null
    }),
    required: t.boolean,
    validationRules: t.union([t.record(t.unknown), t.undefined]),
    metadata: t.union([t.record(t.unknown), t.undefined])
  })),
  safetyParams: t.readonlyArray(t.type({
    id: t.string,
    metric: t.string,
    minValue: t.union([t.number, t.undefined]),
    maxValue: t.union([t.number, t.undefined]),
    unit: t.string,
    criticalThreshold: t.union([t.number, t.undefined]),
    warningThreshold: t.union([t.number, t.undefined]),
    metadata: t.union([t.record(t.unknown), t.undefined])
  })),
  duration: t.number,
  status: t.keyof({
    DRAFT: null,
    ACTIVE: null,
    PAUSED: null,
    COMPLETED: null,
    CANCELLED: null
  }),
  participantCount: t.number,
  createdAt: t.string,
  updatedAt: t.string,
  metadata: t.record(t.unknown)
});

/**
 * Type guard function to validate Protocol objects at runtime
 * @param value - Value to check
 * @returns True if value is a valid Protocol object
 */
export function isProtocol(value: unknown): value is Protocol {
  return ProtocolSchema.safeParse(value).success;
}