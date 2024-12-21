import { ProtocolStatus } from '../types/protocol';
import { UserRole } from '../types/auth';
import { DataPointType } from '../types/data';

/**
 * API Configuration Constants
 * @version 1.0.0
 */
export const API_CONFIG = {
  BASE_URL: process.env.VITE_API_URL || 'https://api.medical-research.platform',
  TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
  VERSIONS: {
    CURRENT: 'v1',
    SUPPORTED: ['v1'],
    DEPRECATED: []
  },
  ENDPOINTS: {
    AUTH: '/auth',
    PROTOCOLS: '/protocols',
    DATA_POINTS: '/data-points',
    USERS: '/users',
    ANALYSIS: '/analysis'
  },
  ERROR_CODES: {
    UNAUTHORIZED: 401,
    FORBIDDEN: 403,
    NOT_FOUND: 404,
    VALIDATION_ERROR: 422,
    SERVER_ERROR: 500
  }
} as const;

/**
 * Authentication Configuration Constants
 * Based on requirements from section 7.1
 */
export const AUTH_CONFIG = {
  TOKEN_EXPIRY: 3600, // 1 hour in seconds
  MFA_CODE_LENGTH: 6,
  PASSWORD_MIN_LENGTH: 8,
  OAUTH_PROVIDERS: {
    GOOGLE: {
      clientId: process.env.VITE_GOOGLE_CLIENT_ID,
      scopes: ['profile', 'email'],
      responseType: 'code'
    },
    APPLE: {
      clientId: process.env.VITE_APPLE_CLIENT_ID,
      scopes: ['name', 'email'],
      responseType: 'code'
    }
  },
  MFA_SETTINGS: {
    REQUIRED_ROLES: [UserRole.PROTOCOL_CREATOR, UserRole.PARTNER, UserRole.ADMINISTRATOR],
    ISSUER: 'Medical Research Platform',
    ALGORITHM: 'SHA1',
    DIGITS: 6,
    PERIOD: 30
  },
  SESSION_CONFIG: {
    STORAGE_KEY: 'mrs_session',
    REFRESH_THRESHOLD: 300, // 5 minutes before expiry
    IDLE_TIMEOUT: 1800 // 30 minutes
  }
} as const;

/**
 * UI Constants
 * Based on design system specifications from section 6.1
 */
export const UI_CONSTANTS = {
  BREAKPOINTS: {
    MOBILE: 320,
    TABLET: 768,
    DESKTOP: 1024,
    WIDE: 1440
  },
  COLORS: {
    PRIMARY: '#2C3E50',
    SECONDARY: '#3498DB',
    ACCENT: '#E74C3C',
    SUCCESS: '#2ECC71',
    WARNING: '#F1C40F',
    ERROR: '#E74C3C',
    BACKGROUND: '#FFFFFF',
    TEXT: '#2C3E50'
  },
  SPACING: {
    BASE: 4,
    SMALL: 8,
    MEDIUM: 16,
    LARGE: 24,
    XLARGE: 32,
    XXLARGE: 48
  },
  TYPOGRAPHY: {
    FONT_FAMILY: {
      PRIMARY: 'Inter, sans-serif',
      SECONDARY: 'Open Sans, sans-serif'
    },
    FONT_WEIGHTS: {
      REGULAR: 400,
      MEDIUM: 500,
      SEMIBOLD: 600,
      BOLD: 700
    },
    LINE_HEIGHT: {
      TIGHT: 1.2,
      NORMAL: 1.5,
      LOOSE: 1.8
    }
  },
  ANIMATION_TIMINGS: {
    FAST: 200,
    NORMAL: 300,
    SLOW: 500
  },
  Z_INDEX_LEVELS: {
    BASE: 0,
    DROPDOWN: 1000,
    STICKY: 1200,
    MODAL: 1300,
    TOOLTIP: 1400,
    NOTIFICATION: 1500
  },
  GRID_CONFIG: {
    COLUMNS: 12,
    GUTTER: {
      MOBILE: 16,
      TABLET: 24,
      DESKTOP: 32
    },
    MAX_WIDTH: 1200
  }
} as const;

/**
 * Data Collection Constants
 * Based on requirements from section 1.3
 */
export const DATA_CONSTANTS = {
  RATING_SCALE: {
    MIN: 1,
    MAX: 5,
    STEP: 1
  },
  FILE_SIZE_LIMIT: 10 * 1024 * 1024, // 10MB in bytes
  ALLOWED_FILE_TYPES: [
    'application/pdf',
    'image/jpeg',
    'image/png',
    'text/csv'
  ],
  VALIDATION_RULES: {
    BLOOD_WORK: {
      REQUIRED_FIELDS: ['markers', 'testDate', 'labName'],
      FILE_REQUIRED: true,
      EXPIRY_DAYS: 30
    },
    CHECK_IN: {
      REQUIRED_FIELDS: ['energyLevel', 'sleepQuality', 'compliance'],
      MAX_SIDE_EFFECTS: 10,
      NOTE_MAX_LENGTH: 1000
    }
  },
  ENCRYPTION_CONFIG: {
    ALGORITHM: 'AES-256-GCM',
    KEY_SIZE: 256,
    PROTECTED_FIELDS: ['markers', 'sideEffects', 'additionalNotes']
  },
  FILE_HANDLING: {
    CHUNK_SIZE: 1024 * 1024, // 1MB chunks for upload
    RETRY_ATTEMPTS: 3,
    CONCURRENT_UPLOADS: 3,
    MIME_TYPE_MAP: {
      'application/pdf': '.pdf',
      'image/jpeg': '.jpg',
      'image/png': '.png',
      'text/csv': '.csv'
    }
  }
} as const;

/**
 * Protocol Status Display Configuration
 */
export const PROTOCOL_STATUS_CONFIG = {
  [ProtocolStatus.DRAFT]: {
    color: UI_CONSTANTS.COLORS.SECONDARY,
    icon: 'draft',
    label: 'Draft'
  },
  [ProtocolStatus.ACTIVE]: {
    color: UI_CONSTANTS.COLORS.SUCCESS,
    icon: 'active',
    label: 'Active'
  },
  [ProtocolStatus.COMPLETED]: {
    color: UI_CONSTANTS.COLORS.PRIMARY,
    icon: 'completed',
    label: 'Completed'
  },
  [ProtocolStatus.ARCHIVED]: {
    color: UI_CONSTANTS.COLORS.TEXT,
    icon: 'archived',
    label: 'Archived'
  }
} as const;

/**
 * Data Point Type Configuration
 */
export const DATA_POINT_TYPE_CONFIG = {
  [DataPointType.BLOOD_WORK]: {
    icon: 'blood',
    label: 'Blood Work',
    description: 'Laboratory blood test results'
  },
  [DataPointType.CHECK_IN]: {
    icon: 'checkin',
    label: 'Weekly Check-in',
    description: 'Regular participant status update'
  }
} as const;

// Global constants
export const API_VERSION = 'v1';
export const DEFAULT_PAGINATION_LIMIT = 10;
export const MAX_FILE_SIZE_MB = 10;
export const TOKEN_STORAGE_KEY = 'mrs_auth_token';
export const REFRESH_TOKEN_KEY = 'mrs_refresh_token';