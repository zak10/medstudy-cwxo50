<template>
  <div 
    class="protocol-details"
    role="main"
    aria-busy="loading"
  >
    <!-- Loading State -->
    <BaseCard v-if="loading" elevation="1">
      <div class="loading-skeleton">
        <div class="skeleton-title"></div>
        <div class="skeleton-content"></div>
      </div>
    </BaseCard>

    <!-- Error State -->
    <BaseCard v-else-if="error" elevation="1" class="error-card">
      <div class="error-message" role="alert">
        <h2>Error Loading Protocol</h2>
        <p>{{ error.message }}</p>
        <button 
          class="retry-button"
          @click="fetchProtocolDetails"
        >
          Retry
        </button>
      </div>
    </BaseCard>

    <!-- Protocol Content -->
    <template v-else-if="currentProtocol">
      <!-- Protocol Header -->
      <BaseCard elevation="2" class="protocol-header">
        <div class="header-content">
          <h1 class="protocol-title">{{ currentProtocol.title }}</h1>
          <div class="protocol-meta">
            <span class="participant-count">
              {{ currentProtocol.participantCount }} Participants
            </span>
            <span class="duration">
              {{ currentProtocol.duration }} Weeks
            </span>
          </div>
        </div>
        <div class="header-actions">
          <button
            v-if="!isEnrolled"
            class="enroll-button"
            :disabled="loading"
            @click="handleEnrollment"
            aria-label="Enroll in protocol"
          >
            Enroll Now
          </button>
          <div 
            v-else 
            class="enrolled-status"
            role="status"
          >
            Enrolled
          </div>
        </div>
      </BaseCard>

      <!-- Protocol Description -->
      <BaseCard elevation="1" class="protocol-description">
        <h2>Description</h2>
        <p>{{ currentProtocol.description }}</p>
      </BaseCard>

      <!-- Requirements Section -->
      <BaseCard elevation="1" class="protocol-requirements">
        <h2>Requirements</h2>
        <ul class="requirements-list">
          <li 
            v-for="req in currentProtocol.requirements"
            :key="req.id"
            class="requirement-item"
          >
            <div class="requirement-type">
              {{ formatRequirementType(req.type) }}
            </div>
            <div class="requirement-frequency">
              {{ formatFrequency(req.frequency) }}
            </div>
            <div 
              class="requirement-required"
              :class="{ required: req.required }"
            >
              {{ req.required ? 'Required' : 'Optional' }}
            </div>
          </li>
        </ul>
      </BaseCard>

      <!-- Safety Parameters -->
      <BaseCard elevation="1" class="protocol-safety">
        <h2>Safety Parameters</h2>
        <div class="safety-parameters">
          <div 
            v-for="param in currentProtocol.safetyParams"
            :key="param.id"
            class="safety-param"
          >
            <h3>{{ param.metric }}</h3>
            <div class="param-details">
              <div class="param-range">
                <span v-if="param.minValue">Min: {{ param.minValue }} {{ param.unit }}</span>
                <span v-if="param.maxValue">Max: {{ param.maxValue }} {{ param.unit }}</span>
              </div>
              <div 
                v-if="param.warningThreshold"
                class="param-threshold warning"
              >
                Warning at: {{ param.warningThreshold }} {{ param.unit }}
              </div>
              <div 
                v-if="param.criticalThreshold"
                class="param-threshold critical"
              >
                Critical at: {{ param.criticalThreshold }} {{ param.unit }}
              </div>
            </div>
          </div>
        </div>
      </BaseCard>

      <!-- Progress Tracking (if enrolled) -->
      <ProtocolProgress
        v-if="isEnrolled"
        :participation="participation"
        :show-details="true"
        @progressUpdate="handleProgressUpdate"
        @error="handleProgressError"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useProtocolStore } from '@/stores/protocol';
import { useUiStore } from '@/stores/ui';
import type { Protocol } from '@/types/protocol';
import BaseCard from '@/components/common/BaseCard.vue';
import ProtocolProgress from '@/components/protocol/ProtocolProgress.vue';

// Store initialization
const protocolStore = useProtocolStore();
const uiStore = useUiStore();
const route = useRoute();

// Local state
const error = ref<Error | null>(null);
const participation = ref<any>(null);
const loading = computed(() => protocolStore.loading);
const currentProtocol = computed(() => protocolStore.currentProtocol);

// Computed properties
const protocolId = computed(() => {
  const id = route.params.id;
  if (!id || typeof id !== 'string') {
    throw new Error('Invalid protocol ID');
  }
  return id;
});

const isEnrolled = computed(() => {
  return participation.value !== null;
});

// Methods
const formatRequirementType = (type: string): string => {
  return type.replace('_', ' ').toLowerCase()
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

const formatFrequency = (frequency: string): string => {
  return frequency.toLowerCase()
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

const fetchProtocolDetails = async () => {
  try {
    error.value = null;
    await protocolStore.fetchProtocolById(protocolId.value);
  } catch (err) {
    error.value = err as Error;
    uiStore.notifyError('Failed to load protocol details');
  }
};

const handleEnrollment = async () => {
  try {
    if (!currentProtocol.value) return;

    const confirmed = await uiStore.confirm({
      title: 'Confirm Enrollment',
      message: 'Are you sure you want to enroll in this protocol?',
      confirmText: 'Enroll',
      cancelText: 'Cancel'
    });

    if (confirmed) {
      const success = await protocolStore.enroll(protocolId.value);
      if (success) {
        uiStore.notifySuccess('Successfully enrolled in protocol');
        await fetchProtocolDetails();
      }
    }
  } catch (err) {
    uiStore.notifyError('Failed to enroll in protocol');
    console.error('Enrollment error:', err);
  }
};

const handleProgressUpdate = (newProgress: number) => {
  if (participation.value) {
    participation.value.progress = newProgress;
  }
};

const handleProgressError = (error: Error) => {
  uiStore.notifyError(`Progress update error: ${error.message}`);
};

// Lifecycle hooks
onMounted(async () => {
  await fetchProtocolDetails();
});
</script>

<style lang="scss" scoped>
@import '@/assets/styles/_variables.scss';
@import '@/assets/styles/_mixins.scss';

.protocol-details {
  max-width: $container-max-width;
  margin: 0 auto;
  padding: spacing(4);
  
  @include respond-to('mobile') {
    padding: spacing(2);
  }
}

.protocol-header {
  margin-bottom: spacing(4);
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    
    @include respond-to('mobile') {
      flex-direction: column;
      gap: spacing(2);
    }
  }
  
  .protocol-title {
    font-family: $font-family-primary;
    font-size: 2rem;
    font-weight: map-get($font-weights, bold);
    color: color(gray, 900);
    margin: 0;
  }
  
  .protocol-meta {
    display: flex;
    gap: spacing(4);
    color: color(gray, 600);
  }
}

.enroll-button {
  @include button-base(primary);
}

.requirements-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: spacing(3);
  
  .requirement-item {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr;
    align-items: center;
    padding: spacing(2);
    background-color: color(gray, 50);
    border-radius: 6px;
    
    @include respond-to('mobile') {
      grid-template-columns: 1fr;
      gap: spacing(1);
    }
  }
}

.safety-parameters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: spacing(4);
  
  .safety-param {
    @include card;
    padding: spacing(3);
    
    h3 {
      margin: 0 0 spacing(2) 0;
      color: color(gray, 900);
    }
  }
  
  .param-threshold {
    margin-top: spacing(2);
    padding: spacing(1) spacing(2);
    border-radius: 4px;
    font-size: 0.875rem;
    
    &.warning {
      background-color: rgba(color(warning), 0.1);
      color: darken(color(warning), 20%);
    }
    
    &.critical {
      background-color: rgba(color(error), 0.1);
      color: darken(color(error), 20%);
    }
  }
}

// Loading skeleton styles
.loading-skeleton {
  .skeleton-title {
    height: 2rem;
    width: 60%;
    background: linear-gradient(90deg, color(gray, 100) 25%, color(gray, 200) 50%, color(gray, 100) 75%);
    background-size: 200% 100%;
    animation: loading 1.5s infinite;
    border-radius: 4px;
  }
  
  .skeleton-content {
    margin-top: spacing(4);
    height: 200px;
    background: linear-gradient(90deg, color(gray, 100) 25%, color(gray, 200) 50%, color(gray, 100) 75%);
    background-size: 200% 100%;
    animation: loading 1.5s infinite;
    border-radius: 4px;
  }
}

@keyframes loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

// Print styles
@media print {
  .protocol-details {
    padding: 0;
  }
  
  .enroll-button {
    display: none;
  }
}
</style>