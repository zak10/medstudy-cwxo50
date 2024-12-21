<template>
  <form 
    class="bloodwork-form"
    @submit.prevent="handleSubmit"
    :data-testid="'bloodwork-form'"
  >
    <!-- Test Date Section -->
    <div class="form-section">
      <BaseInput
        v-model="formData.testDate"
        type="date"
        label="Test Date"
        :error="getFieldError('testDate')"
        required
        :max="maxTestDate"
        :min="minTestDate"
      />
    </div>

    <!-- Lab Information Section -->
    <div class="form-section">
      <BaseInput
        v-model="formData.labName"
        type="text"
        label="Laboratory Name"
        :error="getFieldError('labName')"
        required
        :list="'approved-labs'"
        :sensitive="true"
      />
      <datalist id="approved-labs">
        <option v-for="lab in approvedLabs" :key="lab" :value="lab" />
      </datalist>
    </div>

    <!-- Blood Markers Section -->
    <div class="form-section marker-inputs">
      <h3>Blood Markers</h3>
      <div v-for="(range, marker) in markerRanges" :key="marker" class="marker-field">
        <BaseInput
          v-model.number="formData.markers[marker]"
          type="number"
          :label="formatMarkerLabel(marker, range)"
          :error="getFieldError(`markers.${marker}`)"
          :min="range.min"
          :max="range.max"
          :step="0.1"
          :sensitive="true"
          required
        />
      </div>
    </div>

    <!-- File Upload Section -->
    <div class="form-section upload-zone" :class="{ 'has-error': getFieldError('file') }">
      <label class="upload-label">
        Blood Work Report (PDF/Image)
        <span class="required-indicator">*</span>
      </label>
      <div 
        class="upload-area"
        @drop.prevent="handleFileDrop"
        @dragover.prevent
        @dragenter.prevent
      >
        <input
          type="file"
          ref="fileInput"
          @change="handleFileSelect"
          accept=".pdf,.jpg,.jpeg,.png"
          class="file-input"
        />
        <div v-if="!selectedFile" class="upload-placeholder">
          <span>Drop file here or click to upload</span>
          <small>Supported formats: PDF, JPG, PNG (max 10MB)</small>
        </div>
        <div v-else class="file-preview">
          <span>{{ selectedFile.name }}</span>
          <button type="button" @click="clearFile" class="clear-file">×</button>
        </div>
      </div>
      <div v-if="uploadProgress > 0" class="upload-progress">
        <div class="progress-bar" :style="{ width: `${uploadProgress}%` }" />
        <span>{{ uploadProgress }}%</span>
      </div>
      <span v-if="getFieldError('file')" class="error-message">
        {{ getFieldError('file') }}
      </span>
    </div>

    <!-- Validation Errors -->
    <div v-if="validationErrors.length" class="validation-errors">
      <div 
        v-for="error in validationErrors" 
        :key="error.field"
        class="error-item"
        :class="error.severity"
      >
        {{ error.message }}
      </div>
    </div>

    <!-- Form Actions -->
    <div class="form-actions">
      <button
        type="submit"
        class="submit-button"
        :disabled="!isValid || isSubmitting"
      >
        <span v-if="!isSubmitting">Submit Blood Work</span>
        <span v-else>Submitting...</span>
      </button>
    </div>
  </form>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted } from 'vue'; // v3.3.0
import BaseInput from '@/components/common/BaseInput.vue';
import { BloodWorkData } from '@/types/data';
import useDataCollection from '@/composables/useDataCollection';
import { MARKER_RANGES, APPROVED_LABS } from '@/utils/validation';
import { theme } from '@/config/theme';

export default defineComponent({
  name: 'BloodworkForm',

  components: {
    BaseInput
  },

  props: {
    protocolId: {
      type: String,
      required: true
    }
  },

  emits: ['submitted'],

  setup(props, { emit }) {
    // Initialize data collection composable
    const { 
      submitBloodWork, 
      validationErrors,
      isSubmitting,
      uploadProgress,
      handleFileSelect: handleFileUpload
    } = useDataCollection(props.protocolId);

    // Form state
    const formData = ref<Partial<BloodWorkData>>({
      markers: {},
      testDate: '',
      labName: '',
      fileHash: '',
      reportFileUrl: '',
      encryptionMetadata: {
        algorithm: 'AES-256-GCM',
        keyId: '',
        encryptedAt: new Date(),
        version: '1.0'
      }
    });

    const selectedFile = ref<File | null>(null);
    const fileInput = ref<HTMLInputElement | null>(null);

    // Computed properties
    const isValid = computed(() => {
      return (
        formData.value.testDate &&
        formData.value.labName &&
        Object.keys(formData.value.markers || {}).length > 0 &&
        selectedFile.value &&
        validationErrors.value.length === 0
      );
    });

    const maxTestDate = computed(() => {
      const today = new Date();
      return today.toISOString().split('T')[0];
    });

    const minTestDate = computed(() => {
      const date = new Date();
      date.setDate(date.getDate() - 30);
      return date.toISOString().split('T')[0];
    });

    // Methods
    const formatMarkerLabel = (marker: string, range: { min: number; max: number; unit: string }) => {
      return `${marker.replace('_', ' ').toUpperCase()} (${range.min}-${range.max} ${range.unit})`;
    };

    const getFieldError = (field: string) => {
      return validationErrors.value.find(error => error.field === field)?.message;
    };

    const handleFileDrop = (event: DragEvent) => {
      const files = event.dataTransfer?.files;
      if (files?.length) {
        handleFileSelect(files[0]);
      }
    };

    const handleFileSelect = async (fileOrEvent: File | Event) => {
      const file = fileOrEvent instanceof File ? fileOrEvent : 
        (fileOrEvent.target as HTMLInputElement).files?.[0];
      
      if (file) {
        try {
          await handleFileUpload(file);
          selectedFile.value = file;
        } catch (error) {
          console.error('File upload error:', error);
        }
      }
    };

    const clearFile = () => {
      selectedFile.value = null;
      if (fileInput.value) {
        fileInput.value.value = '';
      }
    };

    const handleSubmit = async () => {
      try {
        if (!isValid.value) return;

        const data: BloodWorkData = {
          ...formData.value as BloodWorkData,
          testDate: new Date(formData.value.testDate as string)
        };

        await submitBloodWork(data);
        emit('submitted', data);
        
        // Reset form
        formData.value = {
          markers: {},
          testDate: '',
          labName: '',
          fileHash: '',
          reportFileUrl: '',
          encryptionMetadata: {
            algorithm: 'AES-256-GCM',
            keyId: '',
            encryptedAt: new Date(),
            version: '1.0'
          }
        };
        clearFile();
      } catch (error) {
        console.error('Submission error:', error);
      }
    };

    return {
      formData,
      selectedFile,
      fileInput,
      isValid,
      isSubmitting,
      uploadProgress,
      validationErrors,
      maxTestDate,
      minTestDate,
      markerRanges: MARKER_RANGES,
      approvedLabs: APPROVED_LABS,
      handleSubmit,
      handleFileSelect,
      handleFileDrop,
      clearFile,
      getFieldError,
      formatMarkerLabel
    };
  }
});
</script>

<style lang="scss" scoped>
// Import theme variables
$colors: v-bind('theme.colors');
$typography: v-bind('theme.typography');
$spacing: v-bind('theme.spacing');

.bloodwork-form {
  display: flex;
  flex-direction: column;
  gap: $spacing.scale.md;
  max-width: 800px;
  margin: 0 auto;
  padding: $spacing.scale.md;

  .form-section {
    display: flex;
    flex-direction: column;
    gap: $spacing.scale.sm;

    h3 {
      font-family: $typography.fontFamily.primary;
      font-weight: $typography.fontWeights.semibold;
      color: $colors.text.primary;
      margin-bottom: $spacing.scale.xs;
    }
  }

  .marker-inputs {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: $spacing.scale.md;
  }

  .upload-zone {
    border: 2px dashed $colors.primary.base;
    border-radius: 8px;
    padding: $spacing.scale.md;

    &.has-error {
      border-color: $colors.semantic.error;
    }

    .upload-label {
      font-weight: $typography.fontWeights.medium;
      margin-bottom: $spacing.scale.xs;
    }

    .upload-area {
      position: relative;
      min-height: 120px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: $colors.background.secondary;
      border-radius: 4px;
      cursor: pointer;

      &:hover {
        background: $colors.background.tertiary;
      }
    }

    .file-input {
      position: absolute;
      width: 100%;
      height: 100%;
      opacity: 0;
      cursor: pointer;
    }

    .upload-progress {
      margin-top: $spacing.scale.xs;
      background: $colors.background.tertiary;
      border-radius: 4px;
      overflow: hidden;

      .progress-bar {
        height: 4px;
        background: $colors.secondary.base;
        transition: width 0.3s ease;
      }
    }
  }

  .validation-errors {
    padding: $spacing.scale.sm;
    border-radius: 4px;
    background: $colors.background.secondary;

    .error-item {
      padding: $spacing.scale.xs;
      margin-bottom: $spacing.scale.xs;
      border-radius: 4px;

      &.error {
        background: rgba($colors.semantic.error, 0.1);
        color: $colors.semantic.error;
      }

      &.warning {
        background: rgba($colors.semantic.warning, 0.1);
        color: $colors.semantic.warning;
      }
    }
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    margin-top: $spacing.scale.md;

    .submit-button {
      padding: $spacing.scale.sm $spacing.scale.md;
      background: $colors.primary.base;
      color: $colors.primary.contrast;
      border: none;
      border-radius: 4px;
      font-weight: $typography.fontWeights.medium;
      cursor: pointer;
      transition: background 0.2s ease;

      &:hover:not(:disabled) {
        background: $colors.primary.hover;
      }

      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
    }
  }
}
</style>