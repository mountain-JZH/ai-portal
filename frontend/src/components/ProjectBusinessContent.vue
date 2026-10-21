<script setup>
import { computed } from 'vue'
import { groupsFor, businessLabel, businessPresentation } from '../utils/projectBoard'
const props = defineProps({ project: { type: Object, required: true } })
const groups = computed(() =>
  groupsFor(props.project).map((group) => ({
    ...group,
    ...businessPresentation(props.project, group),
  })),
)
</script>

<template>
  <div class="business-list">
    <section v-for="group in groups" :key="group.name" class="businessblock">
      <div class="biz-block-header">
        <h4>{{ businessLabel(group.name) }}</h4>
        <span v-if="group.classification" class="biz-block-type">{{ group.classification }}</span>
      </div>
      <div v-if="group.kpis.length" class="biz-kpis" :class="{ one: group.kpis.length === 1 }">
        <div v-for="(item, index) in group.kpis" :key="index" class="biz-kpi">
          <span class="biz-kpi-label">{{ item.label }}</span>
          <div class="biz-kpi-number">
            {{ item.number }}<span class="biz-kpi-unit">{{ item.unit }}</span>
          </div>
        </div>
      </div>
      <div v-for="(item, index) in group.descriptions" :key="index" class="biz-description">
        <span class="biz-description-label">{{ item.label }}</span>
        <div class="biz-description-content">{{ item.value }}</div>
      </div>
      <div v-if="!group.kpis.length && !group.descriptions.length" class="biz-block-empty">
        未填写业务规模
      </div>
    </section>
    <p v-if="!groups.length" class="businessnone">业务类型待确认</p>
  </div>
</template>
