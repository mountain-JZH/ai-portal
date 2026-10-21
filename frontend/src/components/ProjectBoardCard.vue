<script setup>
import { computed } from 'vue'
import ProjectBusinessContent from './ProjectBusinessContent.vue'
import ProjectUpdateBadge from './ProjectUpdateBadge.vue'
import { displayValue, stageTone } from '../utils/projectDisplay'
import { currentPosition, currentStageName, shortStages } from '../utils/projectBoard'
const props = defineProps({
  project: { type: Object, required: true },
  stages: { type: Array, required: true },
  now: { type: Date, default: () => new Date() },
})
defineEmits(['detail', 'history'])
const position = computed(() => currentPosition(props.project, props.stages))
const status = computed(() =>
  props.project.stages[10] === '已完成' && props.project.completedCount === 11
    ? '已完成'
    : position.value == null
      ? '未明确'
      : props.project.stages[position.value - 1] === '进行中'
        ? '进行中'
        : '当前阶段',
)
</script>

<template>
  <article class="project-card" :class="{ isupdated: project.updated }">
    <section class="cardcol card-left">
      <div class="card-topline">
        <span>项目 / {{ String(project.id).padStart(3, '0') }}</span>
        <ProjectUpdateBadge :at="project.latestBusinessUpdateAt" :now="now" />
      </div>
      <h2 class="project-title">{{ project.name }}</h2>
      <div class="project-resource">{{ displayValue(project.resource) }}</div>
      <div class="badges">
        <span class="pill priority">{{ displayValue(project.priority) }}</span
        ><span class="pill">{{ displayValue(project.valueRating) }}</span
        ><span v-for="name in project.businessTypes" :key="name" class="pill business">{{
          name
        }}</span>
      </div>
      <dl class="personrows">
        <div
          v-for="[field, label] in [
            ['leader', '项目组长'],
            ['owner', '项目负责人'],
            ['district', '片区'],
          ]"
          :key="field"
          class="personrow"
        >
          <dt>{{ label }}</dt>
          <dd>{{ displayValue(project[field]) }}</dd>
        </div>
      </dl>
    </section>
    <section class="cardcol card-mid">
      <div class="mid-label">推进状态</div>
      <div class="stage-head">
        <div class="fraction" aria-hidden="true">
          {{ String(project.completedCount).padStart(2, '0')
          }}<span class="fraction-divider">/</span
          ><em>{{ position == null ? '—' : String(position).padStart(2, '0') }}</em
          ><b>/11</b>
        </div>
      </div>
      <div class="fraction-note">
        已完成 {{ project.completedCount }} 个节点，{{
          position == null ? '当前节点未明确' : '当前第 ' + position + ' 个节点'
        }}
      </div>
      <h3 class="stage-title">
        {{ displayValue(currentStageName(project, stages))
        }}<span class="stage-status" :class="{ completed: status === '已完成' }">{{ status }}</span>
      </h3>
      <ol class="timeline-bars" aria-label="11 个实施节点的原始状态">
        <li
          v-for="(name, index) in stages"
          :key="name"
          class="timeline-unit"
          :title="name + ' · ' + displayValue(project.stages[index])"
        >
          <div class="timeline-rect" :class="stageTone(project.stages[index])"></div>
          <div class="timeline-name" :class="{ current: position === index + 1 }">
            {{ shortStages[index] }}
          </div>
          <span class="pb-sr">{{ name }}：{{ displayValue(project.stages[index]) }}</span>
        </li>
      </ol>
      <section class="reportbox">
        <h4 class="smallhead">当前实施情况</h4>
        <p>{{ displayValue(project.situation) }}</p>
        <button
          type="button"
          class="project-history-entry"
          :aria-label="`${project.name}：当前实施情况，查看历史`"
          @click="$emit('history', project, 'situation')"
        >
          <span class="project-history-hint">查看历史</span>
        </button>
      </section>
      <div class="actions">
        <section class="actionbox">
          <h4 class="smallhead">下一步</h4>
          <p>{{ displayValue(project.nextStep) }}</p>
          <button
            type="button"
            class="project-history-entry"
            :aria-label="`${project.name}：下一步，查看历史`"
            @click="$emit('history', project, 'nextStep')"
          >
            <span class="project-history-hint">查看历史</span>
          </button>
        </section>
        <section class="actionbox coord">
          <h4 class="smallhead">需上级协调事项</h4>
          <p :class="{ 'empty-coord': !project.needsCoordination }">
            {{
              project.coordination == null ? '暂无需协调事项' : displayValue(project.coordination)
            }}
          </p>
          <button
            type="button"
            class="project-history-entry"
            :aria-label="`${project.name}：需上级协调事项，查看历史`"
            @click="$emit('history', project, 'coordination')"
          >
            <span class="project-history-hint">查看历史</span>
          </button>
        </section>
      </div>
    </section>
    <section class="cardcol card-right">
      <div class="business-head">
        <strong>项目内容</strong><span>涉及 {{ project.businessTypes.length }} 类业务</span>
      </div>
      <ProjectBusinessContent :project="project" /><button
        type="button"
        class="detailsbtn"
        :aria-label="'查看' + project.name + '项目详情'"
        @click="$emit('detail', project.id)"
      >
        查看项目详情
      </button>
    </section>
  </article>
</template>

<style scoped>
.project-card .card-topline {
  justify-content: flex-start;
  align-items: center;
  gap: 8px;
  /* Preserve the original 10px / 1.5 number row and the title's vertical start. */
  height: 1.5em;
}
.project-card .card-topline > span {
  flex-shrink: 0;
}
</style>
