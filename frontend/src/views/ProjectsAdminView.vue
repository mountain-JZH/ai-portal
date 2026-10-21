<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import ProjectDashboard from '../components/ProjectDashboard.vue'
import ProjectDetail from '../components/ProjectDetail.vue'
import {
  cancelProjectPreview,
  confirmProjects,
  loadProjectDetail,
  loadProjects,
  previewProjects,
} from '../services/projects'
import { displayValue } from '../utils/projectDisplay'
import '../assets/projects.css'

const emptyData = () => ({
  summary: { total: 0, priority: 0, coordination: 0, operational: 0 },
  projects: [],
  coordination: [],
  distribution: [],
  districts: [],
  stages: [],
  businessFields: [],
  filteredCount: 0,
  latestImport: null,
})
const data = ref(emptyData())
const filters = reactive({ search: '', stage: '', district: '', focus: '' })
const loading = ref(true)
const error = ref('')
const success = ref('')
const detail = ref(null)
const detailBusy = ref(false)
const detailDialog = ref(null)
const importDialog = ref(null)
const preview = ref(null)
const importError = ref('')
const importBusy = ref(false)
const filename = ref('')
const fileInput = ref(null)
const importRowsShown = ref(20)
const shownImportRows = computed(() => (preview.value?.rows || []).slice(0, importRowsShown.value))
let disposed = false
let detailVersion = 0
let requestVersion = 0
let controller

async function refresh() {
  const version = ++requestVersion
  controller?.abort()
  controller = new AbortController()
  loading.value = true
  error.value = ''
  try {
    const result = await loadProjects(filters, controller.signal)
    if (!disposed && version === requestVersion) data.value = result
  } catch (failure) {
    if (!disposed && version === requestVersion && failure.name !== 'AbortError') {
      error.value = failure.message || '台账读取失败，请重试。'
      data.value = emptyData()
    }
  } finally {
    if (!disposed && version === requestVersion) loading.value = false
  }
}
function filter(field, value) {
  if (field === 'reset') Object.assign(filters, { search: '', stage: '', district: '', focus: '' })
  else filters[field] = value
  refresh()
}
async function showDetail(id) {
  const version = ++detailVersion
  detailBusy.value = true
  error.value = ''
  try {
    const result = await loadProjectDetail(id)
    if (!disposed && version === detailVersion) {
      detail.value = result
      await nextTick()
      detailDialog.value.showModal()
    }
  } catch (failure) {
    if (!disposed && version === detailVersion) error.value = failure.message
  } finally {
    if (!disposed && version === detailVersion) detailBusy.value = false
  }
}
function openImport() {
  importError.value = ''
  success.value = ''
  preview.value = null
  filename.value = ''
  importRowsShown.value = 20
  if (fileInput.value) fileInput.value.value = ''
  importDialog.value.showModal()
}
async function chooseFile(event) {
  const file = event.target.files?.[0]
  if (!file || importBusy.value) return
  importBusy.value = true
  importError.value = ''
  try {
    if (preview.value?.token) {
      try {
        await cancelProjectPreview(preview.value.token)
      } catch {
        /* Tokens expire without writing projects. */
      }
    }
    preview.value = null
    filename.value = file.name
    if (!/\.xlsx$/i.test(file.name) || file.size > 4 * 1024 * 1024) {
      importError.value = '请选择不超过 4 MB 的 .xlsx 台账。'
      return
    }
    const result = await previewProjects(file)
    if (!disposed) preview.value = result
  } catch (failure) {
    if (!disposed) importError.value = failure.message
  } finally {
    if (!disposed) importBusy.value = false
  }
}
async function closeImport() {
  if (importBusy.value) return
  if (preview.value?.token) {
    try {
      await cancelProjectPreview(preview.value.token)
    } catch {
      /* Expiry also prevents reuse. */
    }
  }
  preview.value = null
  importDialog.value.close()
}
async function confirmImport() {
  if (importBusy.value || !preview.value?.canConfirm || !preview.value.token) return
  importBusy.value = true
  importError.value = ''
  try {
    const result = await confirmProjects(preview.value.token)
    if (disposed) return
    preview.value = null
    importDialog.value.close()
    Object.assign(filters, { search: '', stage: '', district: '', focus: '' })
    success.value = `台账已导入：新增 ${result.counts.new} 项，更新 ${result.counts.updated} 项，未变化 ${result.counts.unchanged} 项。未出现的旧项目已保留。`
    await refresh()
  } catch (failure) {
    if (!disposed) {
      importError.value = failure.message
      if (failure.status === 409) preview.value = null
    }
  } finally {
    if (!disposed) importBusy.value = false
  }
}
onMounted(refresh)
onBeforeUnmount(() => {
  disposed = true
  detailVersion++
  controller?.abort()
})
</script>

<template>
  <main class="projects-page">
    <p v-if="error" class="project-message error" role="alert">
      {{ error }} <button type="button" @click="refresh">重新加载</button>
    </p>
    <p v-if="success" class="project-message success" role="status">{{ success }}</p>
    <p v-if="detailBusy" class="project-message" role="status">正在读取项目完整档案…</p>
    <ProjectDashboard
      :data="data"
      :filters="filters"
      :loading="loading"
      @import="openImport"
      @detail="showDetail"
      @filter="filter"
      @search="filter('search', $event)"
      @refresh="refresh"
    />

    <dialog
      ref="detailDialog"
      class="project-dialog project-detail-dialog"
      aria-labelledby="project-detail-title"
    >
      <div class="project-dialog-toolbar">
        <span>完整项目档案</span
        ><button type="button" autofocus aria-label="关闭项目详情" @click="detailDialog.close()">
          关闭 ×
        </button>
      </div>
      <ProjectDetail
        v-if="detail"
        :project="detail"
        :names="data.stages"
        :business-fields="data.businessFields"
      />
    </dialog>

    <dialog
      ref="importDialog"
      class="project-dialog project-import-dialog"
      aria-labelledby="project-import-title"
      @cancel.prevent="closeImport"
    >
      <div class="project-dialog-toolbar">
        <span>EXCEL IMPORT / 台账导入</span
        ><button
          type="button"
          :disabled="importBusy"
          aria-label="关闭导入窗口"
          @click="closeImport"
        >
          关闭 ×
        </button>
      </div>
      <div class="project-import-content">
        <h2 id="project-import-title">让台账，成为看板。</h2>
        <p class="projects-footnote">
          沿用原 Excel：Sheet1 · A～AG · 前三行为表头，第 4 行起为项目。核对预览后再确认写入。
        </p>
        <label class="project-file-zone"
          ><strong>选择最新项目台账</strong><span>.xlsx · 最大 4 MB · 保留原始多级表头</span
          ><input
            ref="fileInput"
            type="file"
            accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            :disabled="importBusy"
            aria-label="选择项目 Excel 台账"
            @change="chooseFile"
          /><small v-if="filename">{{ filename }}</small></label
        >
        <p v-if="importBusy" role="status" class="project-message">正在处理台账，请稍候…</p>
        <p v-if="importError" role="alert" class="project-message error">{{ importError }}</p>
        <template v-if="preview">
          <div class="project-import-counts">
            <div
              v-for="[field, label] in [
                ['valid', '有效项目'],
                ['new', '新增'],
                ['updated', '更新'],
                ['unchanged', '未变化'],
                ['invalid', '无效 / 占位行'],
              ]"
              :key="field"
            >
              <strong>{{ preview.counts[field] }}</strong
              ><span>{{ label }}</span>
            </div>
          </div>
          <div v-if="preview.errors.length" class="project-message error" role="alert">
            <strong>本批次暂不可导入，请修正台账后重新上传。</strong>
            <ul>
              <li v-for="(message, index) in preview.errors" :key="index">{{ message }}</li>
            </ul>
          </div>
          <details v-if="preview.warnings.length" open class="project-import-warnings">
            <summary>{{ preview.warnings.length }} 条核对提示 · 原始值将完整保留</summary>
            <ul>
              <li v-for="(message, index) in preview.warnings" :key="index">{{ message }}</li>
            </ul>
          </details>
          <div class="project-preview-table">
            <table>
              <caption>
                导入前核对项目（共
                {{
                  preview.rows.length
                }}
                项）
              </caption>
              <thead>
                <tr>
                  <th>Excel 行</th>
                  <th>项目名称 / 资源</th>
                  <th>负责人</th>
                  <th>当前阶段</th>
                  <th>处理结果</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in shownImportRows" :key="row.row">
                  <td>{{ row.row }}</td>
                  <td>
                    {{ row.project.name }}<small>{{ displayValue(row.project.resource) }}</small>
                  </td>
                  <td>{{ displayValue(row.project.owner) }}</td>
                  <td>{{ displayValue(row.project.currentStage) }}</td>
                  <td>{{ { new: '新增', updated: '更新', unchanged: '未变化' }[row.action] }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <button
            v-if="preview.rows.length > importRowsShown"
            type="button"
            class="project-text-button"
            @click="importRowsShown += 50"
          >
            查看更多预览行
          </button>
          <p class="projects-footnote">
            本次未出现的旧项目会继续保留。预览有效期为 30 分钟；项目台账变化后需重新预览。
          </p>
        </template>
        <div class="project-import-actions">
          <button type="button" class="project-button" :disabled="importBusy" @click="closeImport">
            取消</button
          ><button
            type="button"
            class="project-button primary"
            :disabled="importBusy || !preview?.canConfirm || !preview?.token"
            @click="confirmImport"
          >
            确认导入
          </button>
        </div>
      </div>
    </dialog>
  </main>
</template>
