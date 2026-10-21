<script setup>
import { employeeFetch as fetch } from '../utils/employeeAuth'
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { API_BASE_URL } from '../config/api'
import SectionMasthead from './SectionMasthead.vue'
import ChevronRight from './ChevronRight.vue'

const props = defineProps({
  home: {
    type: Boolean,
    default: false,
  },
  previewTool: { type: Object, default: null },
  mastheadImage: {
    type: String,
    default: '',
  },
  mastheadFallbackImage: { type: String, default: '' },
  mastheadTextMode: { type: String, default: 'dark' },
  backgroundImages: {
    type: Object,
    default: () => ({}),
  },
  developmentPreviewImages: {
    type: Array,
    default: () => [],
  },
  featuredToolIds: {
    type: Array,
    default: () => [],
  },
  detailed: {
    type: Boolean,
    default: false,
  },
})

const statusLabels = {
  available: '可使用',
  integrating: '待接入',
  developing: '开发中',
}

const tools = ref([])
const loading = ref(!props.previewTool)
const errorMessage = ref('')
const placeholderCards = [1, 2, 3, 4, 5]
const failedBackgrounds = ref({})

function isSafeRoute(target) {
  return (
    typeof target === 'string' &&
    target.startsWith('/') &&
    !target.startsWith('//')
  )
}

function isSafeStaticTarget(target) {
  return (
    typeof target === 'string' &&
    target.length > 0 &&
    !target.startsWith('//') &&
    !/^[a-z][a-z\d+.-]*:/i.test(target)
  )
}

function isSafeExternalTarget(target) {
  if (typeof target !== 'string') {
    return false
  }

  try {
    return ['http:', 'https:'].includes(new URL(target).protocol)
  } catch {
    return false
  }
}

function resolveAction(tool) {
  if (tool.status !== 'available') {
    return null
  }

  if (
    tool.actionType === 'route' &&
    isSafeRoute(tool.actionTarget)
  ) {
    return {
      component: RouterLink,
      attributes: {
        to: tool.actionTarget,
      },
      symbol: '→',
    }
  }

  if (
    tool.actionType === 'static' &&
    isSafeStaticTarget(tool.actionTarget)
  ) {
    return {
      component: 'a',
      attributes: {
        href: tool.actionTarget,
        target: '_blank',
        rel: 'noopener noreferrer',
      },
      symbol: '↗',
    }
  }

  if (
    tool.actionType === 'external' &&
    isSafeExternalTarget(tool.actionTarget)
  ) {
    return {
      component: 'a',
      attributes: {
        href: tool.actionTarget,
        target: '_blank',
        rel: 'noopener noreferrer',
      },
      symbol: '↗',
    }
  }

  return null
}

const previewImages = computed(() => import.meta.env.DEV && props.home ? props.developmentPreviewImages : [])
function resolveToolCover(path) {
  return typeof path === 'string' && path.startsWith('/uploads/tools/') ? `${API_BASE_URL}${path}` : ''
}

const toolCards = computed(() => (props.previewTool ? [props.previewTool] : tools.value).map((tool, index) => ({
  ...tool,
  action: resolveAction(tool),
  backgroundImage: resolveToolCover(tool.coverImageUrl) || props.backgroundImages[tool.id] || previewImages.value[index] || '',
})))
const visibleToolCards = computed(() => props.home ? toolCards.value.slice(0, 4) : toolCards.value)

function backgroundState(tool) {
  if (!tool.backgroundImage) return 'unconfigured'
  return failedBackgrounds.value[tool.id] === tool.backgroundImage ? 'error' : 'configured'
}

const previewFailures = computed(() => visibleToolCards.value
  .filter((tool) => backgroundState(tool) === 'error')
  .map((tool) => `${tool.title}（ID ${tool.id}）`))
const previewUnconfigured = computed(() => visibleToolCards.value
  .filter((tool) => backgroundState(tool) === 'unconfigured').length)

async function loadTools() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(`${API_BASE_URL}/api/tools`)

    if (!response.ok) throw new Error(`请求失败：${response.status}`)

    const data = await response.json()
    tools.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('工具加载失败：', error)
    tools.value = []
    errorMessage.value = '工具加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

onMounted(() => { if (!props.previewTool) loadTools() })
</script>

<template>
  <section
    class="section"
    :class="{ 'section--detailed': detailed, 'section--home': home, 'section--preview': Boolean(previewTool) }"
  >
    <SectionMasthead
      v-if="home && !previewTool"
      title="AI 与常用工具"
      description="让智能工具更自然地融入日常工作"
      to="/tools"
      :image="mastheadImage"
      :fallback-image="mastheadFallbackImage"
      :text-mode="mastheadTextMode"
      navigation-label="全部"
      navigation-aria-label="查看全部工具"
    />
    <div v-else-if="!previewTool" class="section-header">
      <div>
        <h2>AI 与常用工具</h2>
        <p>将日常工具集中在一个入口</p>
      </div>
    </div>

    <p v-if="previewImages.length" class="tool-preview-notice" role="status">
      本地工具卡图片预览：前两项借用栏目素材，仅用于渐隐验收，非正式工具封面。
      未配置图片：{{ previewUnconfigured }} 项。
      <span v-if="previewFailures.length">已配置但加载失败：{{ previewFailures.join('、') }}。</span>
      <span v-else>当前未报告图片加载失败。</span>
    </p>

    <div
      class="tool-grid"
      :class="{ 'tool-grid--detailed': detailed }"
      :aria-busy="loading"
    >
      <template v-if="loading">
        <article
          v-for="placeholder in home ? placeholderCards.slice(0, 4) : placeholderCards"
          :key="placeholder"
          class="tool-card tool-card--loading"
          aria-hidden="true"
        >
          <span v-if="!home" class="tool-loading-icon" />
          <span class="tool-loading-title" />
          <span class="tool-loading-line" />
          <span class="tool-loading-line tool-loading-line--short" />
        </article>
        <span class="tool-loading-copy" role="status">正在加载工具...</span>
      </template>

      <div
        v-else-if="errorMessage"
        class="tool-state tool-state--error"
        role="alert"
      >
        {{ errorMessage }}
      </div>

      <div v-else-if="!toolCards.length" class="tool-state">
        暂无可用工具
      </div>

      <component
        v-else
        :is="!detailed && tool.action && !previewTool ? tool.action.component : 'article'"
        v-for="tool in visibleToolCards"
        :key="tool.id"
        v-bind="!detailed && tool.action && !previewTool ? tool.action.attributes : {}"
        class="tool-card"
        :data-background-state="home ? backgroundState(tool) : undefined"
        :class="{
          'tool-card-link': !detailed && tool.action && !previewTool,
          [`tool-card--${tool.status}`]: true,
          'tool-card--featured': home && featuredToolIds.includes(tool.id),
          'tool-card--with-background': home && tool.backgroundImage && failedBackgrounds[tool.id] !== tool.backgroundImage,
        }"
        :aria-disabled="home && !tool.action ? 'true' : undefined"
        :aria-label="home && tool.action
          ? tool.title + (tool.action.attributes.target ? '（新标签页打开）' : '')
          : undefined"
      >
        <img
          v-if="home && tool.backgroundImage && failedBackgrounds[tool.id] !== tool.backgroundImage"
          class="tool-background"
          :src="tool.backgroundImage"
          alt=""
          aria-hidden="true"
          @error="failedBackgrounds[tool.id] = tool.backgroundImage"
        >
        <div v-if="!home" class="tool-top">
          <div class="tool-icon">
            {{ tool.icon }}
          </div>

          <span
            v-if="!detailed"
            class="tool-status"
            :class="`tool-status--${tool.status}`"
          >
            {{ statusLabels[tool.status] || tool.status }}
          </span>
        </div>

        <div v-if="home" class="tool-home-content">
          <div class="tool-home-copy">
            <h3>{{ tool.title }}</h3>
            <p>{{ tool.description }}</p>
          </div>
          <span v-if="tool.action" class="tool-home-navigation" aria-hidden="true">
            <span class="tool-home-action-label">启动</span><ChevronRight class="tool-surface-arrow" />
          </span>
          <span v-else class="tool-home-unavailable">敬请期待</span>
        </div>
        <template v-else>
          <h3>{{ tool.title }}</h3>
          <p>{{ tool.description }}</p>
        </template>

        <div
          v-if="detailed && !home"
          class="tool-footer"
        >
          <span
            class="tool-status"
            :class="`tool-status--${tool.status}`"
          >
            {{ statusLabels[tool.status] || tool.status }}
          </span>

          <component
            :is="tool.action ? tool.action.component : 'span'"
            v-bind="tool.action ? tool.action.attributes : {}"
            class="tool-action"
            :class="{ 'tool-action--placeholder': !tool.action }"
            :aria-disabled="tool.action ? undefined : 'true'"
          >
            {{ tool.buttonText }}
            <span v-if="tool.action">{{ tool.action.symbol }}</span>
          </component>
        </div>
      </component>
    </div>
  </section>
</template>

<style scoped>
.section {
  width: calc(100% - 48px);
  max-width: 1200px;
  margin: 72px auto 96px;
}

.section--detailed {
  margin-top: 40px;
}

.section-header {
  margin-bottom: 24px;
}

.section-header h2 {
  margin: 0;

  font-size: 24px;
  font-weight: 600;

  line-height: 1.3;
  color: var(--color-text);
}

.section-header p {
  margin: 8px 0 0;

  color: var(--color-muted);

  font-size: 14px;
}

.tool-grid {
  display: grid;

  grid-template-columns:
    repeat(auto-fit, minmax(210px, 1fr));

  gap: 20px;
}

.tool-card {
  min-height: 206px;

  padding: 24px;

  box-sizing: border-box;

  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);

  background: var(--color-surface);

  box-shadow: var(--shadow-soft);

  transition:
    transform var(--transition-normal),
    box-shadow var(--transition-normal),
    border-color var(--transition-normal);
}

.tool-card-link {
  color: inherit;
  text-decoration: none;
  cursor: pointer;
}

.tool-card--loading {
  display: flex;
  flex-direction: column;
  box-shadow: none;
}

.tool-loading-icon,
.tool-loading-title,
.tool-loading-line {
  display: block;
  border-radius: var(--radius-xs);
  background: #eef1f6;
}

.tool-loading-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
}

.tool-loading-title {
  width: 58%;
  height: 18px;
  margin-top: 22px;
}

.tool-loading-line {
  width: 100%;
  height: 12px;
  margin-top: 14px;
}

.tool-loading-line--short {
  width: 72%;
  margin-top: 9px;
}

.tool-loading-copy {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.tool-state {
  min-height: 206px;
  grid-column: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  box-sizing: border-box;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-muted);
  text-align: center;
}

.tool-state--error {
  color: #b45353;
}

.tool-grid--detailed {
  grid-template-columns: repeat(2, 1fr);
}

.tool-card-link:hover {
  transform: translateY(-2px);

  border-color: var(--color-border-strong);

  box-shadow: var(--shadow-hover);
}

.tool-card--developing {
  background: #fbfcfd;
  box-shadow: none;
}

.tool-card--integrating {
  background: #fffdf8;
}

.tool-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tool-icon {
  width: 44px;
  height: 44px;

  display: flex;
  align-items: center;
  justify-content: center;

  border-radius: var(--radius-md);

  border: 1px solid rgba(216, 225, 242, 0.82);
  background:
    linear-gradient(
      145deg,
      rgba(255, 255, 255, 0.92),
      rgba(234, 239, 255, 0.82)
    );

  color: var(--color-primary);

  font-size: 12px;
  font-weight: 700;

  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.94),
    0 5px 12px rgba(76, 85, 170, 0.08);
}

.tool-status {
  padding: 5px 10px;

  border-radius: var(--radius-xs);

  background: #f1f3f6;

  color: #7b8492;

  font-size: 12px;
  font-weight: 600;
}

.tool-status--available {
  background: #ecf8f2;
  color: #28745b;
}

.tool-status--integrating {
  background: #fff7e5;
  color: #9a6a18;
}

.tool-card h3 {
  margin: 20px 0 8px;

  color: var(--color-text);

  font-size: 18px;
  font-weight: 600;
}

.tool-card p {
  margin: 0;

  color: var(--color-text-secondary);

  line-height: 1.7;

  font-size: 14px;
}

.tool-grid--detailed .tool-card {
  min-height: 244px;

  display: flex;
  flex-direction: column;
}

.tool-grid--detailed .tool-state {
  min-height: 244px;
}

.tool-grid--detailed .tool-card p {
  flex: 1;
}

.tool-footer {
  margin-top: 24px;

  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.tool-action {
  min-height: 40px;
  padding: 0 16px;

  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;

  border: none;
  border-radius: 10px;

  background: linear-gradient(135deg, #4f7cff, #655ce7);
  color: #fff;

  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;

  transition:
    filter var(--transition-fast),
    box-shadow var(--transition-fast);
}

.tool-action:not(:disabled):hover {
  filter: brightness(1.04);
  box-shadow: 0 8px 18px rgba(76, 85, 170, 0.16);
}

.tool-action--placeholder {
  border: 1px solid var(--color-border);
  background: #f1f3f6;
  color: #7b8492;
  cursor: default;
}

@media (max-width: 900px) {
  .tool-grid {
    grid-template-columns:
      repeat(2, 1fr);
  }

  .tool-grid--detailed {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .section {
    width: calc(100% - 32px);
    margin: 56px auto 72px;
  }

  .section--detailed {
    margin-top: 32px;
  }

  .tool-grid {
    grid-template-columns:
      1fr;
  }
}

/* Home-only surface variant. The detailed /tools presentation stays unchanged. */
.section--home {
  width: 100%;
  margin: 0;
  font-family: var(--home-font, inherit);
  color: var(--home-text, #22292c);
}

.section--home .tool-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-top: 20px;
}

.section--home.section--preview .tool-grid {
  grid-template-columns: minmax(0, 1fr);
  margin-top: 0;
}

.section--home .tool-card {
  position: relative;
  isolation: isolate;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  min-width: 0;
  min-height: 0;
  height: auto;
  aspect-ratio: 1 / 1;
  padding: 20px;
  overflow: hidden;
  border: 1px solid var(--home-border, #e5e8e9);
  border-radius: var(--home-radius, 12px);
  background: var(--home-surface, #fff);
  box-shadow: var(--tool-inset-shadow, 0 0 0 0 transparent);
  transition: border-color var(--home-motion, 220ms) var(--home-ease, ease),
    background-color var(--home-motion, 220ms) var(--home-ease, ease),
    transform var(--home-motion, 220ms) var(--home-ease, ease),
    box-shadow var(--home-motion, 220ms) var(--home-ease, ease);
}

.tool-background {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 0;
  width: 100%;
  /* Reserve the two-line copy and navigation before allocating image space. */
  height: min(65%, calc(100% - 144px));
  object-fit: cover;
  pointer-events: none;
}

.section--home .tool-card--with-background::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  height: min(65%, calc(100% - 144px));
  z-index: 0;
  background: linear-gradient(to bottom, rgb(255 255 255 / 0) calc(100% - 40px), var(--home-surface, #fff));
  pointer-events: none;
}

.section--home .tool-card:not(.tool-card--with-background)::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  height: min(65%, calc(100% - 144px));
  background: linear-gradient(to bottom, #f5f6f7, #edf0ef calc(100% - 40px), var(--home-surface, #fff));
  pointer-events: none;
}

.tool-preview-notice {
  margin: 16px 0 0;
  color: var(--home-earth, #6d5b55);
  font-size: 13px;
  line-height: 1.6;
}

@supports (mask-image: linear-gradient(#000, transparent)) or (-webkit-mask-image: linear-gradient(#000, transparent)) {
  .tool-background {
    -webkit-mask-image: linear-gradient(to bottom, #000 calc(100% - 40px), transparent);
    mask-image: linear-gradient(to bottom, #000 calc(100% - 40px), transparent);
  }

  .section--home .tool-card--with-background::after { display: none; }
}

.section--home .tool-card--featured {
  --tool-inset-shadow: inset 0 0 0 1px var(--home-yellow, #f7b334);
  border-color: var(--home-yellow, #f7b334);
}

.section--home .tool-card[aria-disabled="true"] { cursor: default; }

.tool-home-content {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 10px;
  min-width: 0;
}
.tool-home-copy {
  display: grid;
  grid-template-rows: 48.6px 43.4px;
  gap: 8px;
  min-width: 0;
}

.section--home .tool-card h3 {
  align-self: end;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  overflow-wrap: anywhere;
  color: var(--home-text, #22292c);
  font-size: 18px;
  font-weight: 600;
  line-height: 1.35;
}

.section--home .tool-card p {
  align-self: start;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  overflow-wrap: anywhere;
  color: var(--home-secondary, #586165);
  font-size: 14px;
  font-weight: 400;
  line-height: 1.55;
}

.tool-home-navigation,
.tool-home-unavailable {
  justify-self: end;
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  white-space: nowrap;
  color: var(--home-text, #22292c);
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
}
.tool-home-unavailable { color: var(--home-muted, #697378); font-size: 12px; font-weight: 400; }

.tool-home-action-label {
  position: relative;
  isolation: isolate;
  display: inline-block;
  font-size: 15px;
  font-weight: 600;
  line-height: 20px;
  color: var(--home-text, #22292c);
}

.tool-home-action-label::before {
  content: '';
  position: absolute;
  left: 1px;
  top: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(transparent 45%, var(--home-green, #8dfc08) 45%);
  z-index: -1;
  pointer-events: none;
}

.tool-surface-arrow {
  display: block;
  flex: none;
  width: 18px;
  height: 18px;
  fill: none;
  color: var(--home-text, #22292c);
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
  opacity: .8;
  pointer-events: none;
  transition: transform var(--home-motion, 220ms) var(--home-ease, ease);
}

.section--home .tool-card-link:hover {
  transform: translateY(-2px);
  border-color: #9fa9ad;
  box-shadow: var(--tool-inset-shadow, 0 0 0 0 transparent), 0 8px 22px rgb(34 41 44 / 9%);
}
.section--home .tool-card--featured.tool-card-link:hover { border-color: var(--home-yellow, #f7b334); }
.section--home .tool-card-link:active { transform: translateY(0); background-color: #f5f6f7; }
.section--home .tool-card-link:focus-visible { outline: 2px solid var(--home-earth, #6d5b55); outline-offset: 3px; }
.tool-card-link:hover .tool-surface-arrow,
.tool-card-link:focus-visible .tool-surface-arrow { transform: translateX(3px); opacity: 1; }

.section--home .tool-state {
  min-height: 200px;
  border-color: var(--home-border, #e5e8e9);
  color: var(--home-muted, #697378);
  background: var(--home-surface, #fff);
}
.section--home .tool-state--error { color: #a23e3e; }
.section--home .tool-loading-title { margin-top: 0; }

@media (max-width: 1050px) {
  .section--home .tool-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 600px) {
  .section--home { width: 100%; margin: 0; }
  .section--home .tool-grid { grid-template-columns: minmax(0, 1fr); }
}

@media (prefers-reduced-motion: reduce) {
  .section--home .tool-card, .tool-surface-arrow { transition: none; }
  .section--home .tool-card-link:hover,
  .section--home .tool-card-link:active { transform: none; }
  .tool-card-link:hover .tool-surface-arrow,
  .tool-card-link:focus-visible .tool-surface-arrow { transform: none; }
}
</style>
