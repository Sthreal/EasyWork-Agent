<script setup>
function taskStatusText(t) {
  if (!t) return ''
  if (t.status === 'executed') return '✅ 已完成'
  if (t.status === 'failed') return '❌ 失败'
  if (t.status === 'pending_confirm') return '⏳ 待确认'
  return ''
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
    <p class="text">{{ message.text }}</p>
    <p v-if="message.task_id" class="status">任务已提交（ID: {{ message.task_id }}）· 状态：{{ message.status }}</p>
    <p v-if="message.status === 'need_clarify'" class="question">❓ {{ message.question }}</p>
    <p v-else-if="message.message" class="question">⚠️ {{ message.message }}</p>
    <ul v-else-if="message.tasks && message.tasks.length" class="tasks">
      <li v-for="(t, i) in message.tasks" :key="i">
        {{ i + 1 }}. {{ t.action }}<template v-if="t.target"> {{ t.target }}</template>
        <span v-if="t.high_risk" class="risk">（高危）</span>
        <span class="task-status">{{ taskStatusText(t) }}</span>
        <span v-if="taskResult(t)" class="task-result">{{ taskResult(t) }}</span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.card { background: #f7f8fa; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px; }
.text { margin: 0 0 6px; }
.status { margin: 0 0 8px; font-size: 12px; color: #999; }
.question { margin: 0; color: #b25000; }
.tasks { margin: 0; padding-left: 20px; }
.tasks li { margin-bottom: 4px; }
.risk { color: #e64340; font-size: 12px; }
.task-status { margin-left: 6px; font-size: 12px; color: #3370ff; }
.task-result { margin-left: 6px; font-size: 12px; color: #666; }
</style>