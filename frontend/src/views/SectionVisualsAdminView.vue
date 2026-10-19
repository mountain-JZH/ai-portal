<script setup>
import { onMounted, ref } from 'vue'
import { API_BASE_URL } from '../config/api'
import { SECTION_VISUALS, resolveSectionImage } from '../config/sectionVisuals'
import { adminFetch } from '../utils/adminAuth'
import BannerManagementTabs from '../components/BannerManagementTabs.vue'
import MastheadPreview from '../components/MastheadPreview.vue'
import SectionImageCropper from '../components/SectionImageCropper.vue'

const configurations = ref({})
const loading = ref(true)
const errorMessage = ref('')
const successMessage = ref('')
const editingKey = ref('')
const editorBusy = ref(false)
const textModes = ref({})
const savingColor = ref('')
const colorErrors = ref({})

function savedMode(key) { return configurations.value[key]?.textMode === 'light' ? 'light' : 'dark' }

async function loadConfigurations() {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await adminFetch(`${API_BASE_URL}/api/admin/section-visuals`)
    if (!response.ok) throw new Error(`栏目配置加载失败（${response.status}）`)
    const data = await response.json()
    if (!Array.isArray(data)) throw new Error('栏目配置格式不正确')
    configurations.value = Object.fromEntries(data.map((item) => [item.sectionKey, item]))
    textModes.value = Object.fromEntries(SECTION_VISUALS.map(({ key }) => [key, savedMode(key)]))
  } catch (error) { errorMessage.value = error.message || '栏目配置加载失败，请重试' }
  finally { loading.value = false }
}
function saved(data) {
  configurations.value = { ...configurations.value, [data.sectionKey]: data }
  textModes.value[data.sectionKey] = data.textMode
  colorErrors.value[data.sectionKey] = ''
  successMessage.value = `${data.title}配置已保存，刷新首页即可查看。`
  editingKey.value = ''
  editorBusy.value = false
}
function startEditing(key) {
  if (editorBusy.value) return
  successMessage.value = ''
  editingKey.value = key
}

async function saveTextMode(key) {
  if (savingColor.value || editorBusy.value || editingKey.value) return
  savingColor.value = key
  colorErrors.value[key] = ''
  successMessage.value = ''
  try {
    const response = await adminFetch(`${API_BASE_URL}/api/admin/section-visuals/${key}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ textMode: textModes.value[key] }),
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : '文字颜色保存失败')
    if (data.sectionKey !== key || !['dark', 'light'].includes(data.textMode)) throw new Error('服务器返回了无效配置，请重新加载确认')
    saved(data)
  } catch (error) { colorErrors.value[key] = error.message || '保存失败，原配置保持不变' }
  finally { savingColor.value = '' }
}
onMounted(loadConfigurations)
</script>

<template>
  <main class="section-visuals-page">
    <header>
      <h1>栏目背景图管理</h1>
      <p>分别管理两个首页报头，不影响主 Banner 轮播。可单独保存文字颜色，或与新背景一起保存。</p>
    </header>
    <BannerManagementTabs />
    <p v-if="loading" role="status">正在加载当前配置…</p>
    <div v-else-if="errorMessage" role="alert" class="error-message">
      {{ errorMessage }} <button type="button" @click="loadConfigurations">重新加载</button>
    </div>
    <template v-else>
      <p v-if="successMessage" role="status">{{ successMessage }}</p>
      <section v-for="section in SECTION_VISUALS" :key="section.key" class="section-card">
        <div class="section-heading">
          <div>
            <h2>{{ section.title }}</h2>
            <p>建议输出 {{ section.outputWidth }} × {{ section.outputHeight }}px · 比例 {{ (section.width / section.height).toFixed(3) }}:1</p>
          </div>
          <button type="button" :disabled="editorBusy || Boolean(savingColor) || Boolean(editingKey)"
            @click="startEditing(section.key)">更换图片</button>
        </div>
        <fieldset :disabled="editorBusy || Boolean(savingColor)">
          <legend>文字颜色</legend>
          <label><input v-model="textModes[section.key]" type="radio" :name="`text-${section.key}`" value="dark"> 深色文字</label>
          <label><input v-model="textModes[section.key]" type="radio" :name="`text-${section.key}`" value="light"> 浅色文字</label>
          <button type="button" :disabled="Boolean(editingKey) || textModes[section.key] === savedMode(section.key)"
            @click="saveTextMode(section.key)">{{ savingColor === section.key ? '正在保存…' : '保存文字颜色' }}</button>
        </fieldset>
        <p v-if="colorErrors[section.key]" class="error-message" role="alert">{{ colorErrors[section.key] }}；已生效配置未改变。</p>
        <p class="preview-label">{{ textModes[section.key] !== savedMode(section.key) ? '配置预览 · 文字颜色尚未保存' : '当前生效预览' }} · {{ configurations[section.key]?.image ? '已配置背景' : '使用内置默认背景' }}</p>
        <MastheadPreview :section="section" :image="resolveSectionImage(configurations[section.key]?.image)"
          :fallback-image="section.defaultImage" :text-mode="textModes[section.key]" />
        <p class="preview-label">背景明暗变化较大时，请调整取景或更换图片，确保标题、说明及导航均清晰。</p>
        <p v-if="configurations[section.key]?.updatedAt" class="updated-time">更新时间：{{ configurations[section.key].updatedAt }}</p>
        <p v-if="editingKey === section.key">取景期间可在上方切换文字颜色，最终与图片一起保存。</p>
        <SectionImageCropper v-if="editingKey === section.key" :key="section.key" :section="section" :text-mode="textModes[section.key]"
          class="inline-editor" @busy-change="editorBusy = $event" @cancel="editingKey = ''" @saved="saved" />
      </section>
    </template>
  </main>
</template>

<style scoped>
.section-visuals-page { width: 100%; min-width: 0; color: #22292c; }
header { margin-bottom: 24px; }
h1 { margin: 0 0 12px; font-size: 28px; }
h2 { margin: 0 0 8px; font-size: 18px; font-weight: 600; }
p { color: #586165; font-size: 14px; line-height: 1.7; overflow-wrap: anywhere; }
.section-card { min-width: 0; padding: 24px; margin-top: 24px; border: 1px solid #e5e8e9; border-radius: 12px; background: #fff; }
.section-heading { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 16px; }
.section-heading p { margin: 0; }
.preview-label, .updated-time { font-size: 13px; }
.preview-label { margin: 20px 0 12px; }
.inline-editor { margin-top: 24px; }
fieldset { display: flex; flex-wrap: wrap; align-items: center; gap: 16px; margin: 20px 0 0; padding: 12px 0; border: 0; min-width: 0; }
legend { font-size: 14px; font-weight: 600; }
fieldset label { display: flex; align-items: center; gap: 6px; font-size: 14px; }
button { padding: 10px 16px; border: 1px solid #c9cfd2; border-radius: 8px; background: #fff; color: #22292c; font: inherit; font-size: 14px; cursor: pointer; }
button:disabled { opacity: .5; cursor: not-allowed; }
button:focus-visible { outline: 2px solid #6d5b55; outline-offset: 3px; }
.error-message { color: #b33333; }
@media (max-width: 500px) { .section-card { padding: 16px; } }
</style>
