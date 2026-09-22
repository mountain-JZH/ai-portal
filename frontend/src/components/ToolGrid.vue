<script setup>
import { RouterLink } from 'vue-router'

import tools from '../data/tools.json'

defineProps({
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

const toolCards = tools.map((tool) => ({
  ...tool,
  action: resolveAction(tool),
}))
</script>

<template>
  <section
    class="section"
    :class="{ 'section--detailed': detailed }"
  >
    <div class="section-header">
      <div>
        <h2>AI 与常用工具</h2>
        <p>将日常工具集中在一个入口</p>
      </div>
    </div>

    <div
      class="tool-grid"
      :class="{ 'tool-grid--detailed': detailed }"
    >
      <component
        :is="!detailed && tool.action ? tool.action.component : 'article'"
        v-for="tool in toolCards"
        :key="tool.id"
        v-bind="!detailed && tool.action ? tool.action.attributes : {}"
        class="tool-card"
        :class="{
          'tool-card-link': !detailed && tool.action,
          [`tool-card--${tool.status}`]: true,
        }"
      >
        <div class="tool-top">
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

        <h3>
          {{ tool.title }}
        </h3>

        <p>
          {{ tool.description }}
        </p>

        <div
          v-if="detailed"
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
</style>
