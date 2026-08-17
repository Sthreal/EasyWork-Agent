<script setup>
import { ref, onMounted } from 'vue'
import { listPending } from '../api/confirmation'

const pendingCount = ref(0)
const today = ref('')

onMounted(async () => {
  try {
    const items = await listPending()
    pendingCount.value = items.length
  } catch {
    pendingCount.value = 0
  }
  today.value = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
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
    <div class="wb-empty">工作台建设中 · 后续切片接入 KPI / 图表 / 待确认 / 最近任务</div>
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
.wb-empty {
  padding: 60px 20px;
  text-align: center;
  color: var(--color-text-muted);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-card);
}
</style>
