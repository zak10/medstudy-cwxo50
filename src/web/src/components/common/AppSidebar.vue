<template>
  <nav 
    class="sidebar"
    role="navigation"
    aria-label="Main navigation"
    :class="sidebarClasses"
    v-show="isVisible"
  >
    <!-- Sidebar Header -->
    <div class="sidebar-header">
      <button
        class="sidebar-toggle"
        :aria-expanded="isOpen"
        :aria-label="isOpen ? 'Close navigation menu' : 'Open navigation menu'"
        @click="toggleSidebar"
      >
        <span class="toggle-icon" :class="{ 'is-open': isOpen }"></span>
      </button>
    </div>

    <!-- Navigation List -->
    <ul 
      class="navigation-list"
      role="menubar"
      aria-orientation="vertical"
      @keydown="handleKeyboardNavigation"
    >
      <li 
        v-for="item in navigationItems" 
        :key="item.path"
        class="navigation-item"
        role="none"
      >
        <router-link
          :to="item.path"
          class="navigation-link"
          :class="{ 'active': item.isActive }"
          role="menuitem"
          :aria-current="item.isActive ? 'page' : undefined"
          :tabindex="item.isActive ? 0 : -1"
        >
          <span class="icon" :aria-hidden="true">{{ item.icon }}</span>
          <span class="label">{{ item.label }}</span>
        </router-link>
      </li>
    </ul>
  </nav>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue' // v3.3.0
import { useRouter, useRoute } from 'vue-router' // v4.2.0
import { ROUTE_PATHS } from '@/config/routes'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { UserRole } from '@/types/auth'

// Initialize router and route
const router = useRouter()
const route = useRoute()

// Get stores
const authStore = useAuthStore()
const uiStore = useUiStore()

// Component state
const isOpen = ref(localStorage.getItem('sidebarOpen') === 'true')
const isVisible = ref(true)

// Computed properties
const sidebarClasses = computed(() => ({
  'is-open': isOpen.value,
  'is-mobile': uiStore.currentBreakpoint === 'mobile',
  'is-dark': uiStore.theme.dark,
  'reduced-motion': uiStore.reducedMotion
}))

// Navigation items based on auth state and user role
const navigationItems = computed(() => {
  const items = [
    {
      path: ROUTE_PATHS.HOME,
      label: 'Dashboard',
      icon: '🏠',
      isActive: route.path === ROUTE_PATHS.HOME
    }
  ]

  if (authStore.isAuthenticated) {
    items.push({
      path: ROUTE_PATHS.PROTOCOLS,
      label: 'Protocols',
      icon: '📋',
      isActive: route.path.startsWith('/protocols')
    })

    items.push({
      path: ROUTE_PATHS.DATA_COLLECTION,
      label: 'Data Collection',
      icon: '📊',
      isActive: route.path.startsWith('/data')
    })

    items.push({
      path: ROUTE_PATHS.COMMUNITY,
      label: 'Community',
      icon: '👥',
      isActive: route.path.startsWith('/community')
    })

    // Add role-specific items
    if (authStore.user?.role === UserRole.PROTOCOL_CREATOR) {
      items.push({
        path: ROUTE_PATHS.PROTOCOL_CREATE,
        label: 'Create Protocol',
        icon: '➕',
        isActive: route.path === ROUTE_PATHS.PROTOCOL_CREATE
      })
    }
  }

  return items
})

// Methods
const toggleSidebar = () => {
  isOpen.value = !isOpen.value
  localStorage.setItem('sidebarOpen', isOpen.value.toString())
  emit('sidebar-toggle', isOpen.value)
}

const handleKeyboardNavigation = (event: KeyboardEvent) => {
  const items = document.querySelectorAll('.navigation-link')
  const currentIndex = Array.from(items).findIndex(item => item === document.activeElement)

  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault()
      const nextIndex = (currentIndex + 1) % items.length
      ;(items[nextIndex] as HTMLElement).focus()
      break
    case 'ArrowUp':
      event.preventDefault()
      const prevIndex = currentIndex <= 0 ? items.length - 1 : currentIndex - 1
      ;(items[prevIndex] as HTMLElement).focus()
      break
    case 'Escape':
      if (isOpen.value && uiStore.currentBreakpoint === 'mobile') {
        toggleSidebar()
      }
      break
  }
}

// Watchers
watch(() => route.path, () => {
  if (uiStore.currentBreakpoint === 'mobile') {
    isOpen.value = false
  }
})

// Lifecycle hooks
onMounted(() => {
  // Handle responsive visibility
  const mediaQuery = window.matchMedia('(max-width: 768px)')
  const handleMediaChange = (e: MediaQueryListEvent) => {
    isVisible.value = !e.matches || isOpen.value
  }
  mediaQuery.addEventListener('change', handleMediaChange)

  onUnmounted(() => {
    mediaQuery.removeEventListener('change', handleMediaChange)
  })
})

// Emits
const emit = defineEmits<{
  (e: 'sidebar-toggle', value: boolean): void
}>()
</script>

<style lang="scss" scoped>
.sidebar {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  width: var(--sidebar-width, 240px);
  background: var(--surface-color);
  box-shadow: var(--elevation-level1);
  transform: translateX(-100%);
  transition: transform 0.3s ease;
  z-index: var(--z-index-sidebar, 100);

  &.is-open {
    transform: translateX(0);
  }

  &.reduced-motion {
    transition: none;
  }

  @media (min-width: 768px) {
    position: relative;
    transform: none;
  }
}

.sidebar-header {
  height: 64px;
  padding: var(--spacing-md);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  border-bottom: 1px solid var(--border-color);
}

.sidebar-toggle {
  width: var(--touch-target-size, 44px);
  height: var(--touch-target-size, 44px);
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;

  &:focus-visible {
    outline: var(--focus-outline-width) solid var(--focus-outline-color);
    outline-offset: 2px;
  }

  @media (min-width: 768px) {
    display: none;
  }
}

.navigation-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.navigation-item {
  margin: 0;
  padding: 0;
}

.navigation-link {
  display: flex;
  align-items: center;
  padding: var(--spacing-md);
  color: var(--text-primary);
  text-decoration: none;
  transition: background-color 0.2s ease;

  &:hover {
    background-color: var(--hover-color);
  }

  &:focus-visible {
    outline: var(--focus-outline-width) solid var(--focus-outline-color);
    outline-offset: -2px;
  }

  &.active {
    background-color: var(--primary-color);
    color: var(--primary-contrast);
  }

  .icon {
    margin-right: var(--spacing-sm);
    font-size: 1.2em;
  }

  .label {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-medium);
  }
}

// Dark mode styles
.is-dark {
  --surface-color: var(--dark-surface);
  --text-primary: var(--dark-text-primary);
  --hover-color: var(--dark-hover);
}
</style>