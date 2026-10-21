<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import {
  onBeforeRouteLeave,
  onBeforeRouteUpdate,
  RouterLink,
  useRoute,
  useRouter,
} from 'vue-router'
import { currentEmployee } from '../utils/authState'
import {
  editableProject,
  editorStages,
  projectChanges,
  projectFields,
} from '../utils/projectEditor'
import {
  loadEmployeeProjectDetail,
  loadProjectHistory,
  saveEmployeeProject,
} from '../services/projects'
import { importTime } from '../utils/projectDisplay'
import ProjectHistoryDialog from '../components/ProjectHistoryDialog.vue'
import ProjectNodeEditor from '../components/ProjectNodeEditor.vue'
import { nodeDraftStage } from '../utils/projectNodes'

const route = useRoute(),
  router = useRouter()
const permitted = computed(() => Boolean(currentEmployee.value?.canEditProjects))
const project = ref(null),
  original = ref(editableProject()),
  form = reactive(editableProject())
const loading = ref(false),
  saving = ref(false),
  error = ref(''),
  success = ref(''),
  conflict = ref(false)
const recent = ref({}),
  historyDialog = ref(null)
const changes = computed(() => projectChanges(form, original.value))
const dirty = computed(() => Object.keys(changes.value).length > 0)

const isNew = computed(() => !route.params.id)
const mode = ref(route.params.id ? 'progress' : 'archive')
const title = computed(() =>
  isNew.value ? '新增项目' : mode.value === 'progress' ? '更新项目进展' : '维护项目档案',
)
const labels = Object.fromEntries(projectFields)
const basicFields = ['name', 'resource', 'leader', 'owner', 'district']
const attributeFields = ['management', 'ownership', 'customerType', 'priority', 'valueRating']
const businessGroups = [
  { id: 'pv', name: '分布式光伏', fields: ['pvArea', 'pvCapacity'], compact: true },
  { id: 'storage', name: '储能', fields: ['storageCapacity'] },
  { id: 'charging', name: '充电桩', fields: ['chargingScale'] },
  { id: 'energy', name: '分布式能源', fields: ['energyType', 'energyScale'] },
]
const openBusinesses = reactive({})
function updateNodes(nodes) {
  if (!permitted.value || saving.value || loading.value || (!project.value && !isNew.value)) return
  form.stages = [...nodes]
  form.currentStage = nodeDraftStage(
    nodes,
    original.value.stages,
    original.value.currentStage,
    editorStages,
  )
}
function hasBusinessValue(value) {
  return (
    value != null &&
    !['', '/', '／', '-', '—', '无', '暂无', '未填写', '不涉及', 'N/A', 'NA'].includes(
      String(value).trim().toUpperCase(),
    )
  )
}
function initializeBusinessGroups() {
  for (const group of businessGroups)
    openBusinesses[group.id] = group.fields.some((field) => hasBusinessValue(form[field]))
}
function switchMode(value) {
  if (!saving.value && !loading.value && !isNew.value && ['progress', 'archive'].includes(value))
    mode.value = value
}

let controller,
  revision = 0,
  disposed = false
async function load() {
  if (!permitted.value) return
  const version = ++revision
  controller?.abort()
  controller = new AbortController()
  loading.value = true
  error.value = ''
  conflict.value = false
  project.value = null
  try {
    const value = route.params.id
      ? await loadEmployeeProjectDetail(route.params.id, controller.signal)
      : null
    if (disposed || version !== revision) return
    project.value = value
    original.value = editableProject(value || {})
    Object.assign(form, editableProject(value || {}))
    initializeBusinessGroups()
    recent.value = {}
    if (value) {
      const histories = await Promise.all(
        ['situation', 'nextStep', 'coordination'].map(async (field) => [
          field,
          await loadProjectHistory(value.id, field, 0, controller.signal),
        ]),
      )
      if (!disposed && version === revision)
        recent.value = Object.fromEntries(
          histories.map(([field, data]) => [
            field,
            data.items.find(
              (item) => !['baseline', 'initial', 'create'].includes(item.change_type),
            ),
          ]),
        )
    }
  } catch (cause) {
    if (!disposed && version === revision && cause.name !== 'AbortError')
      error.value = cause.message
  } finally {
    if (!disposed && version === revision) loading.value = false
  }
}
async function save() {
  if (!permitted.value || saving.value || loading.value) return
  if (route.params.id && !project.value) return
  if (!String(form.name || '').trim()) {
    error.value = '项目名称必填'
    return
  }
  if (project.value && !dirty.value) {
    success.value = '内容未变化，未产生修改记录。'
    return
  }
  if (!window.confirm('确认保存当前表单中的本次修改？')) return
  saving.value = true
  error.value = ''
  success.value = ''
  conflict.value = false
  try {
    const value = await saveEmployeeProject(
      project.value?.id,
      project.value?.version,
      project.value ? changes.value : editableProject(form),
    )
    if (disposed) return
    project.value = value
    original.value = editableProject(value)
    Object.assign(form, editableProject(value))
    success.value = `保存成功 · 项目 ${value.id} · 版本 ${value.version}`
    saving.value = false
    if (!route.params.id) await router.replace(`/projects/${value.id}/edit`)
    await load()
  } catch (cause) {
    if (!disposed) {
      error.value =
        cause.status === 409
          ? '该项目已被其他人员更新或存在名称/资源冲突，请重新加载并核对修改内容。当前输入已保留。'
          : cause.message
      conflict.value = cause.status === 409
    }
  } finally {
    if (!disposed) saving.value = false
  }
}
function confirmLeave() {
  return (
    !saving.value && (!dirty.value || window.confirm('存在未保存修改，确定离开并放弃当前输入？'))
  )
}
function reload() {
  if (!dirty.value || window.confirm('重新加载将放弃当前未保存输入，是否继续？')) load()
}
function beforeUnload(event) {
  if (saving.value || dirty.value) {
    event.preventDefault()
    event.returnValue = ''
  }
}
onBeforeRouteLeave(confirmLeave)
onBeforeRouteUpdate((to) => to.params.id === route.params.id || confirmLeave())
watch(
  () => route.params.id,
  () => {
    mode.value = route.params.id ? 'progress' : 'archive'
    load()
  },
)
onMounted(() => {
  load()
  window.addEventListener('beforeunload', beforeUnload)
})
onBeforeUnmount(() => {
  disposed = true
  controller?.abort()
  window.removeEventListener('beforeunload', beforeUnload)
})
</script>

<template>
  <main class="project-editor">
    <header>
      <div>
        <p>市场开发 / 项目维护</p>
        <h1>{{ title }}</h1>
      </div>
      <RouterLink to="/projects">返回项目看板</RouterLink>
    </header>
    <section v-if="!permitted" role="alert">
      <h2>没有项目维护权限</h2>
      <p>请联系管理员授予项目维护权限。</p>
    </section>
    <template v-else>
      <section v-if="project" class="editor-context" aria-label="正在维护的项目">
        <h2>{{ project.name }}</h2>
        <dl>
          <div>
            <dt>资源来源</dt>
            <dd>{{ project.resource || '未填写' }}</dd>
          </div>
          <div>
            <dt>当前阶段（已保存）</dt>
            <dd>{{ project.currentStage || '未填写' }}</dd>
          </div>
          <div>
            <dt>项目负责人</dt>
            <dd>{{ project.owner || '未填写' }}</dd>
          </div>
        </dl>
      </section>
      <nav v-if="!isNew" class="editor-modes" aria-label="项目维护模式">
        <button
          type="button"
          :aria-pressed="mode === 'progress'"
          :disabled="saving || loading"
          @click="switchMode('progress')"
        >
          更新项目进展
        </button>
        <button
          type="button"
          :aria-pressed="mode === 'archive'"
          :disabled="saving || loading"
          @click="switchMode('archive')"
        >
          维护项目档案
        </button>
      </nav>
      <p v-if="loading" role="status">正在加载项目资料…</p>
      <form v-else @submit.prevent="save">
        <p v-if="error" role="alert">
          {{ error }}
          <button type="button" :disabled="saving" @click="reload">
            {{ conflict ? '重新加载并核对' : '重新加载' }}
          </button>
        </p>
        <p v-if="success" role="status">{{ success }}</p>
        <p v-if="dirty && !isNew" class="editor-draft" role="status">
          两个模式共享当前草稿；切换不会丢失输入，保存将一并提交所有实际修改。
        </p>
        <fieldset :disabled="saving || (!project && !isNew)">
          <template v-if="mode === 'archive'">
            <section aria-labelledby="editor-basic-title">
              <h2 id="editor-basic-title">项目基本资料</h2>
              <div class="editor-grid">
                <label v-for="field in basicFields" :key="field">
                  <span class="editor-basic-label">
                    {{ labels[field] }}<span v-if="field === 'name'">（必填）</span>
                  </span>
                  <input v-model="form[field]" :required="field === 'name'" maxlength="3000" />
                </label>
              </div>
            </section>
            <section aria-labelledby="editor-attributes-title">
              <h2 id="editor-attributes-title">项目属性</h2>
              <div class="editor-grid">
                <label v-for="field in attributeFields" :key="field"
                  >{{ labels[field] }}<input v-model="form[field]" maxlength="3000"
                /></label>
              </div>
            </section>
            <section aria-labelledby="editor-business-title">
              <h2 id="editor-business-title">项目业务内容</h2>
              <p>可同时维护多种业务。保留原始数值、单位和说明，未知值不必填成零。</p>
              <details
                v-for="group in businessGroups"
                :key="group.id"
                class="editor-business"
                :open="openBusinesses[group.id]"
                @toggle="openBusinesses[group.id] = $event.target.open"
              >
                <summary>{{ group.name }}</summary>
                <div class="editor-grid">
                  <label v-for="field in group.fields" :key="field"
                    >{{ labels[field] }}
                    <input v-if="group.compact" v-model="form[field]" maxlength="50000" />
                    <textarea v-else v-model="form[field]" rows="3" maxlength="50000" />
                  </label>
                </div>
              </details>
            </section>
          </template>
          <section aria-labelledby="editor-stage-title">
            <h2 id="editor-stage-title">实施进度</h2>
            <ProjectNodeEditor
              :model-value="form.stages"
              :baseline="original.stages"
              :current-stage="form.currentStage"
              :disabled="saving || (!project && !isNew)"
              @update:model-value="updateNodes"
            />
            <button v-if="project" type="button" @click="historyDialog.open(project, '')">
              查看节点与项目操作历史
            </button>
          </section>
          <template v-if="mode === 'progress' || isNew">
            <p v-if="isNew" class="editor-initial-note">
              初始实时情况（可选）：与项目资料一次保存，无需先创建空项目。
            </p>
            <section
              v-for="field in ['situation', 'nextStep', 'coordination']"
              :key="field"
              class="editor-narrative"
              :aria-labelledby="`editor-${field}-title`"
            >
              <div class="editor-section-heading">
                <h2 :id="`editor-${field}-title`">{{ labels[field] }}</h2>
                <button v-if="project" type="button" @click="historyDialog.open(project, field)">
                  查看历史
                </button>
              </div>
              <textarea
                v-model="form[field]"
                :aria-labelledby="`editor-${field}-title`"
                :rows="field === 'situation' ? 7 : 4"
                maxlength="50000"
              />
              <small v-if="project">{{
                recent[field]
                  ? `最近修改：${recent[field].employee_name_snapshot}（${recent[field].employee_username_snapshot}）· ${importTime(recent[field].changed_at)}`
                  : '暂无后续修改记录'
              }}</small>
            </section>
          </template>
        </fieldset>
        <footer>
          <span
            >{{ dirty ? '有未保存修改' : '当前内容已同步'
            }}<template v-if="project"> · 版本 {{ project.version }}</template></span
          >
          <RouterLink to="/projects">取消</RouterLink>
          <button type="submit" :disabled="saving || (!project && !isNew)">
            {{
              saving
                ? '保存中…'
                : isNew
                  ? '创建项目'
                  : mode === 'progress'
                    ? '保存本次更新'
                    : '保存档案修改'
            }}
          </button>
        </footer>
      </form>
    </template>
    <ProjectHistoryDialog ref="historyDialog" />
  </main>
</template>

<style scoped>
.project-editor {
  max-width: 1200px;
  margin: auto;
  padding: 32px 24px 64px;
  color: #22292c;
  overflow-wrap: anywhere;
}
.project-editor * {
  box-sizing: border-box;
  min-width: 0;
}
header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  margin-bottom: 24px;
}
h1 {
  font-size: 30px;
  margin: 8px 0;
}
header p,
small {
  color: #6d5b55;
}
a {
  color: #22292c;
  text-underline-offset: 4px;
}
section {
  background: white;
  border: 1px solid #e5e8e8;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
}
h2 {
  font-size: 18px;
  margin: 0 0 18px;
}
section p {
  color: #7e898d;
  font-size: 13px;
  line-height: 1.7;
}
fieldset {
  border: 0;
  margin: 0;
  padding: 0;
}
.editor-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}
.editor-narratives {
  display: grid;
  gap: 24px;
}
label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  line-height: 1.7;
}
.editor-basic-label {
  display: flex;
  align-items: baseline;
  height: 1.7em;
  white-space: nowrap;
}
input,
select,
textarea {
  width: 100%;
  font: inherit;
  color: inherit;
  border: 1px solid #dfe4e4;
  border-radius: 6px;
  padding: 10px 12px;
  background: #fff;
}
textarea {
  resize: vertical;
  min-height: 90px;
  line-height: 1.8;
}
button {
  font: inherit;
  border: 1px solid #dfe4e4;
  border-radius: 6px;
  background: #f5f6f7;
  padding: 9px 14px;
  cursor: pointer;
}
button:disabled {
  opacity: 0.6;
  cursor: default;
}
label button {
  align-self: start;
}
footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: 18px;
  padding: 20px 0;
}
footer span {
  margin-right: auto;
  font-size: 12px;
  color: #6d5b55;
}
button[type='submit'] {
  background: #f7b334;
  border-color: #f7b334;
  font-weight: 700;
}
:focus-visible {
  outline: 3px solid #f7b334;
  outline-offset: 3px;
}
@media (max-width: 650px) {
  .project-editor {
    padding: 22px 14px 40px;
  }
  .editor-grid {
    grid-template-columns: 1fr;
  }
  section {
    padding: 18px;
  }
  header {
    align-items: start;
  }
  h1 {
    font-size: 25px;
  }
}

.editor-context h2 {
  font-size: 19px;
  margin-bottom: 16px;
}
.editor-context dl {
  display: grid;
  grid-template-columns: 1.2fr 1fr 1fr;
  gap: 16px;
  margin: 0;
}
.editor-context dt {
  color: #6d5b55;
  font-size: 12px;
  margin-bottom: 5px;
}
.editor-context dd {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
}
.editor-modes {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 22px;
}
.editor-modes button {
  min-height: 42px;
  padding: 10px 18px;
}
.editor-modes button[aria-pressed='true'] {
  background: #f7b334;
  border-color: #f7b334;
  font-weight: 600;
}
.editor-draft,
.editor-initial-note {
  color: #6d5b55;
  font-size: 12px;
  line-height: 1.8;
  margin: 0 0 18px;
}
.editor-business {
  border-top: 1px solid #e5e8e8;
  padding: 16px 0;
}
summary {
  cursor: pointer;
  font-size: 15px;
  font-weight: 600;
  line-height: 1.8;
}
details[open] > summary {
  margin-bottom: 18px;
}
.editor-section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}
.editor-section-heading h2 {
  margin: 0;
}
.editor-narrative small {
  display: block;
  margin-top: 10px;
  font-size: 12px;
  line-height: 1.8;
}
input,
select,
button {
  min-height: 42px;
}
@media (max-width: 650px) {
  .editor-context dl {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  .editor-modes button {
    flex: 1;
  }
  header > a {
    flex-shrink: 0;
  }
}
</style>
