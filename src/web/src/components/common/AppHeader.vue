<template>
  <header 
    class="app-header" 
    role="banner" 
    aria-label="Main navigation"
  >
    <!-- Logo and Brand Section -->
    <div class="brand-section">
      <router-link 
        to="/" 
        class="logo-link"
        aria-label="Medical Research Platform Home"
      >
        <h1 class="brand-name">Medical Research Platform</h1>
      </router-link>
    </div>

    <!-- Main Navigation -->
    <nav 
      class="nav-menu" 
      :class="{ 'is-mobile-open': isMobileMenuOpen }"
      role="navigation"
      aria-label="Main menu"
    >
      <ul class="nav-list">
        <li v-for="item in navigationItems" :key="item.route">
          <BaseButton
            variant="text"
            size="md"
            :aria-label="item.label"
            @click="navigateTo(item.route)"
          >
            {{ item.label }}
          </BaseButton>
        </li>
      </ul>
    </nav>

    <!-- User Actions -->
    <div class="user-actions">
      <template v-if="isLoggedIn">
        <BaseButton
          variant="outline"
          size="sm"
          aria-label="Log out"
          @click="handleLogout"
        >
          Log Out
        </BaseButton>
      </template>
      <template v-else>
        <BaseButton
          variant="primary"
          size="sm"
          aria-label="Log in"
          @click="navigateTo(ROUTE_NAMES.LOGIN)"
        >
          Log In
        </BaseButton>
      </template>
    </div>

    <!-- Mobile Menu Button -->
    <button
      class="mobile-menu-button"
      :aria-expanded="isMobileMenuOpen"
      aria-controls="mobile-menu"
      aria-label="Toggle menu"
      @click="toggleMobileMenu"
    >
      <span class="sr-only">Menu</span>
      <div class="hamburger" :class="{ 'is-active': isMobileMenuOpen }">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </button>

    <!-- Mobile Menu Overlay -->
    <div 
      id="mobile-menu"
      class="mobile-menu"
      :class="{ 'is-open': isMobileMenuOpen }"
      aria-hidden="!isMobileMenuOpen"
    >
      <nav class="mobile-nav">
        <ul class="mobile-nav-list">
          <li v-for="item in navigationItems" :key="item.route">
            <BaseButton
              variant="text"
              size="lg"
              :aria-label="item.label"
              @click="navigateTo(item.route)"
            >
              {{ item.label }}
            </BaseButton>
          </li>
        </ul>
      </nav>
    </div>
  </header>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { ROUTE_NAMES } from '@/router/routes';
import BaseButton from './BaseButton.vue';

interface NavigationItem {
  label: string;
  route: string;
  roles?: string[];
}

export default defineComponent({
  name: 'AppHeader',

  components: {
    BaseButton
  },

  setup() {
    const router = useRouter();
    const authStore = useAuthStore();
    const isMobileMenuOpen = ref(false);

    // Computed properties
    const isLoggedIn = computed(() => authStore.isAuthenticated);
    const userRole = computed(() => authStore.user?.role);

    const navigationItems = computed(() => {
      const items: NavigationItem[] = [
        {
          label: 'Protocols',
          route: ROUTE_NAMES.PROTOCOLS,
          roles: ['PARTICIPANT', 'PROTOCOL_CREATOR']
        },
        {
          label: 'Data Entry',
          route: ROUTE_NAMES.DATA_COLLECTION,
          roles: ['PARTICIPANT']
        },
        {
          label: 'Community',
          route: ROUTE_NAMES.COMMUNITY,
          roles: ['PARTICIPANT', 'PROTOCOL_CREATOR', 'PARTNER']
        }
      ];

      // Filter items based on user role
      return items.filter(item => {
        if (!item.roles) return true;
        return !userRole.value || item.roles.includes(userRole.value);
      });
    });

    // Methods
    const handleLogout = async () => {
      try {
        await authStore.logout();
        isMobileMenuOpen.value = false;
        await router.push({ name: ROUTE_NAMES.LOGIN });
      } catch (error) {
        console.error('Logout failed:', error);
      }
    };

    const toggleMobileMenu = () => {
      isMobileMenuOpen.value = !isMobileMenuOpen.value;
      document.body.style.overflow = isMobileMenuOpen.value ? 'hidden' : '';
    };

    const navigateTo = async (routeName: string) => {
      try {
        await router.push({ name: routeName });
        isMobileMenuOpen.value = false;
      } catch (error) {
        console.error('Navigation failed:', error);
      }
    };

    return {
      isLoggedIn,
      userRole,
      isMobileMenuOpen,
      navigationItems,
      ROUTE_NAMES,
      handleLogout,
      toggleMobileMenu,
      navigateTo
    };
  }
});
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.app-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 64px;
  padding: 0 vars.spacing(4);
  background-color: vars.color(gray, 50);
  border-bottom: 1px solid vars.color(gray, 200);
  display: flex;
  align-items: center;
  justify-content: space-between;
  z-index: 100;

  @media (max-width: map-get(vars.$breakpoints, tablet)) {
    padding: 0 vars.spacing(2);
  }
}

.brand-section {
  .brand-name {
    font-family: vars.$font-family-primary;
    font-weight: map-get(vars.$font-weights, semibold);
    font-size: 1.25rem;
    color: vars.color(primary);
  }

  .logo-link {
    text-decoration: none;
    color: inherit;

    &:focus-visible {
      outline: 2px solid vars.color(primary);
      outline-offset: 2px;
      border-radius: 4px;
    }
  }
}

.nav-menu {
  display: flex;
  align-items: center;
  margin: 0 vars.spacing(4);

  .nav-list {
    display: flex;
    gap: vars.spacing(4);
    list-style: none;
    margin: 0;
    padding: 0;
  }

  @media (max-width: map-get(vars.$breakpoints, tablet)) {
    display: none;
  }
}

.user-actions {
  display: flex;
  align-items: center;
  gap: vars.spacing(2);

  @media (max-width: map-get(vars.$breakpoints, tablet)) {
    display: none;
  }
}

.mobile-menu-button {
  display: none;
  background: none;
  border: none;
  padding: vars.spacing(2);
  cursor: pointer;

  @media (max-width: map-get(vars.$breakpoints, tablet)) {
    display: block;
  }

  .hamburger {
    width: 24px;
    height: 18px;
    position: relative;
    
    span {
      display: block;
      position: absolute;
      height: 2px;
      width: 100%;
      background: vars.color(primary);
      border-radius: 2px;
      transition: all 0.3s ease;

      &:nth-child(1) { top: 0; }
      &:nth-child(2) { top: 8px; }
      &:nth-child(3) { top: 16px; }
    }

    &.is-active {
      span {
        &:nth-child(1) {
          transform: rotate(45deg);
          top: 8px;
        }
        &:nth-child(2) {
          opacity: 0;
        }
        &:nth-child(3) {
          transform: rotate(-45deg);
          top: 8px;
        }
      }
    }
  }
}

.mobile-menu {
  display: none;
  position: fixed;
  top: 64px;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: vars.color(gray, 50);
  padding: vars.spacing(4);
  transform: translateX(100%);
  transition: transform 0.3s ease;

  @media (max-width: map-get(vars.$breakpoints, tablet)) {
    display: block;
  }

  &.is-open {
    transform: translateX(0);
  }

  .mobile-nav-list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: vars.spacing(4);
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

// Reduced motion support
@media (prefers-reduced-motion: reduce) {
  .mobile-menu,
  .hamburger span {
    transition: none;
  }
}
</style>