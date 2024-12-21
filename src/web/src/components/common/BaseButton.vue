<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="buttonClasses"
    :style="buttonStyles"
    v-bind="ariaAttributes"
    @click="handleClick"
  >
    <slot name="prefix" v-if="!loading"></slot>
    <LoadingSpinner
      v-if="loading"
      size="small"
      :color="variant === 'primary' ? 'secondary' : 'primary'"
      class="button-spinner"
    />
    <span v-if="!loading" class="button-content">
      <slot></slot>
    </span>
    <slot name="suffix" v-if="!loading"></slot>
  </button>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue'; // v3.3.0
import type { Theme } from '@/types/ui';
import LoadingSpinner from '@/components/common/LoadingSpinner.vue';

export default defineComponent({
  name: 'BaseButton',
  
  components: {
    LoadingSpinner
  },

  props: {
    variant: {
      type: String,
      default: 'primary',
      validator: (value: string) => 
        ['primary', 'secondary', 'accent', 'outline', 'text'].includes(value)
    },
    size: {
      type: String,
      default: 'md',
      validator: (value: string) => ['sm', 'md', 'lg'].includes(value)
    },
    type: {
      type: String,
      default: 'button',
      validator: (value: string) => ['button', 'submit', 'reset'].includes(value)
    },
    disabled: {
      type: Boolean,
      default: false
    },
    loading: {
      type: Boolean,
      default: false
    },
    ariaLabel: {
      type: String,
      required: false
    }
  },

  emits: {
    click: (event: MouseEvent) => event instanceof MouseEvent
  },

  setup(props, { emit }) {
    const buttonClasses = computed(() => ({
      'base-button': true,
      [`variant-${props.variant}`]: true,
      [`size-${props.size}`]: true,
      'disabled': props.disabled,
      'loading': props.loading,
      'with-prefix': !!props.$slots.prefix,
      'with-suffix': !!props.$slots.suffix
    }));

    const buttonStyles = computed(() => {
      const theme = (window as any)?.__theme__ as Theme;
      const styles: Record<string, string> = {};

      // Apply theme color tokens based on variant
      if (props.variant === 'primary') {
        styles.backgroundColor = theme.colors.primary;
        styles.color = '#FFFFFF';
      } else if (props.variant === 'secondary') {
        styles.backgroundColor = theme.colors.secondary;
        styles.color = '#FFFFFF';
      } else if (props.variant === 'accent') {
        styles.backgroundColor = theme.colors.accent;
        styles.color = '#FFFFFF';
      }

      // Apply elevation based on variant and state
      if (!props.disabled && props.variant !== 'text') {
        styles.boxShadow = theme.elevation.level1;
      }

      return styles;
    });

    const ariaAttributes = computed(() => ({
      'aria-disabled': props.disabled || props.loading,
      'aria-busy': props.loading,
      'aria-label': props.ariaLabel,
      'role': 'button'
    }));

    const handleClick = (event: MouseEvent) => {
      if (props.disabled || props.loading) {
        event.preventDefault();
        return;
      }
      emit('click', event);
    };

    return {
      buttonClasses,
      buttonStyles,
      ariaAttributes,
      handleClick
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.base-button {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: vars.spacing(2);
  border: none;
  border-radius: 4px;
  font-family: vars.$font-family-primary;
  font-weight: map-get(vars.$font-weights, medium);
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  outline: none;
  white-space: nowrap;
  text-decoration: none;

  &:focus-visible {
    outline: 2px solid vars.color(primary);
    outline-offset: 2px;
  }

  // Size variants
  &.size-sm {
    padding: vars.spacing(1) vars.spacing(3);
    font-size: 0.875rem;
    min-height: 32px;
  }

  &.size-md {
    padding: vars.spacing(2) vars.spacing(4);
    font-size: 1rem;
    min-height: 40px;
  }

  &.size-lg {
    padding: vars.spacing(3) vars.spacing(6);
    font-size: 1.125rem;
    min-height: 48px;
  }

  // Variant styles
  &.variant-primary {
    &:hover:not(.disabled) {
      filter: brightness(110%);
    }
    &:active:not(.disabled) {
      filter: brightness(90%);
    }
  }

  &.variant-secondary {
    &:hover:not(.disabled) {
      filter: brightness(110%);
    }
    &:active:not(.disabled) {
      filter: brightness(90%);
    }
  }

  &.variant-accent {
    &:hover:not(.disabled) {
      filter: brightness(110%);
    }
    &:active:not(.disabled) {
      filter: brightness(90%);
    }
  }

  &.variant-outline {
    background: transparent;
    border: 2px solid vars.color(primary);
    color: vars.color(primary);

    &:hover:not(.disabled) {
      background: rgba(vars.color(primary), 0.1);
    }
  }

  &.variant-text {
    background: transparent;
    color: vars.color(primary);
    padding-left: vars.spacing(2);
    padding-right: vars.spacing(2);

    &:hover:not(.disabled) {
      background: rgba(vars.color(primary), 0.1);
    }
  }

  // States
  &.disabled {
    opacity: 0.6;
    cursor: not-allowed;
    pointer-events: none;
  }

  &.loading {
    cursor: wait;
    pointer-events: none;
  }

  // Loading spinner styles
  .button-spinner {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
  }

  // Content spacing with prefix/suffix
  &.with-prefix {
    padding-left: vars.spacing(2);
  }

  &.with-suffix {
    padding-right: vars.spacing(2);
  }

  // RTL Support
  &:dir(rtl) {
    &.with-prefix {
      padding-right: vars.spacing(2);
      padding-left: vars.spacing(4);
    }
    &.with-suffix {
      padding-left: vars.spacing(2);
      padding-right: vars.spacing(4);
    }
  }

  // Reduced motion support
  @media (prefers-reduced-motion: reduce) {
    transition: none;
  }
}
</style>