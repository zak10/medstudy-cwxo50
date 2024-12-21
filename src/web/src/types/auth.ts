/**
 * Authentication and User Management Type Definitions
 * @version 1.0.0
 * @package @medical-research-platform/web
 */

/**
 * Authentication states for user sessions
 */
export enum AuthState {
  AUTHENTICATED = 'AUTHENTICATED',
  UNAUTHENTICATED = 'UNAUTHENTICATED',
  MFA_REQUIRED = 'MFA_REQUIRED'
}

/**
 * User roles for Role-Based Access Control (RBAC)
 */
export enum UserRole {
  PARTICIPANT = 'PARTICIPANT',
  PROTOCOL_CREATOR = 'PROTOCOL_CREATOR',
  PARTNER = 'PARTNER',
  ADMINISTRATOR = 'ADMINISTRATOR'
}

/**
 * Password validation constants
 */
export const PASSWORD_MIN_LENGTH = 8;
export const PASSWORD_REGEX = '^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d@$!%*#?&]{8,}$';

/**
 * Login credentials interface for authentication
 */
export interface LoginCredentials {
  /** User's email address */
  email: string;
  /** User's password */
  password: string;
  /** Optional MFA verification code */
  mfaCode?: string;
}

/**
 * Registration credentials interface for new user signup
 */
export interface RegisterCredentials {
  /** User's email address */
  email: string;
  /** User's password - must meet PASSWORD_REGEX requirements */
  password: string;
  /** Password confirmation - must match password */
  confirmPassword: string;
  /** User's first name */
  firstName: string;
  /** User's last name */
  lastName: string;
  /** User's assigned role */
  role: UserRole;
}

/**
 * User profile data interface
 */
export interface UserProfile {
  /** Unique user identifier */
  id: string;
  /** User's email address */
  email: string;
  /** User's first name */
  firstName: string;
  /** User's last name */
  lastName: string;
  /** User's assigned role */
  role: UserRole;
  /** Whether MFA is enabled for the user */
  mfaEnabled: boolean;
  /** Optional URL to user's profile image */
  profileImage: string | null;
}

/**
 * Multi-Factor Authentication setup data interface
 */
export interface MFASetupData {
  /** MFA secret key */
  secret: string;
  /** QR code data URL for MFA setup */
  qrCode: string;
  /** Verification code for MFA activation */
  verificationCode: string;
}

/**
 * Authentication tokens interface
 */
export interface AuthTokens {
  /** JWT access token */
  accessToken: string;
  /** JWT refresh token */
  refreshToken: string;
  /** Token expiration time in seconds */
  expiresIn: number;
}