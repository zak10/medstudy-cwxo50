// Vue.js v3.3.0+ type definitions for single-file components and static assets
// This file provides TypeScript declarations to enable proper type checking and IDE support

// Import Vue type definitions
import type { DefineComponent } from 'vue'

/**
 * Type declaration for Vue single-file components (.vue files)
 * Enables TypeScript to properly type-check Vue components
 */
declare module '*.vue' {
  // Define component as a Vue 3 DefineComponent with generic type parameters
  const component: DefineComponent<{}, {}, any>
  export default component
}

/**
 * Type declarations for static image assets
 * Enables proper importing and type checking of image files
 */
declare module '*.svg' {
  const content: string
  export default content
}

declare module '*.png' {
  const content: string
  export default content
}

declare module '*.jpg' {
  const content: string
  export default content
}

/**
 * Type declarations for font assets
 * Enables proper importing and type checking of font files
 */
declare module '*.woff2' {
  const content: string
  export default content
}