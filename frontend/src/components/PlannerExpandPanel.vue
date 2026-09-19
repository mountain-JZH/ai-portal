<script setup>
import PriorityMatrix from './PriorityMatrix.vue'
import ProjectNodeManager from './ProjectNodeManager.vue'

const props = defineProps({
  selectedDate: {
    type: String,
    default: '',
  },
  draggingTodoId: {
    type: String,
    default: '',
  },
  isMatrixModalOpen: {
    type: Boolean,
    default: false,
  },
  nodeDateSelectionMode: {
    type: Object,
    default: () => ({ active: false }),
  },
  nodeDateSelectionResult: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits([
  'task-drag-end',
  'modal-change',
  'request-node-date-selection',
  'node-date-selection-complete',
])
</script>

<template>
  <section
    id="planner-expand-panel"
    class="planner-expand-panel"
    :class="{
      'task-dragging': props.draggingTodoId,
      'matrix-modal-open': props.isMatrixModalOpen,
    }"
    aria-label="工作计划扩展"
  >
    <ProjectNodeManager
      class="timeline-module"
      :node-date-selection-mode="props.nodeDateSelectionMode"
      :node-date-selection-result="props.nodeDateSelectionResult"
      @node-date-selection-complete="emit('node-date-selection-complete', $event)"
      @request-node-date-selection="emit('request-node-date-selection', $event)"
    />

    <PriorityMatrix
      :selected-date="selectedDate"
      :dragging-todo-id="props.draggingTodoId"
      :node-date-selection-active="props.nodeDateSelectionMode.active"
      @modal-change="emit('modal-change', $event)"
      @task-drag-end="emit('task-drag-end')"
    />
  </section>
</template>

<style scoped>
.planner-expand-panel {
  width: 100%;
  min-width: 0;
  min-height: 0;
  display: grid;
  align-items: stretch;
  gap: 24px;
  grid-template-columns: minmax(0, 2.2fr) minmax(310px, 0.9fr);
}

.timeline-module {
  transition: opacity 200ms ease, filter 200ms ease;
}

.planner-expand-panel.task-dragging .timeline-module {
  pointer-events: none;
  opacity: 0.5;
  filter: blur(2px);
}

.planner-expand-panel.matrix-modal-open .timeline-module {
  pointer-events: none;
  opacity: 0.58;
  filter: blur(2px);
}

@media (max-width: 1024px) {
  .planner-expand-panel {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 600px) {
  .planner-expand-panel {
    gap: 16px;
  }

}
</style>
