<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

import {
  QUADRANTS,
  QUADRANT_STORAGE_KEY,
  QUADRANT_STATUS_COLORS,
  QUADRANT_UPDATED_EVENT,
  readQuadrantStore,
  sanitizeQuadrantStore,
  writeQuadrantStore,
} from '../utils/quadrantStorage'
import { readTodoStore, sanitizeTodoStore, TODO_UPDATED_EVENT } from '../utils/todoStorage'
import QuadrantSymbol from './QuadrantSymbol.vue'
import TodoStatusIcon from './TodoStatusIcon.vue'

const props = defineProps({
  selectedDate: { type: String, default: '' },
  draggingTodoId: { type: String, default: '' },
  nodeDateSelectionActive: { type: Boolean, default: false },
})

const emit = defineEmits(['task-drag-end', 'modal-change'])
const todosByDate = ref({})
const quadrantMappings = ref({})
const hoveredQuadrant = ref('')
const activeQuadrant = ref('')
let suppressCardClickUntil = 0

const currentTodos = computed(() => todosByDate.value[props.selectedDate] || [])
const currentMapping = computed(() => quadrantMappings.value[props.selectedDate] || {})
const activeDefinition = computed(() =>
  QUADRANTS.find((quadrant) => quadrant.key === activeQuadrant.value),
)
const activeTasks = computed(() => tasksForQuadrant(activeQuadrant.value))
const sortedActiveTasks = computed(() =>
  [...activeTasks.value].sort((first, second) => Number(first.done) - Number(second.done)),
)
const activeStats = computed(() => getQuadrantStats(activeQuadrant.value))

function tasksForQuadrant(quadrantKey) {
  return currentTodos.value.filter((todo) => currentMapping.value[todo.id] === quadrantKey)
}

function getQuadrantStats(quadrantKey) {
  const tasks = tasksForQuadrant(quadrantKey)
  const completedCount = tasks.filter((todo) => todo.done).length
  return {
    totalCount: tasks.length,
    completedCount,
    pendingCount: tasks.length - completedCount,
  }
}

function quadrantStatus(quadrantKey) {
  const { totalCount, pendingCount } = getQuadrantStats(quadrantKey)
  if (!totalCount) return { state: 'empty', label: '暂无任务', pendingCount: 0 }
  if (!pendingCount) return { state: 'completed', label: '已完成', pendingCount: 0 }
  return { state: 'pending', label: '', pendingCount }
}

function refreshMappings(cleanStoredData = false) {
  let storedValue
  try {
    const storedMappings = localStorage.getItem(QUADRANT_STORAGE_KEY)
    storedValue = storedMappings ? JSON.parse(storedMappings) : {}
  } catch {
    storedValue = {}
  }

  const cleanedMappings = sanitizeQuadrantStore(storedValue, todosByDate.value)
  quadrantMappings.value = cleanedMappings
  if (cleanStoredData && JSON.stringify(storedValue) !== JSON.stringify(cleanedMappings)) {
    writeQuadrantStore(cleanedMappings)
  }
}

function persistMappings(nextMappings) {
  quadrantMappings.value = nextMappings
  writeQuadrantStore(nextMappings)
}

function endTaskDrag() {
  hoveredQuadrant.value = ''
  emit('task-drag-end')
}

function openDetails(quadrantKey) {
  if (props.draggingTodoId || Date.now() < suppressCardClickUntil) return
  activeQuadrant.value = quadrantKey
  emit('modal-change', true)
}

function closeDetails() {
  activeQuadrant.value = ''
  emit('modal-change', false)
}

function handleEscape(event) {
  if (event.key === 'Escape' && activeQuadrant.value) closeDetails()
}

function enterQuadrant(event, quadrantKey) {
  event.preventDefault()
  hoveredQuadrant.value = quadrantKey
  event.dataTransfer.dropEffect = 'move'
}

function leaveQuadrant(event, quadrantKey) {
  if (event.currentTarget.contains(event.relatedTarget)) return
  if (hoveredQuadrant.value === quadrantKey) hoveredQuadrant.value = ''
}

function dropIntoQuadrant(event, quadrantKey) {
  event.preventDefault()
  const todoId = props.draggingTodoId || event.dataTransfer.getData('text/plain')
  if (currentTodos.value.some((todo) => todo.id === todoId)) {
    persistMappings({
      ...quadrantMappings.value,
      [props.selectedDate]: { ...currentMapping.value, [todoId]: quadrantKey },
    })
  }
  suppressCardClickUntil = Date.now() + 250
  endTaskDrag()
}

function handleTodosUpdated(event) {
  todosByDate.value = event.detail?.todos
    ? sanitizeTodoStore(event.detail.todos)
    : readTodoStore()
  refreshMappings(true)
}

function handleQuadrantsUpdated(event) {
  quadrantMappings.value = event.detail?.mappings
    ? sanitizeQuadrantStore(event.detail.mappings, todosByDate.value)
    : readQuadrantStore(todosByDate.value)
}

watch(
  () => props.selectedDate,
  () => {
    todosByDate.value = readTodoStore()
    refreshMappings(true)
    hoveredQuadrant.value = ''
    closeDetails()
  },
  { immediate: true },
)

watch(
  () => props.draggingTodoId,
  (todoId) => {
    if (!todoId) hoveredQuadrant.value = ''
  },
)

onMounted(() => {
  window.addEventListener(TODO_UPDATED_EVENT, handleTodosUpdated)
  window.addEventListener(QUADRANT_UPDATED_EVENT, handleQuadrantsUpdated)
  window.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  window.removeEventListener(TODO_UPDATED_EVENT, handleTodosUpdated)
  window.removeEventListener(QUADRANT_UPDATED_EVENT, handleQuadrantsUpdated)
  window.removeEventListener('keydown', handleEscape)
})
</script>

<template>
  <article
    class="priority-matrix"
    :class="{
      'task-dragging': props.draggingTodoId,
      'node-date-selection-active': props.nodeDateSelectionActive,
    }"
    :style="{
      '--quadrant-empty-color': QUADRANT_STATUS_COLORS.empty,
      '--quadrant-complete-color': QUADRANT_STATUS_COLORS.completed,
    }"
  >
    <div class="matrix-content" :class="{ muted: activeQuadrant }">
      <header class="matrix-header">
        <div>
          <h2>四象限</h2>
          <p>拖动分类，点击象限查看任务详情</p>
        </div>
      </header>

      <div class="quadrant-grid" aria-label="四象限任务概览">
        <button
          v-for="quadrant in QUADRANTS"
          :key="quadrant.key"
          class="quadrant-card"
          :class="[
            `symbol-${quadrant.symbolPosition}`,
            {
              'drop-hover': hoveredQuadrant === quadrant.key,
              subdued: hoveredQuadrant && hoveredQuadrant !== quadrant.key,
            },
          ]"
          :style="{
            '--quadrant-color': quadrant.color,
            '--quadrant-symbol-color': quadrant.color,
          }"
          type="button"
          :aria-label="`${quadrant.label}，${tasksForQuadrant(quadrant.key).length}项任务，点击查看详情`"
          @click="openDetails(quadrant.key)"
          @dragenter="enterQuadrant($event, quadrant.key)"
          @dragover.prevent="enterQuadrant($event, quadrant.key)"
          @dragleave="leaveQuadrant($event, quadrant.key)"
          @drop="dropIntoQuadrant($event, quadrant.key)"
        >
          <strong>{{ quadrant.label }}</strong>
          <span class="quadrant-description">{{ quadrant.description }}</span>
          <span
            class="quadrant-count"
            :class="`is-${quadrantStatus(quadrant.key).state}`"
          >
            <template v-if="quadrantStatus(quadrant.key).state === 'pending'">
              待处理
              <strong>{{ quadrantStatus(quadrant.key).pendingCount }}</strong>
              项
            </template>
            <template v-else>{{ quadrantStatus(quadrant.key).label }}</template>
          </span>
          <QuadrantSymbol
            class="quadrant-symbol-anchor"
            :type="quadrant.symbolType"
          />
          <span v-if="hoveredQuadrant === quadrant.key" class="drop-hint">松开放入</span>
        </button>
      </div>
    </div>

    <Teleport to="body">
      <Transition name="matrix-modal">
        <div
          v-if="activeDefinition"
          class="matrix-dialog-backdrop"
          @click.self="closeDetails"
        >
          <section
            class="matrix-dialog"
            :style="{
              '--quadrant-color': activeDefinition.color,
              '--quadrant-symbol-color': activeDefinition.color,
            }"
            role="dialog"
            aria-modal="true"
            :aria-labelledby="`matrix-dialog-title-${activeDefinition.key}`"
          >
            <header class="dialog-header">
              <div class="dialog-title-group">
                <QuadrantSymbol
                  class="dialog-symbol"
                  :type="activeDefinition.symbolType"
                  size="lg"
                />
                <div>
                  <h3 :id="`matrix-dialog-title-${activeDefinition.key}`">
                    {{ activeDefinition.label }}
                  </h3>
                  <p>
                    共 {{ activeStats.totalCount }} 项 · 待处理 {{ activeStats.pendingCount }} 项
                  </p>
                </div>
              </div>
              <button type="button" aria-label="关闭四象限详情" @click="closeDetails">×</button>
            </header>

            <div v-if="sortedActiveTasks.length" class="dialog-task-list">
              <div
                v-for="todo in sortedActiveTasks"
                :key="todo.id"
                class="dialog-task"
                :class="{ done: todo.done }"
              >
                <TodoStatusIcon :done="todo.done" />
                <span class="dialog-task-text">{{ todo.text }}</span>
              </div>
            </div>
            <p v-else class="dialog-empty">该象限暂无任务</p>
          </section>
        </div>
      </Transition>
    </Teleport>
  </article>
</template>

<style scoped>
.priority-matrix {
  min-width: 0;
  height: 270px;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: var(--color-surface);
  box-shadow: var(--shadow-soft);
}

.priority-matrix.node-date-selection-active {
  pointer-events: none;
  opacity: 0.56;
  filter: blur(2px);
  transition: opacity 200ms ease, filter 200ms ease;
}

.matrix-content {
  height: 100%;
  padding: 18px;
  display: flex;
  flex-direction: column;
  transition: opacity 200ms ease, filter 200ms ease;
}

.matrix-content.muted {
  pointer-events: none;
  opacity: 0.58;
  filter: blur(2px);
}

.matrix-header {
  min-width: 0;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.matrix-header h2 {
  margin: 0;
  color: var(--color-text);
  font-size: 19px;
  line-height: 1.35;
}

.matrix-header p {
  margin: 5px 0 0;
  color: var(--color-muted);
  font-size: 11px;
  line-height: 1.45;
}

.quadrant-grid {
  min-height: 0;
  margin-top: 13px;
  display: grid;
  flex: 1;
  gap: 7px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  grid-template-rows: repeat(2, minmax(0, 1fr));
}

.quadrant-card {
  position: relative;
  min-width: 0;
  min-height: 0;
  padding: 10px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.96);
  color: var(--color-text-secondary);
  text-align: left;
  cursor: pointer;
  transition: opacity 200ms ease, border-color 200ms ease, background-color 200ms ease,
    box-shadow 200ms ease;
}

.quadrant-card:hover,
.quadrant-card:focus-visible {
  border-color: rgba(91, 91, 214, 0.32);
  background: #fff;
  box-shadow: 0 6px 14px rgba(65, 78, 148, 0.09);
}

.quadrant-card:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(91, 91, 214, 0.13), 0 6px 14px rgba(65, 78, 148, 0.09);
}

.priority-matrix.task-dragging .quadrant-card { border-style: dashed; }

.quadrant-card.drop-hover {
  z-index: 2;
  border-color: var(--color-primary);
  border-style: solid;
  background: #fff;
  box-shadow: 0 0 0 2px rgba(91, 91, 214, 0.09), 0 7px 18px rgba(65, 78, 148, 0.12);
}

.quadrant-card.subdued { opacity: 0.72; }

.quadrant-card > strong {
  max-width: calc(100% - 22px);
  overflow: hidden;
  color: var(--color-text-secondary);
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quadrant-description { margin-top: 3px; color: var(--color-muted); font-size: 9px; }

.quadrant-count {
  margin-top: auto;
  color: var(--color-text-secondary);
  font-size: 10px;
  font-weight: 600;
}

.quadrant-count.is-empty { color: var(--quadrant-empty-color); }
.quadrant-count.is-completed { color: var(--quadrant-complete-color); }
.quadrant-count.is-pending { color: var(--color-text-secondary); }
.quadrant-count.is-pending > strong {
  color: var(--quadrant-color);
  font: inherit;
}

.quadrant-symbol-anchor {
  position: absolute;
  opacity: 0.82;
  transition: opacity 200ms ease, transform 200ms ease;
}

.quadrant-card:hover .quadrant-symbol-anchor,
.quadrant-card.drop-hover .quadrant-symbol-anchor {
  opacity: 1;
  transform: scale(1.06);
}

.symbol-bottom-right .quadrant-symbol-anchor { right: 7px; bottom: 6px; }
.symbol-bottom-left .quadrant-symbol-anchor { bottom: 6px; left: 7px; }
.symbol-top-right .quadrant-symbol-anchor { top: 6px; right: 7px; }
.symbol-top-left .quadrant-symbol-anchor { top: 6px; left: 7px; }
.symbol-bottom-left,
.symbol-top-left { align-items: flex-end; text-align: right; }
.symbol-bottom-left .quadrant-count,
.symbol-top-left .quadrant-count { align-self: flex-end; }

.drop-hint {
  position: absolute;
  right: 7px;
  bottom: 6px;
  padding: 2px 5px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  color: var(--color-primary);
  font-size: 8px;
}

.matrix-dialog-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  padding: 20px;
  display: grid;
  place-items: center;
  background: transparent;
}

.matrix-dialog {
  width: min(480px, 100%);
  max-height: min(560px, calc(100vh - 40px));
  padding: 22px;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(91, 91, 214, 0.17);
  border-radius: 12px;
  background: var(--color-surface);
  box-shadow: 0 20px 52px rgba(42, 51, 92, 0.22);
  transition: opacity 180ms ease, filter 180ms ease;
}

.dialog-header,
.dialog-title-group { display: flex; align-items: center; }
.dialog-header {
  justify-content: space-between;
  gap: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--color-border);
}

.dialog-title-group { min-width: 0; gap: 11px; }
.dialog-header h3 { margin: 0; color: var(--color-text); font-size: 18px; }
.dialog-header p { margin: 4px 0 0; color: var(--color-muted); font-size: 11px; }

.dialog-header > button {
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  padding: 0;
  border: 1px solid var(--color-border);
  border-radius: 50%;
  background: var(--color-surface-soft);
  color: var(--color-muted);
  font-size: 19px;
  cursor: pointer;
}

.dialog-header > button:hover { color: var(--color-primary); }
.dialog-header > button:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(91, 91, 214, 0.15);
}

.dialog-task-list {
  min-height: 0;
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 7px;
  overflow-y: auto;
  scrollbar-color: var(--color-border-strong) transparent;
  scrollbar-width: thin;
}

.dialog-task {
  min-width: 0;
  padding: 9px 10px;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 9px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface-soft);
  cursor: default;
}

.dialog-task-text {
  min-width: 0;
  overflow-wrap: anywhere;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.5;
}

.dialog-task.done .dialog-task-text { color: var(--color-muted); text-decoration: line-through; }
.dialog-empty { margin: 42px 0; color: var(--color-muted); font-size: 13px; text-align: center; }

.matrix-modal-enter-active,
.matrix-modal-leave-active { transition: opacity 180ms ease; }
.matrix-modal-enter-active .matrix-dialog,
.matrix-modal-leave-active .matrix-dialog { transition: opacity 180ms ease, transform 180ms ease; }
.matrix-modal-enter-from,
.matrix-modal-leave-to { opacity: 0; }
.matrix-modal-enter-from .matrix-dialog,
.matrix-modal-leave-to .matrix-dialog { opacity: 0; transform: translateY(6px); }

@media (max-width: 420px) {
  .priority-matrix { height: 360px; }
  .matrix-content { padding: 15px; }
  .quadrant-grid { grid-template-columns: minmax(0, 1fr); grid-template-rows: repeat(4, minmax(0, 1fr)); }
  .quadrant-card { padding: 8px 10px; }
  .quadrant-description { display: none; }
  .matrix-dialog-backdrop { padding: 12px; }
  .matrix-dialog { max-height: calc(100vh - 24px); padding: 17px; }
}
</style>
