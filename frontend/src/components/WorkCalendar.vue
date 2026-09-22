<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

import {
  notifyTodosUpdated,
  readTodoStore,
  sanitizeTodoStore,
  TODO_STORAGE_KEY,
  TODO_UPDATED_EVENT,
} from '../utils/todoStorage'
import {
  QUADRANTS,
  QUADRANT_UPDATED_EVENT,
  readQuadrantStore,
  sanitizeQuadrantStore,
  writeQuadrantStore,
} from '../utils/quadrantStorage'
import DeleteConfirm from './DeleteConfirm.vue'
import QuadrantSymbol from './QuadrantSymbol.vue'
import TodoStatusIcon from './TodoStatusIcon.vue'

const props = defineProps({
  plannerExpanded: {
    type: Boolean,
    default: false,
  },
  isTaskDragging: {
    type: Boolean,
    default: false,
  },
  draggingTodoId: {
    type: String,
    default: '',
  },
  isPlanningModalOpen: {
    type: Boolean,
    default: false,
  },
  nodeDateSelectionMode: {
    type: Object,
    default: () => ({ active: false }),
  },
})

const emit = defineEmits([
  'selected-date-change',
  'toggle-planner',
  'task-drag-start',
  'task-drag-end',
  'node-date-selected',
  'cancel-node-date-selection',
])

const MARKER_STORAGE_KEY = 'ai-portal-calendar-v1'
const WEEKDAYS = ['一', '二', '三', '四', '五', '六', '日']
const TODO_WEEKDAYS = ['日', '一', '二', '三', '四', '五', '六']
const MARKER_COLORS = ['green', 'yellow', 'red']
const MARKER_COLOR_LABELS = {
  green: '绿色标记',
  yellow: '黄色标记',
  red: '红色标记',
}

const now = new Date()
const today = {
  year: now.getFullYear(),
  month: now.getMonth(),
  day: now.getDate(),
}

const displayYear = ref(today.year)
const displayMonth = ref(today.month)
const selectedDay = ref(today.day)
const selectedKey = ref(formatDateKey(today.year, today.month, today.day))
const activeView = ref('calendar')
const markerEntries = ref({})
const markerText = ref('')
const markerColor = ref('green')
const todosByDate = ref({})
const quadrantMappings = ref({})
const todoDropActive = ref(false)
const todoInput = ref('')
const storageMessage = ref('')
const pendingDeleteId = ref(null)
const todoDeleteConfirm = ref(null)
const calendarRoot = ref(null)
let todoSequence = 0
let todoDropDepth = 0

const monthLabel = computed(() => `${displayYear.value}年${displayMonth.value + 1}月`)

const selectedTodoDateLabel = computed(() => {
  const weekday = new Date(
    displayYear.value,
    displayMonth.value,
    selectedDay.value,
  ).getDay()
  return `${displayMonth.value + 1}月${selectedDay.value}日 · 星期${TODO_WEEKDAYS[weekday]}`
})

const calendarCells = computed(() => {
  const firstDay = new Date(displayYear.value, displayMonth.value, 1).getDay()
  const leadingBlanks = (firstDay + 6) % 7
  const daysInMonth = new Date(displayYear.value, displayMonth.value + 1, 0).getDate()

  return Array.from({ length: 42 }, (_, index) => {
    const day = index - leadingBlanks + 1
    return day >= 1 && day <= daysInMonth ? day : null
  })
})

const currentTodos = computed(() => todosByDate.value[selectedKey.value] || [])
const completedTodoCount = computed(
  () => currentTodos.value.filter((todo) => todo.done).length,
)
const isConfirming = computed(() => pendingDeleteId.value !== null)

function formatDateKey(year, month, day) {
  return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

function getMarker(day) {
  if (!day) return null
  return markerEntries.value[formatDateKey(displayYear.value, displayMonth.value, day)] || null
}

function getMarkerColor(day) {
  const color = getMarker(day)?.color
  return MARKER_COLORS.includes(color) ? color : ''
}

function isToday(day) {
  return (
    day === today.day &&
    displayYear.value === today.year &&
    displayMonth.value === today.month
  )
}

function isSelected(day) {
  return day !== null && day === selectedDay.value
}

function dateAriaLabel(day) {
  return `${displayYear.value}年${displayMonth.value + 1}月${day}日`
}

function syncMarkerEditor() {
  const marker = markerEntries.value[selectedKey.value]
  markerText.value = marker?.note || ''
  markerColor.value = MARKER_COLORS.includes(marker?.color) ? marker.color : 'green'
}

function selectDate(day) {
  if (!day) return
  selectedDay.value = day
  selectedKey.value = formatDateKey(displayYear.value, displayMonth.value, day)
  storageMessage.value = ''
  pendingDeleteId.value = null
  syncMarkerEditor()
  emit('selected-date-change', selectedKey.value)
}

function handleDateClick(day) {
  selectDate(day)
  if (props.nodeDateSelectionMode.active) {
    emit('node-date-selected', selectedKey.value)
  }
}

function cancelNodeDateSelection() {
  emit('cancel-node-date-selection')
}

function handleEscape() {
  if (props.nodeDateSelectionMode.active) cancelNodeDateSelection()
  else cancelTodoDelete()
}

async function ensureCalendarVisible() {
  await nextTick()
  const bounds = calendarRoot.value?.getBoundingClientRect()
  if (!bounds || (bounds.top >= 0 && bounds.bottom <= window.innerHeight)) return
  calendarRoot.value.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

function changeMonth(offset) {
  const target = new Date(displayYear.value, displayMonth.value + offset, 1)
  const targetYear = target.getFullYear()
  const targetMonth = target.getMonth()
  const daysInTargetMonth = new Date(targetYear, targetMonth + 1, 0).getDate()

  displayYear.value = targetYear
  displayMonth.value = targetMonth
  selectDate(Math.min(selectedDay.value, daysInTargetMonth))
}

function goToToday() {
  displayYear.value = today.year
  displayMonth.value = today.month
  selectDate(today.day)
}

function switchView(view) {
  activeView.value = view
  storageMessage.value = ''
  if (view === 'calendar') pendingDeleteId.value = null
}

function sanitizeMarkerEntries(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {}

  return Object.fromEntries(
    Object.entries(value).flatMap(([key, marker]) => {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(key) || !marker || typeof marker !== 'object') {
        return []
      }

      const note = typeof marker.note === 'string' ? marker.note.trim().slice(0, 30) : ''
      const color = MARKER_COLORS.includes(marker.color) ? marker.color : ''

      return note || color ? [[key, { color, note }]] : []
    }),
  )
}

function persist(storageKey, value) {
  let saved = true

  try {
    localStorage.setItem(storageKey, JSON.stringify(value))
    storageMessage.value = '已保存到本机'
  } catch {
    storageMessage.value = '本地保存失败'
    saved = false
  }

  if (storageKey === TODO_STORAGE_KEY) notifyTodosUpdated(value)
  return saved
}

function handleTodosUpdated(event) {
  todosByDate.value = event.detail?.todos
    ? sanitizeTodoStore(event.detail.todos)
    : readTodoStore()
  refreshQuadrantMappings()
}

function refreshQuadrantMappings() {
  quadrantMappings.value = readQuadrantStore(todosByDate.value)
}

function handleQuadrantsUpdated(event) {
  quadrantMappings.value = event.detail?.mappings
    ? sanitizeQuadrantStore(event.detail.mappings, todosByDate.value)
    : readQuadrantStore(todosByDate.value)
}

function getTodoQuadrant(todoId) {
  return quadrantMappings.value[selectedKey.value]?.[todoId] || ''
}

function getQuadrantDefinition(todoId) {
  const quadrantKey = getTodoQuadrant(todoId)
  return QUADRANTS.find((quadrant) => quadrant.key === quadrantKey)
}

function startTodoDrag(event, todoId) {
  if (isConfirming.value) {
    event.preventDefault()
    return
  }

  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', String(todoId))
  emit('task-drag-start', String(todoId))
}

function endTodoDrag() {
  todoDropDepth = 0
  todoDropActive.value = false
  emit('task-drag-end')
}

function enterTodoDropZone(event) {
  if (!props.isTaskDragging) return
  event.preventDefault()
  todoDropDepth += 1
  todoDropActive.value = true
}

function leaveTodoDropZone() {
  todoDropDepth = Math.max(0, todoDropDepth - 1)
  if (!todoDropDepth) todoDropActive.value = false
}

function dropIntoTodoList(event) {
  event.preventDefault()
  const todoId = props.draggingTodoId || event.dataTransfer.getData('text/plain')
  const currentDateMapping = { ...quadrantMappings.value[selectedKey.value] }

  if (todoId && currentDateMapping[todoId]) {
    delete currentDateMapping[todoId]
    const nextMappings = { ...quadrantMappings.value }
    if (Object.keys(currentDateMapping).length) nextMappings[selectedKey.value] = currentDateMapping
    else delete nextMappings[selectedKey.value]

    quadrantMappings.value = nextMappings
    storageMessage.value = writeQuadrantStore(nextMappings) ? '已移出四象限' : '本地保存失败'
  }

  endTodoDrag()
}

function saveMarker() {
  if (!selectedKey.value) return

  const note = markerText.value.trim().slice(0, 30)
  const color = MARKER_COLORS.includes(markerColor.value) ? markerColor.value : 'green'
  markerEntries.value = {
    ...markerEntries.value,
    [selectedKey.value]: { color, note },
  }
  markerText.value = note
  persist(MARKER_STORAGE_KEY, markerEntries.value)
}

function clearMarker() {
  if (!selectedKey.value) return

  const nextEntries = { ...markerEntries.value }
  delete nextEntries[selectedKey.value]
  markerEntries.value = nextEntries
  markerText.value = ''
  markerColor.value = 'green'
  persist(MARKER_STORAGE_KEY, markerEntries.value)
}

function addTodo() {
  const text = todoInput.value.trim().slice(0, 60)
  if (!selectedKey.value || !text) return

  const nextTodos = [
    ...currentTodos.value,
    {
      id: `${Date.now()}-${++todoSequence}`,
      text,
      done: false,
    },
  ]
  todosByDate.value = { ...todosByDate.value, [selectedKey.value]: nextTodos }
  todoInput.value = ''
  pendingDeleteId.value = null
  persist(TODO_STORAGE_KEY, todosByDate.value)
}

function toggleTodo(todoId) {
  const nextTodos = currentTodos.value.map((todo) =>
    todo.id === todoId ? { ...todo, done: !todo.done } : todo,
  )
  todosByDate.value = { ...todosByDate.value, [selectedKey.value]: nextTodos }
  persist(TODO_STORAGE_KEY, todosByDate.value)
}

async function requestTodoDelete(todoId) {
  pendingDeleteId.value = todoId
  await nextTick()
  todoDeleteConfirm.value?.focusCancel()
}

function cancelTodoDelete() {
  pendingDeleteId.value = null
}

function setTodoDeleteConfirm(instance) {
  todoDeleteConfirm.value = instance
}

function confirmTodoDelete(todoId) {
  const nextTodosForDate = currentTodos.value.filter((todo) => todo.id !== todoId)
  const nextTodos = { ...todosByDate.value }

  if (nextTodosForDate.length) nextTodos[selectedKey.value] = nextTodosForDate
  else delete nextTodos[selectedKey.value]

  todosByDate.value = nextTodos
  pendingDeleteId.value = null
  persist(TODO_STORAGE_KEY, todosByDate.value)
}

onMounted(() => {
  try {
    const storedMarkers = localStorage.getItem(MARKER_STORAGE_KEY)
    markerEntries.value = storedMarkers ? sanitizeMarkerEntries(JSON.parse(storedMarkers)) : {}
  } catch {
    markerEntries.value = {}
  }

  todosByDate.value = readTodoStore()
  refreshQuadrantMappings()
  window.addEventListener(TODO_UPDATED_EVENT, handleTodosUpdated)
  window.addEventListener(QUADRANT_UPDATED_EVENT, handleQuadrantsUpdated)

  syncMarkerEditor()
  emit('selected-date-change', selectedKey.value)
})

watch(
  () => props.nodeDateSelectionMode.active,
  (active) => {
    if (!active) return
    activeView.value = 'calendar'
    pendingDeleteId.value = null
    storageMessage.value = ''
    ensureCalendarVisible()
  },
)

onUnmounted(() => {
  window.removeEventListener(TODO_UPDATED_EVENT, handleTodosUpdated)
  window.removeEventListener(QUADRANT_UPDATED_EVENT, handleQuadrantsUpdated)
})
</script>

<template>
  <section
    ref="calendarRoot"
    class="work-calendar"
    :class="{
      'todo-confirming': isConfirming,
      'task-dragging': props.isTaskDragging,
      'planning-modal-open': props.isPlanningModalOpen,
      'node-date-selection-mode': props.nodeDateSelectionMode.active,
    }"
    aria-label="工作日历"
    @keydown.esc.stop="handleEscape"
  >
    <button
      class="planner-toggle"
      type="button"
      :aria-expanded="props.plannerExpanded"
      aria-controls="planner-expand-panel"
      :aria-label="props.plannerExpanded ? '收起工作计划' : '展开工作计划'"
      :title="props.plannerExpanded ? '收起工作计划' : '展开工作计划'"
      :disabled="props.nodeDateSelectionMode.active"
      @click="emit('toggle-planner')"
    >
      <span aria-hidden="true">{{ props.plannerExpanded ? '−' : '+' }}</span>
    </button>

    <header class="work-card-header">
      <div v-if="props.nodeDateSelectionMode.active" class="node-date-selection-heading">
        <strong :title="`为「${props.nodeDateSelectionMode.nodeTitle}」选择日期`">
          为「{{ props.nodeDateSelectionMode.nodeTitle }}」选择日期
        </strong>
        <button type="button" @click="cancelNodeDateSelection">取消</button>
      </div>
      <div v-else class="view-tabs" role="tablist" aria-label="工作卡片视图">
        <button
          id="calendar-tab"
          class="view-tab"
          :class="{ active: activeView === 'calendar' }"
          type="button"
          role="tab"
          :aria-selected="activeView === 'calendar'"
          aria-controls="calendar-panel"
          :disabled="isConfirming"
          @click="switchView('calendar')"
        >
          我的日历
        </button>
        <button
          id="todo-tab"
          class="view-tab"
          :class="{ active: activeView === 'todo' }"
          type="button"
          role="tab"
          :aria-selected="activeView === 'todo'"
          aria-controls="todo-panel"
          :disabled="isConfirming || props.nodeDateSelectionMode.active"
          @click="switchView('todo')"
        >
          当日待办
        </button>
      </div>
    </header>

    <div class="work-card-content">
      <div
        id="calendar-panel"
        class="work-panel calendar-view"
        :class="{
          'is-active': activeView === 'calendar',
          'is-inactive': activeView !== 'calendar',
        }"
        role="tabpanel"
        :aria-hidden="activeView !== 'calendar'"
        :inert="activeView !== 'calendar'"
        :aria-label="props.nodeDateSelectionMode.active ? '选择节点日期' : undefined"
        :aria-labelledby="props.nodeDateSelectionMode.active ? undefined : 'calendar-tab'"
      >
        <div class="month-toolbar">
          <button class="today-button" type="button" @click="goToToday">今天</button>
          <div class="month-navigation">
            <button type="button" aria-label="上一个月" @click="changeMonth(-1)">‹</button>
            <strong aria-live="polite">{{ monthLabel }}</strong>
            <button type="button" aria-label="下一个月" @click="changeMonth(1)">›</button>
          </div>
        </div>

        <div class="calendar-main">
          <div class="weekdays" aria-hidden="true">
            <span v-for="weekday in WEEKDAYS" :key="weekday">{{ weekday }}</span>
          </div>

          <div class="date-grid">
            <template
              v-for="(day, index) in calendarCells"
              :key="`${displayYear}-${displayMonth}-${index}`"
            >
              <span v-if="day === null" class="date-placeholder" aria-hidden="true"></span>
              <button
                v-else
                class="date-button"
                :class="[
                  { today: isToday(day), selected: isSelected(day) },
                  getMarkerColor(day) ? `marked marker-${getMarkerColor(day)}` : '',
                ]"
                type="button"
                :aria-label="dateAriaLabel(day)"
                :aria-pressed="isSelected(day)"
                @click="handleDateClick(day)"
              >
                <span class="date-number">{{ day }}</span>
              </button>
            </template>
          </div>
        </div>

        <div
          class="marker-editor"
          :class="{ 'selection-hidden': props.nodeDateSelectionMode.active }"
          :aria-hidden="props.nodeDateSelectionMode.active"
        >
          <div class="editor-heading">
            <strong>
              日期标记
              <span>· {{ displayMonth + 1 }}月{{ selectedDay }}日</span>
            </strong>
          </div>

          <div class="marker-controls">
            <input
              v-model="markerText"
              type="text"
              maxlength="30"
              aria-label="简短日期标记"
              placeholder="添加简短标记"
              @keydown.enter="saveMarker"
            />

            <fieldset class="color-options">
              <legend class="sr-only">选择标记颜色</legend>
              <label v-for="color in MARKER_COLORS" :key="color">
                <input
                  v-model="markerColor"
                  type="radio"
                  name="marker-color"
                  :value="color"
                  :aria-label="MARKER_COLOR_LABELS[color]"
                  :title="MARKER_COLOR_LABELS[color]"
                />
                <span :class="`color-${color}`" aria-hidden="true"></span>
              </label>
            </fieldset>

            <button class="primary-action" type="button" @click="saveMarker">保存</button>
            <button class="secondary-action" type="button" @click="clearMarker">清除</button>
          </div>
          <p class="storage-message" aria-live="polite">{{ storageMessage }}</p>
        </div>
      </div>

      <div
        id="todo-panel"
        class="work-panel todo-view"
        :class="{
          'is-active': activeView === 'todo',
          'is-inactive': activeView !== 'todo',
          'is-confirming': isConfirming,
        }"
        role="tabpanel"
        :aria-hidden="activeView !== 'todo'"
        :inert="activeView !== 'todo'"
        aria-labelledby="todo-tab"
      >
        <div class="todo-heading">
          <strong>{{ selectedTodoDateLabel }}</strong>
          <span class="todo-status" aria-live="polite">{{ storageMessage }}</span>
        </div>

        <div class="todo-add-row">
          <input
            v-model="todoInput"
            type="text"
            maxlength="60"
            aria-label="添加一项待办"
            placeholder="添加一项待办"
            :disabled="isConfirming"
            @keydown.enter.prevent="addTodo"
          />
          <button type="button" :disabled="isConfirming" @click="addTodo">新增</button>
        </div>

        <template v-if="currentTodos.length">
          <div
            class="todo-list"
            :class="{ 'drop-active': todoDropActive }"
            role="list"
            @dragenter="enterTodoDropZone"
            @dragover.prevent
            @dragleave="leaveTodoDropZone"
            @drop="dropIntoTodoList"
          >
            <div
              v-for="todo in currentTodos"
              :key="todo.id"
              class="todo-item"
              :class="{
                done: todo.done,
                confirming: pendingDeleteId === todo.id,
                dragging: props.draggingTodoId === todo.id,
              }"
              role="listitem"
            >
              <label class="todo-check">
                <input
                  type="checkbox"
                  :checked="todo.done"
                  :disabled="isConfirming"
                  @change="toggleTodo(todo.id)"
                />
                <TodoStatusIcon :done="todo.done" />
                <span class="sr-only">切换完成状态</span>
              </label>
              <div class="todo-content">
                <span class="todo-text">{{ todo.text }}</span>
                <DeleteConfirm
                  v-if="pendingDeleteId === todo.id"
                  :ref="setTodoDeleteConfirm"
                  class="todo-delete-confirm"
                  message="删除这项待办？"
                  @cancel="cancelTodoDelete"
                  @confirm="confirmTodoDelete(todo.id)"
                />
              </div>
              <div class="todo-drag-control">
                <span
                  v-if="getQuadrantDefinition(todo.id)"
                  class="todo-quadrant-symbol"
                  role="img"
                  :aria-label="`已分类：${getQuadrantDefinition(todo.id).label}`"
                  :style="{
                    '--quadrant-symbol-color': getQuadrantDefinition(todo.id).color,
                  }"
                >
                  <QuadrantSymbol :type="getQuadrantDefinition(todo.id).symbolType" size="sm" />
                </span>
                <button
                  class="todo-drag-handle"
                  type="button"
                  draggable="true"
                  title="拖动到四象限"
                  aria-label="拖动任务进行优先级分类"
                  :disabled="isConfirming"
                  @dragstart="startTodoDrag($event, todo.id)"
                  @dragend="endTodoDrag"
                >
                  <span aria-hidden="true">⠿</span>
                </button>
              </div>
              <button
                class="todo-delete"
                :class="{ hidden: pendingDeleteId === todo.id }"
                type="button"
                :aria-label="`删除待办：${todo.text}`"
                :aria-hidden="pendingDeleteId === todo.id"
                :disabled="isConfirming"
                :tabindex="pendingDeleteId === todo.id ? -1 : 0"
                @click="requestTodoDelete(todo.id)"
              >
                ×
              </button>
            </div>
          </div>
        </template>

        <div
          v-else
          class="todo-empty"
          :class="{ 'drop-active': todoDropActive }"
          @dragenter="enterTodoDropZone"
          @dragover.prevent
          @dragleave="leaveTodoDropZone"
          @drop="dropIntoTodoList"
        >
          <strong>暂无待办事项</strong>
          <span>添加一项今天需要完成的事情</span>
          <span v-if="todoDropActive" class="todo-drop-hint">移出四象限</span>
        </div>

        <p class="todo-progress">已完成 {{ completedTodoCount }} / {{ currentTodos.length }}</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.work-calendar {
  position: relative;

  width: 100%;
  min-width: 0;
  min-height: 0;
  height: auto;
  padding: 18px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: var(--shadow-soft);
}

.work-card-header {
  min-width: 0;
  min-height: 36px;
  padding-right: 52px;
  padding-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  border-bottom: 1px solid var(--color-border);
}

.planner-toggle {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 6;

  width: 34px;
  height: 34px;
  padding: 0;

  display: inline-flex;
  align-items: center;
  justify-content: center;

  border: 1px solid rgba(35, 145, 88, 0.28);
  border-radius: 50%;
  background: #35a86b;
  box-shadow: 0 5px 14px rgba(41, 142, 86, 0.2);

  color: #fff;
  font-size: 22px;
  font-weight: 500;
  line-height: 1;

  cursor: pointer;
  transition: background-color var(--transition-fast), box-shadow var(--transition-fast),
    transform var(--transition-fast);
}

.planner-toggle:hover {
  background: #3db877;
  box-shadow: 0 7px 17px rgba(41, 142, 86, 0.24);
  transform: translateY(-1px);
}

.planner-toggle:focus {
  outline: none;
}

.planner-toggle:focus-visible {
  box-shadow: 0 0 0 3px rgba(53, 168, 107, 0.18), 0 7px 17px rgba(41, 142, 86, 0.24);
}

.planner-toggle:disabled {
  pointer-events: none;
  opacity: 0.52;
  transform: none;
}

.view-tabs {
  flex-shrink: 0;
  padding: 3px;
  display: inline-flex;
  gap: 2px;
  background: var(--color-surface-soft);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

.view-tab {
  height: 27px;
  padding: 0 9px;
  border: 0;
  border-radius: 6px;
  color: var(--color-muted);
  background: transparent;
  font-size: 12px;
  cursor: pointer;
  transition: color var(--transition-fast), background-color var(--transition-fast);
}

.view-tab.active {
  color: var(--color-primary);
  background: var(--color-primary-soft);
}

.work-card-content {
  min-width: 0;
  min-height: 0;
  display: grid;
  flex: 1;
}

.work-panel {
  min-width: 0;
  min-height: 0;
  grid-area: 1 / 1;
}

.work-panel.is-active {
  position: relative;
  z-index: 1;
}

.work-panel.is-inactive {
  visibility: hidden;
  pointer-events: none;
}

.calendar-view {
  display: flex;
  flex-direction: column;
}

.node-date-selection-heading {
  width: 100%;
  height: 35px;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-date-selection-heading strong {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--color-primary);
  font-size: 11px;
}

.node-date-selection-heading button {
  height: 27px;
  flex-shrink: 0;
  padding: 0 8px;
  border: 1px solid rgba(91, 91, 214, 0.2);
  border-radius: 7px;
  background: var(--color-surface);
  color: var(--color-primary);
  font-size: 10px;
  cursor: pointer;
}

.calendar-main {
  min-height: 0;
  display: flex;
  flex: 1;
  flex-direction: column;
}

.month-toolbar {
  min-height: 39px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.today-button,
.month-navigation button {
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  background: var(--color-surface);
  cursor: pointer;
}

.today-button {
  height: 26px;
  padding: 0 9px;
  border-radius: 8px;
  font-size: 12px;
}

.month-navigation {
  display: flex;
  align-items: center;
  gap: 7px;
}

.month-navigation strong {
  min-width: 82px;
  color: var(--color-text);
  font-size: 13px;
  font-weight: 600;
  text-align: center;
}

.month-navigation button {
  width: 30px;
  height: 30px;
  padding: 0;
  border-radius: 50%;
  font-size: 20px;
  line-height: 20px;
}

.today-button:hover,
.month-navigation button:hover {
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.weekdays,
.date-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
}

.weekdays {
  height: 23px;
  flex-shrink: 0;
  align-items: center;
  color: var(--color-muted);
  font-size: 11px;
  text-align: center;
}

.date-grid {
  min-height: 216px;
  grid-template-rows: repeat(6, 36px);
  align-content: space-evenly;
  flex: 1;
}

.date-placeholder,
.date-button {
  min-width: 0;
  min-height: 0;
}

.date-button {
  position: relative;
  width: 100%;
  height: 36px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.date-number {
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  border-radius: 50%;
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1;
  transition: color var(--transition-fast), background-color var(--transition-fast),
    border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.date-button:hover .date-number {
  background: var(--color-surface-soft);
}

.date-button.selected:not(.today):not(.marked) .date-number,
.date-button.selected:not(.today):not(.marked):hover .date-number {
  color: var(--color-primary);
  border-color: var(--color-primary);
  background: var(--color-surface);
}

.date-button.marked .date-number {
  border-color: transparent;
  background: var(--color-surface);
  box-shadow: 0 0 0 1.5px var(--marker-color);
}

.date-button.selected.marked:not(.today) .date-number,
.date-button.selected.marked:not(.today):hover .date-number {
  color: var(--marker-color);
  border-color: transparent;
  background: var(--marker-soft);
  box-shadow: 0 0 0 1.5px var(--marker-color);
}

.date-button.today .date-number,
.date-button.today:hover .date-number {
  color: #fff;
  border-color: transparent;
  background: linear-gradient(135deg, var(--color-primary), #7474e8);
  box-shadow: 0 3px 8px rgb(91 92 232 / 24%);
}

.date-button.today.marked .date-number,
.date-button.today.marked:hover .date-number {
  box-shadow: 0 0 0 1.5px var(--color-surface), 0 0 0 3px var(--marker-color);
}

.date-button:focus {
  outline: none;
}

.date-button:focus-visible .date-number {
  outline: 3px solid rgb(91 91 214 / 16%);
  outline-offset: 3px;
}

.work-calendar.node-date-selection-mode .date-button:hover .date-number,
.work-calendar.node-date-selection-mode .date-button:focus-visible .date-number {
  outline: 1px dashed var(--color-primary);
  outline-offset: 2px;
}

.date-button.marker-green {
  --marker-color: #35a86b;
  --marker-soft: #eff9f3;
}

.color-green {
  background: #35a86b;
}

.date-button.marker-yellow {
  --marker-color: #d59a18;
  --marker-soft: #fff8e8;
}

.color-yellow {
  background: #e4a928;
}

.date-button.marker-red {
  --marker-color: #df5660;
  --marker-soft: #fff1f2;
}

.color-red {
  background: #df5660;
}

.marker-editor {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--color-border);
}

.marker-editor.selection-hidden {
  pointer-events: none;
  visibility: hidden;
}

.editor-heading,
.todo-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.editor-heading strong,
.todo-heading strong {
  color: var(--color-text);
  font-size: 13px;
  font-weight: 600;
}

.editor-heading span,
.todo-status {
  color: var(--color-muted);
  font-size: 11px;
  font-weight: 400;
}

.marker-controls {
  min-width: 0;
  margin-top: 7px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.marker-controls > input,
.todo-add-row input {
  flex: 1 1 90px;
  width: 100%;
  min-width: 0;
  height: 30px;
  padding: 0 9px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  outline: none;
  color: var(--color-text);
  background: var(--color-surface);
  font: inherit;
  font-size: 12px;
}

.marker-controls > input:focus-visible,
.todo-add-row input:focus-visible {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgb(91 92 232 / 9%);
}

.color-options {
  min-width: 0;
  margin: 0;
  padding: 0 2px;
  display: flex;
  gap: 5px;
  border: 0;
}

.color-options label {
  width: 18px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.color-options input {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  opacity: 0;
}

.color-options label span {
  width: 13px;
  height: 13px;
  border: 2px solid var(--color-surface);
  border-radius: 50%;
  box-shadow: 0 0 0 1px var(--color-border-strong);
}

.color-options input:checked + span {
  box-shadow: 0 0 0 2px var(--color-surface), 0 0 0 3px var(--color-primary);
}

.color-options input:focus-visible + span {
  outline: 2px solid var(--color-primary);
  outline-offset: 3px;
}

.primary-action,
.secondary-action,
.todo-add-row button {
  height: 30px;
  padding: 0 8px;
  border-radius: 8px;
  font-size: 11px;
  cursor: pointer;
}

.view-tab:focus,
.node-date-selection-heading button:focus,
.today-button:focus,
.month-navigation button:focus,
.primary-action:focus,
.secondary-action:focus,
.todo-add-row button:focus,
.todo-delete:focus {
  outline: none;
}

.view-tab:focus-visible,
.node-date-selection-heading button:focus-visible,
.today-button:focus-visible,
.month-navigation button:focus-visible,
.primary-action:focus-visible,
.secondary-action:focus-visible,
.todo-add-row button:focus-visible,
.todo-delete:focus-visible {
  box-shadow: 0 0 0 3px rgb(91 91 214 / 16%);
}

.primary-action,
.todo-add-row button {
  border: 1px solid var(--color-primary);
  color: #fff;
  background: var(--color-primary);
}

.secondary-action {
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  background: var(--color-surface);
}

.storage-message {
  min-height: 13px;
  margin: 3px 0 0;
  color: var(--color-muted);
  font-size: 10px;
  line-height: 13px;
  text-align: right;
}

.todo-view {
  padding-top: 13px;
  display: flex;
  flex-direction: column;
}

.work-card-header,
.todo-heading,
.todo-add-row,
.todo-item,
.todo-progress {
  transition: opacity var(--transition-fast), filter var(--transition-fast),
    border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.work-calendar.todo-confirming .work-card-header,
.todo-view.is-confirming .todo-heading,
.todo-view.is-confirming .todo-add-row,
.todo-view.is-confirming .todo-progress {
  pointer-events: none;
  opacity: 0.58;
  filter: blur(2px);
}

.todo-heading > strong {
  min-width: 0;
  overflow-wrap: anywhere;
}

.todo-status {
  min-height: 16px;
  text-align: right;
}

.todo-add-row {
  margin-top: 13px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 7px;
}

.todo-add-row button {
  padding: 0 13px;
}

.todo-list {
  min-height: 0;
  max-height: 260px;
  margin-top: 13px;
  padding-right: 3px;
  display: flex;
  flex: 0 1 auto;
  flex-direction: column;
  gap: 7px;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-color: var(--color-border-strong) transparent;
  scrollbar-width: thin;
}

.todo-item {
  position: relative;

  min-width: 0;
  height: 42px;
  min-height: 42px;
  padding: 7px 8px;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 8px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface-soft);
}

.todo-item.dragging {
  z-index: 5;
  border-color: rgba(91, 91, 214, 0.42);
  box-shadow: 0 8px 20px rgba(65, 78, 148, 0.14);
}

.todo-drag-control {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.todo-quadrant-symbol {
  display: inline-flex;
  opacity: 0.86;
  transition: opacity var(--transition-fast);
}

.todo-item.done .todo-quadrant-symbol {
  opacity: 0.5;
}

.todo-drag-handle {
  width: 24px;
  height: 24px;
  padding: 0;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: #9aa8bd;
  font-size: 17px;
  line-height: 1;
  cursor: grab;
  transition: color var(--transition-fast), background-color var(--transition-fast);
}

.todo-drag-handle:hover {
  background: rgba(91, 91, 214, 0.07);
  color: #71809a;
}

.todo-drag-handle:active,
.todo-item.dragging .todo-drag-handle {
  color: var(--color-primary);
  cursor: grabbing;
}

.todo-drag-handle:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(91, 91, 214, 0.16);
}

.work-calendar.task-dragging .work-card-header,
.work-calendar.task-dragging .todo-heading,
.work-calendar.task-dragging .todo-add-row,
.work-calendar.task-dragging .todo-progress,
.work-calendar.task-dragging .todo-item:not(.dragging) {
  opacity: 0.5;
  filter: blur(2px);
}

.todo-list.drop-active,
.todo-empty.drop-active {
  border-color: rgba(91, 91, 214, 0.4);
  background: rgba(91, 91, 214, 0.055);
  box-shadow: inset 0 0 0 1px rgba(91, 91, 214, 0.08);
}

.todo-list.drop-active::after {
  position: sticky;
  bottom: 4px;
  align-self: center;
  padding: 4px 9px;
  content: '移出四象限';
  border: 1px solid rgba(91, 91, 214, 0.16);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.94);
  color: var(--color-primary);
  font-size: 10px;
}

.todo-drop-hint {
  color: var(--color-primary);
  font-size: 10px;
}

.work-calendar.planning-modal-open > :not(.planner-toggle),
.work-calendar.planning-modal-open > .planner-toggle {
  pointer-events: none;
  opacity: 0.58;
  filter: blur(2px);
}

.todo-item.confirming {
  z-index: 4;
  border-color: rgba(91, 91, 214, 0.28);
  box-shadow: 0 8px 22px rgba(65, 78, 148, 0.14), 0 0 0 2px rgba(91, 91, 214, 0.06);
}

.todo-view.is-confirming .todo-item:not(.confirming) {
  pointer-events: none;
  opacity: 0.58;
  filter: blur(2px);
}

.todo-item.confirming .todo-check {
  pointer-events: none;
}

.todo-check {
  display: inline-flex;
  cursor: pointer;
}

.todo-check input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
}

.todo-check:focus-within {
  border-radius: 50%;
  box-shadow: 0 0 0 3px rgb(91 91 214 / 16%);
}

.todo-content {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.todo-text {
  display: block;
  min-width: 0;
  overflow: hidden;
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.45;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.todo-item.done .todo-text {
  color: var(--color-muted);
  text-decoration: line-through;
}

.todo-delete {
  width: 24px;
  height: 24px;
  padding: 0;
  border: 0;
  border-radius: 8px;
  color: var(--color-muted);
  background: transparent;
  font-size: 18px;
  cursor: pointer;
}

.todo-delete:hover {
  color: #df5660;
}

.todo-delete.hidden {
  visibility: hidden;
}

.todo-delete-confirm {
  position: absolute;
  top: calc(100% + 4px);
  right: 4px;
  z-index: 10;
  min-width: 198px;
}

.todo-item:last-child:not(:only-child) .todo-delete-confirm {
  top: auto;
  bottom: calc(100% + 4px);
}

.todo-progress {
  margin: 3px 2px 0;
  color: var(--color-muted);
  font-size: 10px;
  text-align: right;
}

.todo-empty {
  min-height: 0;
  padding: 24px 0;
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 5px;
  color: var(--color-muted);
  font-size: 12px;
  text-align: center;
}

.todo-empty strong {
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 500;
}

.todo-empty span {
  font-size: 11px;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 768px) {
  .work-card-content {
    display: block;
  }

  .work-panel.is-inactive {
    display: none;
  }

  .todo-list {
    max-height: 320px;
  }
}

@media (max-width: 600px) {
  .work-calendar {
    padding: 15px;
  }
}

@media (max-width: 360px) {
  .marker-controls {
    gap: 4px;
  }

  .marker-controls > input {
    flex-basis: 100%;
  }

  .color-options {
    gap: 3px;
  }

  .primary-action,
  .secondary-action {
    padding: 0 6px;
  }

  .todo-add-row {
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 5px;
  }

  .todo-delete-confirm {
    min-width: 190px;
  }
}
</style>
