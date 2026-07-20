import { ref } from 'vue'

const STORAGE_KEY = 'restocking_submitted_orders'

const loadFromStorage = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch (err) {
    console.error('Failed to parse submitted orders from storage:', err)
    return []
  }
}

// Shared state (singleton pattern), hydrated from localStorage since this
// feature intentionally has no backend persistence
const submittedOrders = ref(loadFromStorage())

const persist = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(submittedOrders.value))
}

export function useSubmittedOrders() {
  const addSubmittedOrder = (order) => {
    submittedOrders.value.unshift(order)
    persist()
  }

  return {
    submittedOrders,
    addSubmittedOrder
  }
}
