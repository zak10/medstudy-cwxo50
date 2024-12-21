<template>
  <footer 
    class="app-footer"
    :class="{ 'rtl': $vuetify?.rtl }"
    :style="footerStyles"
    role="contentinfo"
    aria-label="Site footer"
  >
    <!-- Legal Links Section -->
    <div class="footer-section legal-links">
      <nav aria-label="Legal navigation">
        <ul>
          <li>
            <a 
              href="/terms"
              @click="trackEvent('footer_link_click', { link: 'terms' })"
              class="footer-link"
            >
              Terms of Service
            </a>
          </li>
          <li>
            <a 
              href="/privacy"
              @click="trackEvent('footer_link_click', { link: 'privacy' })"
              class="footer-link"
            >
              Privacy Policy
            </a>
          </li>
          <li>
            <a 
              href="/compliance"
              @click="trackEvent('footer_link_click', { link: 'compliance' })"
              class="footer-link"
            >
              HIPAA Compliance
            </a>
          </li>
        </ul>
      </nav>
    </div>

    <!-- Support Access Section -->
    <div class="footer-section support-section">
      <BaseButton
        variant="secondary"
        size="sm"
        @click="handleSupportClick"
        aria-label="Access support"
      >
        Need Help?
      </BaseButton>
    </div>

    <!-- Copyright Notice -->
    <div class="footer-section copyright">
      <p>
        © {{ currentYear }} Medical Research Platform. All rights reserved.
      </p>
    </div>
  </footer>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue';
import { ErrorBoundary } from '@vueuse/core';
import BaseButton from './BaseButton.vue';
import { UI_CONSTANTS } from '@/config/constants';
import { useAnalytics } from '@/composables/useAnalytics';

export default defineComponent({
  name: 'AppFooter',

  components: {
    BaseButton,
    ErrorBoundary
  },

  props: {
    /**
     * Theme variant for footer styling
     * @values 'light' | 'dark'
     */
    theme: {
      type: String,
      default: 'light',
      validator: (value: string) => ['light', 'dark'].includes(value)
    }
  },

  emits: ['supportClick'],

  setup(props, { emit }) {
    // Analytics composable for tracking footer interactions
    const { trackEvent } = useAnalytics();

    // Computed current year for copyright notice
    const currentYear = computed(() => new Date().getFullYear());

    // Computed styles based on theme and direction
    const footerStyles = computed(() => ({
      '--footer-bg': props.theme === 'light' ? UI_CONSTANTS.COLORS.BACKGROUND : UI_CONSTANTS.COLORS.PRIMARY,
      '--footer-text': props.theme === 'light' ? UI_CONSTANTS.COLORS.TEXT : UI_CONSTANTS.COLORS.BACKGROUND,
      '--footer-link': props.theme === 'light' ? UI_CONSTANTS.COLORS.SECONDARY : UI_CONSTANTS.COLORS.ACCENT,
      padding: `${UI_CONSTANTS.SPACING.MEDIUM}px ${UI_CONSTANTS.SPACING.LARGE}px`
    }));

    // Event Handlers
    const handleSupportClick = () => {
      trackEvent('footer_support_click');
      emit('supportClick');
    };

    const handleKeyboardNavigation = (event: KeyboardEvent) => {
      const focusableElements = 'a[href], button:not([disabled])';
      const elements = Array.from(document.querySelectorAll(focusableElements));
      
      if (event.key === 'Tab') {
        const firstElement = elements[0] as HTMLElement;
        const lastElement = elements[elements.length - 1] as HTMLElement;

        if (event.shiftKey && document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        } else if (!event.shiftKey && document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    };

    return {
      currentYear,
      footerStyles,
      handleSupportClick,
      handleKeyboardNavigation,
      trackEvent
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.app-footer {
  width: 100%;
  background-color: var(--footer-bg);
  color: var(--footer-text);
  font-family: vars.$font-family-primary;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  transition: background-color 0.3s ease;

  display: flex;
  flex-direction: column;
  align-items: center;
  gap: vars.spacing(4);

  @media (min-width: map-get(vars.$breakpoints, tablet)) {
    flex-direction: row;
    justify-content: space-between;
    padding: vars.spacing(4) vars.spacing(6);
  }

  // Footer sections
  .footer-section {
    padding: vars.spacing(2);

    @media (min-width: map-get(vars.$breakpoints, tablet)) {
      padding: 0;
    }
  }

  // Legal links styling
  .legal-links {
    nav {
      ul {
        list-style: none;
        padding: 0;
        margin: 0;
        display: flex;
        flex-wrap: wrap;
        gap: vars.spacing(4);

        li {
          margin: 0;
        }
      }
    }

    .footer-link {
      color: var(--footer-link);
      text-decoration: none;
      font-size: 0.875rem;
      transition: color 0.2s ease;
      position: relative;

      &:hover {
        color: darken(var(--footer-link), 10%);
        text-decoration: underline;
      }

      &:focus-visible {
        outline: 2px solid var(--footer-link);
        outline-offset: 2px;
        border-radius: 2px;
      }
    }
  }

  // Support section styling
  .support-section {
    order: -1;

    @media (min-width: map-get(vars.$breakpoints, tablet)) {
      order: 0;
    }
  }

  // Copyright notice styling
  .copyright {
    font-size: 0.875rem;
    color: var(--footer-text);
    opacity: 0.8;
    text-align: center;

    @media (min-width: map-get(vars.$breakpoints, tablet)) {
      text-align: right;
    }
  }

  // RTL support
  &.rtl {
    direction: rtl;

    .legal-links {
      nav ul {
        flex-direction: row-reverse;
      }
    }

    .copyright {
      @media (min-width: map-get(vars.$breakpoints, tablet)) {
        text-align: left;
      }
    }
  }

  // Reduced motion support
  @media (prefers-reduced-motion: reduce) {
    transition: none;

    .footer-link {
      transition: none;
    }
  }
}
</style>