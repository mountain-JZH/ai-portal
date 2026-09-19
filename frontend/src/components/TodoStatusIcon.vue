<script setup>
defineProps({
  done: {
    type: Boolean,
    default: false,
  },
})
</script>

<template>
  <span
    class="todo-status-icon"
    :class="{ done }"
    role="img"
    :aria-label="done ? '已完成' : '未完成'"
  ></span>
</template>

<style scoped>
.todo-status-icon {
  width: 16px;
  height: 16px;
  flex: 0 0 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border-strong);
  border-radius: 50%;
  background: var(--color-surface);
}

.todo-status-icon.done {
  border-color: var(--color-primary);
  background: var(--color-primary);
}

.todo-status-icon.done::after {
  width: 6px;
  height: 3px;
  content: '';
  border-bottom: 1.5px solid #fff;
  border-left: 1.5px solid #fff;
  transform: translateY(-1px) rotate(-45deg);
}
</style>
