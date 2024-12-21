<template>
  <div 
    class="base-input"
    :class="{ 'base-input--error': !!error }"
  >
    <label 
      :for="inputId" 
      class="base-input__label"
      :data-required="required"
    >
      {{ label }}
    </label>
    
    <input
      :id="inputId"
      ref="inputRef"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      :aria-invalid="!!error"
      :aria-describedby="error ? errorId : undefined"
      :aria-required="required"
      class="base-input__field"
      @input="handleInput"
      @blur="handleBlur"
    />

    <span 
      v-if="error"
      :id="errorId"
      class="base-input__error"
      role="alert"
    >
      {{ error }}
    </span>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue'; // v3.3.0
import debounce from 'lodash/debounce'; // v4.17.21
import xss from 'xss'; // v1.0.14
import { validateLoginCredentials } from '@/utils/validation';
import { theme } from '@/config/theme';

// Types for validation
interface ValidationRule {
  validate: (value: string | number) => boolean;
  message: string;
}

interface ValidationResult {
  isValid: boolean;
  errors: string[];
}

export default defineComponent({
  name: 'BaseInput',

  props: {
    modelValue: {
      type: [String, Number],
      required: true,
    },
    type: {
      type: String,
      default: 'text',
      validator: (value: string) => {
        return ['text', 'number', 'email', 'password'].includes(value);
      },
    },
    label: {
      type: String,
      required: true,
    },
    placeholder: {
      type: String,
      default: '',
    },
    error: {
      type: String,
      default: '',
    },
    required: {
      type: Boolean,
      default: false,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    validationRules: {
      type: Array as () => ValidationRule[],
      default: () => [],
    },
  },

  emits: {
    'update:modelValue': (value: string | number) => true,
    blur: (event: FocusEvent) => true,
    validation: (result: ValidationResult) => true,
  },

  setup(props, { emit }) {
    const inputRef = ref<HTMLInputElement | null>(null);
    const inputId = computed(() => `base-input-${Math.random().toString(36).substr(2, 9)}`);
    const errorId = computed(() => `${inputId.value}-error`);

    // Debounced validation function
    const debouncedValidate = debounce((value: string | number) => {
      const result = validateInput(value);
      emit('validation', result);
    }, 300);

    // Input value sanitization
    const sanitizeInput = (value: string): string => {
      return xss(value, {
        whiteList: {}, // Disable all HTML tags
        stripIgnoreTag: true,
        stripIgnoreTagBody: ['script'],
      });
    };

    // Input validation
    const validateInput = (value: string | number): ValidationResult => {
      const errors: string[] = [];

      // Required field validation
      if (props.required && !value) {
        errors.push('This field is required');
      }

      // Type-specific validation
      if (props.type === 'email' && typeof value === 'string') {
        const emailErrors = validateLoginCredentials({ email: value, password: '' })
          .filter(error => error.field === 'email')
          .map(error => error.message);
        errors.push(...emailErrors);
      }

      // Custom validation rules
      props.validationRules.forEach(rule => {
        if (!rule.validate(value)) {
          errors.push(rule.message);
        }
      });

      return {
        isValid: errors.length === 0,
        errors,
      };
    };

    // Input event handler
    const handleInput = (event: Event) => {
      const target = event.target as HTMLInputElement;
      const sanitizedValue = sanitizeInput(target.value);
      
      emit('update:modelValue', sanitizedValue);
      debouncedValidate(sanitizedValue);
    };

    // Blur event handler
    const handleBlur = (event: FocusEvent) => {
      const result = validateInput(props.modelValue);
      emit('blur', event);
      emit('validation', result);
    };

    return {
      inputRef,
      inputId,
      errorId,
      handleInput,
      handleBlur,
    };
  },
});
</script>

<style lang="scss" scoped>
// Import theme variables
$colors: v-bind('theme.colors');
$typography: v-bind('theme.typography');
$spacing: v-bind('theme.spacing');

// Custom properties
:root {
  --input-height: 40px;
  --input-padding: #{$spacing.scale.xs} #{$spacing.scale.sm};
  --input-border-radius: 4px;
  --input-border-color: #{$colors.primary.base};
  --input-error-color: #{$colors.semantic.error};
  --input-focus-shadow: 0 0 0 2px #{$colors.secondary.base};
}

.base-input {
  display: flex;
  flex-direction: column;
  gap: $spacing.grid;

  &__label {
    font-family: $typography.fontFamily.primary;
    font-weight: $typography.fontWeights.medium;
    color: $colors.text.primary;
    
    &[data-required="true"]:after {
      content: "*";
      color: var(--input-error-color);
      margin-left: 4px;
    }
  }

  &__field {
    height: var(--input-height);
    padding: var(--input-padding);
    border: 1px solid var(--input-border-color);
    border-radius: var(--input-border-radius);
    font-family: $typography.fontFamily.primary;
    font-size: $typography.scale.levels.body;
    transition: all 0.2s ease;

    &:focus {
      outline: none;
      border-color: $colors.secondary.base;
      box-shadow: var(--input-focus-shadow);
    }

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      background-color: $colors.background.tertiary;
    }

    &[aria-invalid="true"] {
      border-color: var(--input-error-color);
    }
  }

  &__error {
    color: var(--input-error-color);
    font-size: $typography.scale.levels.small;
    font-family: $typography.fontFamily.primary;
    margin-top: 4px;
    min-height: 16px;
  }
}
</style>