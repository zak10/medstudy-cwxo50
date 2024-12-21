<template>
  <nav 
    class="breadcrumbs" 
    aria-label="Breadcrumb navigation"
    role="navigation"
  >
    <ol class="breadcrumbs__list" role="list">
      <li 
        v-for="(item, index) in breadcrumbs" 
        :key="item.path"
        class="breadcrumbs__item"
        :class="{
          'breadcrumbs__item--current': item.current,
          'breadcrumbs__item--clickable': item.isClickable
        }"
        :aria-current="item.current ? 'page' : undefined"
        role="listitem"
      >
        <!-- Icon if present -->
        <span 
          v-if="item.icon" 
          class="breadcrumbs__icon"
          aria-hidden="true"
        >
          {{ item.icon }}
        </span>

        <!-- Navigation link or current page text -->
        <template v-if="item.isClickable">
          <a
            :href="item.path"
            class="breadcrumbs__link"
            :aria-label="item.ariaLabel"
            @click.prevent="handleNavigation(item.path)"
          >
            {{ item.label }}
          </a>
        </template>
        <template v-else>
          <span class="breadcrumbs__text">{{ item.label }}</span>
        </template>

        <!-- Separator between items -->
        <span 
          v-if="index < breadcrumbs.length - 1" 
          class="breadcrumbs__separator"
          aria-hidden="true"
        >
          /
        </span>
      </li>
    </ol>
  </nav>
</template>

<script lang="ts">
import { defineComponent, computed } from 'vue'; // ^3.3.0
import { useRoute, useRouter, RouteLocationNormalizedLoaded } from 'vue-router'; // ^4.2.0
import { ROUTE_NAMES, ROUTE_PATHS } from '@/config/routes';

// Interface for breadcrumb items
interface BreadcrumbItem {
  label: string;
  path: string;
  current: boolean;
  isClickable: boolean;
  icon?: string;
  ariaLabel?: string;
}

export default defineComponent({
  name: 'Breadcrumbs',

  setup() {
    const route = useRoute();
    const router = useRouter();

    /**
     * Generates breadcrumb items based on current route
     * @param {RouteLocationNormalizedLoaded} currentRoute - Current route object
     * @returns {BreadcrumbItem[]} Array of breadcrumb items
     */
    const generateBreadcrumbs = (currentRoute: RouteLocationNormalizedLoaded): BreadcrumbItem[] => {
      const pathSegments = currentRoute.path.split('/').filter(Boolean);
      const breadcrumbs: BreadcrumbItem[] = [];

      // Always include home as first breadcrumb
      breadcrumbs.push({
        label: 'Home',
        path: ROUTE_PATHS.HOME,
        current: currentRoute.path === ROUTE_PATHS.HOME,
        isClickable: currentRoute.path !== ROUTE_PATHS.HOME,
        icon: '🏠',
        ariaLabel: 'Navigate to home page'
      });

      // Build path progressively
      let currentPath = '';
      pathSegments.forEach((segment, index) => {
        currentPath += `/${segment}`;
        
        // Skip segments marked as hidden in route meta
        if (currentRoute.matched[index]?.meta?.hideBreadcrumb) {
          return;
        }

        const label = getRouteLabel(segment);
        const isLast = index === pathSegments.length - 1;

        breadcrumbs.push({
          label,
          path: currentPath,
          current: isLast,
          isClickable: !isLast,
          ariaLabel: `Navigate to ${label.toLowerCase()}`
        });
      });

      return breadcrumbs;
    };

    /**
     * Gets human-readable label for route segment
     * @param {string} segment - Route segment
     * @returns {string} Human-readable label
     */
    const getRouteLabel = (segment: string): string => {
      // Check for dynamic route parameters
      if (segment.startsWith(':')) {
        const paramName = segment.slice(1);
        return route.params[paramName]?.toString() || segment;
      }

      // Convert route segment to readable format
      return segment
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    };

    /**
     * Handles navigation when breadcrumb is clicked
     * @param {string} path - Target navigation path
     */
    const handleNavigation = async (path: string): Promise<void> => {
      try {
        // Prevent navigation to current path
        if (path === route.path) {
          return;
        }

        await router.push(path);
      } catch (error) {
        console.error('Navigation failed:', error);
        // Additional error handling could be added here
      }
    };

    // Computed property for breadcrumb items
    const breadcrumbs = computed(() => generateBreadcrumbs(route));

    return {
      breadcrumbs,
      handleNavigation
    };
  }
});
</script>

<style lang="scss" module>
.breadcrumbs {
  padding: 1rem 0;
  font-size: 0.875rem;
  line-height: 1.5;

  &__list {
    display: flex;
    flex-wrap: wrap;
    list-style: none;
    margin: 0;
    padding: 0;
    gap: 0.5rem;
  }

  &__item {
    display: flex;
    align-items: center;
    color: var(--text-secondary);

    &--current {
      color: var(--text-primary);
      font-weight: 500;
    }

    &--clickable {
      .breadcrumbs__link {
        color: var(--primary-color);
        text-decoration: none;
        transition: color 0.2s ease;

        &:hover, &:focus {
          color: var(--primary-color-dark);
          text-decoration: underline;
        }

        &:focus-visible {
          outline: 2px solid var(--primary-color);
          outline-offset: 2px;
          border-radius: 2px;
        }
      }
    }
  }

  &__separator {
    margin: 0 0.5rem;
    color: var(--text-tertiary);
  }

  &__icon {
    margin-right: 0.25rem;
    font-size: 1rem;
  }

  // Responsive styles
  @media (max-width: 768px) {
    font-size: 0.75rem;

    &__list {
      gap: 0.25rem;
    }

    &__separator {
      margin: 0 0.25rem;
    }

    // Hide all but last two items on mobile
    &__item:not(:nth-last-child(-n+2)) {
      display: none;
    }
  }

  // High contrast mode support
  @media (forced-colors: active) {
    .breadcrumbs__link {
      text-decoration: underline;
    }
  }
}
</style>