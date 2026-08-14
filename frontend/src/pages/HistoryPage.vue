<script setup>
import { ref, onMounted } from 'vue'
import { listTasks, exportTasksCsv, createTask } from '../api/task'

const props = defineProps({ user: { type: Object, required: true } })
const emit = defineEmits(['back'])

const items = ref([])
const total = ref(0)
const loading = ref(false)
const expanded = ref({})

const q = ref('')
const statusSel = ref('all') // all / active / done
const dateFrom = ref('')
const dateTo = ref('')

const STATUS_MAP = {
  all: '',
  active: 'need_clarify,planned,pending_confirm',
  done: 'executed,failed,rejected',
}

async function load() {
  loading.value = true
  try {
    const res = await listTasks({
      userId: props.user.user_id,
      q: q.value.trim() || undefined,
      status: STATUS_MAP[statusSel.value] || undefined,
      dateFrom: dateFrom.value || undefined,
      dateTo: dateTo.value || undefined,
      limit: 200,
    })
    items.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  q.value = ''
  statusSel.value = 'all'
  dateFrom.value = ''
  dateTo.value = ''
  load()
}

function exportCsv() {
  exportTasksCsv(items.value)
}

async function resend(t) {
  if (!confirm(`重新提交该任务？\n${t.text}`)) return
  try {
    const result = await createTask(t.text, 1, props.user.user_id, true)
    alert(`已重新提交，生成新任务 ID：${result.task_id}`)
    load()
  } catch (e) {
    alert(`重发失败：${e.message || e}`)
  }
}

function statusBadge(s) {
  switch (s) {
    case 'executed':
      return { text: '✅ 已完成', cls: 'badge-success' }
    case 'failed':
      return { text: '❌ 失败', cls: 'badge-danger' }
    case 'pending_confirm':
      return { text: '⏳ 待确认', cls: 'badge-warning' }
    case 'need_clarify':
      return { text: '❓ 待澄清', cls: 'badge-warning' }
    case 'rejected':
      return { text: '🚫 已拒绝', cls: 'badge-muted' }
    default:
      return { text: s || '已提交', cls: 'badge-muted' }
  }
}

function taskResult(t) {
  try {
    const r = JSON.parse(t.result || '')
    return r.message || ''
  } catch {
    return ''
  }
}

function fmt(created) {
  return created ? created.slice(0, 19).replace('T', ' ') : ''
}

onMounted(load)
</script>

<template>
  <main class="history">
    <header class="page-header">
      <h2>任务历史 <span v-if="total" class="total">（{{ total }}）</span></h2>
      <button class="btn btn-sm" @click="load">刷新</button>
    </header>

    <div class="filter">
      <input v-model="q" class="input" placeholder="搜索任务内容…" @keyup.enter="load" />
      <select v-model="statusSel" class="input select">
        <option value="all">全部状态</option>
        <option value="active">进行中</option>
        <option value="done">已完成</option>
      </select>
      <input v-model="dateFrom" type="date" class="input" @change="load" />
      <span class="sep">至</span>
      <input v-model="dateTo" type="date" class="input" @change="load" />
      <button class="btn btn-sm" @click="load">筛选</button>
      <button class="btn btn-sm" @click="resetFilters">重置</button>
      <button class="btn btn-sm" :disabled="!items.length" @click="exportCsv">导出 CSV</button>
    </div>

    <p v-if="!loading && items.length === 0" class="empty">暂无任务</p>
    <div v-for="t in items" :key="t.task_id" class="item">
      <div class="row" @click="expanded[t.task_id] = !expanded[t.task_id]">
        <span class="text">{{ t.text }}</span>
        <button class="btn btn-sm resend" @click.stop="resend(t)">重发</button>
        <span class="badge" :class="statusBadge(t.status).cls">{{ statusBadge(t.status).text }}</span>
        <span class="meta">{{ fmt(t.created_at) }}</span>
      </div>
      <div v-if="expanded[t.task_id]" class="detail">
        <p v-if="t.question" class="q">❓ {{ t.question }}</p>
        <ul v-if="t.tasks && t.tasks.length" class="steps">
          <li v-for="(s, i) in t.tasks" :key="i" class="step">
            <span class="step-no">{{ i + 1 }}</span>
            <span class="step-action">{{ s.action }}<template v-if="s.target"> {{ s.target }}</template></span>
            <span v-if="s.high_risk" class="badge badge-danger">高危</span>
            <span class="badge" :class="statusBadge(s.status).cls">{{ statusBadge(s.status).text }}</span>
            <span v-if="taskResult(s)" class="step-result">{{ taskResult(s) }}</span>
          </li>
        </ul>
      </div>
    </div>
  </main>
</template>

<style scoped>
.history {
  padding: 24px;
  max-width: var(--content-max-width);
  margin: 0 auto;
}
.filter {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.input {
  padding: 7px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-card);
  color: var(--color-text);
  font-family: inherit;
  font-size: 13px;
}
.input:first-child {
  min-width: 180px;
  flex: 1;
}
.select {
  min-width: 110px;
}
.sep {
  color: var(--color-text-secondary);
  font-size: 13px;
}
.total {
  font-size: 13px;
  color: var(--color-text-secondary);
  font-weight: 400;
}
.item {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  margin-bottom: 10px;
  overflow: hidden;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.item:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-card);
}
.row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 16px;
  cursor: pointer;
}
.text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.resend {
  flex-shrink: 0;
}
.meta {
  color: var(--color-text-secondary);
  font-size: 12px;
  white-space: nowrap;
}
.detail {
  padding: 4px 16px 12px;
  border-top: 1px solid var(--color-border-light);
  background: var(--color-bg);
}
.q {
  margin: 8px 0;
  color: var(--color-warning);
}
.steps {
  padding: 0;
  margin: 8px 0 0;
}
.step {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
  padding: 7px 0;
  border-bottom: 1px solid var(--color-border-light);
}
.step:last-child {
  border-bottom: none;
}
.step-no {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-card);
  color: var(--color-text-secondary);
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.step-action {
  flex: 1;
  min-width: 0;
}
.step-result {
  width: 100%;
  padding-left: 28px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
</style>