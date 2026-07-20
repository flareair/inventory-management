<template>
  <div class="restocking">
    <div class="page-header">
      <h2>{{ t('restocking.title') }}</h2>
      <p>{{ t('restocking.description') }}</p>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div v-if="successMessage" class="success-banner">{{ successMessage }}</div>

      <div class="card">
        <label class="budget-label" for="budget-slider">
          {{ t('restocking.budget.label') }}: <strong>{{ currencySymbol }}{{ budget.toLocaleString() }}</strong>
        </label>
        <input
          id="budget-slider"
          v-model.number="budget"
          type="range"
          min="0"
          max="20000"
          step="100"
          class="budget-slider"
        />
        <p class="budget-hint">{{ t('restocking.budget.hint') }}</p>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.summary.budget') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ budget.toLocaleString() }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.summary.allocated') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ totalAllocated.toLocaleString() }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.summary.remaining') }}</div>
          <div class="stat-value">{{ currencySymbol }}{{ remainingBudget.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.summary.itemsRecommended') }}</div>
          <div class="stat-value">{{ recommendations.length }}</div>
        </div>
      </div>

      <div v-if="budget <= 0" class="card">
        <p class="empty-state">{{ t('restocking.noBudget') }}</p>
      </div>
      <div v-else class="card">
        <div class="card-header">
          <h3 class="card-title">{{ t('restocking.recommendations.title') }}</h3>
          <button
            class="place-order-btn"
            :disabled="recommendations.length === 0 || placingOrder"
            @click="placeOrder"
          >
            {{ placingOrder ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="recommendations.length === 0" class="empty-state">
          {{ t('restocking.recommendations.empty') }}
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th>{{ t('restocking.recommendations.table.sku') }}</th>
                <th>{{ t('restocking.recommendations.table.itemName') }}</th>
                <th>{{ t('restocking.recommendations.table.trend') }}</th>
                <th>{{ t('restocking.recommendations.table.forecastedDemand') }}</th>
                <th>{{ t('restocking.recommendations.table.shortfall') }}</th>
                <th>{{ t('restocking.recommendations.table.recommendedQty') }}</th>
                <th>{{ t('restocking.recommendations.table.unitCost') }}</th>
                <th>{{ t('restocking.recommendations.table.lineTotal') }}</th>
                <th>{{ t('restocking.recommendations.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in recommendations" :key="item.item_sku">
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ item.item_name }}</td>
                <td>
                  <span :class="['badge', item.trend]">
                    {{ t(`trends.${item.trend}`) }}
                  </span>
                </td>
                <td>{{ item.forecasted_demand }}</td>
                <td>{{ item.shortfall }}</td>
                <td>
                  {{ item.quantity }}
                  <span v-if="item.partial" class="badge warning">{{ t('restocking.recommendations.partial') }}</span>
                </td>
                <td>{{ currencySymbol }}{{ item.unit_cost.toLocaleString() }}</td>
                <td><strong>{{ currencySymbol }}{{ item.lineTotal.toLocaleString() }}</strong></td>
                <td>{{ t('restocking.recommendations.leadTimeDays', { days: item.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { useSubmittedOrders } from '../composables/useSubmittedOrders'

const TREND_WEIGHTS = {
  increasing: 1.5,
  stable: 1.0,
  decreasing: 0.5
}

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency } = useI18n()
    const { addSubmittedOrder } = useSubmittedOrders()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const forecasts = ref([])
    const budget = ref(5000)
    const placingOrder = ref(false)
    const successMessage = ref(null)

    const loadForecasts = async () => {
      try {
        loading.value = true
        error.value = null
        forecasts.value = await api.getDemandForecasts()
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const recommendations = computed(() => {
      if (budget.value <= 0) return []

      const candidates = forecasts.value
        .map(item => {
          const shortfall = Math.max(item.forecasted_demand - item.current_demand, 0)
          return { ...item, shortfall }
        })
        .filter(item => item.shortfall > 0)
        .map(item => ({
          ...item,
          priorityScore: item.shortfall * (TREND_WEIGHTS[item.trend] || 1.0)
        }))
        .sort((a, b) => b.priorityScore - a.priorityScore)

      let remainingBudgetLocal = budget.value
      const result = []

      for (const item of candidates) {
        if (remainingBudgetLocal <= 0) break

        const fullCost = item.shortfall * item.unit_cost
        let quantity = 0
        let partial = false

        if (fullCost <= remainingBudgetLocal) {
          quantity = item.shortfall
        } else {
          quantity = Math.floor(remainingBudgetLocal / item.unit_cost)
          partial = true
        }

        if (quantity < 1) continue

        const lineTotal = quantity * item.unit_cost
        remainingBudgetLocal -= lineTotal

        result.push({ ...item, quantity, partial, lineTotal })
      }

      return result
    })

    const totalAllocated = computed(() => {
      return recommendations.value.reduce((sum, item) => sum + item.lineTotal, 0)
    })

    const remainingBudget = computed(() => {
      return budget.value - totalAllocated.value
    })

    const placeOrder = () => {
      if (recommendations.value.length === 0) return

      placingOrder.value = true

      const orderDate = new Date()
      const maxLeadTime = Math.max(...recommendations.value.map(item => item.lead_time_days))
      const expectedDelivery = new Date(orderDate)
      expectedDelivery.setDate(expectedDelivery.getDate() + maxLeadTime)

      const order = {
        id: `RST-${Date.now()}`,
        order_number: `RST-${Date.now()}`,
        items: recommendations.value.map(item => ({
          sku: item.item_sku,
          name: item.item_name,
          quantity: item.quantity,
          unit_cost: item.unit_cost,
          line_total: item.lineTotal,
          lead_time_days: item.lead_time_days
        })),
        status: 'Submitted',
        order_date: orderDate.toISOString(),
        expected_delivery: expectedDelivery.toISOString(),
        total_value: totalAllocated.value,
        budget: budget.value
      }

      addSubmittedOrder(order)

      successMessage.value = t('restocking.orderSuccess', { orderNumber: order.order_number })
      placingOrder.value = false
      budget.value = 5000
    }

    onMounted(loadForecasts)

    return {
      t,
      currencySymbol,
      loading,
      error,
      budget,
      placingOrder,
      successMessage,
      recommendations,
      totalAllocated,
      remainingBudget,
      placeOrder
    }
  }
}
</script>

<style scoped>
.budget-label {
  display: block;
  font-size: 0.938rem;
  font-weight: 500;
  color: #0f172a;
  margin-bottom: 0.75rem;
}

.budget-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: #e2e8f0;
  appearance: none;
  outline: none;
  cursor: pointer;
}

.budget-slider::-webkit-slider-thumb {
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.budget-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2563eb;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.budget-hint {
  margin-top: 0.75rem;
  color: #64748b;
  font-size: 0.813rem;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #64748b;
  font-size: 0.938rem;
}

.place-order-btn {
  background: #2563eb;
  color: white;
  border: none;
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

.place-order-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.place-order-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
}

.success-banner {
  background: #d1fae5;
  border: 1px solid #6ee7b7;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
  font-size: 0.938rem;
}
</style>
