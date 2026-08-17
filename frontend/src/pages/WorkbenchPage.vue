<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, PieChart } from 'echarts/charts'
import { GridComponent, TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { listPending, decide, defer } from '../api/confirmation'
import { listTasks } from '../api/task'

echarts.use([BarChart, PieChart, GridComponent, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const emit = defineEmits(['pending-change'])

const pendingCount = ref(0)
const today = ref('')
const kpi = ref({ todayTasks: 0, successRate: '--', failed: 0, doing: 0 })
const statusRef = ref(null)
const trendRef = ref(null)
let statusChart = null
let trendChart = null

// 待确认
const confs = ref([])
const expanded = ref(new Set())
// 最近任务
const q = ref('')
const statusFilter = ref('all')
const taskItems = ref([])

function fmtDate(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function taskBadge(status) {
  switch (status) {
    case 'executed': return { text: '✅ 已完成', cls: 'badge-success' }
    case 'failed': return { text: '❌ 失败', cls: 'badge-danger' }
    case 'pending_confirm': return { text: '⏳ 待确认', cls: 'badge-warning' }
    case 'need_clarify': return { text: '❓ 待澄清', cls: 'badge-warning' }
    case 'rejected': return { text: '🚫 已拒绝', cls: 'badge-muted' }
    default: return { text: '已提交', cls: 'badge-muted' }
  }
}

function fmtTime(iso) {
  if (!iso) return ''
  return iso.replace('T', ' ').slice(0, 16)
}

// ===== 待确认 =====
function toggleConf(id) {
  const s = new Set(expanded.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  expanded.value = s
}

async function loadConfs() {
  try {
    confs.value = await listPending()
  } catch {
    confs.value = []
  }
  pendingCount.value = confs.value.length
}

async function actConf(conf, action) {
  try {
    if (action === 'approve') await decide(conf.id, true)
    else if (action === 'reject') await decide(conf.id, false)
    else await defer(conf.id)
  } catch (e) {
    alert('操作失败：' + (e.message || e))
  }
  await loadConfs()
  emit('pending-change')
}

// ===== 最近任务 =====
async function loadTasks() {
  const params = { limit: 50 }
  if (q.value.trim()) params.q = q.value.trim()
  if (statusFilter.value === 'doing') params.status = 'planned,need_clarify,pending_confirm'
  else if (statusFilter.value === 'done') params.status = 'executed,failed,rejected'
  try {
    const res = await listTasks(params)
    taskItems.value = res.items
  } catch {
    taskItems.value = []
  }
}
watch(q, loadTasks)
watch(statusFilter, loadTasks)

// ===== 滚动条：滚动时才显示 =====
function flashScrollbar(e) {
  const el = e.currentTarget
  el.classList.add('scrolling')
  clearTimeout(el._scrollTimer)
  el._scrollTimer = setTimeout(() => el.classList.remove('scrolling'), 400)
}

// ===== KPI / 图表 =====
async function loadAll() {
  const now = new Date()
  today.value = now.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
  const todayStr = fmtDate(now)
  const weekAgo = new Date(now)
  weekAgo.setDate(now.getDate() - 6)

  const [pending, recent, todayRes, weekRes] = await Promise.all([
    listPending().catch(() => []),
    listTasks({ limit: 200 }).catch(() => ({ items: [], total: 0 })),
    listTasks({ dateFrom: todayStr, dateTo: todayStr, limit: 200 }).catch(() => ({ items: [], total: 0 })),
    listTasks({ dateFrom: fmtDate(weekAgo), dateTo: todayStr, limit: 500 }).catch(() => ({ items: [], total: 0 })),
  ])
  pendingCount.value = pending.length
  confs.value = pending
  kpi.value.todayTasks = todayRes.total || 0
  const done = recent.items.filter((t) => t.status === 'executed').length
  const failed = recent.items.filter((t) => t.status === 'failed').length
  const doing = recent.items.filter((t) => ['pending_confirm', 'need_clarify', 'planned'].includes(t.status)).length
  kpi.value.failed = failed
  kpi.value.doing = doing
  kpi.value.successRate = done + failed > 0 ? Math.round((done / (done + failed)) * 100) : '--'
  renderStatus(recent.items)
  renderTrend(weekRes.items)
}

function renderStatus(items) {
  if (!statusChart || !statusRef.value) return
  const count = (s) => items.filter((t) => t.status === s).length
  const done = count('executed')
  const doing = items.filter((t) => ['pending_confirm', 'need_clarify', 'planned'].includes(t.status)).length
  const failed = count('failed')
  const rejected = count('rejected')
  statusChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, icon: 'circle', textStyle: { fontSize: 11 } },
    series: [
      {
        type: 'pie',
        radius: ['48%', '72%'],
        center: ['50%', '44%'],
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { formatter: '{b} {c}', fontSize: 11 },
        data: [
          { value: done, name: '已完成', itemStyle: { color: '#00b42a' } },
          { value: doing, name: '进行中', itemStyle: { color: '#ff8800' } },
          { value: failed, name: '失败', itemStyle: { color: '#e64340' } },
          { value: rejected, name: '已拒绝', itemStyle: { color: '#c9cdd4' } },
        ].filter((d) => d.value > 0),
      },
    ],
  })
}

function renderTrend(items) {
  if (!trendChart || !trendRef.value) return
  const map = {}
  items.forEach((t) => {
    const d = (t.created_at || '').slice(0, 10)
    if (d) map[d] = (map[d] || 0) + 1
  })
  const days = []
  const values = []
  for (let i = 6; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    const key = fmtDate(d)
    days.push(key.slice(5))
    values.push(map[key] || 0)
  }
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 16, top: 16, bottom: 28 },
    xAxis: { type: 'category', data: days, axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', minInterval: 1, axisLabel: { fontSize: 11 } },
    series: [
      {
        type: 'bar',
        data: values,
        itemStyle: { color: '#3370ff', borderRadius: [3, 3, 0, 0] },
        label: { show: true, position: 'top', fontSize: 10 },
      },
    ],
  })
}

function initCharts() {
  if (statusRef.value) statusChart = echarts.init(statusRef.value)
  if (trendRef.value) trendChart = echarts.init(trendRef.value)
  loadAll()
  loadTasks()
}

function onResize() {
  if (statusChart) statusChart.resize()
  if (trendChart) trendChart.resize()
}

onMounted(() => {
  initCharts()
  window.addEventListener('resize', onResize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  if (statusChart) statusChart.dispose()
  if (trendChart) trendChart.dispose()
})
</script>

<template>
  <div class="wb">
    <header class="wb-head">
      <div>
        <h1>工作台</h1>
        <p class="date">{{ today }}</p>
      </div>
      <span class="badge badge-pending">待确认 {{ pendingCount }}</span>
    </header>

    <!-- KPI -->
    <div class="kpi-row">
      <div class="kpi">
        <div class="label">今日任务</div>
        <div class="value">{{ kpi.todayTasks }}</div>
        <div class="trend muted">按创建时间统计</div>
      </div>
      <div class="kpi">
        <div class="label">待确认</div>
        <div class="value">{{ pendingCount }}</div>
        <div class="trend" :class="pendingCount ? 'warn' : 'ok'">{{ pendingCount ? '⚠ 有待处理' : '✓ 已清空' }}</div>
      </div>
      <div class="kpi">
        <div class="label">任务成功率</div>
        <div class="value">{{ kpi.successRate }}<span class="unit">%</span></div>
        <div class="trend muted">已完成 / (已完成+失败)</div>
      </div>
      <div class="kpi">
        <div class="label">失败 / 进行中</div>
        <div class="value">{{ kpi.failed }}<span class="unit"> / {{ kpi.doing }}</span></div>
        <div class="trend" :class="kpi.failed ? 'warn' : 'ok'">{{ kpi.failed ? '⚠ 有失败任务' : '✓ 无失败' }}</div>
      </div>
    </div>

    <!-- 图表 -->
    <div class="chart-row">
      <div class="card"><h3>任务状态分布</h3><div ref="statusRef" class="chart-box"></div></div>
      <div class="card"><h3>近 7 天任务量</h3><div ref="trendRef" class="chart-box"></div></div>
    </div>

    <!-- 待确认 / 最近任务 -->
    <div class="bottom-row">
      <div class="card">
        <h3>待确认队列</h3>
        <div class="scroll conf-scroll" @scroll="flashScrollbar">
          <div class="scroll-inner">
            <div v-if="!confs.length" class="empty">🎉 暂无待确认动作</div>
            <div v-for="c in confs" :key="c.id" class="conf-item">
              <div class="conf-head" @click="toggleConf(c.id)">
                <span class="badge badge-danger">高危</span>
                <span v-if="c.is_expired" class="badge badge-muted">超时挂起</span>
                <span class="conf-line"><b>{{ c.action }}</b> {{ c.target }}</span>
                <span class="arrow">▾</span>
              </div>
              <div v-if="expanded.has(c.id)" class="conf-detail">
                <p v-if="c.params" class="conf-preview">📋 {{ c.params }}</p>
                <table v-if="c.preview && c.preview.length" class="diff-table">
                  <thead><tr><th>位置</th><th>原值</th><th>新值</th></tr></thead>
                  <tbody>
                    <tr v-for="(d, i) in c.preview" :key="i">
                      <td>第{{ d.row }}行{{ d.column }}列</td>
                      <td class="old">{{ d.old }}</td>
                      <td class="new">{{ d.new }}</td>
                    </tr>
                  </tbody>
                </table>
                <div class="conf-actions">
                  <button class="btn btn-danger btn-sm" @click="actConf(c, 'approve')">确认执行</button>
                  <button class="btn btn-sm" @click="actConf(c, 'reject')">拒绝</button>
                  <button class="btn btn-sm" @click="actConf(c, 'defer')">稍后</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <h3>最近任务</h3>
        <div class="toolbar">
          <input v-model="q" placeholder="搜索任务内容…" />
          <select v-model="statusFilter">
            <option value="all">全部</option>
            <option value="doing">进行中</option>
            <option value="done">已完成</option>
          </select>
        </div>
        <div class="scroll task-scroll" @scroll="flashScrollbar">
          <div class="scroll-inner">
            <div v-if="!taskItems.length" class="empty">无匹配任务</div>
            <div v-for="t in taskItems" :key="t.task_id" class="task-item">
              <span class="task-text">#{{ t.task_id }} {{ t.text }}</span>
              <span class="badge" :class="taskBadge(t.status).cls">{{ taskBadge(t.status).text }}</span>
              <span class="task-time">{{ fmtTime(t.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.wb {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 28px;
}
.wb-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.wb-head h1 {
  font-size: 20px;
  margin: 0 0 4px;
}
.date {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-secondary);
}
.badge-pending {
  background: var(--color-warning-light);
  color: var(--color-warning);
  font-size: 13px;
  padding: 5px 12px;
  border-radius: 999px;
}
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.kpi {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  box-shadow: var(--shadow-card);
}
.kpi .label {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}
.kpi .value {
  font-size: 28px;
  font-weight: 700;
}
.kpi .unit {
  font-size: 14px;
  font-weight: 400;
  color: var(--color-text-secondary);
}
.kpi .trend {
  font-size: 12px;
  margin-top: 6px;
}
.trend.ok { color: var(--color-success); }
.trend.warn { color: var(--color-warning); }
.trend.muted { color: var(--color-text-muted); }
.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}
.card {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  box-shadow: var(--shadow-card);
}
.card h3 {
  font-size: 15px;
  margin: 0 0 12px;
}
.chart-box {
  width: 100%;
  height: 240px;
}
.bottom-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

/* 滚动区域：固定高度 + 内容不满也能滚（40px 余量）+ overscroll 隔离 + 滚动条滚动时才显示 */
.scroll {
  height: 300px;
  overflow-y: scroll;
  overscroll-behavior: contain;
  scrollbar-width: thin;
  scrollbar-color: transparent transparent;
}
.scroll::-webkit-scrollbar { width: 6px; }
.scroll::-webkit-scrollbar-track { background: transparent; }
.scroll::-webkit-scrollbar-thumb { background: transparent; border-radius: 3px; }
.scroll.scrolling::-webkit-scrollbar-thumb { background: rgba(134, 144, 156, 0.55); }
.scroll.scrolling { scrollbar-color: rgba(134, 144, 156, 0.55) transparent; }
.scroll-inner { min-height: 100%; padding-bottom: 40px; }
.empty {
  color: var(--color-text-muted);
  font-size: 13px;
  padding: 24px 0;
  text-align: center;
}

/* 待确认 */
.conf-item {
  border: 1px solid var(--color-border);
  border-radius: 10px;
  margin-bottom: 8px;
  overflow: hidden;
}
.conf-head {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 11px 14px;
  cursor: pointer;
}
.conf-head:hover { background: var(--color-bg); }
.conf-line { flex: 1; font-size: 14px; }
.arrow { color: var(--color-text-muted); font-size: 11px; transition: transform 0.15s; }
.conf-detail {
  padding: 0 14px 12px;
  border-top: 1px dashed var(--color-border-light);
}
.conf-preview {
  font-size: 12px;
  color: var(--color-warning);
  background: var(--color-warning-light);
  border-radius: 6px;
  padding: 6px 10px;
  margin: 10px 0 8px;
}
.diff-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  margin-bottom: 8px;
}
.diff-table th, .diff-table td {
  border: 1px solid var(--color-border);
  padding: 5px 8px;
  text-align: left;
}
.diff-table th { background: var(--color-bg); font-weight: 600; }
.diff-table .old { color: var(--color-danger); text-decoration: line-through; }
.diff-table .new { color: var(--color-success); font-weight: 600; }
.conf-actions { display: flex; gap: 8px; }

/* 徽标 / 按钮 / 最近任务 */
.badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
}
.badge-danger { background: var(--color-danger-light); color: var(--color-danger); }
.badge-warning { background: var(--color-warning-light); color: var(--color-warning); }
.badge-success { background: var(--color-success-light); color: var(--color-success); }
.badge-muted { background: var(--color-bg); color: var(--color-text-secondary); }
.btn {
  border: 1px solid var(--color-border);
  background: var(--color-card);
  color: var(--color-text);
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
}
.btn-danger { background: var(--color-danger); border-color: var(--color-danger); color: #fff; }
.btn-sm { padding: 5px 10px; }

.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.toolbar input {
  flex: 1;
  min-width: 0;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 7px 12px;
  font-size: 13px;
  outline: none;
  font-family: inherit;
}
.toolbar select {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 7px 8px;
  font-size: 13px;
  background: var(--color-card);
  font-family: inherit;
}
.task-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 6px;
  border-bottom: 1px solid var(--color-border-light);
  font-size: 13px;
}
.task-item:last-child { border-bottom: none; }
.task-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.task-time {
  color: var(--color-text-muted);
  font-size: 12px;
  white-space: nowrap;
}

@media (max-width: 900px) {
  .kpi-row, .chart-row, .bottom-row {
    grid-template-columns: 1fr;
  }
}
</style>
