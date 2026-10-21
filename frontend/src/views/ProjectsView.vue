<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import ProjectBoardCard from '../components/ProjectBoardCard.vue'
import ProjectReadOnlyDetail from '../components/ProjectReadOnlyDetail.vue'
import ProjectHistoryDialog from '../components/ProjectHistoryDialog.vue'
import { currentEmployee } from '../utils/authState'
import { acquireModalPageLock } from '../utils/modalPageLock'
import { RouterLink } from 'vue-router'
import { loadEmployeeProjectDetail, loadEmployeeProjects } from '../services/projects'
import { businessGroups, businessLabel } from '../utils/projectBoard'
import { importTime } from '../utils/projectDisplay'
import { beijingDay } from '../utils/projectUpdates'
import '../assets/project-board.css'

const views = [
  ['overview', '综合总览'],
  ['daily', '今日更新'],
  ['people', '负责人'],
  ['business', '项目业务'],
]
const view = ref('overview')
const updateDays = ref(1)
const updateClock = ref(new Date())
let clockTimer,
  serverClockOffset = 0
const overview = reactive({
  search: '',
  stage: '',
  district: '',
  owner: '',
  leader: '',
  priority: '',
  coordination: false,
  business: '',
})
const people = reactive({ role: 'owner', person: '' })
const businesses = ref([])
const peopleSelections = reactive({ leader: '', owner: '' })
const moreFilters = ref(false)
let searchTimer
const sort = ref('priority')
const data = ref({ projects: [], summary: {}, distribution: [], options: {}, stages: [] })
const loading = ref(false)
const error = ref('')
const detail = ref(null)
const drawer = ref(null)
const historyDialog = ref(null)
function showHistory(project, field = '') {
  historyDialog.value?.open(project, field)
}
const detailLoading = ref(false)
const detailError = ref('')
const visibleCount = ref(12)
let requestId = 0
let detailId = 0
let controller
let detailController
let disposed = false
let returnFocus
let releasePageLock
function lockBackground() {
  releasePageLock ||= acquireModalPageLock()
}
function unlockBackground() {
  releasePageLock?.()
  releasePageLock = null
}
const visible = computed(() => data.value.projects.slice(0, visibleCount.value))
const activeTags = computed(() => {
  if (view.value === 'business') return businesses.value.map(businessLabel)
  if (view.value === 'people')
    return people.person ? [(people.role === 'leader' ? '组长：' : '负责人：') + people.person] : []
  if (view.value !== 'overview') return []
  return [
    overview.business && businessLabel(overview.business),
    overview.owner && '负责人：' + overview.owner,
    overview.leader && '组长：' + overview.leader,
    overview.district,
    overview.stage,
    overview.priority,
    overview.coordination && '需协调',
    overview.search && '搜索：' + overview.search,
  ].filter(Boolean)
})
function scheduleSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(refresh, 250)
}
function choosePerson(person) {
  people.person = person
  peopleSelections[people.role] = person
  refresh()
}
function toggleBusiness(name) {
  businesses.value = businesses.value.includes(name)
    ? businesses.value.filter((item) => item !== name)
    : [...businesses.value, name]
  refresh()
}

async function refresh() {
  const id = ++requestId
  controller?.abort()
  controller = new AbortController()
  loading.value = true
  error.value = ''
  const filters = {
    view: view.value,
    sort: sort.value,
    ...(view.value === 'overview'
      ? overview
      : view.value === 'people'
        ? people
        : view.value === 'business'
          ? { business: businesses.value }
          : { update_days: updateDays.value }),
  }
  try {
    const result = await loadEmployeeProjects(filters, controller.signal)
    if (!disposed && id === requestId) {
      data.value = result
      if (result.updatesAsOf) {
        serverClockOffset = new Date(result.updatesAsOf).getTime() - Date.now()
        updateClock.value = new Date(Date.now() + serverClockOffset)
      }
      visibleCount.value = 12
    }
  } catch (cause) {
    if (!disposed && id === requestId && cause.name !== 'AbortError') error.value = cause.message
  } finally {
    if (!disposed && id === requestId) loading.value = false
  }
}
function changeView(value) {
  clearTimeout(searchTimer)
  view.value = value
  refresh()
}
function changeRole(role) {
  peopleSelections[people.role] = people.person
  people.role = role
  people.person = peopleSelections[role]
  refresh()
}
function reset() {
  if (view.value === 'business') {
    businesses.value = []
    refresh()
    return
  }
  if (view.value === 'people') {
    choosePerson('')
    return
  }
  if (view.value === 'daily') {
    updateDays.value = 1
    refresh()
    return
  }
  Object.assign(overview, {
    search: '',
    stage: '',
    district: '',
    owner: '',
    leader: '',
    priority: '',
    coordination: false,
    business: '',
  })
  people.person = ''
  businesses.value = []
  refresh()
}
async function showDetail(id) {
  const version = ++detailId
  detailController?.abort()
  detailController = new AbortController()
  detail.value = null
  detailError.value = ''
  detailLoading.value = true
  if (!drawer.value?.open) returnFocus = document.activeElement
  await nextTick()
  if (disposed || version !== detailId || !drawer.value) return
  try {
    if (!drawer.value.open) {
      lockBackground()
      drawer.value.showModal()
      drawer.value.querySelector('.closebtn')?.focus({ preventScroll: true })
    }
    const result = await loadEmployeeProjectDetail(id, detailController.signal)
    if (!disposed && version === detailId) detail.value = result
  } catch (cause) {
    if (!drawer.value?.open) unlockBackground()
    if (!disposed && version === detailId && cause.name !== 'AbortError')
      detailError.value = cause.message
  } finally {
    if (!disposed && version === detailId) detailLoading.value = false
  }
}
function closeDetail() {
  drawer.value?.close()
  closed()
}
function closed() {
  // A queued native close event must not cancel a newly reopened drawer.
  if (drawer.value?.open) return
  detailId++
  detailController?.abort()
  detail.value = null
  detailLoading.value = false
  unlockBackground()
  const target = returnFocus
  returnFocus = undefined
  if (!disposed && target?.isConnected) target.focus({ preventScroll: true })
}
function backdrop(event) {
  if (event.target === drawer.value) {
    const r = drawer.value.getBoundingClientRect()
    if (
      event.clientX < r.left ||
      event.clientX > r.right ||
      event.clientY < r.top ||
      event.clientY > r.bottom
    )
      closeDetail()
  }
}
onMounted(() => {
  refresh()
  clockTimer = setInterval(() => {
    const previous = beijingDay(updateClock.value)?.key
    updateClock.value = new Date(Date.now() + serverClockOffset)
    if (previous !== beijingDay(updateClock.value)?.key) refresh()
  }, 60000)
})
onBeforeUnmount(() => {
  clearInterval(clockTimer)
  clearTimeout(searchTimer)
  disposed = true
  controller?.abort()
  detailController?.abort()
  drawer.value?.close()
  closed()
})
</script>

<template>
  <main class="projects-portal">
    <header class="masthead">
      <div>
        <div class="eyebrow">市场开发 / 项目全周期跟踪</div>
        <h1 class="heading"><strong>项目推进看板</strong></h1>
        <p class="subtitle">从项目动态、责任人和业务方向切入，快速了解进度与待协调事项。</p>
      </div>
      <div class="meta-right">
        <RouterLink
          v-if="currentEmployee?.canEditProjects"
          class="project-create-link"
          to="/projects/new"
          >新增项目</RouterLink
        >
        <div>数据来源 <strong>已确认导入的 SQLite 台账</strong></div>
        <div>最近导入（北京时间）：{{ importTime(data.latestImport?.importedAt) }}</div>
        <button type="button" class="meta-refresh" :disabled="loading" @click="refresh">
          刷新数据
        </button>
      </div>
    </header>
    <nav class="tabs" aria-label="切换查看视角">
      <button
        v-for="[id, label] in views"
        :key="id"
        type="button"
        class="viewtab"
        :class="{ active: view === id }"
        :aria-pressed="view === id"
        @click="changeView(id)"
      >
        {{ label
        }}<span v-if="id === 'daily'" class="small-count">{{ data.summary.updated ?? 0 }}</span>
      </button>
    </nav>
    <section class="metrics" aria-label="项目概况">
      <div
        v-for="([key, label, note], index) in [
          ['total', '在库项目', '全体台账项目'],
          ['updated', '今日更新', '北京时间今日实际修改，按项目去重'],
          ['priority', '重点推进', '时序评级为甲'],
          ['coordination', '需协调项目', '填写了需上级协调事项'],
        ]"
        :key="key"
        class="metric"
        :class="{ 'metric-accent': index === 1 }"
      >
        <div class="metric-label">{{ label }}</div>
        <div class="metric-number">
          {{ String(data.summary[key] ?? 0).padStart(2, '0') }}<span>个项目</span>
        </div>
        <div class="metric-note">{{ note }}</div>
      </div>
    </section>
    <section v-if="view === 'daily'" class="scope scope-daily" aria-label="更新日期范围">
      <label class="scope-control"
        >更新范围（北京时间，含今日）
        <select v-model="updateDays" class="update-range-select" @change="refresh">
          <option :value="1">今日</option>
          <option :value="7">近 7 天</option>
          <option :value="30">近 30 天</option>
        </select>
      </label>
    </section>
    <section v-if="view === 'people'" class="scope" aria-label="负责人项目选择">
      <div class="scope-picks">
        <div class="scope-control">
          <span>选择人员，查看对应项目</span>
          <div class="scope-switch">
            <button
              v-for="[role, label] in [
                ['leader', '项目组长'],
                ['owner', '项目负责人'],
              ]"
              :key="role"
              type="button"
              :class="{ active: people.role === role }"
              :aria-pressed="people.role === role"
              @click="changeRole(role)"
            >
              {{ label }}
            </button>
          </div>
        </div>
        <div class="scope-pills">
          <button
            type="button"
            :class="{ active: !people.person }"
            :aria-pressed="!people.person"
            @click="choosePerson('')"
          >
            全部人员</button
          ><button
            v-for="name in data.options[people.role]"
            :key="name"
            type="button"
            :class="{ active: people.person === name }"
            :aria-pressed="people.person === name"
            @click="choosePerson(name)"
          >
            {{ name }} <b>{{ data.personCounts?.[people.role]?.[name] ?? 0 }}</b>
          </button>
        </div>
      </div>
    </section>
    <section v-if="view === 'business'" class="scope" aria-label="项目业务多选">
      <div class="scope-picks">
        <div class="scope-control">
          <span>按项目涉及的业务方向查看</span
          ><span class="biz-selected-summary" aria-live="polite">{{
            businesses.length
              ? '已选 ' + businesses.length + ' 类：' + businesses.map(businessLabel).join('、')
              : '未选择业务类型时，显示全部项目'
          }}</span>
        </div>
        <div class="scope-grid">
          <button
            v-for="group in businessGroups"
            :key="group.name"
            type="button"
            class="biz-pick"
            :class="{ active: businesses.includes(group.name) }"
            :aria-pressed="businesses.includes(group.name)"
            @click="toggleBusiness(group.name)"
          >
            <strong>{{ businessLabel(group.name) }}</strong
            ><small>{{ data.businessCounts?.[group.name] ?? 0 }} 项</small>
          </button>
        </div>
        <p class="biz-note">可同时选多类，按“包含任一所选业务”显示项目；再次点击已选项即可取消。</p>
      </div>
    </section>
    <form
      v-if="view === 'overview'"
      class="filterbar"
      aria-label="综合总览项目筛选"
      @submit.prevent="refresh"
    >
      <div class="filter-top">
        <input
          id="searchInput"
          v-model="overview.search"
          class="search-field"
          type="search"
          aria-label="搜索项目"
          maxlength="300"
          placeholder="搜索项目名称、资源来源、负责人……"
          autocomplete="off"
          @input="scheduleSearch"
        />
        <select
          id="businessFilter"
          v-model="overview.business"
          aria-label="业务类型"
          @change="refresh"
        >
          <option value="">全部业务类型</option>
          <option v-for="group in businessGroups" :key="group.name" :value="group.name">
            {{ businessLabel(group.name) }}
          </option>
        </select>
        <select id="ownerFilter" v-model="overview.owner" aria-label="项目负责人" @change="refresh">
          <option value="">全部项目负责人</option>
          <option v-for="name in data.options.owner" :key="name">{{ name }}</option>
        </select>
        <select id="stageFilter" v-model="overview.stage" aria-label="推进阶段" @change="refresh">
          <option value="">全部推进阶段</option>
          <option v-for="name in [...data.stages, '未明确']" :key="name">{{ name }}</option>
        </select>
        <button
          type="button"
          class="smallbtn"
          :aria-expanded="moreFilters"
          aria-controls="moreFilters"
          @click="moreFilters = !moreFilters"
        >
          更多筛选</button
        ><button type="button" class="resetbtn" @click="reset">重置</button>
      </div>
      <div id="moreFilters" class="filter-more" :hidden="!moreFilters">
        <label
          v-for="[field, label] in [
            ['leader', '项目组长'],
            ['district', '行政片区'],
            ['priority', '开发时序评级'],
          ]"
          :key="field"
          class="field"
          >{{ label
          }}<select v-model="overview[field]" @change="refresh">
            <option value="">全部</option>
            <option v-for="name in data.options[field]" :key="name">{{ name }}</option>
          </select></label
        ><label class="coord-check"
          ><input
            v-model="overview.coordination"
            type="checkbox"
            @change="refresh"
          />仅看需上级协调的项目</label
        >
      </div>
    </form>
    <div class="listbar">
      <h2>
        {{
          view === 'overview'
            ? '项目列表'
            : view === 'daily'
              ? '最近更新的项目'
              : view === 'people'
                ? '人员项目列表'
                : '业务项目列表'
        }}<small>共 {{ data.filteredCount ?? 0 }} 项</small>
      </h2>
      <div v-if="view !== 'daily'" class="list-controls">
        <label for="sortSelect">排序</label
        ><select id="sortSelect" v-model="sort" @change="refresh">
          <option value="priority">时序评级优先</option>
          <option value="updated">最近更新优先</option>
          <option value="name">项目名称</option>
        </select>
      </div>
    </div>
    <div v-if="activeTags.length" class="active-tags">
      <span v-for="tag in activeTags" :key="tag" class="active-tag">{{ tag }}</span>
    </div>
    <div v-if="loading" class="empty" role="status">正在加载项目…</div>
    <div v-else-if="error" class="empty" role="alert">
      <p>{{ error }}</p>
      <button type="button" @click="refresh">重试</button>
    </div>
    <div v-else class="cards">
      <div v-if="!data.projects.length" class="empty">
        <strong>{{ data.summary.total ? '当前没有符合条件的项目' : '暂无项目台账' }}</strong>
        <p>
          {{
            data.summary.total ? '请切换视角或调整筛选条件。' : '管理员确认导入台账后将在此显示。'
          }}
        </p>
        <button v-if="data.summary.total" type="button" @click="reset">重置当前筛选</button>
      </div>
      <ProjectBoardCard
        v-for="project in visible"
        :key="project.id"
        :project="project"
        :stages="data.stages"
        :now="updateClock"
        @detail="showDetail"
        @history="showHistory"
      /><button
        v-if="visibleCount < data.projects.length"
        type="button"
        class="pb-more"
        @click="visibleCount += 12"
      >
        显示更多项目
      </button>
    </div>
    <dialog
      ref="drawer"
      class="drawer"
      aria-labelledby="pb-detail-title"
      @click="backdrop"
      @close="closed"
      @cancel.prevent="closeDetail"
    >
      <header class="drawer-head">
        <strong>项目详情</strong
        ><button
          type="button"
          class="closebtn"
          aria-label="关闭项目详情"
          autofocus
          @click="closeDetail"
        >
          关闭
        </button>
      </header>
      <div class="drawer-inner">
        <h2 v-if="!detail" id="pb-detail-title">项目详情</h2>
        <p v-if="detailLoading" role="status">正在读取项目详情…</p>
        <p v-else-if="detailError" role="alert">{{ detailError }}</p>
        <ProjectReadOnlyDetail
          v-else-if="detail"
          :key="detail.id"
          :project="detail"
          :stages="data.stages"
          @history="showHistory"
        />
      </div>
    </dialog>
    <ProjectHistoryDialog ref="historyDialog" />
  </main>
</template>
