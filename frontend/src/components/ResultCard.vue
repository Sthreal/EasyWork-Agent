<script setup>
import { ref } from 'vue'
import { decide, defer } from '../api/confirmation'
import ChartBlock from './ChartBlock.vue'

defineProps({ message: { type: Object, default: null } })
const emit = defineEmits(['pending-change'])

// confirmation_id -> approved | rejected | deferred（本次会话内的操作结果）
const acted = ref({})

function needsInline(t) {
  return t && t.high_risk && t.confirmation_id != null && t.in_workspace === true && t.status === 'pending_confirm'
}

function actText(t) {
  const st = acted.value[t.confirmation_id]
  if (st === 'approved') return '✅ 已确认执行'
  if (st === 'rejected') return '🚫 已拒绝'
  if (st === 'deferred') return '📥 已转待确认，可到待确认页处理'
  return ''
}

async function onApprove(t) {
  await decide(t.confirmation_id, true)
  acted.value[t.confirmation_id] = 'approved'
  emit('pending-change')
}

async function onReject(t) {
  await decide(t.confirmation_id, false)
  acted.value[t.confirmation_id] = 'rejected'
  emit('pending-change')
}

async function onDefer(t) {
  await defer(t.confirmation_id)
  acted.value[t.confirmation_id] = 'deferred'
  emit('pending-change')
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
    case 'error':
      return { text: '⚠️ 错误', cls: 'badge-danger' }
    default:
      return { text: '已提交', cls: 'badge-muted' }
  }
}

function stepStatus(t) {
  if (!t) return null
  switch (t.status) {
    case 'executed':
      return { text: '已完成', cls: 'badge-success' }
    case 'failed':
      return { text: '失败', cls: 'badge-danger' }
    case 'pending_confirm':
      return { text: '待确认', cls: 'badge-warning' }
    case 'pending':
      return { text: '待执行', cls: 'badge-muted' }
    case 'rejected':
      return { text: '已拒绝', cls: 'badge-muted' }
    default:
      return null
  }
}

function taskResult(t) {
  if (!t) return ''
  try {
    const r = JSON.parse(t.result || '')
    return r.message || ''
  } catch {
    return ''
  }
}

function stepChart(t) {
  if (!t || !t.result) return null
  try {
    const r = JSON.parse(t.result)
    return r.data && r.data.chart ? r.data.chart : null
  } catch {
    return null
  }
}
</script>

<template>
  <div v-if="message" class="card">
    <div class="card-head">
      <span class="badge" :class="statusBadge(message.status).cls">
        {{ statusBadge(message.status).text }}
      </span>
      <span v-if="message.task_id" class="task-id">任务 #{{ message.task_id }}</span>
    </div>
    <p v-if="message.status === 'need_clarify'" class="question">❓ {{ message.question }}</p>
    <p v-else-if="message.message" class="message-text">{{ message.message }}</p>
    <ul v-if="message.tasks && message.tasks.length" class="tasks">
      <li v-for="(t, i) in message.tasks" :key="i" class="task-step">
        <span class="step-no">{{ i + 1 }}</span>
        <span class="step-action">
          {{ t.action }}<template v-if="t.target"> {{ t.target }}</template>
        </span>
        <span v-if="t.high_risk" class="badge badge-danger">高危</span>
        <span v-if="stepStatus(t)" class="badge" :class="stepStatus(t).cls">
          {{ stepStatus(t).text }}
        </span>
        <span v-if="taskResult(t)" class="step-result">{{ taskResult(t) }}</span>
        <div v-if="needsInline(t)" class="inline-confirm">
          <table v-if="t.preview && t.preview.length" class="diff-table">
            <thead>
              <tr><th>位置</th><th>原值</th><th>新值</th></tr>
            </thead>
            <tbody>
              <tr v-for="(d, j) in t.preview" :key="j">
                <td>第{{ d.row }}行{{ d.column }}列</td>
                <td class="old">{{ d.old }}</td>
                <td class="new">{{ d.new }}</td>
              </tr>
            </tbody>
          </table>
          <p v-if="actText(t)" class="act-text">{{ actText(t) }}</p>
          <div v-else class="act-btns">
            <button class="btn btn-danger btn-sm" @click="onApprove(t)">确认执行</button>
            <button class="btn btn-sm" @click="onReject(t)">拒绝</button>
            <button class="btn btn-sm" @click="onDefer(t)">稍后</button>
          </div>
        </div>
        <div v-if="stepChart(t)" class="chart-wrap">
          <ChartBlock :chart="stepChart(t)" />
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.card {
  max-width: 720px;
  margin: 0 auto 14px;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  box-shadow: var(--shadow-card);
}
.card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.task-id {
  font-size: 12px;
  color: var(--color-text-muted);
}
.question {
  margin: 0 0 8px;
  color: var(--color-warning);
  white-space: pre-wrap;
}
.message-text {
  margin: 0;
  color: var(--color-text);
  white-space: pre-wrap;
  word-break: break-word;
}
.tasks {
  padding: 0;
  margin-top: 4px;
}
.task-step {
  display: flex;
  align-items: baseline;
  gap: 8px;
  flex-wrap: wrap;
  padding: 9px 0;
  border-bottom: 1px solid var(--color-border-light);
}
.task-step:last-child {
  border-bottom: none;
}
.step-no {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--color-bg);
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
.inline-confirm {
  width: 100%;
  padding-left: 28px;
  margin-top: 6px;
}
.diff-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  margin-bottom: 8px;
}
.diff-table th,
.diff-table td {
  border: 1px solid var(--color-border);
  padding: 5px 8px;
  text-align: left;
}
.diff-table th {
  background: var(--color-bg);
  font-weight: 600;
}
.diff-table .old {
  color: var(--color-danger);
  text-decoration: line-through;
}
.diff-table .new {
  color: var(--color-success);
  font-weight: 600;
}
.act-btns {
  display: flex;
  gap: 8px;
}
.act-text {
  margin: 0;
  font-size: 13px;
  color: var(--color-primary);
}
.chart-wrap {
  width: 100%;
  padding-left: 28px;
}
</style>
