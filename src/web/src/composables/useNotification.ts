import { ref, computed, onUnmounted } from 'vue' // v3.3.0
import { v4 as uuidv4 } from 'uuid' // v9.0.0
import { NotificationType } from '@/types/ui'
import { useUiStore } from '@/stores/ui'

// Default notification duration in milliseconds
const DEFAULT_DURATION = 5000

/**
 * Interface for notification object structure
 */
interface Notification {
  id: string
  type: NotificationType
  message: string
  duration?: number
  ariaLive?: 'polite' | 'assertive'
}

/**
 * Composable for managing application-wide notifications with accessibility support
 * Implements notification queue management and auto-dismissal functionality
 */
export function useNotification() {
  // Initialize UI store with error boundary
  const uiStore = useUiStore()
  
  // Create computed reference to notifications array
  const notifications = computed(() => uiStore.notifications)
  
  // Map to track notification timeouts for cleanup
  const timeoutMap = ref(new Map<string, number>())
  
  // ARIA live region for screen reader announcements
  let ariaLiveRegion: HTMLDivElement | null = null

  /**
   * Creates and initializes ARIA live region for accessibility
   */
  function initializeAriaLiveRegion() {
    if (!ariaLiveRegion && typeof document !== 'undefined') {
      ariaLiveRegion = document.createElement('div')
      ariaLiveRegion.setAttribute('aria-live', 'polite')
      ariaLiveRegion.setAttribute('aria-atomic', 'true')
      ariaLiveRegion.classList.add('sr-only') // Screen reader only
      document.body.appendChild(ariaLiveRegion)
    }
  }

  /**
   * Updates ARIA live region with notification message
   * @param message - The message to announce
   * @param type - The type of notification
   */
  function announceNotification(message: string, type: NotificationType) {
    if (ariaLiveRegion) {
      const priority = type === NotificationType.ERROR ? 'assertive' : 'polite'
      ariaLiveRegion.setAttribute('aria-live', priority)
      ariaLiveRegion.textContent = message
    }
  }

  /**
   * Shows a new notification with proper accessibility support
   * @param type - The type of notification
   * @param message - The notification message
   * @param duration - Optional duration in milliseconds
   * @returns The unique ID of the created notification
   */
  function showNotification(
    type: NotificationType,
    message: string,
    duration: number = DEFAULT_DURATION
  ): string {
    try {
      // Validate inputs
      if (!message || !type) {
        throw new Error('Notification message and type are required')
      }

      // Generate unique ID
      const id = uuidv4()

      // Create notification object
      const notification: Notification = {
        id,
        type,
        message,
        duration,
        ariaLive: type === NotificationType.ERROR ? 'assertive' : 'polite'
      }

      // Add to store
      uiStore.addNotification(notification)

      // Set up auto-dismiss timer
      if (duration > 0) {
        const timeoutId = window.setTimeout(() => {
          clearNotification(id)
        }, duration)
        timeoutMap.value.set(id, timeoutId)
      }

      // Announce to screen readers
      announceNotification(message, type)

      return id
    } catch (error) {
      console.error('Error showing notification:', error)
      throw error
    }
  }

  /**
   * Clears a specific notification with proper cleanup
   * @param id - The ID of the notification to clear
   */
  function clearNotification(id: string): void {
    try {
      // Clear timeout if exists
      const timeoutId = timeoutMap.value.get(id)
      if (timeoutId) {
        window.clearTimeout(timeoutId)
        timeoutMap.value.delete(id)
      }

      // Remove from store
      uiStore.removeNotification(id)
    } catch (error) {
      console.error('Error clearing notification:', error)
      throw error
    }
  }

  /**
   * Clears all current notifications with batch optimization
   */
  function clearAllNotifications(): void {
    try {
      // Clear all timeouts
      timeoutMap.value.forEach((timeoutId) => {
        window.clearTimeout(timeoutId)
      })
      timeoutMap.value.clear()

      // Clear all notifications from store
      notifications.value.forEach((notification) => {
        uiStore.removeNotification(notification.id)
      })

      // Clear ARIA live region
      if (ariaLiveRegion) {
        ariaLiveRegion.textContent = ''
      }
    } catch (error) {
      console.error('Error clearing all notifications:', error)
      throw error
    }
  }

  // Initialize ARIA live region on mount
  initializeAriaLiveRegion()

  // Cleanup on unmount
  onUnmounted(() => {
    // Clear all timeouts
    timeoutMap.value.forEach((timeoutId) => {
      window.clearTimeout(timeoutId)
    })
    timeoutMap.value.clear()

    // Remove ARIA live region
    if (ariaLiveRegion && document.body.contains(ariaLiveRegion)) {
      document.body.removeChild(ariaLiveRegion)
    }
  })

  // Return public API
  return {
    notifications,
    showNotification,
    clearNotification,
    clearAllNotifications
  }
}