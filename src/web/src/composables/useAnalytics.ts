// External imports
import { ref, computed, onMounted, onUnmounted } from 'vue' // v3.3.0
import { debounce } from 'lodash-es' // v4.17.21

// Internal imports
import { useAnalysisStore } from '../stores/analysis'
import type { 
  AnalysisRequest, 
  AnalysisResult,
  StatisticalSummary,
  PatternDetection,
  AnalysisOptions,
  VisualizationConfig
} from '../types/analysis'
import { useUiStore } from '../stores/ui'

// Constants
const ANALYSIS_CACHE_DURATION = 5 * 60 * 1000 // 5 minutes
const DEBOUNCE_DELAY = 500 // 500ms
const MIN_DATA_QUALITY_SCORE = 0.95
const MAX_RETRY_ATTEMPTS = 3

/**
 * Interface for analysis operation options
 */
interface AnalyticsOptions {
  cacheResults?: boolean
  autoRefresh?: boolean
  refreshInterval?: number
  validateData?: boolean
}

/**
 * Vue composable for managing protocol analysis operations
 * Implements caching, error handling, and performance optimization
 */
export function useAnalytics(
  protocolId: string,
  options: AnalyticsOptions = {}
) {
  // Store instances
  const analysisStore = useAnalysisStore()
  const uiStore = useUiStore()

  // Reactive references
  const currentAnalysis = ref<AnalysisResult | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const refreshTimer = ref<number | null>(null)
  const retryCount = ref(0)

  // Computed properties
  const hasAnalysis = computed(() => 
    currentAnalysis.value !== null && 
    currentAnalysis.value.metadata.dataQualityScore >= MIN_DATA_QUALITY_SCORE
  )

  const statisticalSummary = computed<StatisticalSummary | null>(() => 
    currentAnalysis.value?.statisticalSummary || null
  )

  const analysisQuality = computed(() => 
    currentAnalysis.value?.metadata.dataQualityScore ?? 0
  )

  const significantPatterns = computed<PatternDetection[]>(() => 
    currentAnalysis.value?.patterns.filter(p => p.confidenceScore >= 0.95) ?? []
  )

  /**
   * Fetches analysis results with caching and retry logic
   */
  const fetchAnalysis = async (): Promise<void> => {
    try {
      loading.value = true
      error.value = null

      // Check cache if enabled
      if (options.cacheResults && analysisStore.hasValidAnalysis) {
        currentAnalysis.value = analysisStore.currentAnalysis
        return
      }

      await analysisStore.fetchAnalysisResults(protocolId, !options.cacheResults)
      currentAnalysis.value = analysisStore.currentAnalysis
      retryCount.value = 0

    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to fetch analysis'
      
      // Implement retry logic
      if (retryCount.value < MAX_RETRY_ATTEMPTS) {
        retryCount.value++
        const delay = Math.min(1000 * Math.pow(2, retryCount.value), 10000)
        setTimeout(fetchAnalysis, delay)
      } else {
        uiStore.notifyError('Failed to fetch analysis after multiple attempts')
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * Generates new analysis with enhanced validation
   */
  const generateAnalysis = async (
    request: Omit<AnalysisRequest, 'protocolId'>
  ): Promise<void> => {
    try {
      loading.value = true
      error.value = null

      // Validate request data
      if (!request.dataPoints?.length) {
        throw new Error('Analysis requires data points')
      }

      const analysisRequest: AnalysisRequest = {
        ...request,
        protocolId,
        confidenceThreshold: 0.95
      }

      await analysisStore.runAnalysis(analysisRequest)
      currentAnalysis.value = analysisStore.currentAnalysis
      uiStore.notifySuccess('Analysis generated successfully')

    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to generate analysis'
      uiStore.notifyError(error.value)
    } finally {
      loading.value = false
    }
  }

  /**
   * Updates visualization configuration with accessibility support
   */
  const updateVisualization = (config: VisualizationConfig): void => {
    try {
      analysisStore.updateVisualization({
        ...config,
        config: {
          ...config.config,
          responsive: true,
          showLegend: true
        }
      })
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update visualization'
      uiStore.notifyError(error.value)
    }
  }

  /**
   * Exports analysis results in specified format
   */
  const exportResults = async (format: 'csv' | 'json' | 'pdf'): Promise<void> => {
    try {
      loading.value = true
      error.value = null

      if (!currentAnalysis.value) {
        throw new Error('No analysis results to export')
      }

      await analysisStore.exportAnalysis(protocolId, format)
      uiStore.notifySuccess(`Analysis exported as ${format.toUpperCase()}`)

    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to export analysis'
      uiStore.notifyError(error.value)
    } finally {
      loading.value = false
    }
  }

  /**
   * Clears analysis cache
   */
  const clearCache = (): void => {
    analysisStore.$reset()
    currentAnalysis.value = null
    error.value = null
  }

  // Debounced analysis refresh
  const debouncedRefresh = debounce(fetchAnalysis, DEBOUNCE_DELAY)

  // Lifecycle hooks
  onMounted(() => {
    // Initial fetch
    fetchAnalysis()

    // Set up auto-refresh if enabled
    if (options.autoRefresh && options.refreshInterval) {
      refreshTimer.value = window.setInterval(
        debouncedRefresh,
        options.refreshInterval
      )
    }
  })

  onUnmounted(() => {
    // Clear auto-refresh timer
    if (refreshTimer.value) {
      clearInterval(refreshTimer.value)
    }
    // Clear debounce
    debouncedRefresh.cancel()
  })

  return {
    // State
    currentAnalysis,
    loading,
    error,
    
    // Computed
    hasAnalysis,
    statisticalSummary,
    analysisQuality,
    significantPatterns,
    
    // Methods
    fetchAnalysis,
    generateAnalysis,
    updateVisualization,
    exportResults,
    clearCache
  }
}