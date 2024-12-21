<template>
  <DefaultLayout>
    <!-- Error Boundary for component-level error handling -->
    <ErrorBoundary @error="handleError">
      <!-- Dashboard Header -->
      <header class="dashboard-header">
        <h1 class="dashboard-title">Dashboard</h1>
        <p v-if="activeProtocols.length" class="dashboard-subtitle">
          You are currently participating in {{ activeProtocols.length }} 
          {{ activeProtocols.length === 1 ? 'protocol' : 'protocols' }}
        </p>
      </header>

      <!-- Loading State -->
      <LoadingSpinner 
        v-if="loading" 
        size="large" 
        :label="'Loading dashboard data'"
      />

      <!-- Error State -->
      <div 
        v-else-if="error" 
        class="error-state" 
        role="alert"
        aria-live="polite"
      >
        <p>{{ error.message }}</p>
        <BaseButton 
          variant="primary" 
          @click="fetchDashboardData"
        >
          Retry
        </BaseButton>
      </div>

      <!-- Dashboard Content -->
      <div v-else class="dashboard-content">
        <!-- Active Protocols Section -->
        <section 
          class="protocols-section"
          aria-labelledby="protocols-heading"
        >
          <h2 id="protocols-heading" class="section-title">Active Protocols</h2>
          <div class="protocols-grid">
            <ProtocolCard
              v-for="protocol in activeProtocols"
              :key="protocol.id"
              :protocol="protocol"
              :show-progress="true"
              :loading="loadingStates[protocol.id]"
              @view="navigateToProtocol"
              @error="handleProtocolError"
            />
          </div>
          <p v-if="!activeProtocols.length" class="empty-state">
            You are not currently enrolled in any protocols.
            <router-link to="/protocols">Browse available protocols</router-link>
          </p>
        </section>

        <!-- Pending Data Submissions Section -->
        <section 
          class="submissions-section"
          aria-labelledby="submissions-heading"
        >
          <h2 id="submissions-heading" class="section-title">Pending Submissions</h2>
          <div class="submissions-list">
            <div 
              v-for="(submissions, protocolId) in pendingDataPoints" 
              :key="protocolId"
              class="submission-group"
            >
              <h3 class="protocol-name">{{ getProtocolName(protocolId) }}</h3>
              <ul class="submission-items">
                <li 
                  v-for="submission in submissions" 
                  :key="submission.id"
                  class="submission-item"
                >
                  <span class="submission-type">{{ submission.type }}</span>
                  <span class="submission-due">Due: {{ formatDate(submission.dueDate) }}</span>
                  <BaseButton
                    variant="primary"
                    size="sm"
                    :to="`/data/submission/${protocolId}`"
                  >
                    Submit Data
                  </BaseButton>
                </li>
              </ul>
            </div>
            <p v-if="!hasPendingSubmissions" class="empty-state">
              No pending data submissions.
            </p>
          </div>
        </section>
      </div>
    </ErrorBoundary>
  </DefaultLayout>
</template>

<script lang="ts">
import { defineComponent, onMounted, computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { format } from 'date-fns';

// Component imports
import DefaultLayout from '@/layouts/DefaultLayout.vue';
import ProtocolCard from '@/components/protocol/ProtocolCard.vue';
import BaseButton from '@/components/common/BaseButton.vue';
import LoadingSpinner from '@/components/common/LoadingSpinner.vue';
import ErrorBoundary from '@/components/common/ErrorBoundary.vue';

// Store imports
import { useProtocolStore } from '@/stores/protocol';
import { useDataStore } from '@/stores/data';
import { useUiStore } from '@/stores/ui';

export default defineComponent({
  name: 'Dashboard',

  components: {
    DefaultLayout,
    ProtocolCard,
    BaseButton,
    LoadingSpinner,
    ErrorBoundary
  },

  setup() {
    const router = useRouter();
    const protocolStore = useProtocolStore();
    const dataStore = useDataStore();
    const uiStore = useUiStore();

    // Component state
    const loading = ref(false);
    const error = ref<Error | null>(null);
    const loadingStates = ref<Record<string, boolean>>({});

    // Computed properties
    const activeProtocols = computed(() => protocolStore.activeProtocols);
    
    const pendingDataPoints = computed(() => 
      dataStore.dataPoints.reduce((acc, point) => {
        if (point.status === 'pending') {
          if (!acc[point.protocolId]) {
            acc[point.protocolId] = [];
          }
          acc[point.protocolId].push(point);
        }
        return acc;
      }, {} as Record<string, any[]>)
    );

    const hasPendingSubmissions = computed(() => 
      Object.keys(pendingDataPoints.value).length > 0
    );

    // Methods
    const fetchDashboardData = async () => {
      try {
        loading.value = true;
        error.value = null;

        await Promise.all([
          protocolStore.fetchProtocols(),
          dataStore.fetchDataPoints()
        ]);
      } catch (err) {
        error.value = err as Error;
        uiStore.notifyError('Failed to load dashboard data');
      } finally {
        loading.value = false;
      }
    };

    const navigateToProtocol = async (protocolId: string) => {
      try {
        loadingStates.value[protocolId] = true;
        await router.push(`/protocols/${protocolId}`);
      } catch (err) {
        uiStore.notifyError('Failed to navigate to protocol');
      } finally {
        loadingStates.value[protocolId] = false;
      }
    };

    const handleError = (error: Error) => {
      console.error('Dashboard error:', error);
      uiStore.notifyError('An error occurred in the dashboard');
    };

    const handleProtocolError = (error: Error) => {
      console.error('Protocol error:', error);
      uiStore.notifyError('An error occurred while loading protocol data');
    };

    const getProtocolName = (protocolId: string) => {
      const protocol = protocolStore.protocols.find(p => p.id === protocolId);
      return protocol?.title || 'Unknown Protocol';
    };

    const formatDate = (date: Date) => {
      return format(date, 'MMM d, yyyy');
    };

    // Lifecycle hooks
    onMounted(() => {
      fetchDashboardData();
    });

    return {
      // State
      loading,
      error,
      loadingStates,

      // Computed
      activeProtocols,
      pendingDataPoints,
      hasPendingSubmissions,

      // Methods
      fetchDashboardData,
      navigateToProtocol,
      handleError,
      handleProtocolError,
      getProtocolName,
      formatDate
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_mixins' as mixins;

.dashboard-header {
  margin-bottom: vars.spacing(6);

  .dashboard-title {
    font-family: vars.$font-family-primary;
    font-size: 2rem;
    font-weight: map-get(vars.$font-weights, bold);
    color: vars.color(gray, 900);
    margin: 0 0 vars.spacing(2);
  }

  .dashboard-subtitle {
    font-size: 1.125rem;
    color: vars.color(gray, 600);
    margin: 0;
  }
}

.section-title {
  font-family: vars.$font-family-primary;
  font-size: 1.5rem;
  font-weight: map-get(vars.$font-weights, semibold);
  color: vars.color(gray, 900);
  margin: 0 0 vars.spacing(4);
}

.protocols-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: vars.spacing(4);
  margin-bottom: vars.spacing(6);

  @include mixins.respond-to('mobile') {
    grid-template-columns: 1fr;
  }
}

.submissions-list {
  .submission-group {
    margin-bottom: vars.spacing(4);

    .protocol-name {
      font-size: 1.125rem;
      font-weight: map-get(vars.$font-weights, medium);
      margin-bottom: vars.spacing(2);
    }
  }

  .submission-items {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .submission-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: vars.spacing(3);
    background-color: vars.color(gray, 50);
    border-radius: 8px;
    margin-bottom: vars.spacing(2);

    .submission-type {
      font-weight: map-get(vars.$font-weights, medium);
    }

    .submission-due {
      color: vars.color(gray, 600);
    }
  }
}

.error-state {
  padding: vars.spacing(4);
  background-color: vars.color(error, 50);
  border-radius: 8px;
  margin-bottom: vars.spacing(4);

  p {
    color: vars.color(error);
    margin: 0 0 vars.spacing(3);
  }
}

.empty-state {
  text-align: center;
  color: vars.color(gray, 600);
  padding: vars.spacing(6);
  background-color: vars.color(gray, 50);
  border-radius: 8px;

  a {
    color: vars.color(primary);
    text-decoration: none;
    margin-left: vars.spacing(1);

    &:hover {
      text-decoration: underline;
    }
  }
}

// Print styles
@media print {
  .dashboard-content {
    display: block;
  }

  .protocols-grid {
    display: block;
  }

  .submission-item {
    break-inside: avoid;
  }
}
</style>