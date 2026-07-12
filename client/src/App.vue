<template>
  <div class="app">
    <header class="top-nav">
      <div class="nav-container">
        <div class="logo">
          <h1>{{ t('nav.companyName') }}</h1>
          <span class="subtitle">{{ t('nav.subtitle') }}</span>
        </div>
        <nav class="nav-tabs">
          <router-link to="/" :class="{ active: $route.path === '/' }">
            {{ t('nav.overview') }}
          </router-link>
          <router-link to="/inventory" :class="{ active: $route.path === '/inventory' }">
            {{ t('nav.inventory') }}
          </router-link>
          <router-link to="/orders" :class="{ active: $route.path === '/orders' }">
            {{ t('nav.orders') }}
          </router-link>
          <router-link to="/spending" :class="{ active: $route.path === '/spending' }">
            {{ t('nav.finance') }}
          </router-link>
          <router-link to="/demand" :class="{ active: $route.path === '/demand' }">
            {{ t('nav.demandForecast') }}
          </router-link>
          <router-link to="/restocking" :class="{ active: $route.path === '/restocking' }">
            {{ t('nav.restocking') }}
          </router-link>
          <router-link to="/reports" :class="{ active: $route.path === '/reports' }">
            Reports
          </router-link>
        </nav>
        <LanguageSwitcher />
        <ProfileMenu
          @show-profile-details="showProfileDetails = true"
          @show-tasks="showTasks = true"
        />
      </div>
    </header>
    <FilterBar />
    <main class="main-content">
      <router-view />
    </main>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
:root {
  --bg: #060606;
  --surface: #131313;
  --surface-elevated: #1C1C1C;
  --border: #2D2D2D;
  --border-subtle: #1C1C1C;
  --text-primary: #FFFFFF;
  --text-secondary: #A0A0A0;
  --text-tertiary: #717171;
  --text-body: #E8E8E8;

  --accent-yellow: #FBC00E;
  --accent-yellow-hover: #FDD44D;
  --accent-yellow-active: #DDA80C;
  --accent-orange: #F06516;
  --accent-blue: #7BA8FF;
  --accent-blue-deep: #0047FF;

  --success: #55E66F;
  --warning: #FBC00E;
  --error: #F03016;
  --info: #7BA8FF;

  --chart-1: #ABDBDD; --chart-2: #38C2D7; --chart-3: #0F8ACF;
  --chart-4: #D5E662; --chart-5: #55E66F; --chart-6: #A3C644;
  --chart-7: #AE9BD8; --chart-8: #8940FF; --chart-9: #675B88;
  --chart-10: #A84370; --chart-11: #00A705; --chart-12: #BFBFBF;

  --radius-sm: 6px; --radius-md: 8px; --radius-lg: 12px; --radius-pill: 999px;

  --space-xs: 4px; --space-sm: 8px; --space-md: 16px; --space-lg: 24px;
  --space-xl: 32px; --space-2xl: 48px; --space-3xl: 64px;

  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Monaco', 'Courier New', monospace;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  background: var(--bg);
  color: var(--text-body);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.top-nav {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.4);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-container {
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  padding: 0 2rem;
  height: 70px;
}

.nav-container > .nav-tabs {
  margin-left: auto;
  margin-right: 1rem;
}

.nav-container > .language-switcher {
  margin-right: 1rem;
}

.logo {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}

.logo h1 {
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.025em;
}

.subtitle {
  font-size: 0.813rem;
  color: var(--text-secondary);
  font-weight: 400;
  padding-left: 0.75rem;
  border-left: 1px solid var(--border);
}

.nav-tabs {
  display: flex;
  gap: 0.25rem;
}

.nav-tabs a {
  padding: 0.625rem 1.25rem;
  color: var(--text-secondary);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.938rem;
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
  position: relative;
}

.nav-tabs a:hover {
  color: var(--text-primary);
  background: var(--surface-elevated);
}

.nav-tabs a.active {
  color: var(--accent-yellow);
  background: rgba(251, 192, 14, 0.12);
}

.nav-tabs a.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--accent-yellow);
}

.main-content {
  flex: 1;
  max-width: 1600px;
  width: 100%;
  margin: 0 auto;
  padding: 1.5rem 2rem;
}

.page-header {
  margin-bottom: 1.5rem;
}

.page-header h2 {
  font-size: 1.875rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.375rem;
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--text-secondary);
  font-size: 0.938rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: var(--surface);
  padding: 1.25rem;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: var(--border);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.stat-label {
  color: var(--text-secondary);
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.625rem;
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.025em;
}

.stat-card.warning .stat-value {
  color: var(--warning);
}

.stat-card.success .stat-value {
  color: var(--success);
}

.stat-card.danger .stat-value {
  color: var(--error);
}

.stat-card.info .stat-value {
  color: var(--info);
}

.card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: 1.25rem;
  border: 1px solid var(--border-subtle);
  margin-bottom: 1.25rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.875rem;
  border-bottom: 1px solid var(--border-subtle);
}

.card-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.025em;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--surface-elevated);
  border-top: 1px solid var(--border-subtle);
  border-bottom: 1px solid var(--border-subtle);
}

th {
  text-align: left;
  padding: 0.5rem 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: 0.5rem 0.75rem;
  border-top: 1px solid var(--border-subtle);
  color: var(--text-body);
  font-size: 0.875rem;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--surface-elevated);
}

.badge {
  display: inline-block;
  padding: 0.313rem 0.75rem;
  border-radius: var(--radius-pill);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success {
  background: rgba(85, 230, 111, 0.14);
  color: var(--success);
}

.badge.warning {
  background: rgba(251, 192, 14, 0.14);
  color: var(--warning);
}

.badge.danger {
  background: rgba(240, 48, 22, 0.14);
  color: var(--error);
}

.badge.info {
  background: rgba(123, 168, 255, 0.14);
  color: var(--info);
}

.badge.increasing {
  background: rgba(85, 230, 111, 0.14);
  color: var(--success);
}

.badge.decreasing {
  background: rgba(240, 48, 22, 0.14);
  color: var(--error);
}

.badge.stable {
  background: rgba(123, 168, 255, 0.14);
  color: var(--info);
}

.badge.high {
  background: rgba(240, 48, 22, 0.14);
  color: var(--error);
}

.badge.medium {
  background: rgba(251, 192, 14, 0.14);
  color: var(--warning);
}

.badge.low {
  background: rgba(123, 168, 255, 0.14);
  color: var(--info);
}

.loading {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
  font-size: 0.938rem;
}

.error {
  background: rgba(240, 48, 22, 0.08);
  border: 1px solid rgba(240, 48, 22, 0.3);
  color: var(--error);
  padding: 1rem;
  border-radius: var(--radius-md);
  margin: 1rem 0;
  font-size: 0.938rem;
}
</style>
