// External imports
import { defineStore } from 'pinia' // v2.1.0
import { ref, computed, watch } from 'vue' // v3.3.0

// Internal imports
import { 
  type StatisticalSummary, 
  type AnalysisRequest, 
  type AnalysisResult,
  type PatternDetection,
  type VisualizationConfig,
  type AnalysisMetadata
} from '../types/analysis'
import { getProtocolResults } from '../api/analysis'
import { useUiStore } from './ui'

// Constants
const CACHE_EXPIRATION = 5 * 60 * 1000 // 5 minutes
const MIN_CONFIDENCE_THRESHOLD = 0.95
const MAX_CACHE_SIZE = 50

/**
 * Interface for cached analysis results
 */
interface CachedAnalysis {
  result: AnalysisResult;
  timestamp: number;
}

/**
 * Interface for error tracking details
 */
interface ErrorDetail {
  message: string;
  timestamp: number;
  retryCount: number;
}

/**
 * Pinia store for managing protocol analysis state
 * Implements caching, validation, and error handling
 */
export const useAnalysisStore = defineStore('analysis', () => {
  // UI store for notifications and loading state
  const uiStore = useUiStore()

  // State
  const currentAnalysis = ref<AnalysisResult | null>(null)
  const analysisHistory = ref<Map<string, CachedAnalysis>>(new Map())
  const visualizationConfigs = ref<VisualizationConfig[]>([])
  const confidenceThreshold = ref<number>(MIN_CONFIDENCE_THRESHOLD)
  const analysisErrors = ref<Map<string, ErrorDetail>>(new Map())

  // Computed
  const significantPatterns = computed<PatternDetection[]>(() => {
    if (!currentAnalysis.value?.patterns) return []
    return currentAnalysis.value.patterns.filter(
      pattern => pattern.confidenceScore >= confidenceThreshold.value
    )
  })

  const hasValidAnalysis = computed<boolean>(() => {
    if (!currentAnalysis.value) return false
    const timestamp = analysisHistory.value.get(currentAnalysis.value.metadata.version)?.timestamp
    return timestamp ? (Date.now() - timestamp) < CACHE_EXPIRATION : false
  })

  const analysisMetadata = computed<AnalysisMetadata | null>(() => 
    currentAnalysis.value?.metadata || null
  )

  /**
   * Validates analysis results for data quality and completeness
   */
  function validateAnalysisResults(results: AnalysisResult): boolean {
    if (!results.statisticalSummary || !results.patterns || !results.metadata) {
      return false
    }
    return results.metadata.dataQualityScore >= 0.95 && 
           results.metadata.completeness >= 0.95
  }

  /**
   * Manages the analysis cache with size limits
   */
  function manageCache(): void {
    if (analysisHistory.value.size > MAX_CACHE_SIZE) {
      // Remove oldest entries
      const entries = Array.from(analysisHistory.value.entries())
      const sortedEntries = entries.sort((a, b) => a[1].timestamp - b[1].timestamp)
      const entriesToRemove = sortedEntries.slice(0, entries.length - MAX_CACHE_SIZE)
      entriesToRemove.forEach(([key]) => analysisHistory.value.delete(key))
    }
  }

  /**
   * Fetches analysis results with caching and validation
   */
  async function fetchAnalysisResults(
    protocolId: string, 
    forceRefresh: boolean = false
  ): Promise<void> {
    try {
      uiStore.setLoading(true)

      // Check cache if refresh not forced
      if (!forceRefresh && analysisHistory.value.has(protocolId)) {
        const cached = analysisHistory.value.get(protocolId)
        if (cached && (Date.now() - cached.timestamp) < CACHE_EXPIRATION) {
          currentAnalysis.value = cached.result
          return
        }
      }

      const response = await getProtocolResults(protocolId)
      const results = response.data

      // Validate results
      if (!validateAnalysisResults(results)) {
        throw new Error('Invalid analysis results received')
      }

      // Update cache and current analysis
      currentAnalysis.value = results
      analysisHistory.value.set(protocolId, {
        result: results,
        timestamp: Date.now()
      })

      // Manage cache size
      manageCache()

      // Clear any existing errors
      analysisErrors.value.delete(protocolId)

      uiStore.notifySuccess('Analysis results updated successfully')
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch analysis results'
      
      // Track error details
      analysisErrors.value.set(protocolId, {
        message: errorMessage,
        timestamp: Date.now(),
        retryCount: (analysisErrors.value.get(protocolId)?.retryCount || 0) + 1
      })

      uiStore.notifyError(errorMessage)
      throw error
    } finally {
      uiStore.setLoading(false)
    }
  }

  /**
   * Updates visualization configuration with accessibility support
   */
  function updateVisualization(config: VisualizationConfig): void {
    // Validate configuration
    if (!config.chartType || !config.data || !config.layout) {
      throw new Error('Invalid visualization configuration')
    }

    // Ensure accessibility features
    const accessibleConfig = {
      ...config,
      config: {
        ...config.config,
        responsive: true,
        displayModeBar: true,
        showLegend: true
      },
      layout: {
        ...config.layout,
        font: {
          family: 'Inter, sans-serif',
          size: 14
        },
        margin: {
          l: 50,
          r: 50,
          t: 50,
          b: 50
        }
      }
    }

    // Update or add configuration
    const index = visualizationConfigs.value.findIndex(
      vc => vc.chartType === config.chartType
    )
    
    if (index !== -1) {
      visualizationConfigs.value[index] = accessibleConfig
    } else {
      visualizationConfigs.value.push(accessibleConfig)
    }
  }

  /**
   * Updates confidence threshold with validation
   */
  function setConfidenceThreshold(threshold: number): void {
    if (threshold < MIN_CONFIDENCE_THRESHOLD || threshold > 1) {
      throw new Error(`Confidence threshold must be between ${MIN_CONFIDENCE_THRESHOLD} and 1`)
    }
    confidenceThreshold.value = threshold
  }

  // Watch for changes in confidence threshold
  watch(confidenceThreshold, (newThreshold) => {
    if (currentAnalysis.value) {
      // Recompute significant patterns
      const patterns = currentAnalysis.value.patterns.filter(
        pattern => pattern.confidenceScore >= newThreshold
      )
      // Update visualizations if needed
      if (patterns.length !== significantPatterns.value.length) {
        uiStore.notifyInfo(`Found ${patterns.length} significant patterns at ${newThreshold} confidence`)
      }
    }
  })

  return {
    // State
    currentAnalysis,
    visualizationConfigs,
    confidenceThreshold,
    analysisErrors,

    // Computed
    significantPatterns,
    hasValidAnalysis,
    analysisMetadata,

    // Actions
    fetchAnalysisResults,
    updateVisualization,
    setConfidenceThreshold
  }
})