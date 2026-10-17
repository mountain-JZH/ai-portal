<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  banner: { type: Object, required: true },
})

const emit = defineEmits(['action'])
const desktopFailed = ref(false)

watch(() => props.banner.image, () => { desktopFailed.value = false })

const isImageOnly = computed(() => props.banner.bannerType === 'image_only')
const hasAction = computed(() => (
  !isImageOnly.value && Boolean(props.banner.buttonText?.trim()) &&
  ['route', 'external', 'dify'].includes(props.banner.actionType) &&
  (props.banner.actionType === 'dify' || Boolean(props.banner.actionTarget?.trim()))
))
const hasDesktopImage = computed(() => Boolean(props.banner.image) && !desktopFailed.value)
const desktopFocus = computed(() => `${props.banner.focusX ?? 50}% ${props.banner.focusY ?? 50}%`)

function handleAction() {
  if (hasAction.value) emit('action', props.banner)
}
</script>

<template>
  <div class="banner-frame">
    <article
      class="banner-slide"
      :class="{
        'banner-slide--full': !isImageOnly,
      }"
    >
      <div class="banner-art" :class="{ 'banner-art--empty': !hasDesktopImage }">
        <img
          v-if="hasDesktopImage"
          class="banner-art-image"
          :src="banner.image"
          :alt="banner.altText || ''"
          :style="{ objectPosition: desktopFocus }"
          @error="desktopFailed = true"
        >
        <span v-if="!hasDesktopImage && !isImageOnly" class="banner-image-empty">图片暂无预览</span>
      </div>

      <div v-if="!isImageOnly" class="banner-copy">
        <span class="banner-kicker">{{ banner.kicker || 'AI PORTAL / 信息运维' }}</span>
        <h2>{{ banner.title }}</h2>
        <p v-if="banner.description">{{ banner.description }}</p>
        <button v-if="hasAction" type="button" class="banner-cta" @click="handleAction">
          {{ banner.buttonText }}
        </button>
      </div>
    </article>
  </div>
</template>

<style scoped>
.banner-frame { container: banner-frame / inline-size; width: 100%; height: 100%; min-width: 0; }
.banner-slide {
  position: relative;
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: var(--banner-ui-cloud);
  color: var(--banner-ui-graphite);
}
.banner-art { position: absolute; inset: 0; overflow: hidden; }
.banner-art-image { display: block; width: 100%; height: 100%; object-fit: cover; }
.banner-art--empty { display: grid; place-items: center; background: #e6ebec; }
.banner-image-empty { color: var(--banner-ui-muted); font-size: 1.167cqw; }

.banner-slide--full { background: var(--banner-ui-white); }
.banner-slide--full .banner-art-image {
  -webkit-mask-image: linear-gradient(90deg, transparent 20%, rgba(0, 0, 0, .08) 30%, rgba(0, 0, 0, .35) 42%, rgba(0, 0, 0, .7) 52%, rgba(0, 0, 0, .95) 62%, #000 70%);
  mask-image: linear-gradient(90deg, transparent 20%, rgba(0, 0, 0, .08) 30%, rgba(0, 0, 0, .35) 42%, rgba(0, 0, 0, .7) 52%, rgba(0, 0, 0, .95) 62%, #000 70%);
}
.banner-slide--full .banner-copy {
  position: relative;
  z-index: 1;
  width: 47%;
}
.banner-copy {
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  min-width: 0;
  height: 100%;
  padding: 2.167cqw 2.833cqw 3.5cqw 4.8cqw;
}
.banner-kicker { color: var(--banner-ui-earth); font-size: .917cqw; font-weight: 700; letter-spacing: .11em; }
.banner-copy h2 { width: 100%; margin: .917cqw 0 .583cqw; font-size: 2.7cqw; line-height: 1.19; font-weight: 700; letter-spacing: -.025em; overflow-wrap: anywhere; text-wrap: balance; }
.banner-copy p { margin: 0; color: var(--banner-ui-muted); font-size: 1.12cqw; line-height: 1.55; overflow-wrap: anywhere; }
.banner-cta { box-sizing: border-box; display: inline-flex; align-items: center; justify-content: center; gap: 1.167cqw; min-height: 3.667cqw; max-width: 100%; margin-top: 1.333cqw; padding: .583cqw 1.333cqw; border: 1px solid #d89520; border-radius: .5cqw; background: var(--banner-ui-yellow); color: var(--banner-ui-graphite); font-size: 1.083cqw; font-weight: 700; text-decoration: none; overflow-wrap: anywhere; cursor: pointer; }
.banner-cta:focus-visible { outline: 3px solid var(--banner-ui-green-deep); outline-offset: 3px; }

@container banner-frame (max-width: 600px) {
  .banner-slide .banner-copy { width: 64%; padding: 12px 10px 22px 5%; }
  .banner-slide .banner-kicker { font-size: 9px; }
  .banner-slide .banner-copy h2 { margin: 7px 0 5px; font-size: clamp(14px, 2.7cqw, 18px); }
  .banner-slide .banner-copy p { font-size: clamp(10px, 1.12cqw, 12px); line-height: 1.4; }
  .banner-slide .banner-cta { min-height: 32px; margin-top: 8px; padding: 5px 10px; font-size: 11px; }
  .banner-slide--full .banner-art-image {
    -webkit-mask-image: linear-gradient(90deg, transparent 28%, rgba(0, 0, 0, .08) 43%, rgba(0, 0, 0, .35) 58%, rgba(0, 0, 0, .7) 70%, rgba(0, 0, 0, .95) 78%, #000 85%);
    mask-image: linear-gradient(90deg, transparent 28%, rgba(0, 0, 0, .08) 43%, rgba(0, 0, 0, .35) 58%, rgba(0, 0, 0, .7) 70%, rgba(0, 0, 0, .95) 78%, #000 85%);
  }
}
</style>
