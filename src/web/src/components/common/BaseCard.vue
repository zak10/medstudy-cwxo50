<template>
  <div
    :class="cardClasses"
    :tabindex="clickable ? 0 : undefined"
    :role="clickable ? 'button' : undefined"
    @click="handleClick"
    @keydown="handleKeydown"
  >
    <!-- Optional header slot with border styling -->
    <div v-if="$slots.header" class="base-card__header">
      <slot name="header" />
    </div>

    <!-- Main content area -->
    <div class="base-card__content">
      <slot />
    </div>

    <!-- Optional footer slot with border styling -->
    <div v-if="$slots.footer" class="base-card__footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

// Define props with validation and documentation
const props = defineProps({
  /**
   * Shadow elevation level following design system specifications
   * @values 1-4
   */
  elevation: {
    type: Number,
    default: 1,
    validator: (value: number) => value >= 1 && value <= 4,
  },
  /**
   * Card padding using spacing scale from design system
   * @values 0-16 (mapped to spacing scale)
   */
  padding: {
    type: String,
    default: '4',
  },
  /**
   * Makes card interactive with hover effects and keyboard navigation
   */
  clickable: {
    type: Boolean,
    default: false,
  },
  /**
   * Card border radius size following design system tokens
   * @values sm, md, lg
   */
  borderRadius: {
    type: String,
    default: 'md',
    validator: (value: string) => ['sm', 'md', 'lg'].includes(value),
  },
});

// Define emits with TypeScript types
const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void;
}>();

// Computed classes for dynamic styling
const cardClasses = computed(() => ({
  'base-card': true,
  'base-card--clickable': props.clickable,
  [`base-card--elevation-${props.elevation}`]: true,
  [`base-card--radius-${props.borderRadius}`]: true,
  [`base-card--padding-${props.padding}`]: true,
}));

// Event handlers
const handleClick = (event: MouseEvent) => {
  if (props.clickable) {
    event.preventDefault();
    emit('click', event);
  }
};

const handleKeydown = (event: KeyboardEvent) => {
  if (props.clickable && (event.key === 'Enter' || event.key === ' ')) {
    event.preventDefault();
    emit('click', event as unknown as MouseEvent);
  }
};
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_mixins.scss';

.base-card {
  position: relative;
  background-color: white;
  border: 1px solid map-get($colors, gray, 200);
  transition: box-shadow 0.2s ease-in-out, transform 0.2s ease-in-out;
  width: 100%;

  // Border radius variants
  &--radius {
    &-sm { border-radius: 4px; }
    &-md { border-radius: 8px; }
    &-lg { border-radius: 12px; }
  }

  // Elevation levels using design system tokens
  &--elevation {
    @for $level from 1 through 4 {
      &-#{$level} {
        box-shadow: map-get($elevation-levels, $level);
      }
    }
  }

  // Padding variants using spacing scale
  &--padding {
    @each $key, $value in $spacing {
      &-#{$key} {
        padding: $value;
      }
    }
  }

  // Interactive states for clickable cards
  &--clickable {
    cursor: pointer;
    user-select: none;
    outline: none;

    &:hover {
      transform: translateY(-2px);
      @include elevation(2);
    }

    &:active {
      transform: translateY(0);
      @include elevation(1);
    }

    &:focus-visible {
      outline: 2px solid map-get($colors, primary);
      outline-offset: 2px;
    }
  }

  // Header and footer sections
  &__header,
  &__footer {
    padding: map-get($spacing, 4);
  }

  &__header {
    border-bottom: 1px solid map-get($colors, gray, 200);
  }

  &__footer {
    border-top: 1px solid map-get($colors, gray, 200);
  }

  &__content {
    position: relative;
  }
}

// Print styles
@media print {
  .base-card {
    box-shadow: none !important;
    border: 1px solid map-get($colors, gray, 300);
  }
}
</style>