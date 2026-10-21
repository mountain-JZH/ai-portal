<script setup>
import { stageTone } from '../utils/projectDisplay'
defineProps({ stages: { type: Array, required: true }, names: { type: Array, required: true } })
</script>

<template>
  <ol class="project-segments" aria-label="11 个实施节点状态">
    <li
      v-for="(name, index) in names"
      :key="name"
      :class="stageTone(stages[index])"
      :title="`${index + 1}. ${name}：${stages[index] || '未填写'}`"
    >
      <span class="project-sr-only">{{ name }}：{{ stages[index] || '未填写' }}</span>
    </li>
  </ol>
</template>
