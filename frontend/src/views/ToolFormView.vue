<script setup>
import { computed, onUnmounted, reactive, ref, shallowRef, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { API_BASE_URL } from '../config/api'
import { adminFetch } from '../utils/adminAuth'
import SectionImageCropper from '../components/SectionImageCropper.vue'
import ToolCardPreview from '../components/ToolCardPreview.vue'

const route = useRoute()
const isEdit = computed(() => Boolean(route.params.id))
const toolId = computed(() => String(route.params.id || ''))
const defaults = () => ({
  title: '', description: '', status: 'available', actionType: 'none',
  actionTarget: '', buttonText: '', sortOrder: 0, isActive: true,
})
const form = reactive(defaults())
const loading = ref(false)
const notFound = ref(false)
const loadError = ref('')
const isSubmitting = ref(false)
const successMessage = ref('')
const errorMessage = ref('')
const createdId = ref(null)
const savedImage = ref('')
const pendingImage = shallowRef(null)
const pendingUrl = ref('')
const removeImage = ref(false)
const cropping = ref(false)
const cropBusy = ref(false)
const baseline = ref('')
// Current desktop Tool Card V2 allocates ~144px of a 288px card to the image.
const cropFrame = { key: 'tool-cover', title: '工具卡图片', width: 600, height: 300, outputWidth: 1600, outputHeight: 800 }

const actionTargetHint = computed(() => ({
  none: '无操作不需要目标地址',
  route: '填写 Vue 站内路由，例如 /tools',
  static: '填写静态页面路径，例如 /tools/qstart/index.html',
  external: '填写由用户浏览器直接访问的 URL 或公司内网地址',
})[form.actionType])
const actionTargetPlaceholder = computed(() => ({
  route: '/tools', static: '/tools/qstart/index.html', external: '请输入目标地址', none: '无需填写',
})[form.actionType])

function buildPayload() {
  return {
    title: form.title.trim(), description: form.description, status: form.status,
    actionType: form.actionType, actionTarget: form.actionType === 'none' ? '' : form.actionTarget,
    buttonText: form.buttonText, sortOrder: form.sortOrder, isActive: form.isActive ? 1 : 0,
  }
}
const hasChanges = computed(() => JSON.stringify(buildPayload()) !== baseline.value || Boolean(pendingImage.value) || removeImage.value)
const saveState = computed(() => isSubmitting.value ? '正在保存…' : errorMessage.value ? '保存失败，未生效'
  : hasChanges.value ? '存在未保存更改' : successMessage.value ? '保存成功，已生效' : '尚未修改')
const savedImageUrl = computed(() => savedImage.value.startsWith('/uploads/tools/') ? API_BASE_URL + savedImage.value : '')
const previewImage = computed(() => pendingUrl.value || (removeImage.value ? '' : savedImageUrl.value))
const previewTool = computed(() => ({ ...buildPayload(), id: toolId.value || 'draft', coverImageUrl: '' }))

function releasePending() {
  if (pendingUrl.value) URL.revokeObjectURL(pendingUrl.value)
  pendingUrl.value = ''
  pendingImage.value = null
}
function confirmImage(blob) {
  releasePending()
  pendingImage.value = blob
  pendingUrl.value = URL.createObjectURL(blob)
  removeImage.value = false
  cropping.value = false
  cropBusy.value = false
  successMessage.value = ''
  errorMessage.value = ''
}
function clearImage() {
  releasePending()
  removeImage.value = Boolean(savedImage.value)
  cropping.value = false
  successMessage.value = ''
  errorMessage.value = ''
}
function discardChanges() {
  const snapshot = baseline.value ? JSON.parse(baseline.value) : defaults()
  Object.assign(form, snapshot, { isActive: Boolean(snapshot.isActive) })
  releasePending()
  removeImage.value = false
  cropping.value = false
  successMessage.value = ''
  errorMessage.value = ''
}
function applyTool(data) {
  Object.assign(form, {
    title: data.title || '', description: data.description || '', status: data.status || 'developing',
    actionType: data.actionType || 'none', actionTarget: data.actionTarget || '',
    buttonText: data.buttonText || '', sortOrder: Number(data.sortOrder) || 0,
    isActive: Number(data.isActive) === 1,
  })
  savedImage.value = data.coverImageUrl || ''
  baseline.value = JSON.stringify(buildPayload())
}
function formatError(data, status) {
  if (Array.isArray(data?.detail)) return data.detail.map(item => item.msg).filter(Boolean).join('；') || '字段校验失败'
  return typeof data?.detail === 'string' ? data.detail : `保存失败（HTTP ${status}），请稍后重试`
}
async function initializePage() {
  releasePending()
  Object.assign(form, defaults())
  savedImage.value = ''
  removeImage.value = false
  cropping.value = false
  successMessage.value = ''
  errorMessage.value = ''
  createdId.value = null
  notFound.value = false
  loadError.value = ''
  baseline.value = JSON.stringify(buildPayload())
  if (!isEdit.value) { loading.value = false; return }
  loading.value = true
  try {
    const response = await adminFetch(`${API_BASE_URL}/api/tools/${encodeURIComponent(toolId.value)}`)
    if (response.status === 404) { notFound.value = true; return }
    if (!response.ok) throw new Error('工具加载失败，请稍后重试')
    applyTool(await response.json())
  } catch (error) {
    loadError.value = error.message || '工具加载失败，请稍后重试'
  } finally { loading.value = false }
}
async function submitTool() {
  if (isSubmitting.value || cropping.value || cropBusy.value || (!isEdit.value && createdId.value !== null)) return
  successMessage.value = ''
  errorMessage.value = ''
  if (!form.title.trim()) { errorMessage.value = '请输入工具名称'; return }
  isSubmitting.value = true
  try {
    const body = new FormData()
    body.append('payload', JSON.stringify({ ...buildPayload(), removeImage: removeImage.value }))
    if (pendingImage.value) body.append('file', new File([pendingImage.value], 'tool-cover.webp', { type: 'image/webp' }))
    const url = isEdit.value ? `${API_BASE_URL}/api/admin/tools/${encodeURIComponent(toolId.value)}` : `${API_BASE_URL}/api/admin/tools`
    const response = await adminFetch(url, { method: isEdit.value ? 'PUT' : 'POST', body })
    const data = await response.json().catch(() => null)
    if (response.status === 404 && isEdit.value) { notFound.value = true; return }
    if (!response.ok) throw new Error(formatError(data, response.status))
    applyTool(data)
    releasePending()
    removeImage.value = false
    createdId.value = data.id
    successMessage.value = isEdit.value ? '工具及图片配置已保存'
      : data.coverImageUrl ? '工具创建成功，图片已关联' : '工具创建成功'
  } catch (error) {
    errorMessage.value = error.message || '保存失败，原工具与图片未被替换'
  } finally { isSubmitting.value = false }
}
watch(() => JSON.stringify(buildPayload()), () => { successMessage.value = ''; errorMessage.value = '' }, { flush: 'sync' })
watch(() => route.fullPath, initializePage, { immediate: true })
onUnmounted(releasePending)
</script>

<template>
  <main class="content-form-page tool-editor">
    <div class="content-page-header">
      <div><h1>{{ isEdit ? '编辑工具' : '新增工具' }}</h1><p>维护展示内容与访问入口，预览首页卡片效果。</p></div>
    </div>
    <section v-if="loading" class="content-page-state" role="status">正在加载工具…</section>
    <section v-else-if="notFound" class="content-page-state"><h2>工具不存在</h2><RouterLink to="/admin/tools">返回工具管理</RouterLink></section>
    <section v-else-if="loadError" class="content-page-state content-page-state-error" role="alert">
      <h2>工具加载失败</h2><p>{{ loadError }}</p><RouterLink to="/admin/tools">返回工具管理</RouterLink>
    </section>
    <div v-else class="tool-editor-layout">
      <form class="content-form" @submit.prevent="submitTool">
        <fieldset :disabled="isSubmitting || (!isEdit && createdId !== null)">
          <legend>工具基本信息</legend>
          <div class="content-form-grid">
            <label class="content-form-field content-form-field-wide">
              <span>工具名称 <strong aria-hidden="true">*</strong></span>
              <input v-model="form.title" type="text" required maxlength="200" placeholder="请输入工具名称">
              <small>{{ [...form.title].length }} / 200 字；首页最多显示两行。</small>
            </label>
            <label class="content-form-field content-form-field-wide">
              <span>工具描述</span><textarea v-model="form.description" rows="5" maxlength="1000" placeholder="说明工具用途及适用场景" />
              <small>{{ [...form.description].length }} / 1000 字；首页展示最多两行，完整文字及换行仍会保留。</small>
            </label>
          </div>
        </fieldset>
        <fieldset :disabled="isSubmitting || (!isEdit && createdId !== null)">
          <legend>首页卡片图片</legend>
          <p class="tool-form-hint">取景比例 2:1，输出 1600×800 WebP。图片和文字一起保存后生效。</p>
          <p class="image-state">当前生效：{{ savedImage ? '已配置图片' : '未配置图片' }}</p>
          <code v-if="savedImage">{{ savedImage }}</code>
          <p v-if="pendingImage" class="image-state">已确认新取景，待保存 · {{ Math.round(pendingImage.size / 1024) }} KB</p>
          <p v-else-if="removeImage" class="image-state">待保存：清除图片，恢复中性兜底。</p>
          <div class="image-actions">
            <button type="button" :disabled="cropping" @click="cropping = true">{{ previewImage ? '更换图片并取景' : '选择图片并取景' }}</button>
            <button v-if="previewImage || savedImage" type="button" :disabled="cropping || removeImage" @click="clearImage">清除图片</button>
            <button v-if="pendingImage || removeImage" type="button" :disabled="cropping" @click="releasePending(); removeImage = false">撤销图片更改</button>
          </div>
          <SectionImageCropper v-if="cropping" local-only :section="cropFrame" @confirmed="confirmImage"
            @cancel="cropping = false" @busy-change="cropBusy = $event" />
          <small>清除只解除图片关联，不删除历史上传文件。取消取景不改变当前生效图片。</small>
        </fieldset>
        <fieldset :disabled="isSubmitting || (!isEdit && createdId !== null)">
          <legend>业务配置</legend>
          <div class="content-form-grid">
            <label class="content-form-field"><span>业务状态</span><select v-model="form.status"><option value="available">可用</option><option value="integrating">待接入</option><option value="developing">开发中</option></select></label>
            <label class="content-form-field"><span>按钮文字</span><input v-model="form.buttonText" maxlength="100" placeholder="例如：立即使用"><small>用于工具中心现有操作按钮；首页使用统一启动提示。</small></label>
            <label class="content-form-field"><span>动作类型</span><select v-model="form.actionType"><option value="none">无操作</option><option value="route">站内路由</option><option value="static">静态页面</option><option value="external">外部链接</option></select></label>
            <label class="content-form-field"><span>排序</span><input v-model.number="form.sortOrder" type="number" min="0" step="1" required></label>
            <label class="content-form-field content-form-field-wide"><span>动作目标</span><input v-model="form.actionTarget" maxlength="1000" :disabled="form.actionType === 'none'" :placeholder="actionTargetPlaceholder" aria-describedby="tool-action-target-hint"><small id="tool-action-target-hint">{{ actionTargetHint }}</small></label>
          </div>
          <label class="content-checkbox-field"><input v-model="form.isActive" type="checkbox"><span><strong>启用工具</strong><small>取消勾选后仅在管理列表中保留</small></span></label>
        </fieldset>
        <p class="save-state" role="status">{{ saveState }}</p>
        <div v-if="successMessage && !hasChanges" class="content-status-message content-status-success" role="status">
          {{ successMessage }}，ID：{{ createdId }}
          <RouterLink v-if="!isEdit" :to="`/admin/tools/${createdId}/edit`">继续编辑</RouterLink>
        </div>
        <div v-if="errorMessage" class="content-status-message content-status-error" role="alert">{{ errorMessage }}</div>
        <div class="content-form-actions">
          <RouterLink to="/admin/tools">返回工具管理</RouterLink>
          <button v-if="hasChanges" type="button" class="discard-button" :disabled="isSubmitting || cropBusy || (!isEdit && createdId !== null)" @click="discardChanges">撤销未保存更改</button>
          <button type="submit" :disabled="isSubmitting || cropping || cropBusy || (!isEdit && createdId !== null)">
            {{ isSubmitting ? '正在保存…' : !isEdit && createdId ? '已创建' : isEdit ? '保存修改' : '创建工具' }}
          </button>
        </div>
      </form>
      <aside class="tool-live-preview" aria-label="首页卡片实时预览">
        <h2>首页卡片预览</h2>
        <p>{{ pendingImage || removeImage || hasChanges ? '待保存预览，尚未生效' : '当前已保存配置' }}</p>
        <ToolCardPreview :tool="previewTool" :image="previewImage" />
        <p>288×288 桌面布局。文字截断仅用于展示，预览不执行跳转。</p>
        <p v-if="!form.isActive">此工具已停用，保存后不会在公开工具列表展示。</p>
      </aside>
    </div>
  </main>
</template>

<style scoped>
.tool-editor {
  --color-text: #22292c;
  --color-text-secondary: #586165;
  --color-muted: #697378;
  --color-border: #e5e8e9;
  --color-border-strong: #c9cfd2;
  --color-surface-soft: #f5f6f7;
  --color-primary: #6d5b55;
}
.content-page-header h1 { font-size: 28px; }
.content-page-header::after { background: #f7b334; }
.tool-editor-layout { display: grid; grid-template-columns: minmax(0, 1fr) 288px; gap: 32px; align-items: start; }
.content-form { width: 100%; max-width: none; padding: 0; border: 0; background: none; box-shadow: none; }
fieldset { margin: 0 0 28px; padding: 0 0 28px; border: 0; border-bottom: 1px solid #e5e8e9; min-width: 0; }
legend { padding: 0; margin-bottom: 20px; font-size: 18px; font-weight: 600; }
textarea { min-height: 126px; white-space: pre-wrap; }
small, .tool-form-hint { color: #697378; font-size: 12px; line-height: 1.6; }
.tool-form-hint { margin: 0 0 16px; }
.image-state { color: #586165; font-size: 13px; margin: 12px 0; }
code { display: block; overflow-wrap: anywhere; color: #6d5b55; font-size: 12px; }
.image-actions { display: flex; flex-wrap: wrap; gap: 12px; margin: 16px 0; }
.image-actions button, .content-form-actions .discard-button { padding: 9px 14px; border: 1px solid #c9cfd2; border-radius: 8px; background: #fff; color: #22292c; font-size: 13px; cursor: pointer; box-shadow: none; }
.content-form-actions button[type=submit] { background: #f7b334; color: #22292c; border-color: #f7b334; box-shadow: none; }
.content-form-actions button[type=submit]:hover:not(:disabled) { background: #eaa529; }
button:disabled { cursor: not-allowed; opacity: .55; }
input:focus-visible, textarea:focus-visible, select:focus-visible, button:focus-visible { outline: 2px solid #6d5b55; outline-offset: 3px; }
.tool-live-preview { position: sticky; top: 24px; min-width: 0; }
.tool-live-preview h2 { font-size: 18px; margin: 0 0 12px; }
.tool-live-preview p, .save-state { font-size: 12px; color: #697378; line-height: 1.7; }
.tool-live-preview p { margin: 12px 0; }
.content-form-field input:disabled { background: #f5f6f7; color: #697378; cursor: not-allowed; }
@media (max-width: 1100px) { .tool-editor-layout { grid-template-columns: minmax(0, 1fr); } .tool-live-preview { position: static; } }
</style>
