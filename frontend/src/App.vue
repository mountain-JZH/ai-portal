<script setup>
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'

import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import DifyChatbot from './components/DifyChatbot.vue'

const route = useRoute()
const isStandaloneRoute = computed(() => ['admin', 'auth'].includes(route.meta.layout))
</script>

<template>
  <div class="app">
    <AppHeader v-if="!isStandaloneRoute" />

    <div class="app-content">
      <RouterView />
    </div>

    <AppFooter v-if="!isStandaloneRoute" />

    <DifyChatbot v-if="!isStandaloneRoute" />
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
