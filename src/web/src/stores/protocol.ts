import { defineStore } from 'pinia' // v2.1.0
import { ref, computed } from 'vue' // v3.3.0
import { debounce } from 'lodash-es' // v4.17.21
import CryptoJS from 'crypto-js' // v4.1.1

// Internal imports
import { Protocol, ProtocolStatus } from '../types/protocol'
import { getProtocols, getProtocolById, enrollInProtocol } from '../api/protocol'
import { useUiStore } from './ui'

// Constants
const CACHE_EXPIRY = 5 * 60 * 1000 // 5 minutes
const SEARCH_DEBOUNCE = 300 // 300ms
const ENCRYPTION_KEY = process.env.VUE_APP_ENCRYPTION_KEY || 'default-key'

/**
 * Protocol store for managing protocol state with enhanced security and caching
 */
export const useProtocolStore = defineStore('protocol', () => {
  // UI store for notifications and loading state
  const uiStore = useUiStore()

  // State
  const protocols = ref<Protocol[]>([])
  const currentProtocol = ref<Protocol | null>(null)
  const loading = ref(false)
  const error = ref<Error | null>(null)
  const filters = ref({
    status: ProtocolStatus.ACTIVE,
    search: '',
    page: 1,
    pageSize: 20
  })
  const cache = ref(new Map<string, { data: Protocol; timestamp: number }>())

  // Computed
  const filteredProtocols = computed(() => {
    if (!filters.value.search) return protocols.value

    const searchTerm = filters.value.search.toLowerCase()
    return protocols.value.filter(protocol => 
      protocol.title.toLowerCase().includes(searchTerm) ||
      protocol.description.toLowerCase().includes(searchTerm)
    )
  })

  const activeProtocols = computed(() => 
    protocols.value.filter(p => p.status === ProtocolStatus.ACTIVE)
  )

  const totalPages = computed(() => 
    Math.ceil(filteredProtocols.value.length / filters.value.pageSize)
  )

  /**
   * Encrypts sensitive protocol data
   * @param data - Data to encrypt
   */
  function encryptData(data: any): string {
    return CryptoJS.AES.encrypt(
      JSON.stringify(data),
      ENCRYPTION_KEY
    ).toString()
  }

  /**
   * Decrypts sensitive protocol data
   * @param encryptedData - Encrypted data string
   */
  function decryptData(encryptedData: string): any {
    const bytes = CryptoJS.AES.decrypt(encryptedData, ENCRYPTION_KEY)
    return JSON.parse(bytes.toString(CryptoJS.enc.Utf8))
  }

  /**
   * Checks if cached data is still valid
   * @param timestamp - Cache timestamp
   */
  function isCacheValid(timestamp: number): boolean {
    return Date.now() - timestamp < CACHE_EXPIRY
  }

  /**
   * Fetches protocols with caching and encryption
   */
  async function fetchProtocols() {
    try {
      loading.value = true
      uiStore.setLoading(true)

      const response = await getProtocols({
        page: filters.value.page,
        pageSize: filters.value.pageSize,
        status: filters.value.status
      })

      // Process and encrypt sensitive data
      protocols.value = response.data.items.map(protocol => ({
        ...protocol,
        requirements: encryptData(protocol.requirements),
        safetyParams: encryptData(protocol.safetyParams)
      }))

      error.value = null
    } catch (err) {
      error.value = err as Error
      uiStore.notifyError('Failed to fetch protocols')
      console.error('Protocol fetch error:', err)
    } finally {
      loading.value = false
      uiStore.setLoading(false)
    }
  }

  /**
   * Fetches a single protocol by ID with caching
   * @param id - Protocol ID
   */
  async function fetchProtocolById(id: string) {
    try {
      loading.value = true
      uiStore.setLoading(true)

      // Check cache first
      const cached = cache.value.get(id)
      if (cached && isCacheValid(cached.timestamp)) {
        currentProtocol.value = cached.data
        return
      }

      const response = await getProtocolById(id)
      const protocol = response.data

      // Encrypt sensitive data before caching
      const processedProtocol = {
        ...protocol,
        requirements: encryptData(protocol.requirements),
        safetyParams: encryptData(protocol.safetyParams)
      }

      // Update cache
      cache.value.set(id, {
        data: processedProtocol,
        timestamp: Date.now()
      })

      currentProtocol.value = processedProtocol
      error.value = null
    } catch (err) {
      error.value = err as Error
      uiStore.notifyError('Failed to fetch protocol details')
      console.error('Protocol detail fetch error:', err)
    } finally {
      loading.value = false
      uiStore.setLoading(false)
    }
  }

  /**
   * Enrolls user in a protocol with validation
   * @param protocolId - Protocol ID to enroll in
   */
  async function enroll(protocolId: string): Promise<boolean> {
    try {
      loading.value = true
      uiStore.setLoading(true)

      const protocol = protocols.value.find(p => p.id === protocolId)
      if (!protocol) {
        throw new Error('Protocol not found')
      }

      if (protocol.status !== ProtocolStatus.ACTIVE) {
        throw new Error('Protocol is not active')
      }

      await enrollInProtocol(protocolId, {
        consent: true,
        initialData: {}
      })

      uiStore.notifySuccess('Successfully enrolled in protocol')
      return true
    } catch (err) {
      error.value = err as Error
      uiStore.notifyError('Failed to enroll in protocol')
      console.error('Protocol enrollment error:', err)
      return false
    } finally {
      loading.value = false
      uiStore.setLoading(false)
    }
  }

  // Debounced search handler
  const handleSearch = debounce((searchTerm: string) => {
    filters.value.search = searchTerm
    filters.value.page = 1 // Reset to first page on search
  }, SEARCH_DEBOUNCE)

  return {
    // State
    protocols,
    currentProtocol,
    loading,
    error,
    filters,

    // Computed
    filteredProtocols,
    activeProtocols,
    totalPages,

    // Actions
    fetchProtocols,
    fetchProtocolById,
    enroll,
    handleSearch,

    // Helper functions
    encryptData,
    decryptData
  }
})