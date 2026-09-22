<script setup>
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'

import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import DifyChatbot from './components/DifyChatbot.vue'

const route = useRoute()
const isAdminRoute = computed(() => route.meta.layout === 'admin')
</script>

<template>
  <div class="app">
    <AppHeader v-if="!isAdminRoute" />

    <div class="app-content">
      <RouterView />
    </div>

    <AppFooter v-if="!isAdminRoute" />

    <DifyChatbot v-if="!isAdminRoute" />
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
