<template>
  <div 
    class="data-collection-page"
    role="main"
    aria-labelledby="page-title"
  >
    <h1 id="page-title" class="page-title">Protocol Data Collection</h1>

    <!-- Loading State -->
    <LoadingSpinner
      v-if="dataStore.loading"
      size="large"
      color="primary"
      class="page-loader"
    />

    <!-- Error Alert -->
    <div 
      v-if="error"
      class="error-alert"
      role="alert"
    >
      <p>{{ error.message }}</p>
      <BaseButton
        variant="secondary"
        size="sm"
        @click="loadProtocolData"
      >
        Retry
      </BaseButton>
    </div>

    <!-- Forms Container -->
    <div class="forms-container">
      <!-- Blood Work Form -->
      <section class="form-section">
        <h2>Blood Work Data</h2>
        <BloodworkForm
          :protocol-id="protocolId"
          @submitted="handleBloodWorkSubmitted"
        />
      </section>

      <!-- Check-in Form -->
      <section class="form-section">
        <h2>Weekly Check-in</h2>
        <CheckInForm
          :protocol-id="protocolId"
          @submitted="handleCheckInSubmitted"
        />
      </section>
    </div>

    <!-- Data Points List -->
    <section class="data-points-section">
      <h2>Submitted Data Points</h2>
      <DataPointList
        :protocol-id="protocolId"
        @error="handleDataPointError"
      />
    </section>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from 'vue'; // v3.3.0
import { useRoute } from 'vue-router'; // v4.2.0

// Internal imports
import BloodworkForm from '@/components/data/BloodworkForm.vue';
import CheckInForm from '@/components/data/CheckInForm.vue';
import DataPointList from '@/components/data/DataPointList.vue';
import LoadingSpinner from '@/components/common/LoadingSpinner.vue';
import BaseButton from '@/components/common/BaseButton.vue';
import useDataCollection from '@/composables/useDataCollection';
import useDataStore from '@/stores/data';
import { BloodWorkData, CheckInData } from '@/types/data';
import { theme } from '@/config/theme';

export default defineComponent({
  name: 'DataCollection',

  components: {
    BloodworkForm,
    CheckInForm,
    DataPointList,
    LoadingSpinner,
    BaseButton
  },

  setup() {
    const route = useRoute();
    const dataStore = useDataStore();
    const error = ref<Error | null>(null);

    // Get protocol ID from route params
    const protocolId = route.params.protocolId as string;

    // Initialize data collection composable
    const { submitBloodWork, submitCheckIn } = useDataCollection(protocolId);

    // Handle blood work submission
    const handleBloodWorkSubmitted = async (data: BloodWorkData) => {
      try {
        error.value = null;
        await submitBloodWork(data);
        await dataStore.fetchDataPoints({ protocolId });
      } catch (err) {
        error.value = err as Error;
        console.error('Blood work submission error:', err);
      }
    };

    // Handle check-in submission
    const handleCheckInSubmitted = async (data: CheckInData) => {
      try {
        error.value = null;
        await submitCheckIn(data);
        await dataStore.fetchDataPoints({ protocolId });
      } catch (err) {
        error.value = err as Error;
        console.error('Check-in submission error:', err);
      }
    };

    // Handle data point list errors
    const handleDataPointError = (err: Error) => {
      error.value = err;
      console.error('Data points error:', err);
    };

    // Load initial protocol data
    const loadProtocolData = async () => {
      try {
        error.value = null;
        await dataStore.fetchDataPoints({ protocolId });
      } catch (err) {
        error.value = err as Error;
        console.error('Failed to load protocol data:', err);
      }
    };

    // Load data on component mount
    onMounted(loadProtocolData);

    return {
      protocolId,
      dataStore,
      error,
      handleBloodWorkSubmitted,
      handleCheckInSubmitted,
      handleDataPointError,
      loadProtocolData
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.data-collection-page {
  max-width: vars.$container-max-width;
  margin: 0 auto;
  padding: vars.spacing(4);
  display: flex;
  flex-direction: column;
  gap: vars.spacing(6);

  .page-title {
    font-family: vars.$font-family-primary;
    font-size: vars.typography-scale(h1);
    color: color(primary);
    margin-bottom: vars.spacing(6);
  }

  .page-loader {
    align-self: center;
    margin: vars.spacing(8) 0;
  }

  .error-alert {
    background-color: color(error, 50);
    border: 1px solid color(error, 200);
    border-radius: 4px;
    padding: vars.spacing(4);
    margin-bottom: vars.spacing(4);
    color: color(error, 700);

    p {
      margin-bottom: vars.spacing(2);
    }
  }

  .forms-container {
    display: grid;
    gap: vars.spacing(6);

    @media (min-width: map-get(vars.$breakpoints, desktop)) {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  .form-section {
    background-color: white;
    border-radius: 8px;
    box-shadow: map-get(vars.$elevation-levels, 2);
    padding: vars.spacing(4);

    h2 {
      font-family: vars.$font-family-primary;
      font-size: vars.typography-scale(h2);
      color: color(primary);
      margin-bottom: vars.spacing(4);
    }
  }

  .data-points-section {
    margin-top: vars.spacing(6);

    h2 {
      font-family: vars.$font-family-primary;
      font-size: vars.typography-scale(h2);
      color: color(primary);
      margin-bottom: vars.spacing(4);
    }
  }

  @media (max-width: map-get(vars.$breakpoints, tablet)) {
    padding: vars.spacing(2);
  }
}
</style>