// @version vue ^3.3.0
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { UUID } from 'crypto';

// Internal imports
import { 
  DataPoint, 
  BloodWorkData, 
  CheckInData, 
  DataPointType,
  DataPointStatus,
  VALIDATION_SEVERITY,
  ValidationSchema,
  DataValidationError
} from '../types/data';
import useDataStore from '../stores/data';

// Constants for form state management
const BLOOD_WORK_FORM_INITIAL_STATE: Partial<BloodWorkData> = {
  markers: {},
  testDate: null,
  labName: '',
  fileHash: '',
  reportFileUrl: '',
  encryptionMetadata: {
    algorithm: 'AES-256-GCM',
    keyId: '',
    encryptedAt: new Date(),
    version: '1.0'
  },
  validationSchema: {
    rules: {
      markers: 'required|object',
      testDate: 'required|date',
      labName: 'required|string'
    },
    required: ['markers', 'testDate', 'labName']
  }
};

const CHECK_IN_FORM_INITIAL_STATE: Partial<CheckInData> = {
  energyLevel: 3,
  sleepQuality: 3,
  sideEffects: [],
  additionalNotes: {},
  mood: 3,
  compliance: true,
  validationSchema: {
    rules: {
      energyLevel: 'required|integer|between:1,5',
      sleepQuality: 'required|integer|between:1,5',
      sideEffects: 'array'
    },
    required: ['energyLevel', 'sleepQuality']
  }
};

/**
 * Composable for managing data collection functionality
 * @param protocolId - UUID of the protocol
 * @returns Object containing data collection state and methods
 */
export default function useDataCollection(protocolId: UUID) {
  // Initialize data store
  const dataStore = useDataStore();

  // Reactive state
  const bloodWorkForm = ref({ ...BLOOD_WORK_FORM_INITIAL_STATE });
  const checkInForm = ref({ ...CHECK_IN_FORM_INITIAL_STATE });
  const isSubmitting = ref(false);
  const uploadProgress = ref(0);
  const validationErrors = ref<DataValidationError[]>([]);
  const selectedFile = ref<File | null>(null);

  // Computed properties
  const hasValidationErrors = computed(() => {
    return validationErrors.value.some(
      error => error.severity === VALIDATION_SEVERITY.ERROR
    );
  });

  const isFormValid = computed(() => {
    return !hasValidationErrors.value && !isSubmitting.value;
  });

  const submissionProgress = computed(() => {
    return isSubmitting.value ? uploadProgress.value : 0;
  });

  /**
   * Handles blood work data submission with file upload
   * @param data - Blood work data
   * @returns Promise resolving when submission is complete
   */
  const submitBloodWork = async (data: BloodWorkData): Promise<void> => {
    try {
      if (!selectedFile.value) {
        throw new Error('Blood work report file is required');
      }

      isSubmitting.value = true;
      validationErrors.value = [];

      // Create data point with encryption metadata
      const dataPoint: DataPoint = {
        id: crypto.randomUUID() as UUID,
        protocolId,
        type: DataPointType.BLOOD_WORK,
        data,
        status: DataPointStatus.PENDING,
        recordedAt: new Date(),
        encryptedFields: ['markers', 'labName'],
        validationErrors: []
      };

      // Submit data with file upload
      await dataStore.submitBloodWork(data, selectedFile.value);

      // Reset form state on success
      bloodWorkForm.value = { ...BLOOD_WORK_FORM_INITIAL_STATE };
      selectedFile.value = null;
      uploadProgress.value = 0;

    } catch (error) {
      validationErrors.value.push({
        field: 'submission',
        message: error.message,
        code: 'SUBMISSION_ERROR',
        severity: VALIDATION_SEVERITY.ERROR,
        context: { error }
      });
      throw error;
    } finally {
      isSubmitting.value = false;
    }
  };

  /**
   * Handles weekly check-in data submission
   * @param data - Check-in data
   * @returns Promise resolving when submission is complete
   */
  const submitCheckIn = async (data: CheckInData): Promise<void> => {
    try {
      isSubmitting.value = true;
      validationErrors.value = [];

      // Create data point
      const dataPoint: DataPoint = {
        id: crypto.randomUUID() as UUID,
        protocolId,
        type: DataPointType.CHECK_IN,
        data,
        status: DataPointStatus.PENDING,
        recordedAt: new Date(),
        encryptedFields: ['sideEffects', 'additionalNotes'],
        validationErrors: []
      };

      // Submit data
      await dataStore.submitCheckIn(data);

      // Reset form state on success
      checkInForm.value = { ...CHECK_IN_FORM_INITIAL_STATE };

    } catch (error) {
      validationErrors.value.push({
        field: 'submission',
        message: error.message,
        code: 'SUBMISSION_ERROR',
        severity: VALIDATION_SEVERITY.ERROR,
        context: { error }
      });
      throw error;
    } finally {
      isSubmitting.value = false;
    }
  };

  /**
   * Handles file selection for blood work reports
   * @param file - Selected file
   */
  const handleFileSelect = (file: File | null): void => {
    selectedFile.value = file;
    uploadProgress.value = 0;
  };

  /**
   * Validates form data against schema
   * @param data - Form data to validate
   * @param schema - Validation schema
   * @returns Array of validation errors
   */
  const validateFormData = (
    data: Record<string, any>,
    schema: ValidationSchema
  ): DataValidationError[] => {
    const errors: DataValidationError[] = [];

    schema.required.forEach(field => {
      if (!data[field]) {
        errors.push({
          field,
          message: 'This field is required',
          code: 'REQUIRED_FIELD',
          severity: VALIDATION_SEVERITY.ERROR,
          context: { field }
        });
      }
    });

    return errors;
  };

  // Lifecycle hooks
  onMounted(() => {
    // Initialize forms with default state
    bloodWorkForm.value = { ...BLOOD_WORK_FORM_INITIAL_STATE };
    checkInForm.value = { ...CHECK_IN_FORM_INITIAL_STATE };
  });

  onUnmounted(() => {
    // Clean up any resources
    selectedFile.value = null;
    validationErrors.value = [];
  });

  return {
    // State
    bloodWorkForm,
    checkInForm,
    isSubmitting,
    uploadProgress,
    validationErrors,
    selectedFile,

    // Computed
    hasValidationErrors,
    isFormValid,
    submissionProgress,

    // Methods
    submitBloodWork,
    submitCheckIn,
    handleFileSelect,
    validateFormData
  };
}