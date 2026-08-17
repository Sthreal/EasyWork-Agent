<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, PieChart } from 'echarts/charts'
import { GridComponent, TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { listPending } from '../api/confirmation'
import { listTasks } from '../api/task'

echarts.use([BarChart, PieChart, GridComponent, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const pendingCount = ref(0)
const today = ref('')
const kpi = ref({ todayTasks: 0, successRate: '--', failed: 0, doing: 0 })
const statusRef = ref(null)
const trendRef = ref(null)
let statusChart = null
let trendChart = null

function fmtDate(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

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

    <!-- 待确认 / 最近任务（切片3填充） -->
    <div class="bottom-row">
      <div class="card"><h3>待确认队列</h3><p class="placeholder">切片 3 接入</p></div>
      <div class="card"><h3>最近任务</h3><p class="placeholder">切片 3 接入</p></div>
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
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.placeholder {
  color: var(--color-text-muted);
  font-size: 13px;
  padding: 30px 0;
  text-align: center;
}
@media (max-width: 900px) {
  .kpi-row, .chart-row, .bottom-row {
    grid-template-columns: 1fr;
  }
}
</style>
