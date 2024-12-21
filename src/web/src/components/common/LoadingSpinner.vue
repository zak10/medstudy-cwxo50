<template>
  <div 
    class="loading-spinner" 
    role="status" 
    aria-live="polite"
  >
    <div 
      class="spinner"
      :class="spinnerClasses"
      :style="spinnerStyles"
      aria-hidden="true"
    ></div>
    <span class="sr-only">{{ label }}</span>
  </div>
</template>

<script>
// Vue.js v3.3.0
import { computed, defineComponent } from 'vue';

export default defineComponent({
  name: 'LoadingSpinner',

  props: {
    /**
     * Controls the size of the spinner using design system size tokens
     * @values 'small' | 'medium' | 'large'
     */
    size: {
      type: String,
      default: 'medium',
      validator: value => ['small', 'medium', 'large'].includes(value)
    },

    /**
     * Sets the color of the spinner using design system colors
     * @values 'primary' | 'secondary' | 'accent'
     */
    color: {
      type: String,
      default: 'primary',
      validator: value => ['primary', 'secondary', 'accent'].includes(value)
    },

    /**
     * Controls the speed of the spinning animation
     * @example '1s', '500ms'
     */
    duration: {
      type: String,
      default: '1s',
      validator: value => /^[0-9]+(.[0-9]+)?(s|ms)$/.test(value)
    },

    /**
     * Accessible label for screen readers
     */
    label: {
      type: String,
      default: 'Loading...'
    }
  },

  setup(props) {
    /**
     * Computes classes for spinner styling based on props
     */
    const spinnerClasses = computed(() => ({
      [props.size]: true,
      [props.color]: true,
      'spinner-animated': true
    }));

    /**
     * Computes styles including animation duration and performance optimizations
     */
    const spinnerStyles = computed(() => ({
      '--spinner-duration': props.duration,
      willChange: 'transform',
      transform: 'translateZ(0)', // Hardware acceleration
      backfaceVisibility: 'hidden' // Prevent flickering
    }));

    return {
      spinnerClasses,
      spinnerStyles
    };
  }
});
</script>

<style lang="scss" scoped>
// Import design system variables and animations
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.loading-spinner {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.spinner {
  border: 2px solid transparent;
  border-radius: 50%;
  position: relative;
  will-change: transform;
  transform: translateZ(0);

  // Apply loading spinner animation with reduced motion support
  @include animations.loading-spinner(var(--spinner-duration));

  // Size variants using design system tokens
  &.small {
    width: var(--spinner-size-small, 16px);
    height: var(--spinner-size-small, 16px);
    border-width: 2px;
  }

  &.medium {
    width: var(--spinner-size-medium, 24px);
    height: var(--spinner-size-medium, 24px);
    border-width: 3px;
  }

  &.large {
    width: var(--spinner-size-large, 32px);
    height: var(--spinner-size-large, 32px);
    border-width: 4px;
  }

  // Color variants using design system colors
  &.primary {
    border-top-color: var(--spinner-color-primary, #{map-get(vars.$colors, 'primary')});
  }

  &.secondary {
    border-top-color: var(--spinner-color-secondary, #{map-get(vars.$colors, 'secondary')});
  }

  &.accent {
    border-top-color: var(--spinner-color-accent, #{map-get(vars.$colors, 'accent')});
  }
}

// Screen reader only text
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