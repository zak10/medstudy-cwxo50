<template>
  <!-- Skip link for keyboard navigation -->
  <a 
    href="#main-content" 
    class="skip-link"
    @click.prevent="skipToContent"
  >
    Skip to main content
  </a>

  <div 
    class="app-layout"
    :class="layoutClasses"
    role="application"
    @keydown="handleKeyboardNavigation"
  >
    <ErrorBoundary @error="handleLayoutError">
      <!-- Header Section -->
      <AppHeader
        @menu-toggle="handleSidebarToggle"
        aria-label="Main header"
      />

      <!-- Main Layout Container -->
      <div class="layout-container">
        <!-- Sidebar Navigation -->
        <AppSidebar
          :is-open="isSidebarOpen"
          @sidebar-toggle="handleSidebarToggle"
          aria-label="Main navigation"
        />

        <!-- Main Content Area -->
        <main 
          id="main-content"
          class="main-content"
          :style="mainContentStyles"
          role="main"
          aria-label="Main content"
        >
          <!-- Live Region for Dynamic Updates -->
          <div 
            class="sr-only" 
            role="status" 
            aria-live="polite"
            ref="announcer"
          ></div>

          <!-- Router View with Error Boundary -->
          <ErrorBoundary>
            <router-view v-slot="{ Component }">
              <transition 
                name="fade" 
                mode="out-in"
                @before-enter="handleTransitionStart"
                @after-leave="handleTransitionEnd"
              >
                <component :is="Component" />
              </transition>
            </router-view>
          </ErrorBoundary>
        </main>
      </div>

      <!-- Footer Section -->
      <AppFooter aria-label="Page footer" />
    </ErrorBoundary>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted, onUnmounted } from 'vue'
import { useUiStore } from '@/stores/ui'
import AppHeader from '@/components/common/AppHeader.vue'
import AppSidebar from '@/components/common/AppSidebar.vue'
import AppFooter from '@/components/common/AppFooter.vue'
import ErrorBoundary from '@/components/common/ErrorBoundary.vue'

export default defineComponent({
  name: 'DefaultLayout',

  components: {
    AppHeader,
    AppSidebar,
    AppFooter,
    ErrorBoundary
  },

  setup() {
    const uiStore = useUiStore()
    const isSidebarOpen = ref(localStorage.getItem('sidebarOpen') === 'true')
    const announcer = ref<HTMLElement | null>(null)
    const isTransitioning = ref(false)

    // Computed properties
    const layoutClasses = computed(() => ({
      'sidebar-open': isSidebarOpen.value,
      'sidebar-closed': !isSidebarOpen.value,
      'is-mobile': uiStore.currentBreakpoint === 'mobile',
      'reduced-motion': window.matchMedia('(prefers-reduced-motion: reduce)').matches
    }))

    const mainContentStyles = computed(() => ({
      marginLeft: isSidebarOpen.value && !uiStore.currentBreakpoint === 'mobile' ? '240px' : '0',
      transition: layoutClasses.value['reduced-motion'] ? 'none' : 'margin-left 0.3s ease'
    }))

    // Methods
    const handleSidebarToggle = () => {
      isSidebarOpen.value = !isSidebarOpen.value
      localStorage.setItem('sidebarOpen', isSidebarOpen.value.toString())
      
      // Announce sidebar state for screen readers
      if (announcer.value) {
        announcer.value.textContent = `Sidebar ${isSidebarOpen.value ? 'opened' : 'closed'}`
      }
    }

    const handleKeyboardNavigation = (event: KeyboardEvent) => {
      // Handle keyboard shortcuts
      if (event.altKey && event.key === 'n') {
        event.preventDefault()
        handleSidebarToggle()
      }

      // Handle escape key for closing sidebar on mobile
      if (event.key === 'Escape' && isSidebarOpen.value && uiStore.currentBreakpoint === 'mobile') {
        handleSidebarToggle()
      }
    }

    const skipToContent = () => {
      const mainContent = document.getElementById('main-content')
      if (mainContent) {
        mainContent.focus()
        mainContent.scrollIntoView({ behavior: 'smooth' })
      }
    }

    const handleLayoutError = (error: Error) => {
      uiStore.notifyError('An error occurred in the layout. Please refresh the page.')
      console.error('Layout error:', error)
    }

    const handleTransitionStart = () => {
      isTransitioning.value = true
      if (announcer.value) {
        announcer.value.textContent = 'Loading new content'
      }
    }

    const handleTransitionEnd = () => {
      isTransitioning.value = false
      if (announcer.value) {
        announcer.value.textContent = 'Content loaded'
      }
    }

    // Lifecycle hooks
    onMounted(() => {
      // Handle initial responsive state
      const mediaQuery = window.matchMedia('(max-width: 768px)')
      const handleMediaChange = (e: MediaQueryListEvent) => {
        if (e.matches) {
          isSidebarOpen.value = false
        }
      }
      mediaQuery.addEventListener('change', handleMediaChange)

      // Cleanup
      onUnmounted(() => {
        mediaQuery.removeEventListener('change', handleMediaChange)
      })
    })

    return {
      isSidebarOpen,
      layoutClasses,
      mainContentStyles,
      announcer,
      handleSidebarToggle,
      handleKeyboardNavigation,
      skipToContent,
      handleLayoutError,
      handleTransitionStart,
      handleTransitionEnd
    }
  }
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--background-color, #{vars.color(gray, 50)});
}

.layout-container {
  flex: 1;
  display: flex;
  position: relative;
}

.main-content {
  flex: 1;
  padding: vars.spacing(4);
  margin-top: 64px; // Header height
  min-height: calc(100vh - 64px);
  outline: none;

  &:focus-visible {
    outline: 2px solid vars.color(primary);
    outline-offset: -2px;
  }

  @media (max-width: map-get(vars.$breakpoints, tablet)) {
    padding: vars.spacing(2);
  }
}

.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  padding: vars.spacing(2);
  background-color: vars.color(primary);
  color: #fff;
  z-index: 1000;
  transition: top 0.2s ease;

  &:focus {
    top: 0;
  }
}

// Transition animations
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

// Reduced motion support
@media (prefers-reduced-motion: reduce) {
  .fade-enter-active,
  .fade-leave-active {
    transition: none;
  }

  .main-content {
    scroll-behavior: auto;
  }
}

// Screen reader only class
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