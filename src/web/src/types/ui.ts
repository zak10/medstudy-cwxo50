// Vuetify theme definition import - v3.3.0
import type { ThemeDefinition } from 'vuetify'

/**
 * Notification type variants for the application's notification system
 * @enum {string}
 */
export enum NotificationType {
  SUCCESS = 'success',
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info'
}

/**
 * Type definition for hex color values with WCAG validation
 * Must be a valid 3 or 6 character hex color code
 */
export type HexColor = `#${string}`

/**
 * Type definition for responsive breakpoint keys
 */
export type Breakpoint = 'mobile' | 'tablet' | 'desktop' | 'wide'

/**
 * Type definition for theme mode selection
 */
export type ThemeMode = 'light' | 'dark'

/**
 * Interface for WCAG 2.1 AA compliant color system
 * Defines the application's core color palette
 */
export interface ColorPalette {
  primary: HexColor
  secondary: HexColor
  accent: HexColor
  error: HexColor
  warning: HexColor
  info: HexColor
  success: HexColor
  background: HexColor
  surface: HexColor
  text: {
    primary: HexColor
    secondary: HexColor
    disabled: HexColor
  }
}

/**
 * Interface for typography system configuration
 * Implements consistent typography across the application
 */
export interface Typography {
  fontFamily: {
    primary: string   // Inter font family
    secondary: string // Open Sans font family
  }
  fontWeights: {
    regular: 400
    medium: 500
    semibold: 600
    bold: 700
  }
  fontSize: {
    xs: string
    sm: string
    base: string
    lg: string
    xl: string
    '2xl': string
  }
  lineHeight: {
    tight: number
    normal: number
    relaxed: number
  }
}

/**
 * Interface for 8-point grid spacing system
 * Ensures consistent spacing throughout the application
 */
export interface Spacing {
  baseUnit: number // 8px base unit
  scale: {
    xs: number  // 0.5x base unit
    sm: number  // 1x base unit
    md: number  // 2x base unit
    lg: number  // 3x base unit
    xl: number  // 4x base unit
  }
  container: {
    padding: number   // Container padding
    maxWidth: number  // Maximum container width
  }
}

/**
 * Interface for responsive breakpoints
 * Defines the application's responsive design breakpoints
 */
export interface Breakpoints {
  mobile: number  // 320px
  tablet: number  // 768px
  desktop: number // 1024px
  wide: number    // 1440px
}

/**
 * Interface for elevation levels using box-shadows
 * Implements consistent depth hierarchy
 */
export interface Elevation {
  level1: string // Subtle elevation
  level2: string // Moderate elevation
  level3: string // Prominent elevation
  level4: string // Maximum elevation
}

/**
 * Comprehensive theme configuration interface
 * Combines all theme-related interfaces into a single theme definition
 */
export interface Theme extends ThemeDefinition {
  colors: ColorPalette
  typography: Typography
  spacing: Spacing
  breakpoints: Breakpoints
  elevation: Elevation
}