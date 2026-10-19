<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import {
  loadAdminExchangeResources,
  loadAdminExchangeDetail,
  deleteExchangeResource,
} from '../services/exchange'
import { formatExchangeTimestamp, safeUrl } from '../utils/exchangeDiscovery'

const items = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(true)
const detailLoading = ref(false)
const deletingId = ref(null)
const selected = ref(null)
const errorMessage = ref('')
const successMessage = ref('')
let disposed = false
let detailVersion = 0

async function refresh() {
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await loadAdminExchangeResources(page.value)
    if (disposed) return
    items.value = data.items
    total.value = data.total
  } catch (error) {
    if (!disposed) errorMessage.value = error.message || '读取管理列表失败。'
  } finally {
    if (!disposed) loading.value = false
  }
}
async function changePage(delta) {
  if (loading.value || deletingId.value !== null) return
  page.value += delta
  await refresh()
}
async function viewDetail(item) {
  const version = ++detailVersion
  detailLoading.value = true
  errorMessage.value = ''
  try {
    const detail = await loadAdminExchangeDetail(item.id)
    if (!disposed && version === detailVersion) selected.value = detail
  } catch (error) {
    if (!disposed && version === detailVersion) {
      errorMessage.value = error.message
      if (error.status === 404) selected.value = null
    }
  } finally {
    if (!disposed && version === detailVersion) detailLoading.value = false
  }
}
async function remove(item) {
  if (deletingId.value !== null) return
  if (!window.confirm(`确定删除 ${item.displayNumber} 号分享吗？删除后将不再出现在互通有无中。`))
    return
  deletingId.value = item.id
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const result = await deleteExchangeResource(item.id)
    if (disposed) return
    if (selected.value?.id === item.id) selected.value = null
    detailVersion += 1
    detailLoading.value = false
    if (items.value.length === 1 && page.value > 1) page.value -= 1
    await refresh()
    successMessage.value = result.imageCleanupPending
      ? `${item.displayNumber} 号分享已删除，图片清理失败，请检查服务端日志。`
      : `${item.displayNumber} 号分享已删除。`
  } catch (error) {
    if (disposed) return
    if (error.status === 404) {
      if (selected.value?.id === item.id) selected.value = null
      await refresh()
    }
    errorMessage.value = error.message || '删除失败，请重试。'
  } finally {
    if (!disposed) deletingId.value = null
  }
}
onMounted(refresh)
onBeforeUnmount(() => {
  disposed = true
  detailVersion += 1
})
</script>

<template>
  <main class="content-admin-page exchange-admin">
    <div class="content-page-header">
      <div>
        <span>PORTAL CONTENT</span>
        <h1>互通有无管理</h1>
        <p>查看已发布分享，删除不适宜的内容。时间以北京时间显示。</p>
      </div>
    </div>
    <p v-if="successMessage" class="content-status-message content-status-success" role="status">
      {{ successMessage }}
    </p>
    <p v-if="errorMessage" class="content-status-message content-status-error" role="alert">
      {{ errorMessage }}
    </p>
    <section v-if="loading" class="content-page-state" role="status">正在加载分享…</section>
    <section v-else-if="!items.length" class="content-page-state">暂无分享。</section>
    <div v-else class="content-table-card">
      <div class="content-table-scroll">
        <table class="content-table">
          <thead>
            <tr>
              <th>编号</th>
              <th>标题</th>
              <th>领域</th>
              <th>类型</th>
              <th>提交时间</th>
              <th>图片</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id">
              <td>{{ item.displayNumber }}</td>
              <td class="content-title-cell">
                <strong>{{ item.title }}</strong>
              </td>
              <td>{{ item.domain }}</td>
              <td>{{ item.type }}</td>
              <td>{{ formatExchangeTimestamp(item.createdAt) }}</td>
              <td>{{ item.imageUrl ? '有' : '无' }}</td>
              <td>
                <div class="content-row-actions">
                  <button
                    type="button"
                    :disabled="detailLoading || deletingId !== null"
                    @click="viewDetail(item)"
                  >
                    查看</button
                  ><button
                    type="button"
                    class="delete-action"
                    :disabled="deletingId !== null"
                    @click="remove(item)"
                  >
                    {{ deletingId === item.id ? '删除中…' : '删除' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="exchange-pagination">
      <button
        type="button"
        :disabled="page <= 1 || loading || deletingId !== null"
        @click="changePage(-1)"
      >
        上一页</button
      ><span>第 {{ page }} 页 · {{ total }} 条</span
      ><button
        type="button"
        :disabled="page * 20 >= total || loading || deletingId !== null"
        @click="changePage(1)"
      >
        下一页</button
      ><button type="button" :disabled="loading || deletingId !== null" @click="refresh">
        刷新
      </button>
    </div>
    <p v-if="detailLoading" role="status">正在读取完整内容…</p>
    <section v-if="selected" class="exchange-admin-detail" aria-labelledby="exchange-detail-title">
      <div class="detail-heading">
        <h2 id="exchange-detail-title">{{ selected.displayNumber }} · {{ selected.title }}</h2>
        <button type="button" @click="selected = null">关闭详情</button>
      </div>
      <p>
        {{ selected.domain }} · {{ selected.type }} ·
        {{ formatExchangeTimestamp(selected.createdAt) }}（北京时间）
      </p>
      <h3>描述</h3>
      <p class="full-text">{{ selected.description }}</p>
      <template v-if="selected.reason"
        ><h3>推荐原因</h3>
        <p class="full-text">{{ selected.reason }}</p></template
      >
      <img v-if="selected.imageUrl" :src="selected.imageUrl" alt="已保存的分享封面" />
      <a
        v-if="safeUrl(selected.externalUrl)"
        :href="safeUrl(selected.externalUrl)"
        target="_blank"
        rel="noopener noreferrer"
        >外部跳转 ↗</a
      >
      <p v-if="selected.tags.length">关键词：{{ selected.tags.join('、') }}</p>
      <button
        type="button"
        class="delete-action"
        :disabled="deletingId !== null"
        @click="remove(selected)"
      >
        删除这份分享
      </button>
    </section>
  </main>
</template>

<style scoped>
.exchange-pagination {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin: 20px 0;
  font-size: 13px;
}
button {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font: inherit;
  font-size: 13px;
}
button:disabled {
  opacity: 0.5;
  cursor: default;
}
.delete-action {
  color: #a53434;
}
.exchange-admin-detail {
  padding: 24px;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: #fff;
  overflow-wrap: anywhere;
}
.detail-heading {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 16px;
}
h2 {
  margin: 0 0 16px;
  font-size: 20px;
}
h3 {
  margin: 24px 0 8px;
  font-size: 15px;
}
p {
  font-size: 14px;
  line-height: 1.8;
}
.full-text {
  white-space: pre-wrap;
}
img {
  display: block;
  max-width: 100%;
  width: 440px;
  height: auto;
  margin: 24px 0;
  border-radius: 8px;
}
a {
  display: inline-block;
  margin: 12px 0;
}
@media (max-width: 500px) {
  .exchange-admin-detail {
    padding: 16px;
  }
  .detail-heading {
    flex-direction: column;
  }
}
</style>
