<script setup>
import { displayValue, importTime, scaleValue, stageTone } from '../utils/projectDisplay'
defineProps({
  project: { type: Object, required: true },
  names: { type: Array, required: true },
  businessFields: { type: Array, required: true },
})
</script>

<template>
  <article class="project-detail-content">
    <div class="projects-eyebrow">PROJECT FILE / 项目档案 #{{ project.id }}</div>
    <h2 id="project-detail-title">{{ project.name }}</h2>
    <div class="project-card-ratings">
      <span>{{ displayValue(project.priority) }}</span
      ><span>{{ displayValue(project.valueRating) }}</span>
    </div>
    <p class="projects-footnote">最近导入时间（北京时间）：{{ importTime(project.importedAt) }}</p>
    <dl class="project-detail-facts">
      <div
        v-for="(label, field) in {
          owner: '项目负责人',
          leader: '项目组长',
          resource: '资源名称',
          district: '行政片区',
          customerType: '客户性质',
          management: '管理权',
          ownership: '资产所有权',
          serial: '本次台账序号',
        }"
        :key="field"
      >
        <dt>{{ label }}</dt>
        <dd>{{ displayValue(project[field]) }}</dd>
      </div>
    </dl>
    <section>
      <h3>业务规模</h3>
      <dl class="project-detail-facts">
        <div v-for="[field, label, unit] in businessFields" :key="field">
          <dt>{{ label }}{{ unit ? `（${unit}）` : '' }}</dt>
          <dd>{{ scaleValue(project[field], unit) }}</dd>
        </div>
      </dl>
    </section>
    <section>
      <div class="project-section-heading">
        <h3>全过程实施节点</h3>
        <p>已完成 {{ project.completedCount }} / 11 个节点</p>
      </div>
      <p class="projects-footnote">目前所处阶段：{{ displayValue(project.currentStage) }}</p>
      <ol class="project-timeline">
        <li v-for="(name, index) in names" :key="name" :class="stageTone(project.stages[index])">
          <span class="timeline-marker" aria-hidden="true">{{
            project.stages[index] === '已完成' ? '✓' : String(index + 1).padStart(2, '0')
          }}</span
          ><strong>{{ name }}</strong
          ><span>{{ displayValue(project.stages[index]) }}</span>
        </li>
      </ol>
    </section>
    <section
      v-for="[field, label] in [
        ['situation', '当前推进情况与存在问题'],
        ['nextStep', '下一步打算'],
        ['coordination', '需上级协调事项'],
        ['progressUpdate', '是否有进度更新（台账原值）'],
      ]"
      :key="field"
      class="project-detail-narrative"
    >
      <h3>{{ label }}</h3>
      <p>{{ displayValue(project[field]) }}</p>
    </section>
  </article>
</template>
