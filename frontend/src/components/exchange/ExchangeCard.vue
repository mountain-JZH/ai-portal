<script setup>
import { computed, ref, watch } from 'vue'
import { formatAddedDate, safeUrl } from '../../utils/exchangeDiscovery'

const props = defineProps({ resource: { type: Object, required: true } })
const imageFailed = ref(false)
watch(
  () => props.resource.imageUrl,
  () => {
    imageFailed.value = false
  },
)
const hasImage = computed(() => props.resource.imageUrl && !imageFailed.value)
const externalUrl = computed(() => safeUrl(props.resource.externalUrl))
const addedDate = computed(() => formatAddedDate(props.resource.createdAt))
</script>

<template>
  <article class="discovery-sheet">
    <div class="sheet-copy">
      <div class="archive-line">
        <span class="archive-number num">{{ resource.displayNumber }}</span>
      </div>
      <h2 class="resource-title">{{ resource.title }}</h2>
      <div class="resource-meta">
        <span>{{ resource.domain }}</span
        ><i class="dot" aria-hidden="true" />
        <span>{{ resource.type }}</span>
        <span v-if="addedDate" class="added-date">添加于 {{ addedDate }}</span>
      </div>
      <div class="resource-content">
        <section v-if="resource.description" class="resource-section">
          <h3>描述</h3>
          <p>{{ resource.description }}</p>
        </section>
        <section v-if="resource.reason" class="resource-section resource-reason">
          <h3><span class="reason-highlight">推荐原因</span></h3>
          <p>{{ resource.reason }}</p>
        </section>
        <a
          v-if="externalUrl"
          class="resource-external"
          :href="externalUrl"
          target="_blank"
          rel="noopener noreferrer"
        >
          <span class="external-label">外部跳转</span>
          <svg class="external-arrow" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M7 17 17 7M7 7h10v10" />
          </svg>
          <span class="sr-only">（新标签页打开）</span>
        </a>
      </div>
    </div>
    <div class="visual-column" :class="{ 'visual-column--image': hasImage }">
      <div v-if="hasImage" class="cover-frame">
        <img
          class="cropped-cover"
          :src="resource.imageUrl"
          alt="分享资源封面"
          @error="imageFailed = true"
        />
      </div>
      <div v-else class="uncovered">
        <span class="giant num" aria-hidden="true">{{ resource.displayNumber }}</span>
        <div>
          <p class="note">
            {{
              imageFailed
                ? '封面暂时无法显示，仍可阅读完整内容。'
                : '没有封面，\n也可以有值得分享的发现。'
            }}
          </p>
          <div class="dash" aria-hidden="true" />
        </div>
      </div>
    </div>
  </article>
</template>
