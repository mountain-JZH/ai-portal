<script setup>
import { nextTick, ref } from 'vue'
import ProjectBusinessContent from './ProjectBusinessContent.vue'
import { displayValue, importTime, stageTone } from '../utils/projectDisplay'
import { metricValue } from '../utils/projectBoard'
import { currentEmployee } from '../utils/authState'
import { RouterLink } from 'vue-router'
defineProps({ project: { type: Object, required: true }, stages: { type: Array, required: true } })
defineEmits(['history'])
const tab = ref('overview')
const root = ref(null)
async function selectSection(id) {
  if (!sections.some(([key]) => key === id)) return
  tab.value = id
  await nextTick()
  if (tab.value !== id) return
  const container = root.value?.closest('.drawer-inner')
  if (!container) return
  const navigation = root.value.querySelector('.detail-tabs')
  // Keep the chapter controls and the selected body visible even after a long project title.
  // Scroll this container only; scrollIntoView could also move the dialog or background.
  const top = navigation
    ? Math.max(
        0,
        container.scrollTop +
          navigation.getBoundingClientRect().top -
          container.getBoundingClientRect().top -
          8,
      )
    : 0
  container.scrollTo({ top, behavior: 'instant' })
}
const sections = [
  ['overview', '项目概览'],
  ['progress', '实施进度'],
  ['business', '项目内容'],
  ['updates', '实时情况'],
]
const facts = [
  ['serial', '台账序号'],
  ['leader', '项目组长'],
  ['owner', '项目负责人'],
  ['resource', '资源名称'],
  ['management', '管理权'],
  ['ownership', '资产所有权'],
  ['priority', '开发时序评级'],
  ['valueRating', '开发价值评级'],
  ['customerType', '客户性质'],
  ['district', '所属行政片区'],
  ['currentStage', '目前所处阶段'],
  ['progressUpdate', '是否有进度更新（AG 原值）'],
]
</script>

<template>
  <article ref="root" class="pb-detail">
    <div class="detail-index">项目 / {{ String(project.id).padStart(3, '0') }} · 只读项目档案</div>
    <h2 id="pb-detail-title" class="detail-title">{{ project.name }}</h2>
    <div class="detail-resource">{{ displayValue(project.resource) }}</div>
    <div class="project-detail-actions">
      <RouterLink v-if="currentEmployee?.canEditProjects" :to="`/projects/${project.id}/edit`"
        >编辑项目</RouterLink
      ><button type="button" @click="$emit('history', project, '')">查看节点与项目历史</button>
    </div>
    <div class="badges">
      <span class="pill priority">{{ displayValue(project.priority) }}</span
      ><span class="pill">{{ displayValue(project.valueRating) }}</span
      ><span v-for="name in project.businessTypes" :key="name" class="pill business">{{
        name
      }}</span>
    </div>
    <nav class="detail-tabs" aria-label="项目详情章节">
      <button
        v-for="[id, label] in sections"
        :key="id"
        type="button"
        class="detailtab"
        :class="{ active: tab === id }"
        :aria-pressed="tab === id"
        @click="selectSection(id)"
      >
        {{ label }}
      </button>
    </nav>
    <section v-if="tab === 'overview'" class="detailsection" aria-label="项目概览">
      <h3>项目基本信息</h3>
      <dl class="fieldgrid">
        <div v-for="[field, label] in facts" :key="field" class="fieldrow">
          <dt>{{ label }}</dt>
          <dd>{{ displayValue(project[field]) }}</dd>
        </div>
        <div class="fieldrow">
          <dt>最近导入（北京时间）</dt>
          <dd>{{ importTime(project.importedAt) }}</dd>
        </div>
        <div class="fieldrow">
          <dt>导入批次</dt>
          <dd>{{ project.importId }}</dd>
        </div>
      </dl>
    </section>
    <section
      v-if="tab === 'overview' || tab === 'business'"
      class="detailsection"
      aria-label="项目业务内容"
    >
      <h3>项目业务内容</h3>
      <ProjectBusinessContent :project="project" class="detailbiz" />
      <details class="all-fields">
        <summary>全部业务字段（含未明确值）</summary>
        <dl class="fieldgrid">
          <div
            v-for="[field, label] in [
              ['pvArea', '光伏面积（㎡）'],
              ['pvCapacity', '光伏规模（MW）'],
              ['storageCapacity', '储能规模（原表单位）'],
              ['chargingScale', '充电桩规模'],
              ['energyType', '能源类型'],
              ['energyScale', '能源规模'],
            ]"
            :key="field"
            class="fieldrow"
          >
            <dt>{{ label }}</dt>
            <dd>{{ metricValue(project[field]) }}</dd>
          </div>
        </dl>
      </details>
    </section>
    <section
      v-if="tab === 'overview' || tab === 'progress'"
      class="detailsection"
      aria-label="实施进度"
    >
      <h3>实施节点计划</h3>
      <p class="detail-resource">
        已完成 {{ project.completedCount }} / 11 个节点 · 目前所处阶段：{{
          displayValue(project.currentStage)
        }}
      </p>
      <ol class="stageitems">
        <li
          v-for="(name, index) in stages"
          :key="name"
          class="stageitem"
          :class="stageTone(project.stages[index])"
        >
          <b>{{ String(index + 1).padStart(2, '0') }} · {{ name }}</b
          ><span>{{ displayValue(project.stages[index]) }}</span>
        </li>
      </ol>
    </section>
    <div v-if="tab === 'overview' || tab === 'updates'" aria-label="实时情况">
      <section
        v-for="[field, label, tone] in [
          ['situation', '当前具体推进情况', ''],
          ['nextStep', '下一步打算', 'warm'],
          ['coordination', '需上级协调事项', 'plain'],
          ['progressUpdate', '是否有进度更新（AG 原值）', ''],
        ]"
        :key="field"
        class="detailsection"
      >
        <h3>{{ label }}</h3>
        <p class="detailparagraph" :class="tone">{{ displayValue(project[field]) }}</p>
      </section>
    </div>
  </article>
</template>
