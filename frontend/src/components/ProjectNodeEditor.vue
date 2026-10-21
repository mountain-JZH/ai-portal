<script setup>
import { computed } from 'vue'
import { editorStages } from '../utils/projectEditor'
import { shortStages } from '../utils/projectBoard'
import { firstActiveNode, nextNodeStatus } from '../utils/projectNodes'

const props = defineProps({
  modelValue: { type: Array, required: true },
  baseline: { type: Array, required: true },
  currentStage: { type: String, default: null },
  disabled: Boolean,
})
const emit = defineEmits(['update:modelValue'])
const active = computed(() => firstActiveNode(props.modelValue))
const changed = computed(() => JSON.stringify(props.modelValue) !== JSON.stringify(props.baseline))
const statuses = ['进行中', '已完成', '未开始', '暂缓', '不适用']
function setNode(index, value) {
  if (props.disabled) return
  const nodes = [...props.modelValue]
  nodes[index] = value
  emit('update:modelValue', nodes)
}
function cycle(index) {
  setNode(index, nextNodeStatus(props.modelValue[index]))
}
function undo() {
  if (!props.disabled) emit('update:modelValue', [...props.baseline])
}
function tone(value) {
  return value === '已完成' ? 'done' : value === '进行中' ? 'active' : 'unset'
}
</script>

<template>
  <div class="node-editor">
    <div class="node-heading" aria-live="polite">
      <strong>{{ active >= 0 ? editorStages[active] : currentStage || '当前阶段未设置' }}</strong>
      <span>{{
        active >= 0 ? '进行中 · 按节点顺序优先' : '当前没有进行中的节点，保留原当前阶段'
      }}</span>
    </div>
    <p class="node-help">
      点击循环：未设置 → 进行中 → 已完成 →
      未设置。仅修改草稿，保存后生效；灰色也可能是历史特殊状态。
    </p>
    <div class="node-scroll">
      <ol class="node-bar" aria-label="编辑 11 个实施节点">
        <li
          v-for="(name, index) in editorStages"
          :key="name"
          :data-node-id="`stage_${String(index + 1).padStart(2, '0')}`"
        >
          <button
            type="button"
            :class="tone(modelValue[index])"
            :disabled="disabled"
            :title="`${name}：${modelValue[index] ?? '空白'}；点击改为${nextNodeStatus(modelValue[index]) ?? '空白'}`"
            :aria-label="`${String(index + 1).padStart(2, '0')} ${name}，${modelValue[index] === '' || modelValue[index] == null ? '空白' : modelValue[index]}；点击切换状态`"
            @click="cycle(index)"
          >
            {{ String(index + 1).padStart(2, '0') }}
          </button>
          <span>{{ shortStages[index] }}</span>
        </li>
      </ol>
    </div>
    <button type="button" class="node-undo" :disabled="disabled || !changed" @click="undo">
      撤销节点修改
    </button>
    <details class="node-advanced">
      <summary>高级状态编辑</summary>
      <p class="node-help">保留原始自由文本。空白与“未开始”不同；只有明确修改的节点才会变化。</p>
      <div class="node-fields">
        <label v-for="(name, index) in editorStages" :key="name"
          >{{ index + 1 }} · {{ name }}
          <input
            :value="modelValue[index] ?? ''"
            :disabled="disabled"
            list="node-editor-statuses"
            maxlength="2000"
            @input="setNode(index, $event.target.value)"
          />
        </label>
      </div>
      <datalist id="node-editor-statuses">
        <option v-for="status in statuses" :key="status" :value="status" />
      </datalist>
    </details>
  </div>
</template>

<style scoped>
.node-editor {
  color: #22292c;
}
.node-heading {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 12px;
}
.node-heading strong {
  font-size: 20px;
}
.node-heading span,
.node-help {
  color: #6d5b55;
  font-size: 13px;
  line-height: 1.8;
}
.node-scroll {
  overflow-x: auto;
  padding: 4px;
  margin: 18px -4px;
}
.node-bar {
  list-style: none;
  display: grid;
  grid-template-columns: repeat(11, minmax(54px, 1fr));
  gap: 6px;
  min-width: 660px;
  padding: 0;
  margin: 0;
}
.node-bar li {
  min-width: 0;
  text-align: center;
}
.node-bar button {
  width: 100%;
  min-height: 44px;
  border: 1px solid #dfe4e4;
  border-radius: 5px;
  background: #f5f6f7;
  color: #22292c;
  font: inherit;
  cursor: pointer;
}
.node-bar button.done {
  background: #8dfc08;
  border-color: #8dfc08;
}
.node-bar button.active {
  background: #f7b334;
  border-color: #f7b334;
}
.node-bar li > span {
  display: block;
  font-size: 12px;
  line-height: 1.6;
  margin-top: 8px;
}
.node-undo {
  font: inherit;
  min-height: 42px;
  padding: 8px 12px;
  border: 1px solid #dfe4e4;
  border-radius: 6px;
  background: #f5f6f7;
  color: inherit;
  cursor: pointer;
}
button:disabled {
  opacity: 0.6;
  cursor: default;
}
.node-advanced {
  margin-top: 18px;
  border-top: 1px solid #e5e8e8;
  padding-top: 16px;
}
summary {
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
}
.node-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
}
input {
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  min-height: 42px;
  padding: 10px 12px;
  border: 1px solid #dfe4e4;
  border-radius: 6px;
  font: inherit;
  color: inherit;
  background: white;
}
:focus-visible {
  outline: 3px solid #f7b334;
  outline-offset: 3px;
}
@media (max-width: 650px) {
  .node-fields {
    grid-template-columns: 1fr;
  }
}
</style>
