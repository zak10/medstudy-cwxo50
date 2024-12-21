<template>
  <div 
    class="error-boundary" 
    role="alert" 
    aria-live="assertive"
  >
    <template v-if="error">
      <!-- Custom fallback component if provided -->
      <component 
        v-if="fallbackComponent"
        :is="fallbackComponent"
        :error="error"
        :error-info="errorInfo"
        :retry-count="retryCount"
        :reset-error="resetError"
      />
      
      <!-- Default error UI -->
      <div v-else class="error-message">
        <h2>Something went wrong</h2>
        <p>{{ error.message }}</p>
        
        <button 
          class="retry-button"
          @click="resetError"
          :disabled="retryCount >= maxRetries"
        >
          {{ retryCount < maxRetries ? 'Retry' : 'Max retries reached' }}
        </button>

        <!-- Show detailed error info in development -->
        <details 
          v-if="process.env.NODE_ENV === 'development'"
          class="error-details"
        >
          <summary>Error Details</summary>
          <pre>{{ error.stack }}</pre>
          <pre v-if="componentStack">Component Stack: {{ componentStack }}</pre>
          <pre v-if="errorInfo">Additional Info: {{ JSON.stringify(errorInfo, null, 2) }}</pre>
        </details>
      </div>
    </template>

    <!-- Render child components when no error -->
    <template v-else>
      <slot />
    </template>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue' // v3.3.0
import * as Sentry from '@sentry/vue' // v7.0.0
import { NotificationType } from '../../types/ui'

interface ErrorInfo {
  componentStack?: string;
  lifecycleHook?: string;
  component?: string;
  props?: Record<string, any>;
}

export default defineComponent({
  name: 'ErrorBoundary',

  props: {
    fallbackComponent: {
      type: Object as PropType<any>,
      required: false,
      default: null,
      validator: (value: any) => {
        return value === null || typeof value === 'object'
      }
    }
  },

  data() {
    return {
      error: null as Error | null,
      errorInfo: null as ErrorInfo | null,
      retryCount: 0,
      maxRetries: 3,
      componentStack: null as string | null
    }
  },

  errorCaptured(error: Error, instance: any, info: string) {
    this.handleError(error, {
      componentStack: info,
      component: instance?.$options?.name,
      lifecycleHook: info,
      props: instance?.$props
    })
    return false // Prevent error propagation
  },

  methods: {
    handleError(error: Error, errorInfo: ErrorInfo): void {
      // Set error state
      this.error = error
      this.errorInfo = errorInfo
      this.componentStack = errorInfo.componentStack || null

      // Development logging
      if (process.env.NODE_ENV === 'development') {
        console.error('ErrorBoundary caught an error:', {
          error,
          errorInfo,
          componentStack: this.componentStack,
          retryCount: this.retryCount
        })
      }

      // Report to Sentry with enhanced context
      Sentry.captureException(error, {
        extra: {
          componentStack: this.componentStack,
          errorInfo: this.errorInfo,
          retryCount: this.retryCount,
          maxRetries: this.maxRetries
        },
        tags: {
          componentName: errorInfo.component || 'unknown',
          lifecycleHook: errorInfo.lifecycleHook || 'unknown',
          errorBoundary: 'vue'
        },
        level: 'error'
      })

      // Emit error event for parent components
      this.$emit('error', {
        error,
        errorInfo,
        retryCount: this.retryCount
      })

      // Display error notification
      this.$emit('show-notification', {
        type: NotificationType.ERROR,
        message: 'An error occurred. Please try again or contact support if the problem persists.',
        error: error.message
      })
    },

    resetError(): void {
      // Implement exponential backoff for retries
      const backoffDelay = Math.min(1000 * Math.pow(2, this.retryCount), 5000)

      setTimeout(() => {
        if (this.retryCount < this.maxRetries) {
          this.retryCount++
          this.error = null
          this.errorInfo = null
          this.componentStack = null

          // Log recovery attempt
          if (process.env.NODE_ENV === 'development') {
            console.log(`Attempting recovery - Retry ${this.retryCount}/${this.maxRetries}`)
          }

          // Report recovery attempt to Sentry
          Sentry.addBreadcrumb({
            category: 'error-boundary',
            message: `Recovery attempt ${this.retryCount}/${this.maxRetries}`,
            level: 'info'
          })

          // Emit recovery event
          this.$emit('recovery-attempt', {
            retryCount: this.retryCount,
            maxRetries: this.maxRetries
          })
        }
      }, backoffDelay)
    }
  }
})
</script>

<style scoped>
.error-boundary {
  width: 100%;
  padding: 1rem;
  margin: 0.5rem 0;
}

.error-message {
  background-color: #fef2f2;
  border: 1px solid #fee2e2;
  border-radius: 0.375rem;
  padding: 1rem;
  color: #991b1b;
}

.error-message h2 {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.retry-button {
  margin-top: 1rem;
  padding: 0.5rem 1rem;
  background-color: #dc2626;
  color: white;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.retry-button:hover:not(:disabled) {
  background-color: #b91c1c;
}

.retry-button:disabled {
  background-color: #f87171;
  cursor: not-allowed;
}

.error-details {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #fff1f2;
  border-radius: 0.25rem;
}

.error-details summary {
  cursor: pointer;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.error-details pre {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.875rem;
  line-height: 1.25rem;
  padding: 0.5rem;
  background-color: #fff;
  border-radius: 0.25rem;
  margin: 0.5rem 0;
}
</style>