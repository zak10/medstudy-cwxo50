import { defineConfig } from 'vitest/config'; // ^0.34.0
import { mergeConfig } from 'vite'; // ^4.4.0
import viteConfig from './vite.config';

/**
 * Vitest Configuration
 * Extends the base Vite configuration and sets up the test environment
 * with coverage reporting and Vue-specific test utilities
 */
export default defineConfig((configEnv) => {
  return mergeConfig(
    viteConfig,
    defineConfig({
      test: {
        // Enable global test utilities and mocks
        globals: true,

        // Use jsdom for DOM emulation in tests
        environment: 'jsdom',

        // Global setup files for Vue Test Utils and mocks
        setupFiles: ['./tests/setup.ts'],

        // Test file patterns
        include: [
          'tests/**/*.spec.ts',
          'tests/**/*.test.ts'
        ],

        // Exclude patterns
        exclude: [
          'node_modules',
          'dist',
          '**/*.d.ts',
          'coverage/**/*'
        ],

        // Coverage configuration using v8 provider
        coverage: {
          provider: 'v8',
          reporter: [
            'text',      // Console output
            'json',      // Machine-readable format
            'html',      // Browser-viewable report
            'lcov'       // Standard coverage format
          ],
          exclude: [
            'node_modules/',
            'tests/',
            '**/*.d.ts',
            'src/types/',
            '**/*.spec.ts',
            '**/*.test.ts'
          ],
          // Enforce minimum 80% coverage across all metrics
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80,
          reportsDirectory: './coverage'
        },

        // Dependencies to be inlined during testing
        deps: {
          inline: [
            // Vue ecosystem packages that require special handling
            'vuetify',
            '@vue',
            '@vueuse',
            'vue-router',
            'pinia'
          ]
        },

        // Test timeouts (in milliseconds)
        testTimeout: 10000,
        hookTimeout: 10000,

        // Reuse path aliases from Vite config
        resolve: viteConfig.resolve
      }
    })
  );
});