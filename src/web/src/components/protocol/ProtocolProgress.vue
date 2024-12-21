<template>
  <BaseCard
    :elevation="2"
    padding="4"
    :loading="isLoading"
    class="protocol-progress"
    role="region"
    aria-labelledby="progress-title"
  >
    <!-- Progress Header -->
    <div class="progress-header">
      <h3 id="progress-title" class="progress-title">
        Protocol Progress
      </h3>
      <div 
        class="progress-percentage" 
        :class="{ 'high-contrast': highContrast }"
        aria-live="polite"
      >
        {{ progressPercentage }}
      </div>
    </div>

    <!-- Progress Timeline -->
    <div class="progress-timeline">
      <BaseChart
        :chart-type="'line'"
        :data="chartData"
        :options="chartOptions"
        :high-contrast="highContrast"
        :description="chartDescription"
        @chartClick="handleChartClick"
        @accessibilityAction="handleAccessibilityAction"
      />
    </div>

    <!-- Detailed Progress Info (Conditional) -->
    <div v-if="showDetails" class="progress-details">
      <dl class="progress-metrics">
        <div class="metric-item">
          <dt>Current Week</dt>
          <dd>{{ currentWeek }} of {{ totalWeeks }}</dd>
        </div>
        <div class="metric-item">
          <dt>Data Collection Status</dt>
          <dd>{{ dataCollectionStatus }}</dd>
        </div>
        <div class="metric-item">
          <dt>Completion Rate</dt>
          <dd>{{ completionRate }}%</dd>
        </div>
      </dl>
    </div>
  </BaseCard>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import BaseCard from '@/components/common/BaseCard.vue';
import BaseChart from '@/components/common/BaseChart.vue';
import type { ProtocolParticipation } from '@/types/protocol';
import { CHART_COLORS, DEFAULT_CHART_OPTIONS } from '@/config/charts';

// Props with validation
const props = defineProps({
  participation: {
    type: Object as () => ProtocolParticipation,
    required: true,
    validator: (value: ProtocolParticipation) => {
      return typeof value.progress === 'number' && 
             value.progress >= 0 && 
             value.progress <= 100;
    }
  },
  showDetails: {
    type: Boolean,
    default: false
  },
  highContrast: {
    type: Boolean,
    default: false
  }
});

// Emits with type safety
const emit = defineEmits<{
  (e: 'progressUpdate', newProgress: number): void;
  (e: 'error', error: Error): void;
}>();

// Component state
const isLoading = ref(false);
const currentWeek = computed(() => Math.ceil(props.participation.timeline.elapsed));
const totalWeeks = computed(() => props.participation.timeline.duration);

// Progress formatting with accessibility
const progressPercentage = computed(() => {
  const formatted = `${Math.round(props.participation.progress)}%`;
  return formatted;
});

// Computed color based on progress and contrast mode
const progressColor = computed(() => {
  const colors = props.highContrast ? CHART_COLORS.highContrast : CHART_COLORS;
  if (props.participation.progress < 25) return colors.accent;
  if (props.participation.progress < 75) return colors.secondary;
  return colors.primary;
});

// Chart data preparation
const chartData = computed(() => ({
  labels: props.participation.timeline.checkpoints.map(cp => cp.date),
  datasets: [{
    label: 'Progress',
    data: props.participation.timeline.checkpoints.map(cp => cp.progress),
    borderColor: progressColor.value,
    backgroundColor: progressColor.value,
    tension: 0.4,
    pointRadius: 4,
    pointHoverRadius: 6
  }]
}));

// Enhanced chart options with accessibility
const chartOptions = computed(() => ({
  ...DEFAULT_CHART_OPTIONS,
  plugins: {
    ...DEFAULT_CHART_OPTIONS.plugins,
    accessibility: {
      enabled: true,
      description: chartDescription.value,
      announceDataPoints: true,
      labels: {
        aria: 'Protocol progress chart showing completion percentage over time'
      }
    }
  },
  scales: {
    x: {
      title: {
        display: true,
        text: 'Timeline'
      }
    },
    y: {
      title: {
        display: true,
        text: 'Completion (%)'
      },
      min: 0,
      max: 100
    }
  }
}));

// Accessibility descriptions
const chartDescription = computed(() => 
  `Protocol progress chart showing ${progressPercentage.value} completion over ${totalWeeks.value} weeks`
);

const dataCollectionStatus = computed(() => {
  const status = props.participation.status;
  return status.charAt(0) + status.slice(1).toLowerCase();
});

const completionRate = computed(() => 
  Math.round((props.participation.timeline.completedCheckpoints / 
              props.participation.timeline.totalCheckpoints) * 100)
);

// Event handlers
const handleChartClick = (event: MouseEvent, elements: any[]) => {
  if (elements.length > 0) {
    const index = elements[0].index;
    const checkpoint = props.participation.timeline.checkpoints[index];
    emit('progressUpdate', checkpoint.progress);
  }
};

const handleAccessibilityAction = (action: string, data: any) => {
  if (action === 'announce') {
    // Update ARIA live region with the announced data
    const liveRegion = document.querySelector('[aria-live="polite"]');
    if (liveRegion) {
      liveRegion.textContent = data.message;
    }
  }
};

// Watch for progress changes
watch(() => props.participation.progress, (newValue) => {
  if (newValue < 0 || newValue > 100) {
    emit('error', new Error('Invalid progress value'));
  }
});
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_mixins.scss';

.protocol-progress {
  width: 100%;
  
  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: spacing(4);
    
    @include respond-to('mobile') {
      flex-direction: column;
      align-items: flex-start;
      gap: spacing(2);
    }
  }

  .progress-title {
    font-family: $font-family-primary;
    font-size: map-get($font-weights, medium);
    color: color(gray, 900);
    margin: 0;
  }

  .progress-percentage {
    font-size: map-get($font-weights, bold);
    color: var(--progress-color, #{color(primary)});
    
    &.high-contrast {
      color: var(--progress-color, #{color(highContrast, primary)});
    }
  }

  .progress-timeline {
    height: 300px;
    margin: spacing(4) 0;
    
    @include respond-to('mobile') {
      height: 200px;
    }
  }

  .progress-details {
    margin-top: spacing(4);
    padding-top: spacing(4);
    border-top: 1px solid color(gray, 200);
  }

  .progress-metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: spacing(4);
    margin: 0;
    
    .metric-item {
      dt {
        font-size: map-get($font-weights, normal);
        color: color(gray, 600);
        margin-bottom: spacing(1);
      }
      
      dd {
        font-size: map-get($font-weights, medium);
        color: color(gray, 900);
        margin: 0;
      }
    }
  }
}

// Print styles
@media print {
  .protocol-progress {
    break-inside: avoid;
    
    .progress-timeline {
      height: 200px;
    }
  }
}
</style>