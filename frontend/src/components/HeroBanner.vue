<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import BannerSlide from './banner/BannerSlide.vue'
import { API_BASE_URL } from '../config/api'

const router = useRouter()
const banners = ref([])
const currentIndex = ref(0)
const loading = ref(true)
const errorMessage = ref('')
let timer = null
let isUnmounted = false

const currentBanner = computed(() => banners.value[currentIndex.value] || null)
const currentSlide = computed(() => {
  const banner = currentBanner.value
  if (!banner) return null

  const image = banner.image || ''
  const imageUrl = image.startsWith('/uploads/') ? `${API_BASE_URL}${image}` : image
  const date = typeof banner.date === 'string'
    ? banner.date.replace(/^(\d{4})-(\d{2})-(\d{2})$/, '$1.$2.$3')
    : ''

  return {
    ...banner,
    bannerType: banner.bannerType === 'image_only' ? 'image_only' : 'standard',
    image: imageUrl,
    altText: banner.bannerType === 'image_only' ? 'Banner 头图' : banner.title,
    kicker: [banner.category, date].filter(Boolean).join(' / ') || 'AI PORTAL / 信息运维',
    actionType: banner.action?.type || 'none',
    actionTarget: banner.action?.target || '',
  }
})

function stopAutoPlay() {
  if (timer) clearInterval(timer)
  timer = null
}

function startAutoPlay() {
  stopAutoPlay()
  if (banners.value.length <= 1) return
  timer = setInterval(() => {
    currentIndex.value = (currentIndex.value + 1) % banners.value.length
  }, 5000)
}

function changeBanner(index) {
  if (banners.value.length <= 1) return
  currentIndex.value = (index + banners.value.length) % banners.value.length
  startAutoPlay()
}

async function loadBanners() {
  loading.value = true
  errorMessage.value = ''
  stopAutoPlay()

  try {
    const response = await fetch(`${API_BASE_URL}/api/banners`, { cache: 'no-store' })
    if (!response.ok) throw new Error(`请求失败：${response.status}`)
    const data = await response.json()
    if (isUnmounted) return
    banners.value = Array.isArray(data) ? data : []
    currentIndex.value = 0
  } catch (error) {
    if (isUnmounted) return
    console.error('Banner 加载失败：', error)
    banners.value = []
    errorMessage.value = '轮播内容暂时无法加载'
  } finally {
    if (!isUnmounted) {
      loading.value = false
      startAutoPlay()
    }
  }
}

function handleBannerAction() {
  const action = currentBanner.value?.action
  if (currentBanner.value?.bannerType === 'image_only') return

  if (action?.type === 'dify') {
    document.getElementById('dify-chatbot-bubble-button')?.click()
    return
  }
  if (action?.type === 'route' && action.target?.startsWith('/') && !action.target.startsWith('//')) {
    router.push(action.target)
    return
  }
  if (action?.type === 'external' && action.target) {
    try {
      const url = new URL(action.target)
      if (['http:', 'https:'].includes(url.protocol)) {
        window.open(url.href, '_blank', 'noopener,noreferrer')
      }
    } catch {
      // Ignore invalid external targets.
    }
  }
}

onMounted(() => {
  isUnmounted = false
  loadBanners()
})
onUnmounted(() => {
  isUnmounted = true
  stopAutoPlay()
})
</script>

<template>
  <section class="hero" aria-label="门户轮播" @mouseenter="stopAutoPlay" @mouseleave="startAutoPlay">
    <Transition name="banner" mode="out-in">
      <BannerSlide
        v-if="currentSlide"
        :key="currentBanner.id"
        :banner="currentSlide"
        @action="handleBannerAction"
      />
    </Transition>

    <div v-if="!currentSlide" class="hero-empty" :role="errorMessage ? 'alert' : 'status'">
      {{ loading ? '正在加载轮播内容...' : errorMessage || '暂无轮播内容' }}
    </div>

    <template v-if="banners.length > 1">
      <button class="arrow arrow-left" type="button" aria-label="上一张 Banner" @click="changeBanner(currentIndex - 1)">‹</button>
      <button class="arrow arrow-right" type="button" aria-label="下一张 Banner" @click="changeBanner(currentIndex + 1)">›</button>
      <div class="banner-indicators" aria-label="选择 Banner">
        <button
          v-for="(banner, index) in banners"
          :key="banner.id"
          type="button"
          class="indicator"
          :class="{ active: index === currentIndex }"
          :aria-label="`切换到第 ${index + 1} 张 Banner`"
          :aria-current="index === currentIndex ? 'true' : undefined"
          @click="changeBanner(index)"
        />
      </div>
    </template>
  </section>
</template>

<style scoped>
.hero {
  --banner-ui-white: #fff;
  --banner-ui-cloud: #f5f6f7;
  --banner-ui-graphite: #22292c;
  --banner-ui-yellow: #f7b334;
  --banner-ui-earth: #6d5b55;
  --banner-ui-muted: #586366;
  --banner-ui-green-deep: #375d05;
  position: relative;
  width: calc(100% - 48px);
  max-width: 1200px;
  aspect-ratio: 3.8;
  min-height: 220px;
  margin: 32px auto;
  overflow: hidden;
  border: 1px solid #dce1e2;
  border-radius: 8px;
  background: var(--banner-ui-cloud);
  box-sizing: border-box;
  isolation: isolate;
}

.hero-empty {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: var(--banner-ui-muted);
  font-size: 15px;
}

.hero :deep(.banner-frame) {
  position: absolute;
  inset: 0;
}

.arrow {
  position: absolute;
  z-index: 3;
  top: 50%;
  display: grid;
  place-items: center;
  width: clamp(30px, 3.5%, 42px);
  aspect-ratio: 1;
  padding: 0;
  border: 1px solid rgba(34, 41, 44, .15);
  border-radius: 50%;
  background: rgba(255, 255, 255, .86);
  color: var(--banner-ui-graphite);
  font-size: clamp(20px, 2.2vw, 28px);
  line-height: 1;
  cursor: pointer;
  transform: translateY(-50%);
}
.arrow-left { left: 8px; }
.arrow-right { right: 8px; }

.banner-indicators {
  position: absolute;
  z-index: 3;
  left: 50%;
  bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 9px;
  border-radius: 20px;
  background: rgba(255, 255, 255, .86);
  transform: translateX(-50%);
}
.indicator {
  width: 7px;
  height: 7px;
  padding: 0;
  border: 0;
  border-radius: 20px;
  background: #9a9e9f;
  cursor: pointer;
}
.indicator.active { width: 20px; background: var(--banner-ui-graphite); }
.hero button:focus-visible { outline: 3px solid var(--banner-ui-green-deep); outline-offset: 2px; }
.banner-enter-active, .banner-leave-active { transition: opacity .25s ease; }
.banner-enter-from, .banner-leave-to { opacity: 0; }

@media (max-width: 600px) {
  .hero { width: calc(100% - 32px); margin: 20px auto; }
  .arrow { display: none; }
  .banner-indicators { bottom: 7px; }
}

@media (prefers-reduced-motion: reduce) {
  .banner-enter-active, .banner-leave-active { transition: none; }
}
</style>
