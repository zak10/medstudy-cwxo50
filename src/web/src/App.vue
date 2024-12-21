<template>
  <ErrorBoundary @error="handleErrorBoundary">
    <div 
      id="app" 
      class="app-container"
      role="application"
      aria-live="polite"
    >
      <!-- Main Navigation Header -->
      <AppHeader
        @auth-state-change="handleAuthStateChange"
        @navigation-change="handleNavigationChange"
      />

      <!-- Main Content Area -->
      <main 
        class="main-content"
        role="main"
        :aria-busy="isLoading"
      >
        <div class="router-view-container">
          <RouterView v-slot="{ Component }">
            <Transition
              name="page"
              mode="out-in"
              @before-leave="beforeRouteTransition"
              @after-enter="afterRouteTransition"
            >
              <component :is="Component" />
            </Transition>
          </RouterView>
        </div>

        <!-- Global Loading Overlay -->
        <div 
          v-if="isLoading"
          class="loading-overlay"
          role="progressbar"
          aria-valuetext="Loading..."
        >
          <LoadingSpinner 
            size="large"
            color="primary"
            :aria-label="'Application loading'"
          />
        </div>

        <!-- Global Notification System -->
        <Notification
          position="top-right"
          :max-notifications="5"
          @dismiss="handleNotificationDismiss"
        />
      </main>

      <!-- Application Footer -->
      <AppFooter
        @support-click="handleSupportClick"
        @legal-link-click="handleLegalLinkClick"
      />
    </div>
  </ErrorBoundary>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useUiStore } from '@/stores/ui';
import AppHeader from '@/components/common/AppHeader.vue';
import AppFooter from '@/components/common/AppFooter.vue';
import Notification from '@/components/common/Notification.vue';
import ErrorBoundary from '@/components/common/ErrorBoundary.vue';
import LoadingSpinner from '@/components/common/LoadingSpinner.vue';
import { UI_CONSTANTS } from '@/config/constants';

export default defineComponent({
  name: 'App',

  components: {
    AppHeader,
    AppFooter,
    Notification,
    ErrorBoundary,
    LoadingSpinner
  },

  setup() {
    const router = useRouter();
    const authStore = useAuthStore();
    const uiStore = useUiStore();
    const isLoading = ref(false);

    // Initialize authentication state
    onMounted(async () => {
      try {
        await authStore.initializeAuth();
      } catch (error) {
        console.error('Auth initialization failed:', error);
        uiStore.notifyError('Failed to initialize application');
      }
    });

    // Route transition handlers
    const beforeRouteTransition = () => {
      isLoading.value = true;
      document.body.style.overflow = 'hidden';
    };

    const afterRouteTransition = () => {
      isLoading.value = false;
      document.body.style.overflow = '';
    };

    // Event handlers
    const handleAuthStateChange = async (newState: string) => {
      if (newState === 'unauthenticated') {
        await router.push({ name: 'login' });
      }
    };

    const handleNavigationChange = (route: string) => {
      router.push(route).catch(error => {
        console.error('Navigation failed:', error);
        uiStore.notifyError('Navigation failed');
      });
    };

    const handleSupportClick = () => {
      uiStore.notifyInfo('Support system opening...');
      // Implement support system integration
    };

    const handleLegalLinkClick = (link: string) => {
      router.push(`/legal/${link}`).catch(error => {
        console.error('Legal navigation failed:', error);
        uiStore.notifyError('Failed to access legal information');
      });
    };

    const handleNotificationDismiss = (id: string) => {
      uiStore.removeNotification(id);
    };

    const handleErrorBoundary = (error: Error) => {
      console.error('Error boundary caught:', error);
      uiStore.notifyError('An unexpected error occurred');
    };

    return {
      isLoading,
      beforeRouteTransition,
      afterRouteTransition,
      handleAuthStateChange,
      handleNavigationChange,
      handleSupportClick,
      handleLegalLinkClick,
      handleNotificationDismiss,
      handleErrorBoundary
    };
  }
});
</script>

<style lang="scss">
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--app-bg-color, #{vars.color(background)});
  color: var(--app-text-color, #{vars.color(text)});
  font-family: vars.$font-family-primary;
}

.main-content {
  flex: 1;
  padding-top: var(--header-height, 64px);
  position: relative;
  max-width: vars.$container-max-width;
  margin: 0 auto;
  width: 100%;
  padding: vars.spacing(4);

  @media (max-width: map-get(vars.$breakpoints, tablet)) {
    padding: vars.spacing(2);
  }
}

.router-view-container {
  min-height: calc(100vh - var(--header-height) - var(--footer-height));
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: vars.$z-index-overlay;
}

// Page transition animations
.page-enter-active,
.page-leave-active {
  transition: opacity 0.3s ease;
}

.page-enter-from,
.page-leave-to {
  opacity: 0;
}

// Reduced motion preferences
@media (prefers-reduced-motion: reduce) {
  .page-enter-active,
  .page-leave-active {
    transition: none;
  }
}

// High contrast mode support
@media (forced-colors: active) {
  .app-container {
    forced-color-adjust: auto;
  }
}
</style>