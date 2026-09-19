<script setup>
import { ref } from 'vue'

defineProps({
  message: {
    type: String,
    required: true,
  },
  detail: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['confirm', 'cancel'])
const cancelButton = ref(null)

function focusCancel() {
  cancelButton.value?.focus()
}

defineExpose({ focusCancel })
</script>

<template>
  <div class="delete-confirm" role="alertdialog" aria-modal="true" @keydown.esc.stop="emit('cancel')">
    <div class="delete-confirm-copy">
      <strong>{{ message }}</strong>
      <small v-if="detail">{{ detail }}</small>
    </div>
    <div class="delete-confirm-actions">
      <button class="delete-action" type="button" @click="emit('confirm')">删除</button>
      <button ref="cancelButton" class="cancel-action" type="button" @click="emit('cancel')">
        取消
      </button>
    </div>
  </div>
</template>

<style scoped>
.delete-confirm {
  min-width: 0;
  padding: 8px 9px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface);
  box-shadow: 0 10px 24px rgba(65, 78, 148, 0.16);
}

.delete-confirm-copy {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.delete-confirm-copy strong,
.delete-confirm-copy small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delete-confirm-copy strong {
  color: var(--color-text-secondary);
  font-size: 11px;
  font-weight: 500;
}

.delete-confirm-copy small {
  color: var(--color-muted);
  font-size: 9px;
}

.delete-confirm-actions {
  flex-shrink: 0;
  display: flex;
  gap: 6px;
}

button {
  height: 28px;
  padding: 0 9px;
  border-radius: 8px;
  font: inherit;
  font-size: 10px;
  cursor: pointer;
}

.delete-action {
  border: 1px solid rgb(200 66 78 / 28%);
  background: #fff4f5;
  color: #c8424e;
}

.cancel-action {
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-secondary);
}

button:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(91, 91, 214, 0.15);
}

@media (max-width: 420px) {
  .delete-confirm {
    gap: 7px;
  }

  .delete-confirm-copy small {
    white-space: normal;
  }
}
</style>
