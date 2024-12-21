<template>
  <form 
    class="check-in-form"
    @submit.prevent="handleSubmit"
    aria-labelledby="form-title"
    novalidate
  >
    <h2 id="form-title" class="form-title">Weekly Check-in</h2>

    <!-- Energy Level Rating -->
    <div class="form-group">
      <BaseInput
        v-model="formData.energyLevel"
        type="number"
        label="Energy Level (1-5)"
        :error="validationErrors.energyLevel"
        :min="RATING_SCALE.MIN"
        :max="RATING_SCALE.MAX"
        :step="RATING_SCALE.STEP"
        required
        aria-describedby="energy-level-hint"
      />
      <span id="energy-level-hint" class="input-hint">
        1 = Very Low, 5 = Very High
      </span>
    </div>

    <!-- Sleep Quality Rating -->
    <div class="form-group">
      <BaseInput
        v-model="formData.sleepQuality"
        type="number"
        label="Sleep Quality (1-5)"
        :error="validationErrors.sleepQuality"
        :min="RATING_SCALE.MIN"
        :max="RATING_SCALE.MAX"
        :step="RATING_SCALE.STEP"
        required
        aria-describedby="sleep-quality-hint"
      />
      <span id="sleep-quality-hint" class="input-hint">
        1 = Very Poor, 5 = Excellent
      </span>
    </div>

    <!-- Side Effects -->
    <div class="form-group">
      <BaseInput
        v-model="formData.sideEffects"
        type="text"
        label="Side Effects"
        :error="validationErrors.sideEffects"
        placeholder="Enter any side effects, separated by commas"
        aria-describedby="side-effects-hint"
      />
      <span id="side-effects-hint" class="input-hint">
        Optional: List any side effects you've experienced
      </span>
    </div>

    <!-- Additional Notes -->
    <div class="form-group">
      <BaseInput
        v-model="formData.additionalNotes"
        type="textarea"
        label="Additional Notes"
        :error="validationErrors.additionalNotes"
        placeholder="Enter any additional observations or notes"
        maxlength="1000"
        aria-describedby="notes-hint"
      />
      <span id="notes-hint" class="input-hint">
        Optional: Maximum 1000 characters
      </span>
    </div>

    <!-- Error Summary for Screen Readers -->
    <div 
      v-if="hasErrors"
      class="error-summary"
      role="alert"
      aria-live="polite"
    >
      <p>Please correct the following errors:</p>
      <ul>
        <li v-for="(error, field) in validationErrors" :key="field">
          {{ error }}
        </li>
      </ul>
    </div>

    <!-- Submit Button -->
    <BaseButton
      type="submit"
      variant="primary"
      :loading="isSubmitting"
      :disabled="!isFormValid || isSubmitting"
      aria-busy="isSubmitting"
    >
      Submit Check-in
    </BaseButton>
  </form>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue'; // v3.3.0
import debounce from 'lodash-es/debounce'; // v4.17.21

// Internal imports
import BaseInput from '@/components/common/BaseInput.vue';
import BaseButton from '@/components/common/BaseButton.vue';
import { CheckInData, RATING_SCALE } from '@/types/data';
import useDataCollection from '@/composables/useDataCollection';
import { theme } from '@/config/theme';

export default defineComponent({
  name: 'CheckInForm',

  components: {
    BaseInput,
    BaseButton
  },

  props: {
    protocolId: {
      type: String,
      required: true,
      validator: (value: string) => /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value)
    }
  },

  emits: {
    submitted: (data: CheckInData) => true,
    error: (error: Error) => error instanceof Error
  },

  setup(props, { emit }) {
    // Initialize data collection composable
    const { submitCheckIn, validateFormData, sanitizeInput } = useDataCollection(props.protocolId);

    // Form state
    const formData = ref<Partial<CheckInData>>({
      energyLevel: 3,
      sleepQuality: 3,
      sideEffects: [],
      additionalNotes: {},
      mood: 3,
      compliance: true
    });

    const validationErrors = ref<Record<string, string>>({});
    const isSubmitting = ref(false);

    // Computed properties
    const hasErrors = computed(() => Object.keys(validationErrors.value).length > 0);
    const isFormValid = computed(() => !hasErrors.value);

    // Debounced validation function
    const validateForm = debounce(async () => {
      const errors = await validateFormData(formData.value, {
        rules: {
          energyLevel: 'required|integer|between:1,5',
          sleepQuality: 'required|integer|between:1,5',
          sideEffects: 'array',
          additionalNotes: 'object'
        },
        required: ['energyLevel', 'sleepQuality']
      });

      validationErrors.value = errors.reduce((acc, error) => ({
        ...acc,
        [error.field]: error.message
      }), {});

      return errors.length === 0;
    }, 300);

    // Form submission handler
    const handleSubmit = async () => {
      try {
        if (!await validateForm()) {
          return;
        }

        isSubmitting.value = true;

        // Sanitize input data
        const sanitizedData = {
          ...formData.value,
          sideEffects: sanitizeInput(formData.value.sideEffects?.join(',')).split(','),
          additionalNotes: sanitizeInput(JSON.stringify(formData.value.additionalNotes))
        };

        // Submit data
        await submitCheckIn(sanitizedData as CheckInData);

        // Emit success event
        emit('submitted', sanitizedData as CheckInData);

        // Reset form
        resetForm();

      } catch (error) {
        emit('error', error as Error);
      } finally {
        isSubmitting.value = false;
      }
    };

    // Form reset handler
    const resetForm = () => {
      formData.value = {
        energyLevel: 3,
        sleepQuality: 3,
        sideEffects: [],
        additionalNotes: {},
        mood: 3,
        compliance: true
      };
      validationErrors.value = {};
    };

    return {
      formData,
      validationErrors,
      isSubmitting,
      hasErrors,
      isFormValid,
      RATING_SCALE,
      handleSubmit,
      resetForm
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.check-in-form {
  display: flex;
  flex-direction: column;
  gap: vars.spacing(4);
  max-width: 600px;
  margin: 0 auto;
  padding: vars.spacing(4);

  .form-title {
    font-family: vars.$font-family-primary;
    font-size: vars.typography-scale(h2);
    color: vars.color(primary);
    margin-bottom: vars.spacing(4);
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: vars.spacing(2);
  }

  .input-hint {
    font-size: vars.typography-scale(small);
    color: vars.color(gray, 600);
    margin-top: vars.spacing(1);
  }

  .error-summary {
    background-color: vars.color(error, 50);
    border: 1px solid vars.color(error);
    border-radius: 4px;
    padding: vars.spacing(3);
    margin-top: vars.spacing(4);

    p {
      color: vars.color(error);
      font-weight: vars.$font-weights-medium;
      margin-bottom: vars.spacing(2);
    }

    ul {
      list-style-type: disc;
      margin-left: vars.spacing(4);
      color: vars.color(error);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    * {
      transition: none;
    }
  }

  @media screen and (max-width: vars.$breakpoints-tablet) {
    padding: vars.spacing(3);
  }
}
</style>