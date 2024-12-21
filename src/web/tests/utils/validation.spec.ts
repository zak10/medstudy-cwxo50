import { describe, it, expect, beforeEach } from 'vitest';
import { 
  validateLoginCredentials, 
  validateRegistrationData, 
  validateBloodWorkData,
  PASSWORD_MIN_LENGTH,
  PASSWORD_PATTERN,
  VALIDATION_ERRORS,
  APPROVED_LABS,
  MARKER_RANGES
} from '../../src/utils/validation';
import { LoginCredentials, RegisterCredentials, UserRole } from '../../src/types/auth';
import { BloodWorkData, VALIDATION_SEVERITY } from '../../src/types/data';

describe('validateLoginCredentials', () => {
  let validCredentials: LoginCredentials;

  beforeEach(() => {
    validCredentials = {
      email: 'test@example.com',
      password: 'SecurePass123!@#'
    };
  });

  it('should return empty array for valid credentials', () => {
    const errors = validateLoginCredentials(validCredentials);
    expect(errors).toHaveLength(0);
  });

  it('should validate email format', () => {
    const invalidEmails = [
      'test@.com',
      '@example.com',
      'test@example.',
      'test@exam ple.com',
      'test@example.c',
      'test.example.com',
      '<script>alert(1)</script>@example.com' // XSS attempt
    ];

    invalidEmails.forEach(email => {
      const errors = validateLoginCredentials({ ...validCredentials, email });
      expect(errors).toContainEqual(expect.objectContaining({
        field: 'email',
        code: 'INVALID_EMAIL_FORMAT',
        message: VALIDATION_ERRORS.INVALID_EMAIL,
        severity: VALIDATION_SEVERITY.ERROR
      }));
    });
  });

  it('should validate password complexity', () => {
    const invalidPasswords = [
      'short',                  // Too short
      'onlylowercase',         // Missing uppercase
      'ONLYUPPERCASE',         // Missing lowercase
      'NoSpecialChars123',     // Missing special chars
      'NoNumbers!!!',          // Missing numbers
      ' '.repeat(PASSWORD_MIN_LENGTH) // Spaces only
    ];

    invalidPasswords.forEach(password => {
      const errors = validateLoginCredentials({ ...validCredentials, password });
      expect(errors).toContainEqual(expect.objectContaining({
        field: 'password',
        code: 'INVALID_PASSWORD_FORMAT',
        message: VALIDATION_ERRORS.INVALID_PASSWORD,
        severity: VALIDATION_SEVERITY.ERROR
      }));
    });
  });

  it('should validate required fields', () => {
    const errors = validateLoginCredentials({ email: '', password: '' });
    expect(errors).toContainEqual(expect.objectContaining({
      field: 'password',
      code: 'MISSING_PASSWORD',
      message: VALIDATION_ERRORS.REQUIRED_FIELD
    }));
  });
});

describe('validateRegistrationData', () => {
  let validRegistration: RegisterCredentials;

  beforeEach(() => {
    validRegistration = {
      email: 'test@example.com',
      password: 'SecurePass123!@#',
      confirmPassword: 'SecurePass123!@#',
      firstName: 'John',
      lastName: 'Doe',
      role: UserRole.PARTICIPANT
    };
  });

  it('should return empty array for valid registration data', () => {
    const errors = validateRegistrationData(validRegistration);
    expect(errors).toHaveLength(0);
  });

  it('should validate password confirmation match', () => {
    const errors = validateRegistrationData({
      ...validRegistration,
      confirmPassword: 'DifferentPass123!@#'
    });
    expect(errors).toContainEqual(expect.objectContaining({
      field: 'confirmPassword',
      code: 'PASSWORD_MISMATCH',
      message: VALIDATION_ERRORS.PASSWORD_MISMATCH
    }));
  });

  it('should validate password strength', () => {
    const weakPasswords = [
      'password123!',          // Common password
      'qwerty123!@#',         // Keyboard pattern
      '11111111!@#Aa',        // Repeated characters
      'January2023!',         // Date-based
      'Password123!'          // Dictionary word
    ];

    weakPasswords.forEach(password => {
      const errors = validateRegistrationData({
        ...validRegistration,
        password,
        confirmPassword: password
      });
      expect(errors).toContainEqual(expect.objectContaining({
        field: 'password',
        code: 'WEAK_PASSWORD',
        message: VALIDATION_ERRORS.WEAK_PASSWORD,
        severity: VALIDATION_SEVERITY.ERROR
      }));
    });
  });

  it('should validate email domain', () => {
    const suspiciousEmails = [
      'test@temporary.com',
      'test@disposable.com',
      'test@mailinator.com',
      'test@tempmail.com'
    ];

    suspiciousEmails.forEach(email => {
      const errors = validateRegistrationData({ ...validRegistration, email });
      expect(errors.some(error => 
        error.field === 'email' && 
        error.severity === VALIDATION_SEVERITY.WARNING
      )).toBeTruthy();
    });
  });
});

describe('validateBloodWorkData', () => {
  let validBloodWork: BloodWorkData;
  const currentDate = new Date();
  const testDate = new Date(currentDate.setDate(currentDate.getDate() - 7));

  beforeEach(() => {
    validBloodWork = {
      markers: {
        vitamin_d: 45,
        b12: 500
      },
      testDate,
      labName: 'Quest Diagnostics',
      fileHash: 'abc123',
      reportFileUrl: 'https://example.com/report.pdf',
      encryptionMetadata: {
        algorithm: 'AES-256-GCM',
        keyId: 'key-1',
        encryptedAt: new Date(),
        version: '1.0'
      },
      validationSchema: {
        rules: {},
        required: ['vitamin_d', 'b12']
      }
    };
  });

  it('should return empty array for valid blood work data', () => {
    const errors = validateBloodWorkData(validBloodWork);
    expect(errors).toHaveLength(0);
  });

  it('should validate marker ranges', () => {
    const invalidMarkers = {
      vitamin_d: 100, // Above max
      b12: 100        // Below min
    };

    const errors = validateBloodWorkData({
      ...validBloodWork,
      markers: invalidMarkers
    });

    expect(errors).toContainEqual(expect.objectContaining({
      field: 'markers.vitamin_d',
      code: 'INVALID_MARKER_VALUE',
      severity: VALIDATION_SEVERITY.WARNING
    }));
    expect(errors).toContainEqual(expect.objectContaining({
      field: 'markers.b12',
      code: 'INVALID_MARKER_VALUE',
      severity: VALIDATION_SEVERITY.WARNING
    }));
  });

  it('should validate test date range', () => {
    const oldDate = new Date();
    oldDate.setDate(oldDate.getDate() - 40);

    const errors = validateBloodWorkData({
      ...validBloodWork,
      testDate: oldDate
    });

    expect(errors).toContainEqual(expect.objectContaining({
      field: 'testDate',
      code: 'INVALID_TEST_DATE',
      message: VALIDATION_ERRORS.INVALID_TEST_DATE,
      severity: VALIDATION_SEVERITY.ERROR
    }));
  });

  it('should validate approved laboratories', () => {
    const errors = validateBloodWorkData({
      ...validBloodWork,
      labName: 'Unauthorized Lab'
    });

    expect(errors).toContainEqual(expect.objectContaining({
      field: 'labName',
      code: 'UNAPPROVED_LAB',
      message: VALIDATION_ERRORS.INVALID_LAB,
      severity: VALIDATION_SEVERITY.ERROR,
      context: expect.objectContaining({
        approvedLabs: APPROVED_LABS
      })
    }));
  });

  it('should validate encryption metadata', () => {
    const invalidEncryption = {
      ...validBloodWork,
      encryptionMetadata: {
        algorithm: '',
        keyId: '',
        encryptedAt: new Date(),
        version: '1.0'
      }
    };

    const errors = validateBloodWorkData(invalidEncryption);
    expect(errors).toContainEqual(expect.objectContaining({
      field: 'encryption',
      code: 'MISSING_ENCRYPTION_METADATA',
      message: VALIDATION_ERRORS.INVALID_ENCRYPTION,
      severity: VALIDATION_SEVERITY.ERROR
    }));
  });

  it('should validate required markers', () => {
    const missingMarkers = {
      ...validBloodWork,
      markers: {
        vitamin_d: 45
        // b12 missing
      }
    };

    const errors = validateBloodWorkData(missingMarkers);
    expect(errors).toContainEqual(expect.objectContaining({
      field: 'markers.b12',
      code: 'MISSING_REQUIRED_MARKER',
      message: VALIDATION_ERRORS.REQUIRED_FIELD,
      severity: VALIDATION_SEVERITY.ERROR
    }));
  });

  it('should run custom validators when provided', () => {
    const customValidators = {
      vitamin_d: (value: number) => value % 2 === 0 // Example: must be even
    };

    const dataWithCustomValidation = {
      ...validBloodWork,
      validationSchema: {
        ...validBloodWork.validationSchema,
        customValidators
      }
    };

    const errors = validateBloodWorkData(dataWithCustomValidation);
    expect(errors).toContainEqual(expect.objectContaining({
      field: 'markers.vitamin_d',
      code: 'CUSTOM_VALIDATION_FAILED',
      severity: VALIDATION_SEVERITY.ERROR
    }));
  });
});