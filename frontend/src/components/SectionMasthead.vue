<script setup>
import { computed, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import ChevronRight from './ChevronRight.vue'

const props = defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  to: { type: String, required: true },
  image: { type: String, default: '' },
  fallbackImage: { type: String, default: '' },
  preview: { type: Boolean, default: false },
  textMode: { type: String, default: 'dark' },
  navigationLabel: { type: String, default: '' },
  navigationAriaLabel: { type: String, default: '' },
})

const failureCount = ref(0)
const displayedImage = computed(() => {
  if (failureCount.value === 0) return props.image || props.fallbackImage
  if (failureCount.value === 1 && props.image && props.image !== props.fallbackImage) return props.fallbackImage
  return ''
})
watch(() => [props.image, props.fallbackImage], () => { failureCount.value = 0 })
</script>

<template>
  <component :is="preview ? 'div' : RouterLink" :to="preview ? undefined : to"
    class="section-masthead" :class="{ 'is-preview': preview, 'is-light': textMode === 'light', 'has-image-error': failureCount > 0 }"
    :aria-label="preview ? undefined : navigationAriaLabel || `进入${title}`">
    <slot name="background">
      <img
        v-if="displayedImage"
        :key="displayedImage"
        class="masthead-image"
        :src="displayedImage"
        alt=""
        aria-hidden="true"
        @error="failureCount += 1"
      >
    </slot>
    <div class="masthead-copy">
      <h2>{{ title }}</h2>
      <p v-if="description">{{ description }}</p>
    </div>
    <span class="masthead-navigation" aria-hidden="true"><ChevronRight :size="28" stroke-width="3" class="masthead-arrow" /></span>
  </component>
</template>

<style scoped>
.section-masthead {
  --masthead-text-primary: #22292c;
  --masthead-text-secondary: #586165;
  --masthead-navigation-color: var(--masthead-text-primary);
  position: relative;
  isolation: isolate;
  display: flex;
  align-items: center;
  gap: 24px;
  width: 100%;
  min-width: 0;
  height: var(--home-masthead-height, 128px);
  padding: 16px var(--masthead-inline-padding, 32px);
  overflow: hidden;
  border-radius: var(--home-radius, 12px);
  background: var(--home-subtle, #f5f6f7);
  color: var(--masthead-text-primary);
  font-family: var(--home-font, inherit);
  text-decoration: none;
  cursor: pointer;
  transition: box-shadow var(--home-motion, 220ms) var(--home-ease, ease);
}

.is-light {
  --masthead-text-primary: #fff;
  --masthead-text-secondary: #f1f3f3;
}
/* A failed image falls back to a light bundled/neutral background. Render safe
   dark ink locally; never change the saved light preference. */
.is-light.has-image-error {
  --masthead-text-primary: #22292c;
  --masthead-text-secondary: #586165;
}

.masthead-image {
  position: absolute;
  inset: 0;
  z-index: -1;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  pointer-events: none;
}

.masthead-copy {
  display: grid;
  gap: 8px;
  flex: 1;
  max-width: 480px;
  min-width: 0;
}

h2 {
  margin: 0;
  color: var(--masthead-text-primary);
  font-size: 24px;
  font-weight: 600;
  line-height: 1.25;
  letter-spacing: normal;
  overflow-wrap: anywhere;
}

p {
  margin: 0;
  color: var(--masthead-text-secondary);
  font-size: 14px;
  font-weight: 400;
  line-height: 1.5;
  letter-spacing: normal;
  overflow-wrap: anywhere;
}

.masthead-navigation {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--masthead-navigation-slot, 28px);
  flex-shrink: 0;
  margin-left: auto;
  white-space: nowrap;
  color: var(--masthead-navigation-color);
}

.masthead-arrow {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  fill: none;
  stroke: currentColor;
  stroke-width: 3;
  stroke-linecap: round;
  stroke-linejoin: round;
  opacity: .8;
  pointer-events: none;
  transition: transform var(--home-motion, 220ms) var(--home-ease, ease),
    opacity var(--home-motion-fast, 140ms) var(--home-ease, ease);
}

.section-masthead:not(.is-preview):hover { box-shadow: inset 0 0 0 1px rgb(34 41 44 / 16%); }
.section-masthead:not(.is-preview):active { box-shadow: inset 0 0 0 2px rgb(34 41 44 / 22%); }
.is-preview { cursor: default; }
.section-masthead:focus-visible { outline: 2px solid var(--home-earth, #6d5b55); outline-offset: 3px; }
.section-masthead:not(.is-preview):hover .masthead-arrow,
.section-masthead:focus-visible .masthead-arrow { transform: translateX(3px); opacity: 1; }

@media (max-width: 768px) {
  .section-masthead:not(.is-preview) { height: auto; min-height: var(--home-masthead-height, 128px); }
  .section-masthead:not(.is-preview) .masthead-image { object-position: left center; }
}

@media (max-width: 480px) {
  .section-masthead:not(.is-preview) { padding: 24px var(--masthead-inline-padding, 20px); flex-direction: column; align-items: stretch; gap: 16px; }
  .section-masthead:not(.is-preview) .masthead-navigation { align-self: flex-end; }
  .section-masthead:not(.is-preview) h2 { font-size: 22px; line-height: 30px; }
}

@media (prefers-reduced-motion: reduce) {
  .section-masthead, .masthead-arrow { transition: none; }
  .section-masthead:hover .masthead-arrow,
  .section-masthead:focus-visible .masthead-arrow { transform: none; }
}
</style>
