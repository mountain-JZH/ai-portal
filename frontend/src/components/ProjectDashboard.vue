<script setup>
import { computed, ref, watch } from 'vue'
import ProjectStageProgress from './ProjectStageProgress.vue'
import { displayValue, importTime } from '../utils/projectDisplay'

const props = defineProps({
  data: { type: Object, required: true },
  filters: { type: Object, required: true },
  loading: Boolean,
})
const emit = defineEmits(['import', 'detail', 'filter', 'search', 'refresh'])
const visibleCount = ref(12)
watch(
  () => props.data,
  () => {
    visibleCount.value = 12
  },
)
const visibleProjects = computed(() => props.data.projects.slice(0, visibleCount.value))
const maxStage = computed(() => Math.max(1, ...props.data.distribution.map((stage) => stage.count)))
const metrics = [
  { key: 'total', label: '在库项目', caption: '有效项目 · 全部台账', filter: '', marker: '01' },
  {
    key: 'priority',
    label: '重点推进',
    caption: '时序评级含“尽快推进”',
    filter: 'priority',
    marker: '02',
  },
  {
    key: 'coordination',
    label: '需协调项目',
    caption: '已填写有效协调事项',
    filter: 'coordination',
    marker: '03',
  },
  {
    key: 'operational',
    label: '已投运项目',
    caption: '竣工投运节点明确已完成',
    filter: 'operational',
    marker: '04',
  },
]
</script>

<template>
  <div class="projects-dashboard" :aria-busy="loading">
    <header class="projects-heading">
      <div>
        <div class="projects-eyebrow"><span></span> MARKET DEVELOPMENT / 项目开发</div>
        <h1>项目推进<span>总览</span><i aria-hidden="true">↗</i></h1>
        <p>市场部项目开发 · 全周期进度与重点事项</p>
      </div>
      <div class="projects-heading-actions">
        <small
          >最近导入时间（北京时间）<strong>{{
            importTime(data.latestImport?.importedAt)
          }}</strong></small
        >
        <button class="project-button primary" type="button" @click="emit('import')">
          <span aria-hidden="true">＋</span> 导入最新台账
        </button>
      </div>
    </header>

    <div class="projects-metrics" aria-label="全部在库项目统计">
      <button
        v-for="metric in metrics"
        :key="metric.key"
        type="button"
        class="projects-metric"
        :class="{
          highlighted: metric.key === 'priority',
          selected: filters.focus === metric.filter && !!metric.filter,
        }"
        :aria-pressed="filters.focus === metric.filter"
        @click="emit('filter', 'focus', metric.filter)"
      >
        <span class="metric-top"
          >{{ metric.label }}<small>{{ metric.marker }}</small></span
        >
        <span class="metric-number"
          >{{ loading ? '—' : data.summary[metric.key] }}<small>项</small></span
        >
        <span class="metric-caption">{{ metric.caption }}<span aria-hidden="true">↗</span></span>
      </button>
    </div>

    <section class="projects-panel projects-distribution" aria-labelledby="project-stage-title">
      <div class="project-section-heading">
        <div>
          <span class="section-index">01 /</span>
          <h2 id="project-stage-title">项目实施阶段</h2>
        </div>
        <p>按台账当前阶段统计 · 点击筛选</p>
      </div>
      <div class="projects-stage-chart">
        <button
          v-for="(stage, index) in data.distribution"
          :key="stage.name"
          type="button"
          :class="{ selected: filters.stage === stage.name }"
          :aria-pressed="filters.stage === stage.name"
          @click="emit('filter', 'stage', filters.stage === stage.name ? '' : stage.name)"
        >
          <span class="stage-chart-label"
            ><small>{{ String(index + 1).padStart(2, '0') }}</small
            >{{ stage.name }}<strong>{{ stage.count }}</strong></span
          >
          <span class="stage-chart-track"
            ><span :style="{ width: `${(stage.count / maxStage) * 100}%` }"></span
          ></span>
        </button>
      </div>
      <p class="projects-footnote">
        每个项目仅计入一个当前阶段；缺失或无法匹配的原值归入“未明确”。
      </p>
    </section>

    <section class="projects-list-section" aria-labelledby="project-list-title">
      <div class="project-section-heading">
        <div>
          <span class="section-index">02 /</span>
          <h2 id="project-list-title">项目档案</h2>
          <span class="project-count">{{ data.filteredCount }} 项</span>
        </div>
        <button
          class="project-text-button"
          type="button"
          :disabled="loading"
          @click="emit('refresh')"
        >
          刷新台账 ↻
        </button>
      </div>
      <form
        class="projects-filters"
        @submit.prevent="emit('search', $event.target.elements.search.value)"
      >
        <label class="projects-search"
          ><span aria-hidden="true">⌕</span
          ><input
            name="search"
            :value="filters.search"
            placeholder="搜索项目、负责人、资源或推进情况"
            aria-label="搜索项目"
          /><button type="submit">搜索</button></label
        >
        <label
          ><span class="project-sr-only">当前阶段</span
          ><select
            :value="filters.stage"
            aria-label="当前阶段"
            @change="emit('filter', 'stage', $event.target.value)"
          >
            <option value="">全部阶段</option>
            <option v-for="stage in data.distribution" :key="stage.name">{{ stage.name }}</option>
          </select></label
        >
        <label
          ><span class="project-sr-only">行政片区</span
          ><select
            :value="filters.district"
            aria-label="行政片区"
            @change="emit('filter', 'district', $event.target.value)"
          >
            <option value="">全部片区</option>
            <option v-for="district in data.districts" :key="district">{{ district }}</option>
          </select></label
        >
        <label
          ><span class="project-sr-only">重点事项</span
          ><select
            :value="filters.focus"
            aria-label="重点事项"
            @change="emit('filter', 'focus', $event.target.value)"
          >
            <option value="">全部项目</option>
            <option value="priority">重点推进</option>
            <option value="coordination">需协调</option>
            <option value="operational">已投运</option>
          </select></label
        >
        <button
          v-if="Object.values(filters).some(Boolean)"
          class="project-text-button"
          type="button"
          @click="emit('filter', 'reset', '')"
        >
          清除筛选
        </button>
      </form>
      <div class="projects-legend">
        <span><i class="done"></i>已完成</span><span><i class="active"></i>进行中</span
        ><span><i class="blank"></i>未填写</span><span><i class="other"></i>其他原始状态</span>
      </div>
      <p v-if="loading" class="projects-empty" role="status">正在读取项目台账…</p>
      <div v-else-if="!data.projects.length" class="projects-empty">
        <span aria-hidden="true">▤</span>
        <h3>
          {{ data.summary.total ? '没有符合筛选条件的项目' : '从一份台账，开始看清项目全貌' }}
        </h3>
        <p>
          {{
            data.summary.total
              ? '请调整搜索词或清除筛选条件。'
              : '导入原有 Excel，自动整理实施节点、推进情况与下一步安排。'
          }}
        </p>
        <button
          v-if="!data.summary.total"
          type="button"
          class="project-button primary"
          @click="emit('import')"
        >
          导入首份项目台账
        </button>
      </div>
      <div v-else class="projects-card-grid">
        <button
          v-for="project in visibleProjects"
          :key="project.id"
          class="project-card"
          type="button"
          @click="emit('detail', project.id)"
        >
          <span class="project-card-top"
            ><span>{{ displayValue(project.district) }}</span
            ><span v-if="project.needsCoordination" class="coordination-tag">需协调</span
            ><span v-else class="project-card-number"
              >#{{ String(project.id).padStart(3, '0') }}</span
            ></span
          >
          <h3>{{ project.name }}</h3>
          <span class="project-card-owner">负责人 {{ displayValue(project.owner) }}</span>
          <span class="project-card-ratings"
            ><span>{{ displayValue(project.priority) }}</span
            ><span>{{ displayValue(project.valueRating) }}</span></span
          >
          <span class="project-card-stage"
            ><strong>{{ displayValue(project.currentStage) }}</strong
            ><span>已完成 {{ project.completedCount }} / 11 节点</span></span
          >
          <ProjectStageProgress :stages="project.stages" :names="data.stages" />
          <span class="project-card-copy"
            ><small>当前推进</small><span>{{ displayValue(project.situation) }}</span></span
          >
          <span class="project-card-copy"
            ><small>下一步</small><span>{{ displayValue(project.nextStep) }}</span></span
          >
          <span class="project-card-bottom">查看完整项目档案<span aria-hidden="true">↗</span></span>
        </button>
      </div>
      <button
        v-if="data.projects.length > visibleCount"
        type="button"
        class="project-button project-load-more"
        @click="visibleCount += 12"
      >
        查看更多项目（{{ visibleCount }} / {{ data.projects.length }}）
      </button>
    </section>

    <section class="projects-panel projects-coordination" aria-labelledby="coordination-title">
      <div class="project-section-heading">
        <div>
          <span class="section-index">03 /</span>
          <h2 id="coordination-title">需协调事项</h2>
          <span class="project-count">{{ data.coordination.length }} 项</span>
        </div>
        <p>全部台账 · 集中跟进，推动下一步</p>
      </div>
      <p v-if="!data.coordination.length" class="projects-footnote">
        暂无已填写的需上级协调事项。“无”、斜杠与空白均不计入。
      </p>
      <article
        v-for="project in data.coordination"
        :key="project.id"
        class="project-coordination-row"
      >
        <div>
          <button type="button" class="project-text-button" @click="emit('detail', project.id)">
            {{ project.name }} ↗</button
          ><small
            >{{ displayValue(project.owner) }} · {{ displayValue(project.currentStage) }}</small
          >
        </div>
        <p>{{ project.coordination }}</p>
      </article>
    </section>
    <footer class="projects-footer">
      PROJECT DEVELOPMENT <span>以原始台账为准 · 导入时间不代表业务更新时间</span>
    </footer>
  </div>
</template>
