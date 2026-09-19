<script setup>
import { RouterView } from 'vue-router'

import AppHeader from './components/AppHeader.vue'
import AppFooter from './components/AppFooter.vue'
import DifyChatbot from './components/DifyChatbot.vue'
</script>

<template>
  <div class="app">
    <AppHeader />

    <div class="app-content">
      <RouterView />
    </div>

    <AppFooter />

    <DifyChatbot />
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
