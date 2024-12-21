<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <div
      v-show="modelValue"
      class="modal-backdrop"
      aria-hidden="true"
      data-test="modal-backdrop"
      @click="handleBackdropClick"
      @touchstart.prevent="handleBackdropClick"
    />
    
    <!-- Modal Container -->
    <div
      v-show="modelValue"
      class="modal-container"
      role="dialog"
      aria-modal="true"
      :aria-labelledby="title ? 'modal-title' : undefined"
      :style="{ width, maxWidth: '90vw' }"
      data-test="modal-container"
    >
      <!-- Header Section -->
      <header v-if="title" class="modal-header">
        <h2 id="modal-title" class="modal-title">{{ title }}</h2>
        <button
          type="button"
          class="modal-close"
          aria-label="Close modal"
          @click="handleBackdropClick"
        >
          <span aria-hidden="true">&times;</span>
        </button>
      </header>

      <!-- Content Section -->
      <div class="modal-content">
        <slot />
      </div>

      <!-- Footer Section -->
      <footer v-if="$slots.footer" class="modal-footer">
        <slot name="footer" />
      </footer>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'

// Define props with TypeScript types
interface Props {
  modelValue: boolean
  title?: string
  width?: string
  closeOnBackdrop?: boolean
  focusFirst?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  title: '',
  width: '500px',
  closeOnBackdrop: true,
  focusFirst: ''
})

// Define emits with TypeScript types
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'close'): void
  (e: 'opened'): void
}>()

// Store references for focus management
const previousActiveElement = ref<HTMLElement | null>(null)
let focusableElements: HTMLElement[] = []

// Handle backdrop click
const handleBackdropClick = (event: Event) => {
  event.stopPropagation()
  if (props.closeOnBackdrop) {
    emit('update:modelValue', false)
    emit('close')
    restoreFocus()
  }
}

// Handle escape key press
const handleEscapeKey = (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    event.preventDefault()
    emit('update:modelValue', false)
    emit('close')
    restoreFocus()
  }
}

// Focus trap implementation
const trapFocus = (event: KeyboardEvent) => {
  if (event.key !== 'Tab') return

  const modal = event.currentTarget as HTMLElement
  focusableElements = Array.from(
    modal.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
  ) as HTMLElement[]

  if (focusableElements.length === 0) return

  const firstElement = focusableElements[0]
  const lastElement = focusableElements[focusableElements.length - 1]

  if (event.shiftKey) {
    if (document.activeElement === firstElement) {
      lastElement.focus()
      event.preventDefault()
    }
  } else {
    if (document.activeElement === lastElement) {
      firstElement.focus()
      event.preventDefault()
    }
  }
}

// Focus management helpers
const setInitialFocus = () => {
  if (props.focusFirst) {
    const firstElement = document.querySelector(props.focusFirst) as HTMLElement
    if (firstElement) {
      firstElement.focus()
    }
  } else {
    const firstFocusable = focusableElements[0]
    if (firstFocusable) {
      firstFocusable.focus()
    }
  }
}

const restoreFocus = () => {
  if (previousActiveElement.value) {
    previousActiveElement.value.focus()
  }
}

// Lifecycle hooks
onMounted(() => {
  previousActiveElement.value = document.activeElement as HTMLElement
  document.addEventListener('keydown', handleEscapeKey)
  document.addEventListener('keydown', trapFocus)
  
  // Set aria-hidden on main app
  const mainApp = document.getElementById('app')
  if (mainApp) {
    mainApp.setAttribute('aria-hidden', 'true')
  }

  // Initial focus management
  setInitialFocus()
  
  // Emit opened event after animation
  setTimeout(() => emit('opened'), 300)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscapeKey)
  document.removeEventListener('keydown', trapFocus)
  
  // Restore aria-hidden on main app
  const mainApp = document.getElementById('app')
  if (mainApp) {
    mainApp.removeAttribute('aria-hidden')
  }
  
  restoreFocus()
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/_variables' as vars;
@use '@/assets/styles/_animations' as animations;

.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(vars.$colors.gray-900, 0.75);
  z-index: 50;
  will-change: opacity;
  -webkit-tap-highlight-color: transparent;
  @include animations.fade-in(0.2s);
}

.modal-container {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: #fff;
  border-radius: vars.$spacing-2;
  box-shadow: map-get(vars.$elevation-levels, 3);
  z-index: 51;
  max-height: 90vh;
  overflow-y: auto;
  will-change: opacity, transform;
  -webkit-overflow-scrolling: touch;
  @include animations.fade-in(0.3s);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: vars.$spacing-4;
  border-bottom: 1px solid vars.$colors.gray-200;
}

.modal-title {
  margin: 0;
  font-family: vars.$font-family-primary;
  font-size: 1.25rem;
  font-weight: map-get(vars.$font-weights, semibold);
  color: vars.$colors.gray-900;
}

.modal-close {
  padding: vars.$spacing-2;
  background: transparent;
  border: none;
  color: vars.$colors.gray-500;
  cursor: pointer;
  transition: color 0.2s ease;

  &:hover,
  &:focus {
    color: vars.$colors.gray-700;
  }

  &:focus {
    outline: 2px solid vars.$colors.primary;
    outline-offset: 2px;
  }
}

.modal-content {
  padding: vars.$spacing-4;
}

.modal-footer {
  padding: vars.$spacing-4;
  border-top: 1px solid vars.$colors.gray-200;
  display: flex;
  justify-content: flex-end;
  gap: vars.$spacing-2;
}

@media (max-width: map-get(vars.$breakpoints, mobile)) {
  .modal-container {
    width: 100% !important;
    max-width: none !important;
    height: 100%;
    border-radius: 0;
  }
}
</style>