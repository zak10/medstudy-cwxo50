<template>
  <div 
    class="not-found"
    role="main"
    aria-labelledby="error-heading"
  >
    <div class="error-content">
      <h1 
        class="error-code"
        aria-hidden="true"
      >
        404
      </h1>
      
      <h2 
        id="error-heading"
        class="error-heading"
      >
        Page Not Found
      </h2>
      
      <p class="error-description">
        The page you're looking for doesn't exist or has been moved.
      </p>

      <div class="action-container">
        <BaseButton
          variant="primary"
          size="lg"
          :aria-label="'Return to dashboard'"
          @click="handleReturn"
        >
          Return to Dashboard
        </BaseButton>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'; // v3.3.0
import { useRouter } from 'vue-router'; // v4.2.0
import BaseButton from '@/components/common/BaseButton.vue';

export default defineComponent({
  name: 'NotFound',

  components: {
    BaseButton
  },

  setup() {
    const router = useRouter();

    const handleReturn = async (): Promise<void> => {
      try {
        // Log 404 error encounter for analytics
        console.error('404 Error: Page not found', {
          path: window.location.pathname,
          timestamp: new Date().toISOString()
        });

        // Navigate to dashboard
        await router.push({ name: 'dashboard' });
      } catch (error) {
        console.error('Navigation error:', error);
        // Fallback to home route if dashboard navigation fails
        await router.push('/');
      }
    };

    return {
      handleReturn
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: vars.spacing(4);
  background-color: map-get(vars.$colors, 'gray', 50);

  .error-content {
    text-align: center;
    max-width: 600px;
    @include animations.fade-in(0.5s);

    .error-code {
      font-family: vars.$font-family-primary;
      font-size: 8rem;
      font-weight: map-get(vars.$font-weights, bold);
      color: map-get(vars.$colors, 'gray', 300);
      line-height: 1;
      margin: 0 0 vars.spacing(4);
    }

    .error-heading {
      font-family: vars.$font-family-primary;
      font-size: 2rem;
      font-weight: map-get(vars.$font-weights, semibold);
      color: map-get(vars.$colors, primary);
      margin: 0 0 vars.spacing(3);
    }

    .error-description {
      font-family: vars.$font-family-secondary;
      font-size: 1.125rem;
      color: map-get(vars.$colors, 'gray', 600);
      margin: 0 0 vars.spacing(6);
      line-height: 1.5;
    }

    .action-container {
      margin-top: vars.spacing(6);
    }
  }
}

// Responsive breakpoints
@media (max-width: map-get(vars.$breakpoints, tablet)) {
  .not-found {
    padding: vars.spacing(3);

    .error-content {
      .error-code {
        font-size: 6rem;
      }

      .error-heading {
        font-size: 1.5rem;
      }

      .error-description {
        font-size: 1rem;
      }
    }
  }
}

// Reduced motion support
@media (prefers-reduced-motion: reduce) {
  .error-content {
    animation: none;
  }
}

// High contrast mode support
@media (forced-colors: active) {
  .not-found {
    border: 1px solid CanvasText;
  }
}
</style>