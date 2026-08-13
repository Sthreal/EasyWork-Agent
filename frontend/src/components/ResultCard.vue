<script setup>
defineProps({ message: { type: Object, required: true } })
</script>

<template>
  <div class="card">
    <p class="text">{{ message.text }}</p>
    <p class="status">任务已提交（ID: {{ message.task_id }}）· 状态：{{ message.status }}</p>
    <p v-if="message.status === 'need_clarify'" class="question">❓ {{ message.question }}</p>
    <ul v-else-if="message.tasks && message.tasks.length" class="tasks">
      <li v-for="(t, i) in message.tasks" :key="i">
        {{ i + 1 }}. {{ t.action }}<template v-if="t.target"> {{ t.target }}</template>
        <span v-if="t.high_risk" class="risk">（高危，需确认）</span>
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
</style>