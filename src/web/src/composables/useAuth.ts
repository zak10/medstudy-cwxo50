/**
 * Authentication Composable
 * Provides secure authentication functionality and user management hooks
 * @package @medical-research-platform/web
 * @version 1.0.0
 */

import { ref, computed, onMounted } from 'vue'; // v3.3.0
import { useAuthStore } from '../stores/auth';
import { 
  AuthState, 
  LoginCredentials, 
  RegisterCredentials,
  PASSWORD_REGEX,
  PASSWORD_MIN_LENGTH
} from '../types/auth';

// Error message constants for consistent user feedback
const AUTH_ERROR_MESSAGES = {
  INVALID_CREDENTIALS: 'Invalid email or password',
  MFA_REQUIRED: 'Please enter your MFA code',
  REGISTRATION_FAILED: 'Registration failed. Please try again',
  NETWORK_ERROR: 'Network error. Please check your connection',
  PASSWORD_REQUIREMENTS: 'Password must meet security requirements',
  RATE_LIMIT_EXCEEDED: 'Too many attempts. Please try again later',
  SESSION_EXPIRED: 'Your session has expired. Please login again',
  INVALID_TOKEN: 'Invalid or expired token',
  MFA_TIMEOUT: 'MFA verification timeout. Please try again',
  SYSTEM_ERROR: 'System error. Please contact support'
} as const;

// MFA verification timeout (5 minutes)
const MFA_VERIFICATION_TIMEOUT = 300000;

/**
 * Authentication composable providing secure user authentication functionality
 * @returns Authentication state and methods
 */
export function useAuth() {
  const authStore = useAuthStore();
  
  // Loading states
  const isLoading = ref(false);
  const isMFAVerifying = ref(false);
  
  // Error state
  const error = ref<string | null>(null);
  
  // Computed properties with memoization
  const isAuthenticated = computed(() => authStore.authState === AuthState.AUTHENTICATED);
  const requiresMFA = computed(() => authStore.authState === AuthState.MFA_REQUIRED);
  const user = computed(() => authStore.user);

  /**
   * Validates email format
   * @param email Email to validate
   */
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  /**
   * Validates password strength
   * @param password Password to validate
   */
  const validatePassword = (password: string): boolean => {
    const passwordRegex = new RegExp(PASSWORD_REGEX);
    return password.length >= PASSWORD_MIN_LENGTH && passwordRegex.test(password);
  };

  /**
   * Handles user login with enhanced security
   * @param credentials Login credentials
   * @returns Promise resolving to login success status
   */
  const handleLogin = async (credentials: LoginCredentials): Promise<boolean> => {
    try {
      error.value = null;
      isLoading.value = true;

      // Validate email format
      if (!validateEmail(credentials.email)) {
        throw new Error('Invalid email format');
      }

      // Handle MFA verification
      if (requiresMFA.value && !credentials.mfaCode) {
        throw new Error(AUTH_ERROR_MESSAGES.MFA_REQUIRED);
      }

      if (requiresMFA.value) {
        isMFAVerifying.value = true;
        const mfaTimeout = setTimeout(() => {
          throw new Error(AUTH_ERROR_MESSAGES.MFA_TIMEOUT);
        }, MFA_VERIFICATION_TIMEOUT);

        const success = await authStore.verifyMFA(credentials.mfaCode!);
        clearTimeout(mfaTimeout);
        isMFAVerifying.value = false;
        return success;
      }

      return await authStore.login(credentials);

    } catch (err) {
      error.value = err instanceof Error ? err.message : AUTH_ERROR_MESSAGES.SYSTEM_ERROR;
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  /**
   * Handles new user registration with validation
   * @param userData Registration credentials
   * @returns Promise resolving to registration success status
   */
  const handleRegister = async (userData: RegisterCredentials): Promise<boolean> => {
    try {
      error.value = null;
      isLoading.value = true;

      // Validate email
      if (!validateEmail(userData.email)) {
        throw new Error('Invalid email format');
      }

      // Validate password strength
      if (!validatePassword(userData.password)) {
        throw new Error(AUTH_ERROR_MESSAGES.PASSWORD_REQUIREMENTS);
      }

      // Validate password confirmation
      if (userData.password !== userData.confirmPassword) {
        throw new Error('Passwords do not match');
      }

      // Attempt registration
      const success = await authStore.register(userData);
      
      if (success) {
        // Auto-login after successful registration
        await handleLogin({
          email: userData.email,
          password: userData.password
        });
      }

      return success;

    } catch (err) {
      error.value = err instanceof Error ? err.message : AUTH_ERROR_MESSAGES.REGISTRATION_FAILED;
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  /**
   * Handles user logout with cleanup
   */
  const handleLogout = async (): Promise<void> => {
    try {
      isLoading.value = true;
      await authStore.logout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      isLoading.value = false;
    }
  };

  // Initialize authentication state on mount
  onMounted(async () => {
    try {
      isLoading.value = true;
      await authStore.initializeAuth();
    } catch (err) {
      console.error('Auth initialization error:', err);
      error.value = AUTH_ERROR_MESSAGES.SYSTEM_ERROR;
    } finally {
      isLoading.value = false;
    }
  });

  return {
    // State
    isLoading,
    isMFAVerifying,
    error,

    // Computed
    isAuthenticated,
    requiresMFA,
    user,

    // Methods
    handleLogin,
    handleRegister,
    handleLogout,

    // Constants
    AUTH_ERROR_MESSAGES
  };
}