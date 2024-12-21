<template>
  <div 
    class="file-upload"
    :class="{ 'dragging': isDragging }"
    @drop.prevent="handleDrop"
    @dragover.prevent="() => isDragging = true"
    @dragenter.prevent="() => isDragging = true"
    @dragleave.prevent="() => isDragging = false"
    role="region"
    aria-label="File upload area"
  >
    <!-- Hidden file input for accessibility -->
    <input
      type="file"
      ref="fileInput"
      class="visually-hidden"
      :accept="allowedTypes.join(',')"
      @change="handleFileSelect"
      :aria-label="'Upload blood work report for protocol ' + protocolId"
    >

    <!-- Drag and drop zone -->
    <div 
      class="drop-zone"
      :aria-busy="isUploading"
      role="button"
      tabindex="0"
      @keydown.space.prevent="triggerFileInput"
      @keydown.enter.prevent="triggerFileInput"
    >
      <div v-if="!selectedFile" class="drop-content">
        <span class="drop-icon">📄</span>
        <p class="drop-text">
          Drag and drop your blood work report here or
          <BaseButton 
            variant="text"
            @click="triggerFileInput"
            :disabled="isUploading"
          >
            browse files
          </BaseButton>
        </p>
        <p class="file-requirements">
          Accepted formats: {{ allowedTypes.join(', ') }} (Max {{ formatFileSize(maxSize) }})
        </p>
      </div>

      <!-- Selected file display -->
      <div v-else class="selected-file">
        <span class="file-name">{{ selectedFile.name }}</span>
        <span class="file-size">({{ formatFileSize(selectedFile.size) }})</span>
        <BaseButton
          v-if="!isUploading"
          variant="text"
          @click="clearFile"
          aria-label="Remove selected file"
        >
          Remove
        </BaseButton>
      </div>
    </div>

    <!-- Upload progress and controls -->
    <div v-if="selectedFile" class="upload-controls">
      <div 
        v-if="isUploading" 
        class="progress-container"
        role="progressbar"
        :aria-valuenow="uploadProgress"
        aria-valuemin="0"
        aria-valuemax="100"
      >
        <div 
          class="progress-bar"
          :style="{ width: `${uploadProgress}%` }"
        ></div>
        <span class="progress-text">{{ uploadProgress }}% uploaded</span>
      </div>

      <div class="button-group">
        <BaseButton
          v-if="!isUploading"
          variant="primary"
          :disabled="!selectedFile"
          @click="uploadFile"
        >
          Upload Report
        </BaseButton>
        <BaseButton
          v-else
          variant="secondary"
          @click="cancelUpload"
        >
          Cancel Upload
        </BaseButton>
      </div>
    </div>

    <!-- Error display -->
    <div 
      v-if="errorState.message"
      class="error-message"
      role="alert"
    >
      {{ errorState.message }}
    </div>

    <!-- Screen reader announcements -->
    <div 
      aria-live="polite" 
      class="visually-hidden"
    >
      {{ screenReaderMessage }}
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue'; // v3.3.0
import CryptoJS from 'crypto-js'; // v4.1.1
import BaseButton from '@/components/common/BaseButton.vue';
import { uploadBloodWork } from '@/api/data';
import type { BloodWorkData } from '@/types/data';

export default defineComponent({
  name: 'FileUpload',

  components: {
    BaseButton
  },

  props: {
    protocolId: {
      type: String,
      required: true
    },
    maxSize: {
      type: Number,
      default: 10 * 1024 * 1024 // 10MB
    },
    allowedTypes: {
      type: Array as () => string[],
      default: () => ['.pdf', '.jpg', '.png']
    },
    chunkSize: {
      type: Number,
      default: 1024 * 1024 // 1MB chunks
    }
  },

  emits: {
    fileUploaded: (data: BloodWorkData) => true,
    error: (message: string, code: string) => true,
    scanComplete: (isClean: boolean) => true
  },

  setup(props, { emit }) {
    const selectedFile = ref<File | null>(null);
    const uploadProgress = ref(0);
    const isDragging = ref(false);
    const isUploading = ref(false);
    const uploadController = ref<AbortController | null>(null);
    const fileInput = ref<HTMLInputElement | null>(null);
    const errorState = ref({ message: '', code: '' });
    const screenReaderMessage = ref('');

    // File validation
    const validateFile = async (file: File): Promise<boolean> => {
      errorState.value = { message: '', code: '' };

      // Size validation
      if (file.size > props.maxSize) {
        errorState.value = {
          message: `File size exceeds maximum allowed size of ${formatFileSize(props.maxSize)}`,
          code: 'SIZE_EXCEEDED'
        };
        return false;
      }

      // Type validation
      const fileExtension = `.${file.name.split('.').pop()?.toLowerCase()}`;
      if (!props.allowedTypes.includes(fileExtension)) {
        errorState.value = {
          message: `Invalid file type. Allowed types: ${props.allowedTypes.join(', ')}`,
          code: 'INVALID_TYPE'
        };
        return false;
      }

      // Generate file hash for integrity check
      const fileHash = await generateFileHash(file);
      
      return true;
    };

    // File hash generation
    const generateFileHash = async (file: File): Promise<string> => {
      return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => {
          const wordArray = CryptoJS.lib.WordArray.create(e.target?.result as ArrayBuffer);
          const hash = CryptoJS.SHA256(wordArray).toString();
          resolve(hash);
        };
        reader.readAsArrayBuffer(file);
      });
    };

    // Handle file selection
    const handleFileSelect = async (event: Event) => {
      const input = event.target as HTMLInputElement;
      if (input.files?.length) {
        const file = input.files[0];
        if (await validateFile(file)) {
          selectedFile.value = file;
          updateScreenReaderMessage(`File ${file.name} selected`);
        }
      }
    };

    // Handle file drop
    const handleDrop = async (event: DragEvent) => {
      isDragging.value = false;
      const file = event.dataTransfer?.files[0];
      if (file && await validateFile(file)) {
        selectedFile.value = file;
        updateScreenReaderMessage(`File ${file.name} dropped`);
      }
    };

    // File upload
    const uploadFile = async () => {
      if (!selectedFile.value) return;

      try {
        isUploading.value = true;
        uploadController.value = new AbortController();
        updateScreenReaderMessage('Upload started');

        const fileHash = await generateFileHash(selectedFile.value);
        
        const result = await uploadBloodWork(
          selectedFile.value,
          {
            protocolId: props.protocolId,
            fileHash,
            uploadedAt: new Date().toISOString()
          },
          {
            onProgress: (progress: number) => {
              uploadProgress.value = Math.round(progress);
              updateScreenReaderMessage(`Upload progress ${Math.round(progress)}%`);
            },
            signal: uploadController.value.signal
          }
        );

        emit('fileUploaded', result.data);
        updateScreenReaderMessage('Upload completed successfully');
        clearFile();
      } catch (error: any) {
        if (error.name === 'AbortError') {
          updateScreenReaderMessage('Upload cancelled');
          return;
        }
        
        errorState.value = {
          message: error.message || 'Upload failed',
          code: error.code || 'UPLOAD_ERROR'
        };
        emit('error', errorState.value.message, errorState.value.code);
        updateScreenReaderMessage('Upload failed');
      } finally {
        isUploading.value = false;
        uploadProgress.value = 0;
        uploadController.value = null;
      }
    };

    // Utility functions
    const formatFileSize = (bytes: number): string => {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
    };

    const triggerFileInput = () => {
      fileInput.value?.click();
    };

    const clearFile = () => {
      selectedFile.value = null;
      if (fileInput.value) {
        fileInput.value.value = '';
      }
      updateScreenReaderMessage('File selection cleared');
    };

    const cancelUpload = () => {
      uploadController.value?.abort();
      isUploading.value = false;
      uploadProgress.value = 0;
    };

    const updateScreenReaderMessage = (message: string) => {
      screenReaderMessage.value = message;
    };

    return {
      selectedFile,
      uploadProgress,
      isDragging,
      isUploading,
      errorState,
      fileInput,
      screenReaderMessage,
      handleFileSelect,
      handleDrop,
      uploadFile,
      clearFile,
      cancelUpload,
      triggerFileInput,
      formatFileSize
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.file-upload {
  border: 2px dashed map-get(vars.$colors, 'gray', 300);
  border-radius: 8px;
  padding: vars.spacing(4);
  transition: all 0.2s ease;

  &.dragging {
    border-color: map-get(vars.$colors, 'primary');
    background-color: rgba(map-get(vars.$colors, 'primary'), 0.05);
  }
}

.drop-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  cursor: pointer;
  padding: vars.spacing(4);
  text-align: center;

  &:focus {
    outline: 2px solid map-get(vars.$colors, 'primary');
    outline-offset: 2px;
  }
}

.drop-content {
  .drop-icon {
    font-size: 2rem;
    margin-bottom: vars.spacing(2);
  }

  .drop-text {
    margin: vars.spacing(2) 0;
    color: map-get(vars.$colors, 'gray', 700);
  }

  .file-requirements {
    font-size: 0.875rem;
    color: map-get(vars.$colors, 'gray', 500);
  }
}

.selected-file {
  display: flex;
  align-items: center;
  gap: vars.spacing(2);
  padding: vars.spacing(2);
  background-color: map-get(vars.$colors, 'gray', 100);
  border-radius: 4px;

  .file-name {
    font-weight: map-get(vars.$font-weights, medium);
  }

  .file-size {
    color: map-get(vars.$colors, 'gray', 500);
  }
}

.upload-controls {
  margin-top: vars.spacing(4);
}

.progress-container {
  margin-bottom: vars.spacing(3);
  background-color: map-get(vars.$colors, 'gray', 200);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar {
  height: 4px;
  background-color: map-get(vars.$colors, 'primary');
  transition: width 0.2s ease;
}

.progress-text {
  font-size: 0.875rem;
  color: map-get(vars.$colors, 'gray', 600);
  margin-top: vars.spacing(1);
}

.error-message {
  margin-top: vars.spacing(3);
  padding: vars.spacing(2);
  color: map-get(vars.$colors, 'error');
  background-color: rgba(map-get(vars.$colors, 'error'), 0.1);
  border-radius: 4px;
}

.button-group {
  display: flex;
  gap: vars.spacing(2);
  justify-content: center;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

// Reduced motion support
@media (prefers-reduced-motion: reduce) {
  .file-upload,
  .progress-bar {
    transition: none;
  }
}
</style>