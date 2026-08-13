<script setup>
defineProps({ message: { type: Object, required: true } })
</script>

<template>
  <div class="card">
    <p class="text">{{ message.text }}</p>
    <p class="status">任务已提交（ID: {{ message.task_id }}）· 状态：{{ message.status }}</p>
  </div>
</template>

<style scoped>
.card { background: #f7f8fa; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px; }
.text { margin: 0 0 6px; }
.status { margin: 0; font-size: 12px; color: #999; }
</style>