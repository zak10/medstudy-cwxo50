<template>
  <div class="data-submission" :data-testid="'data-submission-page'">
    <!-- Page Header -->
    <header class="data-submission__header">
      <h1>Submit Protocol Data</h1>
      <p class="data-submission__description">
        Submit your blood work results and weekly check-in data for protocol tracking.
      </p>
    </header>

    <!-- Form Container -->
    <div class="data-submission__content">
      <!-- Form Type Selection -->
      <div class="data-submission__selector">
        <button 
          v-for="type in formTypes" 
          :key="type.value"
          class="selector-button"
          :class="{ active: selectedFormType === type.value }"
          @click="selectedFormType = type.value"
        >
          {{ type.label }}
        </button>
      </div>

      <!-- Dynamic Form Section -->
      <div class="data-submission__form">
        <!-- Blood Work Form -->
        <BloodworkForm
          v-if="selectedFormType === 'blood_work'"
          :protocol-id="protocolId"
          @validation="handleValidation"
          @submitted="handleSubmissionSuccess"
        />

        <!-- Weekly Check-in Form -->
        <div v-else-if="selectedFormType === 'check_in'" class="check-in-form">
          <form @submit.prevent="handleCheckInSubmit">
            <!-- Energy Level -->
            <div class="form-group">
              <label>Energy Level</label>
              <div class="rating-scale">
                <template v-for="n in 5" :key="n">
                  <input
                    type="radio"
                    :id="`energy-${n}`"
                    v-model="checkInData.energyLevel"
                    :value="n"
                    name="energy"
                  />
                  <label :for="`energy-${n}`">{{ n }}</label>
                </template>
              </div>
            </div>

            <!-- Sleep Quality -->
            <div class="form-group">
              <label>Sleep Quality</label>
              <div class="rating-scale">
                <template v-for="n in 5" :key="n">
                  <input
                    type="radio"
                    :id="`sleep-${n}`"
                    v-model="checkInData.sleepQuality"
                    :value="n"
                    name="sleep"
                  />
                  <label :for="`sleep-${n}`">{{ n }}</label>
                </template>
              </div>
            </div>

            <!-- Side Effects -->
            <div class="form-group">
              <label>Side Effects (if any)</label>
              <div class="side-effects-list">
                <div v-for="effect in sideEffectOptions" :key="effect">
                  <input
                    type="checkbox"
                    :id="effect"
                    v-model="checkInData.sideEffects"
                    :value="effect"
                  />
                  <label :for="effect">{{ effect }}</label>
                </div>
              </div>
            </div>

            <!-- Additional Notes -->
            <div class="form-group">
              <label>Additional Notes</label>
              <textarea
                v-model="checkInData.additionalNotes.text"
                rows="4"
                placeholder="Enter any additional observations or notes..."
              ></textarea>
            </div>

            <!-- Submit Button -->
            <button 
              type="submit"
              class="submit-button"
              :disabled="isSubmitting || !isFormValid"
            >
              {{ isSubmitting ? 'Submitting...' : 'Submit Check-in' }}
            </button>
          </form>
        </div>
      </div>
    </div>

    <!-- Notifications -->
    <div 
      v-if="notification.isActive"
      class="notification"
      :class="notification.type"
    >
      {{ notification.message }}
    </div>

    <!-- Auto-save Indicator -->
    <div v-if="lastSaved" class="auto-save-indicator">
      Last saved: {{ formatLastSaved }}
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted, onUnmounted } from 'vue'; // v3.3.0
import { useNotification } from '@vueuse/core'; // v10.0.0
import { useField } from 'vee-validate'; // v4.9.0
import BloodworkForm from '@/components/data/BloodworkForm.vue';
import useDataCollection from '@/composables/useDataCollection';
import { DataPointType, CheckInData } from '@/types/data';
import { theme } from '@/config/theme';

// Form types configuration
const formTypes = [
  { label: 'Blood Work Results', value: 'blood_work' },
  { label: 'Weekly Check-in', value: 'check_in' }
];

// Side effect options
const sideEffectOptions = [
  'Headache',
  'Nausea',
  'Fatigue',
  'Dizziness',
  'Other'
];

export default defineComponent({
  name: 'DataSubmission',

  components: {
    BloodworkForm
  },

  props: {
    protocolId: {
      type: String,
      required: true
    }
  },

  emits: ['submitSuccess', 'validationError'],

  setup(props, { emit }) {
    // Composables
    const { notification } = useNotification();
    const {
      checkInForm,
      isSubmitting,
      validationErrors,
      submitCheckIn,
      validateFormData
    } = useDataCollection(props.protocolId);

    // Reactive state
    const selectedFormType = ref<DataPointType>(DataPointType.BLOOD_WORK);
    const lastSaved = ref<Date | null>(null);
    const checkInData = ref<Partial<CheckInData>>({
      energyLevel: 3,
      sleepQuality: 3,
      sideEffects: [],
      additionalNotes: { text: '' },
      mood: 3,
      compliance: true
    });

    // Computed properties
    const isFormValid = computed(() => {
      return validationErrors.value.length === 0;
    });

    const formatLastSaved = computed(() => {
      if (!lastSaved.value) return '';
      return new Intl.DateTimeFormat('en-US', {
        hour: 'numeric',
        minute: 'numeric',
        second: 'numeric'
      }).format(lastSaved.value);
    });

    // Methods
    const handleValidation = (result: { isValid: boolean; errors: any[] }) => {
      if (!result.isValid) {
        emit('validationError', result.errors);
      }
    };

    const handleSubmissionSuccess = () => {
      notification.value = {
        type: 'success',
        message: 'Data submitted successfully',
        isActive: true
      };
      emit('submitSuccess');
    };

    const handleCheckInSubmit = async () => {
      try {
        await submitCheckIn(checkInData.value as CheckInData);
        handleSubmissionSuccess();
        // Reset form
        checkInData.value = {
          energyLevel: 3,
          sleepQuality: 3,
          sideEffects: [],
          additionalNotes: { text: '' },
          mood: 3,
          compliance: true
        };
      } catch (error) {
        notification.value = {
          type: 'error',
          message: error.message,
          isActive: true
        };
      }
    };

    // Auto-save functionality
    const autoSaveForm = async () => {
      try {
        const formState = {
          type: selectedFormType.value,
          data: selectedFormType.value === DataPointType.CHECK_IN ? 
            checkInData.value : null
        };
        localStorage.setItem('formDraft', JSON.stringify(formState));
        lastSaved.value = new Date();
      } catch (error) {
        console.error('Auto-save error:', error);
      }
    };

    // Lifecycle hooks
    onMounted(() => {
      // Restore draft if available
      const savedDraft = localStorage.getItem('formDraft');
      if (savedDraft) {
        const { type, data } = JSON.parse(savedDraft);
        selectedFormType.value = type;
        if (type === DataPointType.CHECK_IN && data) {
          checkInData.value = data;
        }
      }

      // Set up auto-save interval
      const autoSaveInterval = setInterval(autoSaveForm, 30000);
      onUnmounted(() => clearInterval(autoSaveInterval));
    });

    return {
      // State
      selectedFormType,
      checkInData,
      isSubmitting,
      lastSaved,
      notification,
      formTypes,
      sideEffectOptions,

      // Computed
      isFormValid,
      formatLastSaved,

      // Methods
      handleValidation,
      handleSubmissionSuccess,
      handleCheckInSubmit
    };
  }
});
</script>

<style lang="scss" scoped>
// Import theme variables
$colors: v-bind('theme.colors');
$typography: v-bind('theme.typography');
$spacing: v-bind('theme.spacing');

.data-submission {
  padding: $spacing.scale.lg;
  max-width: 1200px;
  margin: 0 auto;

  &__header {
    margin-bottom: $spacing.scale.xl;
    
    h1 {
      font-family: $typography.fontFamily.primary;
      font-size: $typography.scale.levels.h1;
      color: $colors.text.primary;
      margin-bottom: $spacing.scale.sm;
    }
  }

  &__description {
    color: $colors.text.secondary;
    font-size: $typography.scale.levels.body;
  }

  &__selector {
    display: flex;
    gap: $spacing.scale.sm;
    margin-bottom: $spacing.scale.lg;

    .selector-button {
      padding: $spacing.scale.sm $spacing.scale.md;
      border: 1px solid $colors.primary.base;
      border-radius: 4px;
      background: transparent;
      color: $colors.primary.base;
      cursor: pointer;
      transition: all 0.2s ease;

      &.active {
        background: $colors.primary.base;
        color: $colors.primary.contrast;
      }

      &:hover:not(.active) {
        background: $colors.background.secondary;
      }
    }
  }

  .form-group {
    margin-bottom: $spacing.scale.md;

    label {
      display: block;
      margin-bottom: $spacing.scale.xs;
      font-weight: $typography.fontWeights.medium;
      color: $colors.text.primary;
    }
  }

  .rating-scale {
    display: flex;
    gap: $spacing.scale.md;
    margin-top: $spacing.scale.xs;

    input[type="radio"] {
      display: none;

      & + label {
        padding: $spacing.scale.xs $spacing.scale.sm;
        border: 1px solid $colors.primary.base;
        border-radius: 4px;
        cursor: pointer;
      }

      &:checked + label {
        background: $colors.primary.base;
        color: $colors.primary.contrast;
      }
    }
  }

  .side-effects-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: $spacing.scale.sm;
  }

  textarea {
    width: 100%;
    padding: $spacing.scale.sm;
    border: 1px solid $colors.primary.base;
    border-radius: 4px;
    resize: vertical;
    font-family: $typography.fontFamily.primary;

    &:focus {
      outline: none;
      border-color: $colors.secondary.base;
      box-shadow: 0 0 0 2px rgba($colors.secondary.base, 0.2);
    }
  }

  .submit-button {
    width: 100%;
    padding: $spacing.scale.sm;
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

  .notification {
    position: fixed;
    bottom: $spacing.scale.lg;
    right: $spacing.scale.lg;
    padding: $spacing.scale.sm $spacing.scale.md;
    border-radius: 4px;
    animation: slideIn 0.3s ease;

    &.success {
      background: $colors.semantic.success;
      color: #fff;
    }

    &.error {
      background: $colors.semantic.error;
      color: #fff;
    }
  }

  .auto-save-indicator {
    position: fixed;
    bottom: $spacing.scale.sm;
    left: $spacing.scale.sm;
    font-size: $typography.scale.levels.small;
    color: $colors.text.secondary;
  }
}

@keyframes slideIn {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>