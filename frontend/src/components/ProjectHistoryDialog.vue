<script setup>
import { nextTick, onBeforeUnmount, ref } from 'vue'
import { loadProjectHistory } from '../services/projects'
import { acquireModalPageLock } from '../utils/modalPageLock'
import { displayValue, importTime } from '../utils/projectDisplay'
import { projectFields, editorStages } from '../utils/projectEditor'

const dialog = ref(null)
const project = ref(null)
const field = ref('')
const items = ref([])
const total = ref(0)
const loading = ref(false)
const error = ref('')
let controller,
  revision = 0,
  releaseLock,
  trigger,
  disposed = false
const labels = {
  ...Object.fromEntries(projectFields),
  ...Object.fromEntries(
    editorStages.map((name, index) => [
      `stage_${String(index + 1).padStart(2, '0')}`,
      `${index + 1} · ${name}`,
    ]),
  ),
  __created__: '创建项目',
  serial: '原台账序号',
  progressUpdate: 'Excel 进度更新标记',
}
const kinds = {
  baseline: '历史台账初始值',
  initial: '初始填写',
  create: '创建项目',
  fill: '首次填写',
  clear: '清空内容',
  update: '修改',
  restore: '恢复旧值',
}
async function load(more = false) {
  const version = ++revision
  controller?.abort()
  controller = new AbortController()
  loading.value = true
  error.value = ''
  try {
    const data = await loadProjectHistory(
      project.value.id,
      field.value,
      more ? items.value.length : 0,
      controller.signal,
    )
    if (!disposed && version === revision) {
      items.value = more ? [...items.value, ...data.items] : data.items
      total.value = data.total
    }
  } catch (cause) {
    if (!disposed && version === revision && cause.name !== 'AbortError')
      error.value = cause.message
  } finally {
    if (!disposed && version === revision) loading.value = false
  }
}
async function open(value, name = '') {
  if (!dialog.value?.open) trigger = document.activeElement
  project.value = value
  field.value = name
  items.value = []
  total.value = 0
  await nextTick()
  if (disposed || !dialog.value) return
  try {
    if (!dialog.value.open) {
      releaseLock = acquireModalPageLock()
      dialog.value.showModal()
      dialog.value.querySelector('button')?.focus({ preventScroll: true })
    }
  } catch (cause) {
    releaseLock?.()
    releaseLock = null
    throw cause
  }
  await load()
}
function closed() {
  if (dialog.value?.open) return
  revision++
  controller?.abort()
  releaseLock?.()
  releaseLock = null
  const target = trigger
  trigger = null
  if (!disposed && target?.isConnected) target.focus({ preventScroll: true })
}
function close() {
  dialog.value?.close()
  closed()
}
function backdrop(event) {
  if (event.target !== dialog.value) return
  const r = dialog.value.getBoundingClientRect()
  if (
    event.clientX < r.left ||
    event.clientX > r.right ||
    event.clientY < r.top ||
    event.clientY > r.bottom
  )
    close()
}
onBeforeUnmount(() => {
  disposed = true
  close()
})
defineExpose({ open })
</script>

<template>
  <dialog
    ref="dialog"
    class="project-history-dialog"
    aria-labelledby="project-history-title"
    @cancel.prevent="close"
    @close="closed"
    @click="backdrop"
  >
    <header>
      <div>
        <h2 id="project-history-title">{{ labels[field] || (field ? field : '项目操作记录') }}</h2>
        <p>{{ project?.name }}</p>
      </div>
      <button type="button" aria-label="关闭项目历史" autofocus @click="close">关闭</button>
    </header>
    <div class="project-history-body">
      <p v-if="error" role="alert">
        {{ error }} <button type="button" @click="load(false)">重试</button>
      </p>
      <p v-if="loading" role="status">正在读取历史…</p>
      <p
        v-if="
          !loading &&
          !error &&
          (!items.length ||
            items.every((item) => ['baseline', 'initial', 'create'].includes(item.change_type)))
        "
      >
        暂无后续修改记录。初始内容仅代表创建或实际入库时的快照。
      </p>
      <article v-for="item in items" :key="item.id">
        <div class="project-history-meta">
          <strong>{{ kinds[item.change_type] || item.change_type }}</strong
          ><span
            >{{ item.changed_at ? importTime(item.changed_at) : '历史台账初始值（时间未提供）' }} ·
            版本 {{ item.project_version }}</span
          >
        </div>
        <p>
          {{ item.employee_name_snapshot || '未记录姓名'
          }}<span v-if="item.employee_username_snapshot"
            >（{{ item.employee_username_snapshot }}）</span
          >
          ·
          {{
            item.actor_type === 'admin_import'
              ? '管理员执行导入'
              : item.actor_type === 'legacy_import'
                ? '非原始业务发生时间'
                : '员工维护'
          }}
        </p>
        <p v-if="!field">字段：{{ labels[item.field_name] || item.field_name }}</p>
        <dl>
          <div>
            <dt>修改前</dt>
            <dd>{{ displayValue(item.old_value) }}</dd>
          </div>
          <div>
            <dt>修改后</dt>
            <dd>{{ displayValue(item.new_value) }}</dd>
          </div>
        </dl>
      </article>
      <button
        v-if="items.length < total && !error"
        type="button"
        :disabled="loading"
        @click="load(true)"
      >
        加载更多历史
      </button>
    </div>
  </dialog>
</template>

<style scoped>
.project-history-dialog {
  position: fixed;
  inset: 0;
  margin: auto;
  width: min(900px, calc(100vw - 28px));
  max-width: 100%;
  max-height: 85vh;
  max-height: 85dvh;
  border: 1px solid #e5e8e8;
  border-radius: 12px;
  padding: 0;
  color: #22292c;
  background: #fff;
  overflow: hidden;
}
.project-history-dialog[open] {
  display: flex;
  flex-direction: column;
}
.project-history-dialog::backdrop {
  background: rgb(20 29 31 / 0.38);
}
header {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 18px;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e8e8;
  flex-shrink: 0;
}
h2 {
  font-size: 18px;
  margin: 0;
}
p {
  font-size: 12px;
  line-height: 1.7;
  overflow-wrap: anywhere;
}
header p {
  margin: 8px 0 0;
  color: #6d5b55;
}
button {
  font: inherit;
  white-space: nowrap;
  border: 1px solid #dfe4e4;
  border-radius: 5px;
  background: #f5f6f7;
  padding: 8px 12px;
  cursor: pointer;
}
button:focus-visible {
  outline: 3px solid #f7b334;
  outline-offset: 2px;
}
.project-history-body {
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0;
  overscroll-behavior: contain;
  padding: 20px 24px;
}
.project-history-body article {
  border: 1px solid #e5e8e8;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 14px;
}
.project-history-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: space-between;
  font-size: 12px;
}
.project-history-meta span {
  color: #7e898d;
}
dl {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin: 12px 0 0;
}
dl > div {
  min-width: 0;
}
dt {
  font-size: 11px;
  color: #7e898d;
  margin-bottom: 6px;
}
dd {
  margin: 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font-size: 13px;
  line-height: 1.8;
}
@media (max-width: 650px) {
  header,
  .project-history-body {
    padding: 16px;
  }
  dl {
    grid-template-columns: 1fr;
  }
}
</style>
