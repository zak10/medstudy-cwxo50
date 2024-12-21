<template>
  <div class="base-select">
    <label 
      :for="selectId" 
      class="base-select__label"
      :aria-required="required"
    >
      {{ label }}
      <span v-if="required" class="base-select__required">*</span>
    </label>

    <select
      :id="selectId"
      class="base-select__field"
      :value="modelValue"
      :required="required"
      :disabled="disabled"
      :aria-invalid="!!error"
      :aria-describedby="error ? errorId : undefined"
      :aria-required="required"
      @change="handleSelect"
      @blur="validate"
    >
      <option value="" disabled selected>{{ placeholder }}</option>
      <option 
        v-for="option in options" 
        :key="option.value" 
        :value="option.value"
      >
        {{ option.label }}
      </option>
    </select>

    <span 
      v-if="error"
      :id="errorId"
      class="base-select__error"
      role="alert"
    >
      {{ error }}
    </span>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue'; // v3.3.0
import { colors, typography, spacing } from '@/config/theme';
import { useValidation } from '@/composables/useValidation';

export default defineComponent({
  name: 'BaseSelect',

  props: {
    modelValue: {
      type: [String, Number, Boolean, Object],
      required: true,
    },
    options: {
      type: Array as () => Array<{value: any, label: string}>,
      required: true,
    },
    label: {
      type: String,
      required: true,
    },
    placeholder: {
      type: String,
      default: 'Select an option',
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
      type: Array,
      default: () => [],
    },
  },

  emits: ['update:modelValue', 'change', 'validation'],

  setup(props, { emit }) {
    const { validateField } = useValidation();
    
    // Generate unique IDs for accessibility
    const selectId = `select-${Math.random().toString(36).substr(2, 9)}`;
    const errorId = `${selectId}-error`;

    // Handle select value changes
    const handleSelect = async (event: Event) => {
      const target = event.target as HTMLSelectElement;
      const selectedOption = props.options.find(opt => opt.value === target.value);
      
      if (selectedOption) {
        emit('update:modelValue', selectedOption.value);
        emit('change', event);

        // Validate after change
        const validationResult = await validate();
        emit('validation', validationResult);
      }
    };

    // Validate select value
    const validate = async () => {
      if (props.validationRules.length) {
        const validationResult = await validateField(props.label, props.modelValue);
        return validationResult;
      }
      return [];
    };

    // Get selected option label
    const getSelectedLabel = computed(() => {
      const selectedOption = props.options.find(opt => opt.value === props.modelValue);
      return selectedOption ? selectedOption.label : props.placeholder;
    });

    return {
      selectId,
      errorId,
      handleSelect,
      validate,
      getSelectedLabel,
    };
  },
});
</script>

<style scoped>
.base-select {
  display: flex;
  flex-direction: column;
  gap: v-bind('spacing.grid');
}

.base-select__label {
  font-family: v-bind('typography.fontFamily.primary');
  font-weight: v-bind('typography.fontWeights.medium');
  color: v-bind('colors.text.primary');
  font-size: 14px;
}

.base-select__required {
  color: v-bind('colors.semantic.error');
  margin-left: 4px;
}

.base-select__field {
  height: var(--select-height);
  padding: var(--select-padding);
  border: 1px solid var(--select-border-color);
  border-radius: var(--select-border-radius);
  font-family: v-bind('typography.fontFamily.primary');
  font-size: 14px;
  background-color: v-bind('colors.background.primary');
  color: v-bind('colors.text.primary');
  cursor: pointer;
  transition: all 0.2s ease;
  width: 100%;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  padding-right: 32px;
}

.base-select__field:focus {
  outline: none;
  border-color: v-bind('colors.secondary.base');
  box-shadow: var(--select-focus-shadow);
}

.base-select__field:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: v-bind('colors.background.tertiary');
}

.base-select__field[aria-invalid="true"] {
  border-color: var(--select-error-color);
}

.base-select__error {
  color: v-bind('colors.semantic.error');
  font-size: 12px;
  font-family: v-bind('typography.fontFamily.primary');
  margin-top: 4px;
}

:root {
  --select-height: 40px;
  --select-padding: 8px 12px;
  --select-border-radius: 4px;
  --select-border-color: v-bind('colors.primary.base');
  --select-error-color: v-bind('colors.semantic.error');
  --select-focus-shadow: 0 0 0 2px v-bind('colors.secondary.base');
}
</style>
```

This implementation:

1. Follows the design system specifications with consistent typography, colors, and spacing
2. Implements WCAG 2.1 AA compliance with proper ARIA attributes and keyboard navigation
3. Provides validation integration through the useValidation composable
4. Includes error handling and display
5. Supports v-model binding with proper prop/emit handling
6. Implements all required props and events
7. Uses scoped styling with CSS variables for theming
8. Includes proper accessibility features like labels and ARIA attributes
9. Provides visual feedback for different states (focus, error, disabled)
10. Implements a custom dropdown arrow using SVG
11. Supports placeholder text and required field indication
12. Includes proper TypeScript typing

The component can be used like this:

```vue
<BaseSelect
  v-model="selectedValue"
  :options="[
    { value: 1, label: 'Option 1' },
    { value: 2, label: 'Option 2' }
  ]"
  label="Select Option"
  required
  :validation-rules="['required']"
  @change="handleChange"
  @validation="handleValidation"
/>