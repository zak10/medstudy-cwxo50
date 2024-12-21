import { defineStore } from 'pinia' // v2.1.0
import { ref, computed } from 'vue' // v3.3.0
import { NotificationType, type Notification } from '../types/ui'
import theme from '../config/theme'

// Constants
const DEFAULT_NOTIFICATION_DURATION = 5000 // 5 seconds
const MAX_NOTIFICATIONS = 5 // Maximum number of concurrent notifications

/**
 * Pinia store for managing global UI state including theme, notifications,
 * loading states, and responsive breakpoints
 */
export const useUiStore = defineStore('ui', () => {
  // State
  const notifications = ref<Notification[]>([])
  const notificationTimeouts = ref<Map<string, number>>(new Map())
  const isLoading = ref(false)
  const currentBreakpoint = ref<string>('mobile')
  const currentTheme = ref(theme)

  // Computed
  const activeNotifications = computed(() => notifications.value)
  const breakpointWidth = computed(() => theme.breakpoints[currentBreakpoint.value])
  const isDesktopOrLarger = computed(() => 
    ['desktop', 'wide'].includes(currentBreakpoint.value)
  )

  /**
   * Adds a new notification to the queue with automatic removal
   * @param notification The notification to add
   */
  function addNotification(notification: Omit<Notification, 'id'>) {
    const id = crypto.randomUUID()
    const duration = notification.duration || DEFAULT_NOTIFICATION_DURATION

    // Remove oldest notification if queue is full
    if (notifications.value.length >= MAX_NOTIFICATIONS) {
      const oldestId = notifications.value[0].id
      removeNotification(oldestId)
    }

    // Add new notification
    notifications.value.push({
      ...notification,
      id,
      type: notification.type || NotificationType.INFO
    })

    // Set timeout for auto-removal
    const timeoutId = window.setTimeout(() => {
      removeNotification(id)
    }, duration)

    notificationTimeouts.value.set(id, timeoutId)
  }

  /**
   * Removes a notification from the queue by ID
   * @param id The ID of the notification to remove
   */
  function removeNotification(id: string) {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index !== -1) {
      notifications.value.splice(index, 1)
      
      // Clear timeout
      const timeoutId = notificationTimeouts.value.get(id)
      if (timeoutId) {
        window.clearTimeout(timeoutId)
        notificationTimeouts.value.delete(id)
      }
    }
  }

  /**
   * Updates the global loading state
   * @param loading The new loading state
   */
  function setLoading(loading: boolean) {
    isLoading.value = loading
    // Update aria-busy attribute on root element
    document.documentElement.setAttribute('aria-busy', loading.toString())
  }

  /**
   * Updates the current breakpoint based on window width
   */
  function updateBreakpoint() {
    const width = window.innerWidth
    
    if (width >= theme.breakpoints.wide) {
      currentBreakpoint.value = 'wide'
    } else if (width >= theme.breakpoints.desktop) {
      currentBreakpoint.value = 'desktop'
    } else if (width >= theme.breakpoints.tablet) {
      currentBreakpoint.value = 'tablet'
    } else {
      currentBreakpoint.value = 'mobile'
    }
  }

  /**
   * Initializes responsive breakpoint detection
   */
  function initializeBreakpointDetection() {
    // Initial breakpoint check
    updateBreakpoint()

    // Add resize listener
    window.addEventListener('resize', updateBreakpoint)

    // Cleanup on store destruction
    onUnmounted(() => {
      window.removeEventListener('resize', updateBreakpoint)
    })
  }

  // Initialize breakpoint detection
  initializeBreakpointDetection()

  return {
    // State
    notifications: activeNotifications,
    isLoading,
    currentBreakpoint,
    theme: currentTheme,
    isDesktopOrLarger,

    // Actions
    addNotification,
    removeNotification,
    setLoading,
    updateBreakpoint,

    // Helper functions for specific notification types
    notifySuccess: (message: string, duration?: number) => 
      addNotification({ type: NotificationType.SUCCESS, message, duration }),
    notifyError: (message: string, duration?: number) => 
      addNotification({ type: NotificationType.ERROR, message, duration }),
    notifyWarning: (message: string, duration?: number) => 
      addNotification({ type: NotificationType.WARNING, message, duration }),
    notifyInfo: (message: string, duration?: number) => 
      addNotification({ type: NotificationType.INFO, message, duration })
  }
})