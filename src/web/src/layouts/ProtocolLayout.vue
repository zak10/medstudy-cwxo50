<template>
  <div 
    class="protocol-layout"
    :class="layoutClasses"
    role="main"
    aria-label="Protocol page layout"
  >
    <!-- Main Navigation Header -->
    <AppHeader class="protocol-layout__header" />

    <!-- Enhanced Sidebar with Mobile Support -->
    <AppSidebar
      class="protocol-layout__sidebar"
      :is-open="sidebarState.isOpen"
      @sidebar-toggle="handleSidebarToggle"
      @touchstart="handleTouchStart"
      @touchmove="handleTouchMove"
      @touchend="handleTouchEnd"
    />

    <!-- Main Content Area with Focus Management -->
    <main 
      class="protocol-layout__content"
      :class="{ 'with-sidebar': sidebarState.isOpen }"
      ref="mainContent"
      tabindex="-1"
    >
      <!-- Protocol Progress Component -->
      <ProtocolProgress
        v-if="showProgress"
        :participation="currentParticipation"
        :show-details="true"
        :aria-label="'Protocol progress tracking'"
      />

      <!-- Router View for Protocol Pages -->
      <router-view v-slot="{ Component }">
        <transition
          name="fade"
          mode="out-in"
          @enter="handleTransitionEnter"
          @leave="handleTransitionLeave"
        >
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- Mobile Sidebar Overlay -->
    <div 
      v-if="showOverlay"
      class="protocol-layout__overlay"
      aria-hidden="true"
      @click="handleSidebarToggle(false)"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'; // v3.3.0
import AppHeader from '@/components/common/AppHeader.vue';
import AppSidebar from '@/components/common/AppSidebar.vue';
import ProtocolProgress from '@/components/protocol/ProtocolProgress.vue';
import { useUiStore } from '@/stores/ui';

// Component state
const mainContent = ref<HTMLElement | null>(null);
const touchStartX = ref(0);
const touchDeltaX = ref(0);
const showOverlay = ref(false);
const showProgress = ref(true);
const currentParticipation = ref({});

// UI store for responsive state
const uiStore = useUiStore();

// Sidebar state management
const sidebarState = ref({
  isOpen: localStorage.getItem('sidebarOpen') === 'true',
  isAnimating: false,
  touchThreshold: 50
});

// Computed classes for dynamic styling
const layoutClasses = computed(() => ({
  'is-mobile': uiStore.currentBreakpoint === 'mobile',
  'sidebar-open': sidebarState.value.isOpen,
  'is-animating': sidebarState.value.isAnimating,
  'reduced-motion': uiStore.reducedMotion
}));

// Touch interaction handlers
const handleTouchStart = (event: TouchEvent) => {
  if (uiStore.currentBreakpoint !== 'mobile') return;
  touchStartX.value = event.touches[0].clientX;
  touchDeltaX.value = 0;
};

const handleTouchMove = (event: TouchEvent) => {
  if (uiStore.currentBreakpoint !== 'mobile') return;
  touchDeltaX.value = event.touches[0].clientX - touchStartX.value;
};

const handleTouchEnd = () => {
  if (Math.abs(touchDeltaX.value) > sidebarState.value.touchThreshold) {
    handleSidebarToggle(touchDeltaX.value > 0);
  }
  touchDeltaX.value = 0;
};

// Sidebar toggle with animation handling
const handleSidebarToggle = (force?: boolean) => {
  const newState = force !== undefined ? force : !sidebarState.value.isOpen;
  
  sidebarState.value.isAnimating = true;
  sidebarState.value.isOpen = newState;
  
  // Persist sidebar state for desktop
  if (uiStore.currentBreakpoint !== 'mobile') {
    localStorage.setItem('sidebarOpen', newState.toString());
  }
  
  // Update overlay state for mobile
  showOverlay.value = newState && uiStore.currentBreakpoint === 'mobile';
  
  // Handle focus management
  if (!newState && mainContent.value) {
    mainContent.value.focus();
  }
  
  // Reset animation state
  setTimeout(() => {
    sidebarState.value.isAnimating = false;
  }, 300);
};

// Transition handlers
const handleTransitionEnter = (el: Element) => {
  el.setAttribute('tabindex', '-1');
  (el as HTMLElement).focus();
};

const handleTransitionLeave = (el: Element) => {
  el.removeAttribute('tabindex');
};

// Keyboard navigation
const handleKeyboardNavigation = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && sidebarState.value.isOpen && uiStore.currentBreakpoint === 'mobile') {
    handleSidebarToggle(false);
  }
};

// Lifecycle hooks
onMounted(() => {
  window.addEventListener('keydown', handleKeyboardNavigation);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyboardNavigation);
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;
@use '@/assets/styles/_breakpoints' as breakpoints;

.protocol-layout {
  display: grid;
  grid-template-areas:
    "header header"
    "sidebar main";
  grid-template-rows: 64px 1fr;
  grid-template-columns: auto 1fr;
  min-height: 100vh;
  background-color: vars.color(gray, 50);

  // Header styling
  &__header {
    grid-area: header;
    position: sticky;
    top: 0;
    z-index: vars.$z-index-header;
  }

  // Sidebar styling
  &__sidebar {
    grid-area: sidebar;
    width: 240px;
    transition: transform 0.3s ease;

    @include breakpoints.respond-to('mobile') {
      position: fixed;
      left: 0;
      height: calc(100vh - 64px);
      transform: translateX(-100%);
    }
  }

  // Main content styling
  &__content {
    grid-area: main;
    padding: vars.spacing(4);
    overflow-y: auto;
    transition: margin-left 0.3s ease;

    &:focus {
      outline: none;
    }

    &.with-sidebar {
      @include breakpoints.respond-to('desktop') {
        margin-left: 240px;
      }
    }
  }

  // Overlay styling
  &__overlay {
    display: none;
    position: fixed;
    top: 64px;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: vars.$z-index-overlay;
    transition: opacity 0.3s ease;
  }

  // Mobile-specific styles
  &.is-mobile {
    grid-template-areas:
      "header"
      "main";
    grid-template-columns: 1fr;

    .protocol-layout__overlay {
      display: block;
    }
  }

  // Animation states
  &.is-animating {
    .protocol-layout__sidebar,
    .protocol-layout__content,
    .protocol-layout__overlay {
      transition: all 0.3s ease;
    }
  }

  // Reduced motion support
  &.reduced-motion {
    .protocol-layout__sidebar,
    .protocol-layout__content,
    .protocol-layout__overlay {
      transition: none;
    }
  }
}

// Transition animations
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// Print styles
@media print {
  .protocol-layout {
    display: block;
    
    &__header,
    &__sidebar,
    &__overlay {
      display: none;
    }

    &__content {
      margin: 0;
      padding: 0;
    }
  }
}
</style>