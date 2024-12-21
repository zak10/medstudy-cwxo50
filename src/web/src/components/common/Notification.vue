<template>
  <div
    class="notification-container"
    :class="containerClasses"
    role="region"
    aria-live="polite"
    aria-relevant="additions removals"
    data-testid="notification-container"
  >
    <TransitionGroup
      name="notification"
      tag="div"
      :appear="true"
      class="notification-list"
    >
      <div
        v-for="notification in visibleNotifications"
        :key="notification.id"
        :class="[
          'notification',
          getNotificationClass(notification.type)
        ]"
        :role="notification.type === 'error' ? 'alert' : 'status'"
        :aria-live="notification.type === 'error' ? 'assertive' : 'polite'"
        tabindex="0"
        data-testid="notification-item"
      >
        <div class="notification-content">
          <span class="notification-icon" aria-hidden="true">
            <!-- Dynamic icon based on notification type -->
            <i :class="getIconClass(notification.type)"></i>
          </span>
          <span class="notification-message">{{ notification.message }}</span>
          <button
            class="notification-dismiss"
            @click="handleDismiss(notification.id)"
            :aria-label="`Dismiss ${notification.type} notification`"
            type="button"
          >
            <span aria-hidden="true">&times;</span>
          </button>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue' // v3.3.0
import { TransitionGroup } from 'vue' // v3.3.0
import { NotificationType } from '@/types/ui'
import { useUiStore } from '@/stores/ui'
import { useNotification } from '@/composables/useNotification'

// Props
const props = withDefaults(defineProps<{
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left'
  maxNotifications?: number
}>(), {
  position: 'top-right',
  maxNotifications: 5
})

// Emits
const emit = defineEmits<{
  (e: 'dismissed', id: string): void
}>()

// Store and composable initialization
const uiStore = useUiStore()
const { clearNotification } = useNotification()

// Computed
const visibleNotifications = computed(() => {
  return [...uiStore.notifications]
    .sort((a, b) => b.timestamp - a.timestamp)
    .slice(0, props.maxNotifications)
})

const containerClasses = computed(() => ({
  [`notification-container--${props.position}`]: true,
  'notification-container--reduced-motion': window.matchMedia('(prefers-reduced-motion: reduce)').matches
}))

// Methods
const getNotificationClass = (type: NotificationType) => ({
  [`notification--${type}`]: true,
  'notification--high-contrast': window.matchMedia('(forced-colors: active)').matches
})

const getIconClass = (type: NotificationType) => {
  const iconMap = {
    [NotificationType.SUCCESS]: 'check-circle',
    [NotificationType.ERROR]: 'exclamation-circle',
    [NotificationType.WARNING]: 'exclamation-triangle',
    [NotificationType.INFO]: 'information-circle'
  }
  return `icon-${iconMap[type]}`
}

const handleDismiss = async (id: string) => {
  try {
    await clearNotification(id)
    emit('dismissed', id)
  } catch (error) {
    console.error('Failed to dismiss notification:', error)
  }
}

// Lifecycle hooks
onMounted(() => {
  // Add resize listener for responsive adjustments
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.notification-container {
  position: fixed;
  z-index: var(--notification-z-index, 1000);
  display: flex;
  flex-direction: column;
  gap: var(--notification-margin, 8px);
  max-width: var(--notification-width, 320px);
  width: 100%;
  pointer-events: none;
  padding: 16px;
}

/* Position variants */
.notification-container--top-right {
  top: 0;
  right: 0;
}

.notification-container--top-left {
  top: 0;
  left: 0;
}

.notification-container--bottom-right {
  bottom: 0;
  right: 0;
}

.notification-container--bottom-left {
  bottom: 0;
  left: 0;
}

.notification {
  background: white;
  border-radius: 6px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 12px 16px;
  pointer-events: auto;
  position: relative;
  transition: all 0.2s ease;
}

/* Notification type variants */
.notification--success {
  border-left: 4px solid #2ECC71;
  background-color: #F0FDF4;
}

.notification--error {
  border-left: 4px solid #E74C3C;
  background-color: #FEF2F2;
}

.notification--warning {
  border-left: 4px solid #F1C40F;
  background-color: #FFFBEB;
}

.notification--info {
  border-left: 4px solid #3498DB;
  background-color: #EFF6FF;
}

.notification-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.notification-message {
  flex: 1;
  font-size: 14px;
  line-height: 1.5;
  color: #1A202C;
}

.notification-dismiss {
  background: transparent;
  border: none;
  color: #64748B;
  cursor: pointer;
  padding: 4px;
  transition: color 0.2s ease;
}

.notification-dismiss:hover {
  color: #1A202C;
}

.notification-dismiss:focus {
  outline: 2px solid #3498DB;
  outline-offset: 2px;
}

/* Animations */
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

/* Reduced motion preferences */
@media (prefers-reduced-motion: reduce) {
  .notification-container--reduced-motion .notification,
  .notification-container--reduced-motion .notification-enter-active,
  .notification-container--reduced-motion .notification-leave-active {
    transition: opacity 0.1s ease;
    transform: none;
  }
}

/* High contrast mode support */
@media (forced-colors: active) {
  .notification--high-contrast {
    border: 2px solid currentColor;
  }
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .notification-container {
    --notification-width: 100%;
    padding: 8px;
  }
}
</style>