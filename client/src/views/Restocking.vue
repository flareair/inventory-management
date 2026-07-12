<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div class="card">
      <div class="card-header">
        <h3 class="card-title">{{ t('restocking.budgetLabel') }}</h3>
        <div class="budget-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
      </div>
      <input
        type="range"
        min="0"
        max="50000"
        step="500"
        v-model.number="budget"
        class="budget-slider"
      />
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="successMessage" class="success-message">{{ successMessage }}</div>
      <div v-if="submitError" class="error">{{ submitError }}</div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations') }} ({{ recommendations.length }})</h3>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.noRecommendations') }}
        </div>
        <template v-else>
          <div class="table-container">
            <table>
              <thead>
                <tr>
                  <th class="col-select">{{ t('restocking.table.select') }}</th>
                  <th>{{ t('restocking.table.sku') }}</th>
                  <th>{{ t('restocking.table.name') }}</th>
                  <th>{{ t('restocking.table.category') }}</th>
                  <th>{{ t('restocking.table.warehouse') }}</th>
                  <th>{{ t('restocking.table.reason') }}</th>
                  <th>{{ t('restocking.table.recommendedQuantity') }}</th>
                  <th>{{ t('restocking.table.unitCost') }}</th>
                  <th>{{ t('restocking.table.recommendedCost') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in recommendations" :key="item.sku">
                  <td class="col-select">
                    <input type="checkbox" v-model="selected[item.sku]" />
                  </td>
                  <td><strong>{{ item.sku }}</strong></td>
                  <td>{{ translateProductName(item.name) }}</td>
                  <td>{{ item.category }}</td>
                  <td>{{ translateWarehouse(item.warehouse) }}</td>
                  <td>
                    <span :class="['badge', getReasonClass(item.reason)]">
                      {{ getReasonLabel(item.reason) }}
                    </span>
                  </td>
                  <td>{{ item.recommended_quantity }}</td>
                  <td>{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</td>
                  <td><strong>{{ currencySymbol }}{{ item.recommended_cost.toLocaleString() }}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="order-footer">
            <div :class="['selected-total', { over: selectedTotal > budget }]">
              {{ t('restocking.selectedTotal', { selected: `${currencySymbol}${selectedTotal.toLocaleString()}`, budget: `${currencySymbol}${budget.toLocaleString()}` }) }}
            </div>
            <button
              class="place-order-btn"
              :disabled="!canPlaceOrder"
              @click="placeOrder"
            >
              {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const budget = ref(10000)
    const loading = ref(true)
    const error = ref(null)
    const recommendations = ref([])
    const selected = ref({})

    const submitting = ref(false)
    const submitError = ref(null)
    const successMessage = ref(null)

    let debounceTimer = null

    const loadRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        const data = await api.getRestockRecommendations(budget.value)
        recommendations.value = data

        const selectionState = {}
        data.forEach(item => {
          selectionState[item.sku] = true
        })
        selected.value = selectionState
      } catch (err) {
        error.value = 'Failed to load restock recommendations: ' + err.message
      } finally {
        loading.value = false
      }
    }

    watch(budget, () => {
      successMessage.value = null
      submitError.value = null
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        loadRecommendations()
      }, 300)
    })

    const selectedItems = computed(() => {
      return recommendations.value.filter(item => selected.value[item.sku])
    })

    const selectedTotal = computed(() => {
      return selectedItems.value.reduce((sum, item) => sum + item.recommended_cost, 0)
    })

    const canPlaceOrder = computed(() => {
      return selectedItems.value.length > 0 && selectedTotal.value <= budget.value && !submitting.value
    })

    const reasonClassMap = {
      'Below reorder point': 'danger',
      'Increasing demand': 'increasing',
      'Demand shortfall': 'warning'
    }

    const reasonLabelKeyMap = {
      'Below reorder point': 'restocking.reasons.belowReorderPoint',
      'Increasing demand': 'restocking.reasons.increasingDemand',
      'Demand shortfall': 'restocking.reasons.demandShortfall'
    }

    const getReasonClass = (reason) => reasonClassMap[reason] || 'info'
    const getReasonLabel = (reason) => {
      const key = reasonLabelKeyMap[reason]
      return key ? t(key) : reason
    }

    const placeOrder = async () => {
      if (!canPlaceOrder.value) return
      try {
        submitting.value = true
        submitError.value = null
        successMessage.value = null

        const items = selectedItems.value.map(item => ({
          sku: item.sku,
          name: item.name,
          quantity: item.recommended_quantity,
          unit_cost: item.unit_cost
        }))

        const order = await api.submitRestockOrder({ budget: budget.value, items })

        successMessage.value = t('restocking.orderSuccess', {
          orderNumber: order.order_number,
          count: order.items.length,
          days: order.lead_time_days
        })

        await loadRecommendations()
      } catch (err) {
        submitError.value = 'Failed to place restock order: ' + err.message
      } finally {
        submitting.value = false
      }
    }

    onMounted(loadRecommendations)

    return {
      t,
      currencySymbol,
      budget,
      loading,
      error,
      recommendations,
      selected,
      selectedTotal,
      canPlaceOrder,
      submitting,
      submitError,
      successMessage,
      getReasonClass,
      getReasonLabel,
      placeOrder,
      translateProductName,
      translateWarehouse
    }
  }
}
</script>

<style scoped>
.budget-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
}

.budget-slider {
  width: 100%;
  accent-color: var(--accent-yellow);
}

.empty-state {
  padding: 3rem 1rem;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.938rem;
}

.col-select {
  width: 60px;
  text-align: center;
}

.success-message {
  background: rgba(85, 230, 111, 0.14);
  border: 1px solid rgba(85, 230, 111, 0.4);
  color: var(--success);
  padding: 1rem;
  border-radius: var(--radius-md);
  margin: 1rem 0;
  font-size: 0.938rem;
}

.order-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}

.selected-total {
  font-size: 0.938rem;
  font-weight: 600;
  color: var(--text-primary);
}

.selected-total.over {
  color: var(--error);
}

.place-order-btn {
  padding: 0.625rem 1.5rem;
  background: var(--accent-yellow);
  color: #060606;
  border: none;
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: 0.938rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: var(--accent-yellow-hover);
}

.place-order-btn:disabled {
  background: var(--surface-elevated);
  color: var(--text-tertiary);
  cursor: not-allowed;
}
</style>
