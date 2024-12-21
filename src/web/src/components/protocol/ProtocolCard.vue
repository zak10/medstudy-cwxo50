<template>
  <BaseCard
    :elevation="2"
    :clickable="interactive"
    :loading="loading"
    :class="cardClasses"
    role="article"
    :aria-label="protocol.title"
    @click="handleClick"
    @keypress="handleKeyPress"
  >
    <!-- Protocol Image -->
    <img
      v-if="protocol.imageUrl"
      :src="protocol.imageUrl"
      :alt="`Visual representation of ${protocol.title}`"
      class="protocol-card__image"
      loading="lazy"
    />

    <!-- Protocol Header -->
    <div class="protocol-card__header">
      <h3 class="protocol-card__title">{{ protocol.title }}</h3>
      <div 
        class="protocol-card__status"
        :class="[`status-${protocol.status.toLowerCase()}`]"
        :style="{ backgroundColor: statusColor }"
        role="status"
        :aria-label="`Protocol status: ${protocol.status}`"
      ></div>
    </div>

    <!-- Protocol Description -->
    <p class="protocol-card__description">{{ protocol.description }}</p>

    <!-- Protocol Metrics -->
    <div class="protocol-card__metrics" role="group" aria-label="Protocol metrics">
      <div class="metric">
        <span class="metric__label">{{ t('protocol.duration') }}</span>
        <span class="metric__value">{{ durationText }}</span>
      </div>
      <div class="metric">
        <span class="metric__label">{{ t('protocol.participants') }}</span>
        <span class="metric__value">{{ protocol.participantCount }}</span>
      </div>
    </div>

    <!-- Progress Component (if enabled) -->
    <ProtocolProgress
      v-if="showProgress"
      :participation="protocol"
      :high-contrast="highContrast"
      class="protocol-card__progress"
    />

    <!-- Action Buttons -->
    <div 
      v-if="interactive"
      class="protocol-card__actions"
      role="group"
      aria-label="Protocol actions"
    >
      <BaseButton
        variant="primary"
        size="md"
        :loading="loading"
        :disabled="loading"
        :aria-label="`Enroll in ${protocol.title}`"
        @click="handleEnroll"
      >
        {{ t('protocol.enroll') }}
      </BaseButton>
    </div>
  </BaseCard>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue'; // v3.3.0
import { useI18n } from 'vue-i18n'; // v9.2.0
import type { Protocol } from '@/types/protocol';
import BaseCard from '@/components/common/BaseCard.vue';
import BaseButton from '@/components/common/BaseButton.vue';
import ProtocolProgress from '@/components/protocol/ProtocolProgress.vue';

export default defineComponent({
  name: 'ProtocolCard',

  components: {
    BaseCard,
    BaseButton,
    ProtocolProgress,
  },

  props: {
    protocol: {
      type: Object as () => Protocol,
      required: true,
    },
    showProgress: {
      type: Boolean,
      default: false,
    },
    interactive: {
      type: Boolean,
      default: true,
    },
    loading: {
      type: Boolean,
      default: false,
    },
    highContrast: {
      type: Boolean,
      default: false,
    },
  },

  emits: {
    view: (protocolId: string) => typeof protocolId === 'string',
    enroll: (protocolId: string) => typeof protocolId === 'string',
    error: (error: Error) => error instanceof Error,
  },

  setup(props, { emit }) {
    const { t } = useI18n();

    const statusColor = computed(() => {
      const colors = {
        ACTIVE: '#2ECC71',
        PAUSED: '#F1C40F',
        COMPLETED: '#3498DB',
        CANCELLED: '#E74C3C',
        DRAFT: '#95A5A6',
      };
      return colors[props.protocol.status] || colors.DRAFT;
    });

    const durationText = computed(() => {
      const weeks = props.protocol.duration;
      if (weeks < 4) {
        return t('protocol.duration.weeks', { count: weeks });
      }
      const months = Math.round(weeks / 4);
      return t('protocol.duration.months', { count: months });
    });

    const cardClasses = computed(() => ({
      'protocol-card': true,
      'protocol-card--interactive': props.interactive,
      'protocol-card--loading': props.loading,
      'protocol-card--high-contrast': props.highContrast,
      'protocol-card--with-progress': props.showProgress,
    }));

    const handleClick = (event: MouseEvent) => {
      if (!props.interactive || props.loading) return;
      
      try {
        emit('view', props.protocol.id);
      } catch (error) {
        emit('error', error instanceof Error ? error : new Error('Failed to handle click'));
      }
    };

    const handleEnroll = (event: MouseEvent) => {
      event.stopPropagation();
      if (props.loading) return;

      try {
        emit('enroll', props.protocol.id);
      } catch (error) {
        emit('error', error instanceof Error ? error : new Error('Failed to enroll'));
      }
    };

    const handleKeyPress = (event: KeyboardEvent) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        handleClick(event as unknown as MouseEvent);
      }
    };

    return {
      t,
      statusColor,
      durationText,
      cardClasses,
      handleClick,
      handleEnroll,
      handleKeyPress,
    };
  },
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_mixins' as mixins;

.protocol-card {
  display: flex;
  flex-direction: column;
  gap: vars.spacing(4);
  min-height: 200px;
  transition: all 0.2s ease;

  &__image {
    width: 100%;
    height: 160px;
    object-fit: cover;
    border-radius: vars.spacing(2);
  }

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: vars.spacing(3);
  }

  &__title {
    font-family: vars.$font-family-primary;
    font-size: 1.25rem;
    font-weight: map-get(vars.$font-weights, semibold);
    color: vars.color(gray, 900);
    margin: 0;
  }

  &__status {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    transition: background-color 0.2s ease;
  }

  &__description {
    font-size: 1rem;
    color: vars.color(gray, 600);
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  &__metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: vars.spacing(4);

    .metric {
      display: flex;
      flex-direction: column;
      gap: vars.spacing(1);

      &__label {
        font-size: 0.875rem;
        color: vars.color(gray, 500);
      }

      &__value {
        font-size: 1rem;
        font-weight: map-get(vars.$font-weights, medium);
        color: vars.color(gray, 900);
      }
    }
  }

  &__actions {
    margin-top: auto;
    padding-top: vars.spacing(4);
    display: flex;
    gap: vars.spacing(3);
  }

  // High contrast mode
  &--high-contrast {
    border: 2px solid currentColor;

    .protocol-card__title {
      color: vars.color(gray, 900);
    }

    .protocol-card__description {
      color: vars.color(gray, 800);
    }
  }

  // Interactive states
  &--interactive {
    cursor: pointer;

    &:hover {
      transform: translateY(-2px);
    }

    &:active {
      transform: translateY(0);
    }
  }

  // Loading state
  &--loading {
    pointer-events: none;
    opacity: 0.7;
  }

  // Responsive adjustments
  @include mixins.respond-to('mobile') {
    min-height: 180px;

    &__image {
      height: 120px;
    }

    &__title {
      font-size: 1.125rem;
    }
  }
}

// Print styles
@media print {
  .protocol-card {
    break-inside: avoid;
    border: 1px solid vars.color(gray, 300);
    box-shadow: none !important;

    &__actions {
      display: none;
    }
  }
}
</style>