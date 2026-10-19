<script setup>
import { computed, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import ExchangeCard from '../components/exchange/ExchangeCard.vue'
import ExchangeSubmitForm from '../components/exchange/ExchangeSubmitForm.vue'
import { loadExchangeResources } from '../services/exchange'
import { createDiscovery, selectResources } from '../utils/exchangeDiscovery'
import '../assets/exchange.css'

const resources = shallowRef([])
const selectedId = ref(null)
const query = ref('')
const status = ref('')
const searchError = ref('')
const loading = ref(true)
const loadError = ref('')
const shareOpen = ref(false)
const current = computed(() => resources.value.find((resource) => resource.id === selectedId.value))
let deck = createDiscovery([])
let disposed = false

function replaceResources(items, preferred = selectedId.value) {
  resources.value = items
  deck = createDiscovery(
    items.map((item) => item.id),
    preferred,
  )
  selectedId.value = deck.current() ?? deck.draw()
}
onMounted(async () => {
  try {
    const items = await loadExchangeResources()
    if (!disposed) replaceResources(items)
  } catch (error) {
    if (!disposed) loadError.value = error.message || '暂时无法读取分享，请稍后重新进入。'
  } finally {
    if (!disposed) loading.value = false
  }
})
function discover() {
  if (resources.value.length < 2) return
  searchError.value = ''
  selectedId.value = deck.draw()
  status.value = `发现 ${current.value.displayNumber} 号：${current.value.title}`
}
function search() {
  searchError.value = ''
  if (!query.value.trim()) {
    searchError.value = '请输入资源编号或关键词。'
    return
  }
  const matches = selectResources(resources.value, query.value)
  if (!matches.length) {
    searchError.value = `没有找到“${query.value.trim()}”对应的分享，请换个编号或关键词。`
    return
  }
  selectedId.value = deck.select(matches[0].id)
  status.value = `已定位 ${current.value.displayNumber} 号：${current.value.title}${matches.length > 1 ? `。共 ${matches.length} 条匹配，先展示第一条` : ''}。`
}
async function onSubmitted(resource) {
  replaceResources(
    [resource, ...resources.value.filter((item) => item.id !== resource.id)],
    resource.id,
  )
  searchError.value = ''
  status.value = `分享成功 · ${resource.displayNumber}`
  try {
    const items = await loadExchangeResources()
    if (!disposed) replaceResources(items, resource.id)
  } catch {
    // Creation already committed; retain the confirmed resource if list refresh fails.
  }
}
onBeforeUnmount(() => {
  disposed = true
})
</script>

<template>
  <main class="exchange-page">
    <div class="exchange-inner">
      <section class="intro" aria-labelledby="exchange-title">
        <div>
          <div class="eyebrow">DISCOVERY SPACE</div>
          <h1 id="exchange-title">互通<span class="yellow-mark">有无</span></h1>
          <p>分享一点发现，让有用的知识被更多人看见。</p>
        </div>
        <button class="share-button" @click="shareOpen = true">
          <span class="plus" aria-hidden="true"
            ><svg viewBox="0 0 18 20"><path d="M9 4v12M3 10h12" /></svg></span
          >分享
        </button>
      </section>
      <div class="toolbar">
        <form class="search" role="search" @submit.prevent="search">
          <label class="sr-only" for="exchange-search">资源编号、标题或关键词</label>
          <input
            id="exchange-search"
            v-model="query"
            type="search"
            placeholder="编号 / 标题 / 关键词"
            autocomplete="off"
          />
          <button type="submit" :disabled="loading">查找</button>
        </form>
      </div>
      <p v-if="searchError" class="search-feedback" role="alert">{{ searchError }}</p>
      <p class="sr-only" role="status" aria-live="polite">{{ status }}</p>
      <section v-if="current" aria-label="随机发现">
        <div class="shuffle-shell">
          <ExchangeCard :key="current.id" :resource="current" />
          <div class="browse-controls">
            <button class="discovery-action" :disabled="resources.length < 2" @click="discover">
              发现<span class="discovery-action-arrow" aria-hidden="true">→</span>
            </button>
          </div>
        </div>
      </section>
      <section v-else class="empty" aria-live="polite">
        <h2>{{ loading ? '正在寻找发现…' : '这次还没有遇见。' }}</h2>
        <p>
          {{ loadError || '还没有分享，来分享第一个发现吧。' }}
        </p>
        <button class="discovery-action" disabled>
          发现<span class="discovery-action-arrow" aria-hidden="true">→</span>
        </button>
      </section>
      <ExchangeSubmitForm :open="shareOpen" @close="shareOpen = false" @submitted="onSubmitted" />
    </div>
  </main>
</template>
