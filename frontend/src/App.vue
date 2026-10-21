<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'

import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import { currentEmployee, fetchCurrentEmployee } from './utils/employeeAuth'

const route = useRoute()
const router = useRouter()
const isStandaloneRoute = computed(() => ['admin', 'auth'].includes(route.meta.layout))
const mayRender = computed(() => route.meta.layout === 'auth' || Boolean(currentEmployee.value))
async function recheck() {
  try {
    const employee = await fetchCurrentEmployee()
    if (!employee && route.name !== 'login') await router.replace({ name: 'login', query: { redirect: route.fullPath } })
  } catch { /* Next API operation still fails closed. */ }
}
onMounted(() => window.addEventListener('focus', recheck))
onUnmounted(() => window.removeEventListener('focus', recheck))
</script>

<template>
  <div class="app">
    <AppHeader v-if="mayRender && !isStandaloneRoute" />

    <div class="app-content">
      <RouterView v-if="mayRender" :key="currentEmployee?.id || 'anonymous'" />
    </div>

    <AppFooter v-if="mayRender && !isStandaloneRoute" />
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;

  display: flex;
  flex-direction: column;
}

.app-content {
  flex: 1;
}
</style>
