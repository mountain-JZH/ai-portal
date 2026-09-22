<script setup>
import { ref } from 'vue'

import HeroBanner from '../components/HeroBanner.vue'
import NewsList from '../components/NewsList.vue'
import PlannerExpandPanel from '../components/PlannerExpandPanel.vue'
import ToolGrid from '../components/ToolGrid.vue'
import WorkCalendar from '../components/WorkCalendar.vue'

const isPlannerExpanded = ref(false)
const plannerSelectedDate = ref('')
const draggingTodoId = ref('')
const isMatrixModalOpen = ref(false)
const nodeDateSelectionMode = ref({ active: false })
const nodeDateSelectionResult = ref(null)
let nodeDateSelectionSequence = 0

function togglePlanner() {
  isPlannerExpanded.value = !isPlannerExpanded.value
}

function updatePlannerSelectedDate(dateKey) {
  plannerSelectedDate.value = dateKey
}

function startTaskDrag(todoId) {
  draggingTodoId.value = String(todoId)
}

function endTaskDrag() {
  draggingTodoId.value = ''
}

function updateMatrixModal(open) {
  isMatrixModalOpen.value = Boolean(open)
}

function startNodeDateSelection(request) {
  nodeDateSelectionResult.value = null
  nodeDateSelectionMode.value = { active: true, ...request }
}

function selectNodeDate(date) {
  if (!nodeDateSelectionMode.value.active) return
  nodeDateSelectionSequence += 1
  nodeDateSelectionResult.value = {
    ...nodeDateSelectionMode.value,
    date,
    requestId: nodeDateSelectionSequence,
  }
}

function finishNodeDateSelection() {
  nodeDateSelectionMode.value = { active: false }
  nodeDateSelectionResult.value = null
}

</script>

<template>
  <main
    class="home"
    :class="{
      'planner-expanded': isPlannerExpanded,
    }"
  >
    <section class="home-banner-section">
      <HeroBanner class="home-hero" />
    </section>

    <section class="home-content-grid">
      <div class="home-main-column">
        <NewsList class="home-news" />
      </div>

      <aside class="home-side-column">
        <WorkCalendar
          :planner-expanded="isPlannerExpanded"
          :is-task-dragging="Boolean(draggingTodoId)"
          :is-planning-modal-open="isMatrixModalOpen"
          :dragging-todo-id="draggingTodoId"
          :node-date-selection-mode="nodeDateSelectionMode"
          @cancel-node-date-selection="finishNodeDateSelection"
          @node-date-selected="selectNodeDate"
          @selected-date-change="updatePlannerSelectedDate"
          @task-drag-end="endTaskDrag"
          @task-drag-start="startTaskDrag"
          @toggle-planner="togglePlanner"
        />
      </aside>
    </section>

    <Transition name="planner-expand">
      <div v-if="isPlannerExpanded" class="home-planner-shell">
        <PlannerExpandPanel
          :selected-date="plannerSelectedDate"
          :dragging-todo-id="draggingTodoId"
          :is-matrix-modal-open="isMatrixModalOpen"
          :node-date-selection-mode="nodeDateSelectionMode"
          :node-date-selection-result="nodeDateSelectionResult"
          @modal-change="updateMatrixModal"
          @node-date-selection-complete="finishNodeDateSelection"
          @request-node-date-selection="startNodeDateSelection"
          @task-drag-end="endTaskDrag"
        />
      </div>
    </Transition>

    <ToolGrid class="home-tools" />
  </main>
</template>

<style scoped>
.home {
  width: calc(100% - 48px);
  max-width: 1200px;
  margin: 0 auto;
  padding-top: 32px;
}

.home-banner-section,
.home-main-column,
.home-side-column {
  min-width: 0;
  min-height: 0;
}

.home-main-column,
.home-side-column {
  display: flex;
}

.home-content-grid {
  margin-top: 64px;

  display: grid;
  align-items: stretch;
  gap: 24px;
  grid-template-columns: minmax(0, 2.2fr) minmax(310px, 0.9fr);
}

:deep(.home-hero),
:deep(.home-news),
:deep(.home-tools) {
  width: 100%;
  max-width: none;
  margin: 0;
}

:deep(.home-news),
:deep(.work-calendar) {
  height: 100%;
}

:deep(.home-tools) {
  margin: 48px 0 96px;
}

.home-planner-shell {
  width: 100%;
  max-height: 900px;
  margin-top: 28px;
  overflow: hidden;
}

.planner-expanded :deep(.home-tools) {
  margin-top: 36px;
}

.planner-expand-enter-active,
.planner-expand-leave-active {
  transition: max-height 220ms ease, margin-top 220ms ease, opacity 200ms ease,
    transform 200ms ease;
}

.planner-expand-enter-from,
.planner-expand-leave-to {
  max-height: 0;
  margin-top: 0;
  opacity: 0;
  transform: translateY(-8px);
}

@media (max-width: 1024px) {
  .home-planner-shell {
    margin-top: 24px;
  }

  .planner-expanded :deep(.home-tools) {
    margin-top: 32px;
  }
}

@media (max-width: 768px) {
  .home-content-grid {
    align-items: start;
    grid-template-columns: minmax(0, 1fr);
    gap: 32px;
    margin-top: 56px;
  }

  .home-main-column,
  .home-side-column {
    display: block;
  }

  :deep(.home-news),
  :deep(.work-calendar) {
    height: auto;
  }

}

@media (max-width: 600px) {
  .home {
    width: calc(100% - 32px);
    padding-top: 20px;
  }

  .home-content-grid {
    gap: 24px;
    margin-top: 48px;
  }

  :deep(.home-tools) {
    margin: 40px 0 72px;
  }
}
</style>
