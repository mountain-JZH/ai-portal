<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'

import DeleteConfirm from './DeleteConfirm.vue'

const props = defineProps({
  nodeDateSelectionMode: {
    type: Object,
    default: () => ({ active: false }),
  },
  nodeDateSelectionResult: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['request-node-date-selection', 'node-date-selection-complete'])

const PROJECT_STORAGE_KEY = 'ai-portal-projects-v1'
const CURRENT_PROJECT_STORAGE_KEY = 'ai-portal-current-project-v1'

const projects = ref([])
const currentProjectId = ref('')
const editorMode = ref('')
const projectName = ref('')
const nodeId = ref('')
const nodeTitle = ref('')
const nodeDate = ref('')
const nodeDone = ref(false)
const deleteTarget = ref('')
const storageMessage = ref('')
const feedbackMessage = ref('')
const deleteConfirm = ref(null)
let idSequence = 0

const todayKey = formatDateKey(new Date())
const currentProject = computed(() =>
  projects.value.find((project) => project.id === currentProjectId.value) || null,
)
const sortedNodes = computed(() =>
  [...(currentProject.value?.nodes || [])].sort(
    (first, second) => first.date.localeCompare(second.date) || first.order - second.order,
  ),
)
const completedNodeCount = computed(
  () => currentProject.value?.nodes.filter((node) => node.done).length || 0,
)
const currentNode = computed(() => sortedNodes.value.find((node) => !node.done) || null)

function formatDateKey(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(
    date.getDate(),
  ).padStart(2, '0')}`
}

function formatShortDate(date) {
  const match = date.match(/^\d{4}-(\d{2})-(\d{2})$/)
  return match ? `${Number(match[1])}/${Number(match[2])}` : date
}

function createId(prefix) {
  idSequence += 1
  return `${prefix}_${Date.now()}_${idSequence}`
}

function sanitizeProjects(value) {
  if (!Array.isArray(value)) return []

  return value.flatMap((project, projectIndex) => {
    if (!project || typeof project !== 'object' || typeof project.name !== 'string') return []
    const name = project.name.trim().slice(0, 40)
    if (!name) return []

    const nodes = Array.isArray(project.nodes)
      ? project.nodes.flatMap((node, nodeIndex) => {
          if (
            !node ||
            typeof node !== 'object' ||
            typeof node.title !== 'string' ||
            !/^\d{4}-\d{2}-\d{2}$/.test(node.date)
          ) {
            return []
          }
          const title = node.title.trim().slice(0, 40)
          if (!title) return []
          return [
            {
              id: String(node.id ?? `node_${projectIndex}_${nodeIndex}`),
              title,
              date: node.date,
              done: Boolean(node.done),
              createdAt: typeof node.createdAt === 'string' ? node.createdAt : '',
              order: Number.isFinite(node.order) ? node.order : nodeIndex,
            },
          ]
        })
      : []

    return [
      {
        id: String(project.id ?? `project_${projectIndex}`),
        name,
        createdAt: typeof project.createdAt === 'string' ? project.createdAt : '',
        nodes,
      },
    ]
  })
}

function persist(nextProjects = projects.value, nextCurrentId = currentProjectId.value) {
  projects.value = nextProjects
  currentProjectId.value = nextCurrentId
  try {
    localStorage.setItem(PROJECT_STORAGE_KEY, JSON.stringify(nextProjects))
    localStorage.setItem(CURRENT_PROJECT_STORAGE_KEY, nextCurrentId)
    storageMessage.value = ''
    return true
  } catch {
    storageMessage.value = '本地保存失败'
    return false
  }
}

function resetEditor() {
  editorMode.value = ''
  projectName.value = ''
  nodeId.value = ''
  nodeTitle.value = ''
  nodeDate.value = ''
  nodeDone.value = false
  deleteTarget.value = ''
  storageMessage.value = ''
}

async function requestDelete(target) {
  deleteTarget.value = target
  await nextTick()
  deleteConfirm.value?.focusCancel()
}

function openProjectCreate() {
  resetEditor()
  editorMode.value = 'create-project'
}

function createProject() {
  const name = projectName.value.trim().slice(0, 40)
  if (!name) return
  const project = {
    id: createId('project'),
    name,
    createdAt: new Date().toISOString(),
    nodes: [],
  }
  persist([...projects.value, project], project.id)
  resetEditor()
}

function switchProject(event) {
  const projectId = event.target.value
  if (!projects.value.some((project) => project.id === projectId)) return
  persist(projects.value, projectId)
}

function openProjectManage() {
  if (!currentProject.value) return
  resetEditor()
  projectName.value = currentProject.value.name
  editorMode.value = 'manage-project'
}

function renameProject() {
  const name = projectName.value.trim().slice(0, 40)
  if (!name || !currentProject.value) return
  persist(
    projects.value.map((project) =>
      project.id === currentProject.value.id ? { ...project, name } : project,
    ),
  )
  resetEditor()
}

function deleteProject() {
  if (!currentProject.value) return
  const remainingProjects = projects.value.filter(
    (project) => project.id !== currentProject.value.id,
  )
  persist(remainingProjects, remainingProjects[0]?.id || '')
  resetEditor()
}

function openNodeCreate() {
  resetEditor()
  editorMode.value = 'create-node'
}

function openNodeEdit(node) {
  resetEditor()
  editorMode.value = 'edit-node'
  nodeId.value = node.id
  nodeTitle.value = node.title
  nodeDate.value = node.date
  nodeDone.value = node.done
}

function requestNodeDateSelection() {
  const title = nodeTitle.value.trim().slice(0, 40)
  if (!title) {
    storageMessage.value = '请先填写节点名称'
    return
  }
  if (!currentProject.value) return

  storageMessage.value = ''
  emit('request-node-date-selection', {
    mode: editorMode.value === 'create-node' ? 'create' : 'edit',
    projectId: currentProject.value.id,
    nodeId: editorMode.value === 'edit-node' ? nodeId.value : null,
    nodeTitle: title,
  })
}

function saveNodeChanges() {
  const title = nodeTitle.value.trim().slice(0, 40)
  if (!currentProject.value || !nodeId.value || !title || !nodeDate.value) return

  const nodes = currentProject.value.nodes.map((node) =>
    node.id === nodeId.value
      ? { ...node, title, date: nodeDate.value, done: nodeDone.value }
      : node,
  )

  persist(
    projects.value.map((project) =>
      project.id === currentProject.value.id ? { ...project, nodes } : project,
    ),
  )
  resetEditor()
  feedbackMessage.value = `节点已更新 · ${title}`
}

function applySelectedDate(result) {
  if (!result?.requestId || !result.date || !/^\d{4}-\d{2}-\d{2}$/.test(result.date)) return
  const project = projects.value.find((item) => item.id === result.projectId)
  const title = typeof result.nodeTitle === 'string' ? result.nodeTitle.trim().slice(0, 40) : ''

  if (!project || !title) {
    storageMessage.value = '目标项目不存在'
    emit('node-date-selection-complete', { success: false })
    return
  }

  if (result.mode === 'create') {
    const nodes = [
      ...project.nodes,
      {
        id: createId('node'),
        title,
        date: result.date,
        done: false,
        createdAt: new Date().toISOString(),
        order: Math.max(-1, ...project.nodes.map((node) => node.order)) + 1,
      },
    ]

    const saved = persist(
      projects.value.map((item) => (item.id === project.id ? { ...item, nodes } : item)),
      project.id,
    )
    resetEditor()
    feedbackMessage.value = saved
      ? `已添加节点 · ${title} · ${formatShortDate(result.date)}`
      : '本地保存失败'
    emit('node-date-selection-complete', { success: saved })
    return
  }

  const targetNode = project.nodes.find((node) => node.id === result.nodeId)
  if (!targetNode || editorMode.value !== 'edit-node' || nodeId.value !== result.nodeId) {
    storageMessage.value = '目标节点不存在'
    emit('node-date-selection-complete', { success: false })
    return
  }

  nodeDate.value = result.date
  storageMessage.value = ''
  emit('node-date-selection-complete', { success: true })
}

function deleteNode() {
  if (!currentProject.value || !nodeId.value) return
  const nodes = currentProject.value.nodes.filter((node) => node.id !== nodeId.value)
  persist(
    projects.value.map((project) =>
      project.id === currentProject.value.id ? { ...project, nodes } : project,
    ),
  )
  resetEditor()
}

function nodeState(node) {
  if (node.done) return { key: 'done', label: '已完成' }
  if (node.date < todayKey) return { key: 'overdue', label: '已逾期' }
  if (node.id === currentNode.value?.id) return { key: 'current', label: '当前节点' }
  return { key: 'upcoming', label: '后续节点' }
}

onMounted(() => {
  try {
    const storedProjects = localStorage.getItem(PROJECT_STORAGE_KEY)
    projects.value = storedProjects ? sanitizeProjects(JSON.parse(storedProjects)) : []
  } catch {
    projects.value = []
  }

  try {
    const storedCurrentId = localStorage.getItem(CURRENT_PROJECT_STORAGE_KEY) || ''
    currentProjectId.value = projects.value.some((project) => project.id === storedCurrentId)
      ? storedCurrentId
      : projects.value[0]?.id || ''
  } catch {
    currentProjectId.value = projects.value[0]?.id || ''
  }
})

watch(
  () => props.nodeDateSelectionResult?.requestId,
  () => applySelectedDate(props.nodeDateSelectionResult),
)
</script>

<template>
  <article class="project-node-manager">
    <header class="manager-header">
      <div>
        <h2>项目节点管理</h2>
        <p>记录项目关键节点与目标日期</p>
      </div>
      <button v-if="currentProject" type="button" @click="openProjectCreate">+ 新建项目</button>
    </header>

    <div v-if="!currentProject" class="project-empty">
      <strong>还没有项目</strong>
      <p>创建一个项目，开始记录关键节点。</p>
      <button type="button" @click="openProjectCreate">+ 新建项目</button>
    </div>

    <div v-else class="project-content">
      <div class="project-toolbar">
        <label>
          <span>当前项目</span>
          <select :value="currentProjectId" aria-label="切换当前项目" @change="switchProject">
            <option v-for="project in projects" :key="project.id" :value="project.id">
              {{ project.name }}
            </option>
          </select>
        </label>
        <button type="button" @click="openProjectManage">管理项目</button>
        <button type="button" @click="openNodeCreate">+ 添加节点</button>
      </div>

      <div class="project-summary">
        <span v-if="currentProject.nodes.length">
          {{ completedNodeCount }} / {{ currentProject.nodes.length }} 已完成
        </span>
        <span v-else>尚未添加节点</span>
        <strong v-if="currentNode">
          当前节点：{{ currentNode.title }} · {{ formatShortDate(currentNode.date) }}
        </strong>
        <strong v-else-if="currentProject.nodes.length">项目节点已全部完成</strong>
      </div>

      <div v-if="sortedNodes.length" class="node-timeline" aria-label="项目节点时间轴">
        <div
          class="timeline-line"
          :style="{ width: `${Math.max(0, sortedNodes.length - 1) * 130}px` }"
          aria-hidden="true"
        ></div>
        <button
          v-for="node in sortedNodes"
          :key="node.id"
          class="timeline-node"
          :class="`state-${nodeState(node).key}`"
          type="button"
          :aria-label="`${node.title}，${node.date}，${nodeState(node).label}`"
          @click="openNodeEdit(node)"
        >
          <span class="node-marker" aria-hidden="true">
            {{ node.done ? '✓' : '' }}
          </span>
          <strong>{{ node.title }}</strong>
          <time :datetime="node.date">{{ formatShortDate(node.date) }}</time>
          <small>{{ nodeState(node).label }}</small>
        </button>
      </div>
      <button v-else class="node-empty" type="button" @click="openNodeCreate">
        尚未添加节点，点击添加
      </button>
      <p v-if="feedbackMessage" class="manager-feedback" aria-live="polite">
        {{ feedbackMessage }}
      </p>
    </div>

    <section
      v-if="editorMode"
      class="editor-panel"
      :class="{
        'delete-confirming': deleteTarget,
        'compact-node-create': editorMode === 'create-node',
      }"
      aria-label="项目节点编辑"
    >
      <template v-if="editorMode === 'create-project' || editorMode === 'manage-project'">
        <h3>{{ editorMode === 'create-project' ? '新建项目' : '管理项目' }}</h3>
        <label class="field-label">
          项目名称
          <input v-model="projectName" type="text" maxlength="40" placeholder="输入项目名称" />
        </label>
        <div class="editor-action-zone">
          <DeleteConfirm
            v-if="deleteTarget === 'project'"
            ref="deleteConfirm"
            class="manager-delete-confirm"
            :message="`删除项目“${currentProject?.name || ''}”？`"
            detail="项目中的节点也会一并删除"
            @cancel="deleteTarget = ''"
            @confirm="deleteProject"
          />
          <div v-else class="editor-actions unified-actions">
            <button
              v-if="editorMode === 'manage-project'"
              class="danger-link"
              type="button"
              @click="requestDelete('project')"
            >
              删除
            </button>
            <button type="button" @click="resetEditor">取消</button>
            <button
              class="primary"
              type="button"
              :disabled="!projectName.trim()"
              @click="editorMode === 'create-project' ? createProject() : renameProject()"
            >
              {{ editorMode === 'create-project' ? '新增' : '保存' }}
            </button>
          </div>
        </div>
      </template>

      <template v-else-if="editorMode === 'create-node'">
        <h3>新增节点</h3>
        <div class="node-create-row">
          <input
            v-model="nodeTitle"
            type="text"
            maxlength="40"
            aria-label="节点名称"
            placeholder="输入节点名称"
            :disabled="props.nodeDateSelectionMode.active"
            @keydown.enter="requestNodeDateSelection"
          />
          <button
            class="primary"
            type="button"
            :disabled="!nodeTitle.trim() || props.nodeDateSelectionMode.active"
            @click="requestNodeDateSelection"
          >
            选日期
          </button>
          <button
            class="compact-cancel"
            type="button"
            :disabled="props.nodeDateSelectionMode.active"
            @click="resetEditor"
          >
            取消
          </button>
        </div>
      </template>

      <template v-else>
        <h3>编辑节点</h3>
        <label class="field-label">
          节点名称
          <input
            v-model="nodeTitle"
            type="text"
            maxlength="40"
            placeholder="输入节点名称"
            :disabled="props.nodeDateSelectionMode.active"
          />
        </label>
        <div v-if="editorMode === 'edit-node'" class="node-date-row">
          <span>目标日期</span>
          <strong>{{ nodeDate ? formatShortDate(nodeDate) : '尚未选择' }}</strong>
          <button
            type="button"
            :disabled="props.nodeDateSelectionMode.active || deleteTarget === 'node'"
            @click="requestNodeDateSelection"
          >
            重新选择
          </button>
        </div>
        <label v-if="editorMode === 'edit-node'" class="done-field">
          <input
            v-model="nodeDone"
            type="checkbox"
            :aria-label="nodeDone ? '已完成' : '未完成'"
            :disabled="props.nodeDateSelectionMode.active"
          />
          <span class="done-control" aria-hidden="true">
            <span>{{ nodeDone ? '✓' : '○' }}</span>
            {{ nodeDone ? '已完成' : '未完成' }}
          </span>
        </label>
        <div class="editor-action-zone">
          <DeleteConfirm
            v-if="deleteTarget === 'node'"
            ref="deleteConfirm"
            class="manager-delete-confirm"
            :message="`删除节点“${nodeTitle}”？`"
            @cancel="deleteTarget = ''"
            @confirm="deleteNode"
          />
          <div v-else class="editor-actions unified-actions">
            <button
              class="danger-link"
              type="button"
              :disabled="props.nodeDateSelectionMode.active"
              @click="requestDelete('node')"
            >
              删除
            </button>
            <button
              type="button"
              :disabled="props.nodeDateSelectionMode.active"
              @click="resetEditor"
            >
              取消
            </button>
            <button
              class="primary"
              type="button"
              :disabled="!nodeTitle.trim() || props.nodeDateSelectionMode.active"
              @click="saveNodeChanges"
            >
              保存
            </button>
          </div>
        </div>
      </template>
      <p class="storage-message" aria-live="polite">{{ storageMessage }}</p>
    </section>
  </article>
</template>

<style scoped>
.project-node-manager {
  position: relative;
  min-width: 0;
  height: 270px;
  padding: 18px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: var(--color-surface);
  box-shadow: var(--shadow-soft);
}

.manager-header,
.project-toolbar,
.project-summary,
.editor-actions {
  display: flex;
  align-items: center;
}

.manager-header { justify-content: space-between; gap: 14px; }
.manager-header h2 { margin: 0; color: var(--color-text); font-size: 19px; line-height: 1.35; }
.manager-header p { margin: 5px 0 0; color: var(--color-muted); font-size: 11px; }

button,
select,
input { font: inherit; }

.manager-header > button,
.project-toolbar > button,
.project-empty button,
.editor-actions button {
  height: 28px;
  padding: 0 9px;
  border: 1px solid var(--color-border);
  border-radius: 7px;
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: 10px;
  cursor: pointer;
}

.manager-header > button,
.project-toolbar > button:last-child,
.editor-actions .primary {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: #fff;
}

.project-empty {
  height: 165px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--color-muted);
  text-align: center;
}
.project-empty strong { color: var(--color-text-secondary); font-size: 14px; }
.project-empty p { margin: 6px 0 12px; font-size: 11px; }

.project-content { min-width: 0; margin-top: 12px; }
.project-toolbar { min-width: 0; gap: 7px; }
.project-toolbar label { min-width: 0; display: flex; flex: 1; align-items: center; gap: 7px; }
.project-toolbar label span { flex-shrink: 0; color: var(--color-muted); font-size: 10px; }
.project-toolbar select {
  min-width: 0;
  height: 28px;
  flex: 1;
  padding: 0 7px;
  border: 1px solid var(--color-border);
  border-radius: 7px;
  background: var(--color-surface-soft);
  color: var(--color-text-secondary);
  font-size: 10px;
}

.project-summary { min-width: 0; margin-top: 9px; justify-content: space-between; gap: 10px; }
.project-summary span { flex-shrink: 0; color: var(--color-muted); font-size: 10px; }
.project-summary strong {
  min-width: 0;
  overflow: hidden;
  color: var(--color-primary);
  font-size: 10px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-timeline {
  position: relative;
  min-width: 0;
  height: 124px;
  margin-top: 8px;
  padding: 9px 4px 4px;
  display: flex;
  gap: 0;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-color: var(--color-border-strong) transparent;
  scrollbar-width: thin;
}

.timeline-line {
  position: absolute;
  top: 21px;
  right: auto;
  left: 65px;
  height: 1px;
  background: var(--color-border-strong);
}

.timeline-node {
  position: relative;
  z-index: 1;
  min-width: 130px;
  width: 130px;
  padding: 0 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  border: 0;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
}

.node-marker {
  width: 25px;
  height: 25px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--color-border-strong);
  border-radius: 50%;
  background: var(--color-surface);
  color: #fff;
  font-size: 11px;
}
.timeline-node strong { max-width: 100%; margin-top: 7px; overflow: hidden; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.timeline-node time { margin-top: 2px; color: var(--color-muted); font-size: 9px; }
.timeline-node small { margin-top: 2px; color: var(--color-muted); font-size: 9px; }
.timeline-node.state-done .node-marker { border-color: var(--color-primary); background: var(--color-primary); }
.timeline-node.state-current .node-marker { border-color: var(--color-primary); background: var(--color-primary); box-shadow: 0 0 0 4px rgba(91, 91, 214, 0.13); }
.timeline-node.state-overdue .node-marker { border-color: #d77a80; }
.timeline-node.state-overdue small { color: #bd5961; }

.node-empty {
  width: 100%;
  height: 112px;
  margin-top: 8px;
  border: 1px dashed var(--color-border-strong);
  border-radius: 9px;
  background: var(--color-surface-soft);
  color: var(--color-muted);
  font-size: 11px;
  cursor: pointer;
}

.editor-panel {
  position: absolute;
  inset: 0;
  z-index: 4;
  padding: 18px;
  overflow-y: auto;
  border-radius: 12px;
  background: var(--color-surface);
}
.editor-panel h3 { margin: 0 0 13px; color: var(--color-text); font-size: 16px; }
.field-label { display: grid; gap: 5px; color: var(--color-muted); font-size: 10px; }
.field-label input {
  min-width: 0;
  height: 31px;
  padding: 0 9px;
  border: 1px solid var(--color-border);
  border-radius: 7px;
  color: var(--color-text-secondary);
}
.node-create-row {
  min-width: 0;
  display: grid;
  align-items: center;
  gap: 8px;
  grid-template-columns: minmax(0, 1fr) auto auto;
}
.node-create-row input {
  min-width: 0;
  height: 34px;
  padding: 0 10px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  color: var(--color-text-secondary);
}
.node-create-row button {
  height: 34px;
  padding: 0 12px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
  color: var(--color-text-secondary);
  font-size: 11px;
  cursor: pointer;
}
.node-create-row .primary {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: #fff;
}
.node-create-row .compact-cancel {
  padding-inline: 6px;
  border-color: transparent;
}
.node-create-row button:disabled { cursor: default; opacity: 0.45; }
.node-date-row {
  min-width: 0;
  margin-top: 9px;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-muted);
  font-size: 10px;
}
.node-date-row strong { color: var(--color-text-secondary); font-size: 11px; }
.node-date-row button {
  height: 27px;
  margin-left: auto;
  padding: 0 8px;
  border: 1px solid var(--color-border);
  border-radius: 7px;
  background: var(--color-surface);
  color: var(--color-primary);
  font-size: 10px;
  cursor: pointer;
}
.done-field {
  position: relative;
  width: fit-content;
  margin-top: 11px;
  display: inline-flex;
  cursor: pointer;
}
.done-field input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
}
.done-control {
  min-height: 30px;
  padding: 0 10px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface-soft);
  color: var(--color-text-secondary);
  font-size: 11px;
}
.done-control > span { color: var(--color-primary); font-size: 14px; }
.done-field input:focus-visible + .done-control {
  box-shadow: 0 0 0 3px rgba(91, 91, 214, 0.15);
}
.done-field input:disabled + .done-control { cursor: default; opacity: 0.55; }
.editor-action-zone {
  position: relative;
  min-height: 34px;
  margin-top: 16px;
}
.editor-actions {
  margin-top: 0;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 7px;
}
.unified-actions button {
  min-width: 64px;
  height: 34px;
  padding: 0 12px;
  border-radius: 8px;
}
.editor-actions .danger-link {
  border-color: rgba(189, 89, 97, 0.24);
  background: #fffafa;
  color: #bd5961;
}
.editor-actions button:disabled { cursor: default; opacity: 0.45; }
.manager-delete-confirm {
  position: absolute;
  top: 0;
  right: 0;
  z-index: 2;
  width: min(100%, 430px);
}
.editor-panel.delete-confirming > :not(.editor-action-zone) {
  pointer-events: none;
  opacity: 0.58;
  filter: blur(2px);
}
.manager-feedback {
  position: absolute;
  right: 18px;
  bottom: 7px;
  left: 18px;
  margin: 0;
  overflow: hidden;
  color: var(--color-primary);
  font-size: 9px;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.storage-message { min-height: 12px; margin: 5px 0 0; color: var(--color-muted); font-size: 9px; text-align: right; }

button:focus-visible,
select:focus-visible,
input:focus-visible { outline: none; box-shadow: 0 0 0 3px rgba(91, 91, 214, 0.15); }

@media (max-width: 600px) {
  .project-node-manager { padding: 15px; }
  .manager-header { align-items: flex-start; }
  .manager-header > button { flex-shrink: 0; }
  .project-toolbar { flex-wrap: wrap; }
  .project-toolbar label { flex-basis: 100%; }
  .project-summary { align-items: flex-start; flex-direction: column; gap: 3px; }
  .node-timeline { height: 100px; }
  .node-date-row { flex-wrap: wrap; }
}
</style>
