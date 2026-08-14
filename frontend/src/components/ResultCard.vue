<script setup>
defineProps({ message: { type: Object, default: null } })

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
</style>
