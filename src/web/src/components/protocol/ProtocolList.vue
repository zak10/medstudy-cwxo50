<template>
  <div 
    class="protocol-list" 
    role="region" 
    aria-label="Protocol List"
    data-testid="protocol-list"
  >
    <!-- Loading State -->
    <div v-if="loading" class="loading-skeleton" aria-busy="true">
      <div v-for="n in 6" :key="n" class="skeleton-card"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" role="alert" class="error-state">
      <p>{{ error }}</p>
      <BaseButton @click="fetchProtocols">Retry</BaseButton>
    </div>

    <!-- Protocol List Content -->
    <template v-else>
      <!-- Filter Section -->
      <ProtocolFilter
        :initial-filters="filters"
        :loading="loading"
        @filter-change="handleFilterChange"
      />

      <!-- Virtual Scrolling Protocol Grid -->
      <VirtualScroller
        class="protocol-grid"
        :items="displayedProtocols"
        :item-height="400"
        v-slot="{ item }"
      >
        <ProtocolCard
          :protocol="item"
          :show-progress="true"
          @view="handleProtocolSelect"
          @enroll="handleEnroll"
        />
      </VirtualScroller>

      <!-- Empty State -->
      <div 
        v-if="displayedProtocols.length === 0" 
        class="empty-state"
        role="status"
      >
        <p>No protocols found matching your criteria</p>
      </div>

      <!-- Pagination -->
      <div 
        v-if="displayedProtocols.length > 0"
        class="pagination"
        role="navigation"
        aria-label="Protocol list pagination"
      >
        <BaseButton
          variant="text"
          :disabled="filters.page === 1"
          @click="handlePageChange(filters.page - 1)"
          aria-label="Previous page"
        >
          Previous
        </BaseButton>
        <span class="page-info" role="status">
          Page {{ filters.page }} of {{ totalPages }}
        </span>
        <BaseButton
          variant="text"
          :disabled="filters.page === totalPages"
          @click="handlePageChange(filters.page + 1)"
          aria-label="Next page"
        >
          Next
        </BaseButton>
      </div>
    </template>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted, onUnmounted, watch } from 'vue'; // v3.3.0
import { debounce } from 'lodash-es'; // v4.17.21
import { VirtualScroller } from 'vue-virtual-scroller'; // v2.0.0
import ProtocolCard from './ProtocolCard.vue';
import ProtocolFilter from './ProtocolFilter.vue';
import BaseButton from '@/components/common/BaseButton.vue';
import { useProtocolStore } from '@/stores/protocol';
import type { Protocol } from '@/types/protocol';

export default defineComponent({
  name: 'ProtocolList',

  components: {
    ProtocolCard,
    ProtocolFilter,
    BaseButton,
    VirtualScroller,
  },

  setup() {
    const protocolStore = useProtocolStore();
    const error = ref<string | null>(null);
    const filters = ref({
      search: '',
      status: null,
      duration: null,
      page: 1,
      pageSize: 20,
    });

    // Computed properties
    const displayedProtocols = computed(() => {
      return protocolStore.filteredProtocols;
    });

    const totalPages = computed(() => {
      return protocolStore.totalPages;
    });

    const loading = computed(() => {
      return protocolStore.loading;
    });

    // Debounced filter handler
    const handleFilterChange = debounce((newFilters: typeof filters.value) => {
      filters.value = {
        ...filters.value,
        ...newFilters,
        page: 1, // Reset to first page on filter change
      };
      fetchProtocols();
    }, 300);

    // Page change handler
    const handlePageChange = (newPage: number) => {
      filters.value.page = newPage;
      fetchProtocols();
    };

    // Protocol selection handler
    const handleProtocolSelect = (protocol: Protocol) => {
      emit('protocol-selected', protocol);
    };

    // Enrollment handler
    const handleEnroll = async (protocolId: string) => {
      try {
        const success = await protocolStore.enroll(protocolId);
        if (success) {
          emit('enroll', protocolId);
        }
      } catch (err) {
        error.value = 'Failed to enroll in protocol';
      }
    };

    // Fetch protocols with error handling
    const fetchProtocols = async () => {
      try {
        error.value = null;
        await protocolStore.fetchProtocols();
      } catch (err) {
        error.value = 'Failed to load protocols';
      }
    };

    // Initialize real-time updates
    const initializeRealTimeUpdates = () => {
      const cleanup = protocolStore.subscribeToUpdates();
      return cleanup;
    };

    // Lifecycle hooks
    onMounted(() => {
      fetchProtocols();
      const cleanup = initializeRealTimeUpdates();
      onUnmounted(cleanup);
    });

    // Watch for store changes
    watch(() => protocolStore.protocols, () => {
      error.value = null;
    });

    return {
      displayedProtocols,
      totalPages,
      loading,
      error,
      filters,
      handleFilterChange,
      handlePageChange,
      handleProtocolSelect,
      handleEnroll,
      fetchProtocols,
    };
  },
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_mixins' as mixins;

.protocol-list {
  display: flex;
  flex-direction: column;
  gap: vars.spacing(6);
  min-height: 0;
  overflow: hidden;
}

.protocol-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: vars.spacing(4);
  container-type: inline-size;

  @container (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.loading-skeleton {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: vars.spacing(4);

  .skeleton-card {
    height: 400px;
    background: var(--color-skeleton);
    border-radius: 8px;
    animation: pulse 1.5s ease-in-out infinite;
  }
}

.empty-state {
  text-align: center;
  padding: vars.spacing(8);
  color: vars.color(gray, 600);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: vars.spacing(4);
  padding: vars.spacing(4) 0;

  .page-info {
    color: vars.color(gray, 600);
  }
}

@keyframes pulse {
  0% { opacity: 0.6; }
  50% { opacity: 0.8; }
  100% { opacity: 0.6; }
}

// Print styles
@media print {
  .protocol-list {
    gap: vars.spacing(4);
  }

  .protocol-grid {
    display: block;
  }

  .pagination,
  .loading-skeleton {
    display: none;
  }
}
</style>