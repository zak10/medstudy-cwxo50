<template>
  <div 
    class="protocol-browse" 
    role="main" 
    aria-label="Protocol Browser"
    data-testid="protocol-browse"
  >
    <!-- Page Header -->
    <header class="protocol-browse__header">
      <h1>Browse Protocols</h1>
      <p class="protocol-browse__description">
        Discover and join community-driven medical research protocols
      </p>
    </header>

    <!-- Protocol Filter -->
    <ProtocolFilter
      :initial-filters="activeFilters"
      :loading="loading"
      @filter-change="handleFilterChange"
      ref="filterRef"
    />

    <!-- Loading State -->
    <div 
      v-if="loading" 
      class="protocol-browse__loading"
      role="status"
      aria-busy="true"
    >
      <LoadingSpinner size="large" />
      <span class="sr-only">Loading protocols...</span>
    </div>

    <!-- Error State -->
    <div 
      v-else-if="error"
      class="protocol-browse__error"
      role="alert"
    >
      <p>{{ error }}</p>
      <BaseButton @click="retryFetch">Retry</BaseButton>
    </div>

    <!-- Protocol List -->
    <ProtocolList
      v-else
      :protocols="filteredProtocols"
      :loading="loading"
      @protocol-selected="handleProtocolSelect"
      @enroll="handleEnroll"
    />

    <!-- Empty State -->
    <div 
      v-if="!loading && filteredProtocols.length === 0"
      class="protocol-browse__empty"
      role="status"
    >
      <p>No protocols found matching your criteria</p>
      <BaseButton @click="resetFilters">Reset Filters</BaseButton>
    </div>

    <!-- Pagination -->
    <div 
      v-if="totalPages > 1"
      class="protocol-browse__pagination"
      role="navigation"
      aria-label="Protocol list pagination"
    >
      <BaseButton
        variant="text"
        :disabled="currentPage === 1"
        @click="handlePageChange(currentPage - 1)"
        aria-label="Previous page"
      >
        Previous
      </BaseButton>
      <span class="pagination__info">
        Page {{ currentPage }} of {{ totalPages }}
      </span>
      <BaseButton
        variant="text"
        :disabled="currentPage === totalPages"
        @click="handlePageChange(currentPage + 1)"
        aria-label="Next page"
      >
        Next
      </BaseButton>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onUnmounted, watch } from 'vue';
import { debounce } from 'lodash-es';
import ProtocolList from '@/components/protocol/ProtocolList.vue';
import ProtocolFilter from '@/components/protocol/ProtocolFilter.vue';
import BaseButton from '@/components/common/BaseButton.vue';
import LoadingSpinner from '@/components/common/LoadingSpinner.vue';
import { useProtocolStore } from '@/stores/protocol';
import { useNotification } from '@/composables/useNotification';
import type { Protocol } from '@/types/protocol';

export default defineComponent({
  name: 'ProtocolBrowse',

  components: {
    ProtocolList,
    ProtocolFilter,
    BaseButton,
    LoadingSpinner
  },

  setup() {
    const protocolStore = useProtocolStore();
    const { showNotification } = useNotification();
    const filterRef = ref<InstanceType<typeof ProtocolFilter> | null>(null);

    // State
    const error = ref<string | null>(null);
    const currentPage = ref(1);
    const activeFilters = ref({
      search: '',
      status: null,
      duration: null
    });

    // Computed from store
    const loading = computed(() => protocolStore.loading);
    const filteredProtocols = computed(() => protocolStore.filteredProtocols);
    const totalPages = computed(() => protocolStore.totalPages);

    // Debounced filter handler
    const handleFilterChange = debounce((filters: typeof activeFilters.value) => {
      activeFilters.value = filters;
      currentPage.value = 1;
      fetchProtocols();
    }, 300);

    // Page change handler
    const handlePageChange = (page: number) => {
      currentPage.value = page;
      fetchProtocols();
    };

    // Protocol selection handler
    const handleProtocolSelect = (protocol: Protocol) => {
      router.push(`/protocols/${protocol.id}`);
    };

    // Enrollment handler
    const handleEnroll = async (protocolId: string) => {
      try {
        const success = await protocolStore.enroll(protocolId);
        if (success) {
          showNotification('success', 'Successfully enrolled in protocol');
        }
      } catch (err) {
        showNotification('error', 'Failed to enroll in protocol');
        console.error('Enrollment error:', err);
      }
    };

    // Reset filters
    const resetFilters = () => {
      if (filterRef.value) {
        filterRef.value.reset();
      }
      activeFilters.value = {
        search: '',
        status: null,
        duration: null
      };
      currentPage.value = 1;
      fetchProtocols();
    };

    // Fetch protocols with error handling
    const fetchProtocols = async () => {
      try {
        error.value = null;
        await protocolStore.fetchProtocols({
          page: currentPage.value,
          ...activeFilters.value
        });
      } catch (err) {
        error.value = 'Failed to load protocols';
        console.error('Protocol fetch error:', err);
      }
    };

    // Retry fetch handler
    const retryFetch = () => {
      error.value = null;
      fetchProtocols();
    };

    // Setup real-time updates
    const setupRealTimeUpdates = () => {
      const cleanup = protocolStore.subscribeToUpdates();
      return cleanup;
    };

    // Lifecycle hooks
    onMounted(() => {
      fetchProtocols();
      const cleanup = setupRealTimeUpdates();
      onUnmounted(cleanup);
    });

    // Watch for store changes
    watch(() => protocolStore.protocols, () => {
      error.value = null;
    });

    return {
      // State
      error,
      loading,
      currentPage,
      activeFilters,
      filteredProtocols,
      totalPages,
      filterRef,

      // Methods
      handleFilterChange,
      handlePageChange,
      handleProtocolSelect,
      handleEnroll,
      resetFilters,
      retryFetch
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_mixins' as mixins;

.protocol-browse {
  padding: vars.spacing(6);
  max-width: vars.$container-max-width;
  margin: 0 auto;
  min-height: 100vh;

  &__header {
    margin-bottom: vars.spacing(6);

    h1 {
      font-family: vars.$font-family-primary;
      font-size: vars.typography(h1);
      color: vars.color(gray, 900);
      margin-bottom: vars.spacing(2);
    }

    &__description {
      color: vars.color(gray, 600);
      font-size: vars.typography(body);
    }
  }

  &__loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: vars.spacing(8);
  }

  &__error {
    background-color: vars.color(error, 50);
    border: 1px solid vars.color(error);
    border-radius: vars.spacing(2);
    padding: vars.spacing(4);
    margin: vars.spacing(4) 0;
    text-align: center;

    p {
      color: vars.color(error);
      margin-bottom: vars.spacing(3);
    }
  }

  &__empty {
    text-align: center;
    padding: vars.spacing(8);
    color: vars.color(gray, 600);
  }

  &__pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: vars.spacing(4);
    margin-top: vars.spacing(6);

    .pagination__info {
      color: vars.color(gray, 600);
    }
  }

  // Responsive adjustments
  @include mixins.respond-to('mobile') {
    padding: vars.spacing(4);

    &__header {
      margin-bottom: vars.spacing(4);
    }
  }
}

// Print styles
@media print {
  .protocol-browse {
    padding: 0;

    &__pagination,
    &__loading {
      display: none;
    }
  }
}
</style>