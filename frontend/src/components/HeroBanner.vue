<script setup>
import {
  computed,
  onMounted,
  onUnmounted,
  ref,
} from 'vue'
import { useRouter } from 'vue-router'

import { API_BASE_URL } from '../config/api'


const router = useRouter()
const banners = ref([])
const currentIndex = ref(0)
const failedImageIds = ref([])
const loading = ref(true)
const errorMessage = ref('')
const visualThemes = {
  通知: {
    className: 'theme-notice',
    label: 'INTERNAL NOTICE',
  },
  宣贯: {
    className: 'theme-security',
    label: 'SECURITY BRIEF',
  },
  行业动态: {
    className: 'theme-industry',
    label: 'INDUSTRY UPDATE',
  },
}

let timer = null
let isUnmounted = false


const currentBanner = computed(() => {
  return banners.value[currentIndex.value] || null
})


const hasBannerImage = computed(() => {
  return (
    Boolean(currentBanner.value?.image) &&
    !failedImageIds.value.includes(currentBanner.value.id)
  )
})


const currentVisualTheme = computed(() => {
  return visualThemes[currentBanner.value?.category] || {
    className: 'theme-general',
    label: 'FEATURED CONTENT',
  }
})


function formatBannerDate(date) {
  if (typeof date !== 'string') {
    return ''
  }

  const match = date.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  return match ? `${match[1]}.${match[2]}.${match[3]}` : date
}


function stopAutoPlay() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}


function startAutoPlay() {
  stopAutoPlay()

  if (banners.value.length <= 1) {
    return
  }

  timer = setInterval(() => {
    currentIndex.value =
      (currentIndex.value + 1) % banners.value.length
  }, 5000)
}


function nextBanner() {
  if (banners.value.length <= 1) {
    return
  }

  currentIndex.value =
    (currentIndex.value + 1) % banners.value.length

  startAutoPlay()
}


function previousBanner() {
  if (banners.value.length <= 1) {
    return
  }

  currentIndex.value =
    (
      currentIndex.value
      - 1
      + banners.value.length
    ) % banners.value.length

  startAutoPlay()
}


function goToBanner(index) {
  if (
    banners.value.length <= 1 ||
    index < 0 ||
    index >= banners.value.length
  ) {
    return
  }

  currentIndex.value = index

  startAutoPlay()
}


async function loadBanners() {
  loading.value = true
  errorMessage.value = ''
  stopAutoPlay()

  try {
    const response = await fetch(`${API_BASE_URL}/api/banners`, {
      cache: 'no-store',
    })

    if (!response.ok) {
      throw new Error(`请求失败：${response.status}`)
    }

    const data = await response.json()
    banners.value = Array.isArray(data) ? data : []
    currentIndex.value = 0
    failedImageIds.value = []
  } catch (error) {
    console.error('Banner 加载失败：', error)
    banners.value = []
    currentIndex.value = 0
    errorMessage.value = '轮播内容暂时无法加载'
  } finally {
    loading.value = false
    if (!isUnmounted) startAutoPlay()
  }
}


function handleBannerAction() {
  const action = currentBanner.value?.action

  if (action?.type === 'dify') {
    document
      .getElementById('dify-chatbot-bubble-button')
      ?.click()

    return
  }

  if (
    action?.type === 'route' &&
    action.target?.startsWith('/') &&
    !action.target.startsWith('//')
  ) {
    router.push(action.target)

    return
  }

  if (action?.type === 'external' && action.target) {
    try {
      const url = new URL(action.target)

      if (['http:', 'https:'].includes(url.protocol)) {
        window.open(
          url.href,
          '_blank',
          'noopener,noreferrer',
        )
      }
    } catch {
      // Ignore invalid external targets from future data entries.
    }
  }
}


function handleImageError() {
  const bannerId = currentBanner.value?.id

  if (
    bannerId !== undefined &&
    !failedImageIds.value.includes(bannerId)
  ) {
    failedImageIds.value = [
      ...failedImageIds.value,
      bannerId,
    ]
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
  <section
    class="hero"
    @mouseenter="stopAutoPlay"
    @mouseleave="startAutoPlay"
  >
    <div
      v-if="currentBanner"
      class="hero-left"
    >

      <Transition
        name="banner"
        mode="out-in"
      >
        <div
          :key="currentBanner.id"
          class="banner-copy"
        >
          <div class="banner-meta">
            <span>{{ currentBanner.category }}</span>
            <span aria-hidden="true">·</span>
            <time :datetime="currentBanner.date">
              {{ formatBannerDate(currentBanner.date) }}
            </time>
          </div>

          <h1>
            {{ currentBanner.title }}
          </h1>

          <p class="description">
            {{ currentBanner.description }}
          </p>

          <button
            v-if="currentBanner.buttonText && currentBanner.action?.type !== 'none'"
            type="button"
            class="hero-button"
            @click="handleBannerAction"
          >
            {{ currentBanner.buttonText }}
          </button>
        </div>
      </Transition>


    </div>


    <div
      v-if="currentBanner"
      class="hero-visual"
    >
      <Transition
        name="visual"
        mode="out-in"
      >
        <img
          v-if="hasBannerImage"
          :key="currentBanner.image"
          :src="currentBanner.image"
          :alt="currentBanner.title"
          class="banner-image"
          @error="handleImageError"
        >

        <div
          v-else
          :key="`default-${currentBanner.id}`"
          class="visual-card"
          :class="currentVisualTheme.className"
        >
          <span class="visual-kicker">
            {{ currentBanner.category }}
          </span>

          <strong class="visual-main">
            {{ currentVisualTheme.label }}
          </strong>

          <span class="visual-accent" aria-hidden="true"></span>

          <span class="visual-caption">重点资讯</span>

        </div>
      </Transition>
    </div>


    <div
      v-if="banners.length > 1"
      class="banner-indicators"
    >
      <button
        v-for="(banner, index) in banners"
        :key="banner.id"
        class="indicator"
        :class="{
          active: index === currentIndex
        }"
        :aria-label="`切换到第 ${index + 1} 张 Banner`"
        @click="goToBanner(index)"
      ></button>
    </div>


    <button
      v-if="banners.length > 1"
      class="arrow arrow-left"
      aria-label="上一张"
      @click="previousBanner"
    >
      ‹
    </button>

    <button
      v-if="banners.length > 1"
      class="arrow arrow-right"
      aria-label="下一张"
      @click="nextBanner"
    >
      ›
    </button>

    <div
      v-if="loading"
      class="hero-empty"
      role="status"
    >
      正在加载轮播内容...
    </div>

    <div
      v-else-if="errorMessage"
      class="hero-empty"
      role="alert"
    >
      {{ errorMessage }}
    </div>

    <div
      v-else-if="!currentBanner"
      class="hero-empty"
    >
      暂无轮播内容
    </div>
  </section>
</template>


<style scoped>
.hero {
  position: relative;

  width: calc(100% - 48px);
  max-width: 1200px;

  height: 380px;

  margin: 32px auto;
  padding: 52px 56px;

  box-sizing: border-box;

  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 32px;

  overflow: hidden;

  border: 1px solid rgba(226, 232, 240, 0.9);
  isolation: isolate;

  border-radius: var(--radius-xl);

  background:
    radial-gradient(
      circle at 82% 28%,
      rgba(110, 120, 235, 0.16),
      transparent 31%
    ),
    radial-gradient(
      circle at 68% 88%,
      rgba(90, 166, 255, 0.1),
      transparent 34%
    ),
    linear-gradient(
      135deg,
      #fbfdff 0%,
      #edf2ff 100%
    );

  box-shadow: var(--shadow-card);
}


/* ---------------------------
   左侧内容区域
--------------------------- */

.hero-left {
  position: relative;
  z-index: 2;

  flex: 1 1 58%;
  min-width: 0;

  height: 276px;

  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}


.banner-copy {
  width: 100%;
  height: 246px;
}


.banner-meta {
  height: 24px;

  display: flex;
  align-items: center;
  gap: 7px;

  font-size: 12px;
  line-height: 24px;
  font-weight: 600;

  color: var(--color-text-secondary);
  letter-spacing: 0.5px;
}

.banner-meta time {
  color: var(--color-muted);
}


h1 {
  height: 96px;

  margin: 12px 0 6px;

  display: flex;
  align-items: center;

  overflow: hidden;

  font-size: 40px;
  line-height: 1.2;
  font-weight: 650;

  color: var(--color-text);
}


.description {
  height: 54px;

  margin: 0;

  overflow: hidden;

  color: var(--color-text-secondary);

  font-size: 15px;
  line-height: 1.8;
}


.hero-button {
  height: 42px;

  margin-top: 12px;
  padding: 0 22px;

  border: none;
  border-radius: 10px;

  background: linear-gradient(135deg, #4f7cff, #655ce7);

  color: white;

  font-size: 14px;
  font-weight: 600;

  cursor: pointer;

  box-shadow: 0 8px 18px rgba(83, 92, 205, 0.18);

  transition:
    transform var(--transition-normal),
    filter var(--transition-normal),
    box-shadow var(--transition-normal);
}


.hero-button:hover {
  transform: translateY(-1px);
  filter: brightness(1.04);

  box-shadow:
    0 8px 20px
    rgba(83, 92, 205, 0.2);
}


/* ---------------------------
   圆点
--------------------------- */

.banner-indicators {
  position: absolute;
  bottom: 18px;
  left: 50%;
  z-index: 6;

  width: fit-content;
  height: 24px;
  padding: 0 9px;

  display: flex;
  align-items: center;

  gap: 8px;

  border: 1px solid rgba(255, 255, 255, 0.74);
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.56);

  -webkit-backdrop-filter: blur(12px);
  backdrop-filter: blur(12px);

  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.88);

  transform: translateX(-50%);
}


.indicator {
  width: 8px;
  height: 8px;

  padding: 0;

  border: none;
  border-radius: 999px;

  background: #c7ced8;

  cursor: pointer;

  transition:
    width var(--transition-normal),
    background var(--transition-normal);
}


.indicator.active {
  width: 26px;

  background: var(--color-primary);
}


/* ---------------------------
   右侧视觉区域
--------------------------- */

.hero-visual {
  position: relative;
  z-index: 2;

  flex: 0 1 42%;
  min-width: 320px;
  max-width: 430px;
  height: 230px;

  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-empty {
  width: 100%;

  color: var(--color-muted);
  font-size: 16px;
  text-align: center;
}

.hero-visual::before,
.hero-visual::after {
  content: "";

  position: absolute;

  pointer-events: none;
}

.hero-visual::before {
  inset: 8px 0;
  border: 1px solid rgba(116, 126, 226, 0.12);
  border-radius: 28px;
  background:
    radial-gradient(circle at 72% 32%, rgba(112, 121, 226, 0.16), transparent 35%),
    linear-gradient(145deg, rgba(255, 255, 255, 0.5), rgba(235, 240, 255, 0.42));
}

.hero-visual::after {
  top: 26px;
  right: 10px;
  width: 176px;
  height: 176px;
  border: 1px solid rgba(91, 91, 214, 0.12);
  border-radius: 50%;
}


.banner-image {
  position: relative;
  z-index: 2;

  width: min(100%, 360px);
  height: 230px;

  display: block;

  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: var(--radius-lg);
  object-fit: cover;

  box-shadow:
    0 16px 36px
    rgba(15, 23, 42, 0.08);
}


.visual-card {
  position: relative;

  width: min(100%, 360px);
  height: 230px;

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  padding: 34px;

  align-items: flex-start;

  border: 1px solid rgba(255, 255, 255, 0.9);

  z-index: 2;

  border-radius: var(--radius-xl);

  background:
    radial-gradient(circle at 82% 24%, var(--theme-glow), transparent 38%),
    rgba(255, 255, 255, 0.72);

  box-shadow:
    0 16px 36px
    rgba(65, 78, 148, 0.12);

  -webkit-backdrop-filter: blur(16px);
  backdrop-filter: blur(16px);
}

.visual-kicker {
  color: var(--theme-color);

  font-size: 12px;
  font-weight: 600;

  letter-spacing: 1px;
}


.visual-main {
  max-width: 100%;
  margin-top: 14px;

  overflow-wrap: anywhere;

  color: var(--color-text);
  font-size: 32px;
  line-height: 1.08;
  font-weight: 650;
  letter-spacing: 0.5px;
}


.visual-accent {
  width: 64px;
  height: 3px;
  margin-top: 22px;

  border-radius: 999px;
  background: linear-gradient(90deg, var(--theme-color), transparent);
}


.visual-caption {
  margin-top: 12px;

  color: var(--color-muted);

  font-size: 12px;
  letter-spacing: 1px;
}

.theme-notice {
  --theme-color: #5b5bd6;
  --theme-glow: rgba(91, 91, 214, 0.16);
}

.theme-security {
  --theme-color: #3f75c7;
  --theme-glow: rgba(63, 117, 199, 0.16);
}

.theme-industry {
  --theme-color: #5573a9;
  --theme-glow: rgba(85, 115, 169, 0.15);
}

.theme-general {
  --theme-color: var(--color-primary);
  --theme-glow: rgba(91, 91, 214, 0.14);
}


/* ---------------------------
   左右切换按钮
--------------------------- */

.arrow {
  position: absolute;
  top: 50%;

  z-index: 5;

  width: 42px;
  height: 42px;

  display: flex;
  align-items: center;
  justify-content: center;

  transform: translateY(-50%);

  border: 1px solid var(--color-border);
  border-radius: 50%;

  background:
    rgba(255, 255, 255, 0.72);

  color: var(--color-text-secondary);

  font-size: 26px;
  line-height: 1;

  cursor: pointer;

  -webkit-backdrop-filter: blur(12px);
  backdrop-filter: blur(12px);

  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 8px 20px rgba(65, 78, 148, 0.1);

  opacity: 0;

  transition:
    opacity var(--transition-fast),
    background var(--transition-fast),
    border-color var(--transition-fast);
}


.hero:hover .arrow {
  opacity: 1;
}

.arrow:focus-visible {
  opacity: 1;
  outline: none;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.9),
    0 8px 20px rgba(65, 78, 148, 0.1),
    0 0 0 3px rgba(91, 91, 214, 0.16);
}


.arrow:hover {
  background: #ffffff;
  border-color: rgba(91, 91, 214, 0.24);
}


.arrow-left {
  left: 14px;
}


.arrow-right {
  right: 14px;
}


/* ---------------------------
   Banner切换动画
--------------------------- */

.banner-enter-active,
.banner-leave-active {
  transition:
    opacity 0.28s ease,
    transform 0.28s ease;
}


.banner-enter-from {
  opacity: 0;

  transform: translateX(18px);
}


.banner-leave-to {
  opacity: 0;

  transform: translateX(-12px);
}


.visual-enter-active,
.visual-leave-active {
  transition: opacity 0.24s ease;
}


.visual-enter-from,
.visual-leave-to {
  opacity: 0;
}


/* ---------------------------
   手机 / 小屏
--------------------------- */

@media (max-width: 1140px) {

  .hero {
    height: 380px;

    padding: 48px 44px;
  }


  .hero-left {
    flex: 1;

    height: 276px;
  }


  .hero-visual {
    flex: 0 1 38%;
    min-width: 280px;
  }


  .banner-image,
  .visual-card {
    width: min(100%, 300px);
  }

}


@media (max-width: 900px) {

  .hero-visual {
    display: none;
  }

}


@media (max-width: 760px) {

  .hero {
    width: calc(100% - 32px);

    height: 390px;

    margin: 20px auto;
    padding: 38px 30px;

    border-radius: var(--radius-lg);
  }


  .hero-left {
    width: 100%;
    height: 310px;

    flex: none;
  }


  .banner-copy {
    height: 286px;
  }


  .banner-indicators {
    bottom: 13px;
  }


  h1 {
    height: 110px;

    font-size: 31px;
  }


  .description {
    height: 80px;

    font-size: 14px;
  }


  .hero-visual {
    display: none;
  }


  .arrow {
    display: none;
  }

}
</style>
