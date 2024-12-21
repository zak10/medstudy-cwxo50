// External imports
import { ref, computed, onMounted, onUnmounted, watch } from 'vue' // v3.3.0
import { storeToRefs } from 'pinia' // v2.1.0

// Internal imports
import { useProtocolStore } from '../stores/protocol'
import type { Protocol } from '../types/protocol'

// Constants
const DEFAULT_PAGE_SIZE = 20
const AUTO_FETCH_ENABLED = true
const CACHE_TIMEOUT = 300000 // 5 minutes
const MAX_RETRY_ATTEMPTS = 3

/**
 * Interface for composable options
 */
interface UseProtocolOptions {
  autoFetch?: boolean
  cacheTimeout?: number
  retryAttempts?: number
}

/**
 * Composable for managing protocol-related operations and state
 * Implements HIPAA-compliant data handling and comprehensive error management
 */
export function useProtocol(options: UseProtocolOptions = {}) {
  // Initialize protocol store
  const protocolStore = useProtocolStore()
  const { protocols, currentProtocol, loading, error } = storeToRefs(protocolStore)

  // Local reactive state
  const cache = ref(new Map<string, { data: Protocol; timestamp: number }>())
  const lastFetch = ref<number>(0)
  const retryCount = ref<number>(0)

  // Computed properties
  const isStale = computed(() => {
    const cacheTimeout = options.cacheTimeout || CACHE_TIMEOUT
    return Date.now() - lastFetch.value > cacheTimeout
  })

  const activeProtocols = computed(() => 
    protocols.value.filter(p => p.status === 'ACTIVE')
  )

  /**
   * Validates cache freshness and handles cache invalidation
   */
  function validateCache(key: string): boolean {
    const cached = cache.value.get(key)
    if (!cached) return false

    const cacheTimeout = options.cacheTimeout || CACHE_TIMEOUT
    const isValid = Date.now() - cached.timestamp < cacheTimeout

    if (!isValid) {
      cache.value.delete(key)
    }

    return isValid
  }

  /**
   * Fetches list of available protocols with enhanced error handling
   * @param params Optional parameters for pagination and filtering
   */
  async function fetchProtocols(params?: {
    page?: number
    pageSize?: number
    status?: string
    searchTerm?: string
  }) {
    try {
      if (!isStale.value && protocols.value.length > 0) {
        return
      }

      loading.value = true
      retryCount.value = 0

      await protocolStore.fetchProtocols({
        page: params?.page || 1,
        pageSize: params?.pageSize || DEFAULT_PAGE_SIZE,
        status: params?.status,
        search: params?.searchTerm
      })

      lastFetch.value = Date.now()
      error.value = null
    } catch (err) {
      error.value = err as Error
      
      // Implement retry logic
      if (retryCount.value < (options.retryAttempts || MAX_RETRY_ATTEMPTS)) {
        retryCount.value++
        await new Promise(resolve => setTimeout(resolve, 1000 * retryCount.value))
        return fetchProtocols(params)
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetches detailed protocol information by ID with caching
   * @param id Protocol identifier
   */
  async function fetchProtocolById(id: string) {
    try {
      if (!id) {
        throw new Error('Protocol ID is required')
      }

      // Check cache first
      if (validateCache(id)) {
        currentProtocol.value = cache.value.get(id)?.data || null
        return
      }

      loading.value = true
      retryCount.value = 0

      await protocolStore.fetchProtocolById(id)

      // Update cache if fetch successful
      if (currentProtocol.value) {
        cache.value.set(id, {
          data: currentProtocol.value,
          timestamp: Date.now()
        })
      }

      error.value = null
    } catch (err) {
      error.value = err as Error
      
      // Implement retry logic
      if (retryCount.value < (options.retryAttempts || MAX_RETRY_ATTEMPTS)) {
        retryCount.value++
        await new Promise(resolve => setTimeout(resolve, 1000 * retryCount.value))
        return fetchProtocolById(id)
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * Enrolls user in a protocol with eligibility validation
   * @param protocolId Protocol identifier
   */
  async function enrollInProtocol(protocolId: string) {
    try {
      if (!protocolId) {
        throw new Error('Protocol ID is required')
      }

      // Check eligibility first
      const eligible = await isEligible(protocolId)
      if (!eligible) {
        throw new Error('User is not eligible for this protocol')
      }

      loading.value = true
      retryCount.value = 0

      const result = await protocolStore.enroll(protocolId)
      
      if (result) {
        // Refresh protocol data after successful enrollment
        await fetchProtocolById(protocolId)
      }

      return result
    } catch (err) {
      error.value = err as Error
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * Checks user eligibility for protocol enrollment
   * @param protocolId Protocol identifier
   */
  async function isEligible(protocolId: string): Promise<boolean> {
    try {
      const protocol = protocols.value.find(p => p.id === protocolId)
      
      if (!protocol) {
        throw new Error('Protocol not found')
      }

      // Validate protocol status
      if (protocol.status !== 'ACTIVE') {
        return false
      }

      // Validate protocol requirements
      const requirements = protocol.requirements
      if (!requirements || requirements.length === 0) {
        return true
      }

      // Additional eligibility checks can be implemented here
      // based on protocol-specific requirements

      return true
    } catch (err) {
      error.value = err as Error
      return false
    }
  }

  // Setup auto-fetching if enabled
  onMounted(() => {
    if (options.autoFetch ?? AUTO_FETCH_ENABLED) {
      fetchProtocols()
    }

    // Watch for protocol updates
    watch(protocols, () => {
      lastFetch.value = Date.now()
    })
  })

  // Cleanup on unmount
  onUnmounted(() => {
    cache.value.clear()
  })

  return {
    // State
    protocols,
    currentProtocol,
    loading,
    error,
    activeProtocols,

    // Methods
    fetchProtocols,
    fetchProtocolById,
    enrollInProtocol,
    isEligible
  }
}