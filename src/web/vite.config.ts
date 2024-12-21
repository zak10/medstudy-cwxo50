import { defineConfig } from 'vite'; // ^4.4.0
import vue from '@vitejs/plugin-vue'; // ^4.2.0
import path from 'path'; // ^1.8.0

export default defineConfig({
  // Vue plugin configuration with advanced template compilation options
  plugins: [
    vue({
      template: {
        compilerOptions: {
          // Handle custom element tags for web components
          isCustomElement: (tag) => tag.includes('-'),
          // Enable static hoisting for performance
          hoistStatic: true,
          // Enable identifier prefixing for SSR compatibility
          prefixIdentifiers: true
        },
        // Enable reactivity transform for better performance
        reactivityTransform: true,
        script: {
          // Enable defineModel macro for v-model composition
          defineModel: true,
          // Enable props destructuring
          propsDestructure: true
        }
      }
    })
  ],

  // Module resolution configuration
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@views': path.resolve(__dirname, './src/views'),
      '@stores': path.resolve(__dirname, './src/stores'),
      '@utils': path.resolve(__dirname, './src/utils')
    },
    extensions: ['.ts', '.tsx', '.js', '.jsx', '.vue', '.json'],
    preserveSymlinks: true
  },

  // Build configuration for production
  build: {
    target: 'es2020',
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: true,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.debug']
      },
      mangle: true
    },
    rollupOptions: {
      output: {
        // Manual chunk splitting for optimal caching
        manualChunks: {
          vue: ['vue', 'vue-router', 'pinia'],
          chart: ['chart.js'],
          ui: ['vuetify'],
          utils: ['lodash', 'date-fns'],
          forms: ['vee-validate', 'yup']
        },
        // Asset naming patterns
        chunkFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]'
      }
    },
    cssCodeSplit: true,
    reportCompressedSize: true,
    chunkSizeWarningLimit: 1000
  },

  // Development server configuration
  server: {
    port: 3000,
    strictPort: true,
    cors: true,
    // API proxy configuration for backend integration
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: true,
        configure: (proxy, options) => {
          // Custom proxy configuration for WebSocket support
          proxy.on('error', (err, req, res) => {
            console.warn('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, res) => {
            // Add custom headers if needed
          });
        }
      }
    },
    // Hot Module Replacement configuration
    hmr: {
      overlay: true,
      clientPort: 3000,
      timeout: 120000
    },
    watch: {
      ignored: ['**/node_modules/**', '**/dist/**', '**/.git/**']
    }
  },

  // Dependency optimization configuration
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'chart.js', 'vuetify'],
    exclude: ['vitest'],
    esbuildOptions: {
      target: 'es2020'
    }
  },

  // CSS processing configuration
  css: {
    devSourcemap: true,
    preprocessorOptions: {
      scss: {
        additionalData: "@import '@/styles/variables.scss';"
      }
    }
  }
});