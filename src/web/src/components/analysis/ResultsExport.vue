<template>
  <div 
    class="results-export"
    role="region" 
    aria-live="polite"
  >
    <!-- Format Selection -->
    <div class="format-select">
      <label 
        for="export-format"
        class="format-label"
      >
        Export Format
      </label>
      <select
        id="export-format"
        v-model="selectedFormat"
        class="format-dropdown"
        :disabled="isExporting"
        aria-describedby="format-description"
      >
        <option 
          v-for="format in exportFormats"
          :key="format.id"
          :value="format.id"
        >
          {{ format.label }}
        </option>
      </select>
      <span id="format-description" class="sr-only">
        Select the format for exporting analysis results
      </span>
    </div>

    <!-- Export Button -->
    <BaseButton
      variant="primary"
      :loading="isExporting"
      :disabled="!selectedFormat"
      :aria-label="`Export results as ${selectedFormat.toUpperCase()}`"
      @click="handleExport"
      class="export-button"
    >
      {{ isExporting ? 'Exporting...' : 'Export Results' }}
    </BaseButton>

    <!-- Progress Indicator -->
    <div 
      v-if="isExporting && exportProgress > 0"
      class="progress-container"
      role="progressbar"
      :aria-valuenow="exportProgress"
      aria-valuemin="0"
      aria-valuemax="100"
    >
      <div 
        class="progress-bar"
        :style="{ width: `${exportProgress}%` }"
      ></div>
      <span class="progress-text">{{ exportProgress }}%</span>
    </div>

    <!-- Error Message -->
    <div 
      v-if="error"
      class="error-message"
      role="alert"
    >
      {{ error.message }}
      <BaseButton
        variant="text"
        @click="handleRetry"
        class="retry-button"
      >
        Retry Export
      </BaseButton>
    </div>

    <!-- Screen Reader Announcements -->
    <div aria-live="assertive" class="sr-only">
      <span v-if="isExporting">Export in progress</span>
      <span v-if="error">Export failed: {{ error.message }}</span>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'; // v3.3.0
import BaseButton from '@/components/common/BaseButton.vue';
import { exportAnalysis } from '@/api/analysis';

export default defineComponent({
  name: 'ResultsExport',

  components: {
    BaseButton
  },

  props: {
    protocolId: {
      type: String,
      required: true,
      validator: (value: string) => /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value)
    }
  },

  emits: ['exportComplete', 'exportError'],

  setup(props, { emit }) {
    const exportFormats = ref([
      { id: 'csv', label: 'CSV', mimeType: 'text/csv' },
      { id: 'json', label: 'JSON', mimeType: 'application/json' },
      { id: 'pdf', label: 'PDF', mimeType: 'application/pdf' }
    ]);

    const selectedFormat = ref('csv');
    const isExporting = ref(false);
    const exportProgress = ref(0);
    const error = ref<{ message: string; retryCount: number } | null>(null);
    const MAX_RETRY_ATTEMPTS = 3;

    const handleExport = async () => {
      if (!selectedFormat.value || isExporting.value) return;

      isExporting.value = true;
      exportProgress.value = 0;
      error.value = null;

      try {
        const format = exportFormats.value.find(f => f.id === selectedFormat.value);
        if (!format) throw new Error('Invalid export format');

        const blob = await exportAnalysis(props.protocolId, selectedFormat.value);
        await downloadFile(
          blob,
          `protocol-${props.protocolId}-analysis.${selectedFormat.value}`,
          format.mimeType
        );

        emit('exportComplete', { format: selectedFormat.value });
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Export failed';
        error.value = { message: errorMessage, retryCount: 0 };
        emit('exportError', error.value);
      } finally {
        isExporting.value = false;
        exportProgress.value = 0;
      }
    };

    const downloadFile = async (blob: Blob, filename: string, mimeType: string) => {
      // Validate blob and MIME type
      if (!(blob instanceof Blob)) {
        throw new Error('Invalid export data received');
      }

      // Create secure URL with proper content type
      const url = URL.createObjectURL(new Blob([blob], { type: mimeType }));

      try {
        // Create temporary link with download attributes
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.rel = 'noopener noreferrer';
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        
        // Clean up
        document.body.removeChild(link);
      } finally {
        // Always revoke the URL to prevent memory leaks
        URL.revokeObjectURL(url);
      }
    };

    const handleRetry = async () => {
      if (!error.value || error.value.retryCount >= MAX_RETRY_ATTEMPTS) {
        error.value = null;
        return;
      }

      error.value.retryCount++;
      await handleExport();
    };

    return {
      exportFormats,
      selectedFormat,
      isExporting,
      exportProgress,
      error,
      handleExport,
      handleRetry
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.results-export {
  display: flex;
  flex-direction: column;
  gap: vars.spacing(4);
  padding: vars.spacing(4);
}

.format-select {
  display: flex;
  flex-direction: column;
  gap: vars.spacing(2);

  .format-label {
    font-weight: map-get(vars.$font-weights, medium);
    color: vars.color(gray, 800);
  }

  .format-dropdown {
    padding: vars.spacing(2);
    border: 1px solid vars.color(gray, 300);
    border-radius: 4px;
    background-color: white;
    font-family: vars.$font-family-primary;

    &:focus {
      outline: 2px solid vars.color(primary);
      outline-offset: 2px;
    }

    &:disabled {
      background-color: vars.color(gray, 100);
      cursor: not-allowed;
    }
  }
}

.export-button {
  align-self: flex-start;
}

.progress-container {
  width: 100%;
  height: 4px;
  background-color: vars.color(gray, 200);
  border-radius: 2px;
  overflow: hidden;

  .progress-bar {
    height: 100%;
    background-color: vars.color(primary);
    transition: width 0.3s ease-in-out;

    @media (prefers-reduced-motion: reduce) {
      transition: none;
    }
  }

  .progress-text {
    font-size: 0.875rem;
    color: vars.color(gray, 600);
    margin-top: vars.spacing(1);
  }
}

.error-message {
  color: vars.color(error);
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: vars.spacing(2);
}

.retry-button {
  font-size: 0.875rem;
}

.sr-only {
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
</style>