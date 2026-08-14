<script setup>
import { ref, onMounted } from 'vue'
import { listTasks } from '../api/task'

const props = defineProps({ user: { type: Object, required: true } })
const emit = defineEmits(['back'])

const items = ref([])
const loading = ref(false)
const expanded = ref({})

async function load() {
  loading.value = true
  try {
    items.value = await listTasks(props.user.user_id)
  } finally {
    loading.value = false
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
      <h2>任务历史</h2>
      <button class="btn btn-sm" @click="load">刷新</button>
    </header>
    <p v-if="!loading && items.length === 0" class="empty">暂无任务</p>
    <div v-for="t in items" :key="t.task_id" class="item">
      <div class="row" @click="expanded[t.task_id] = !expanded[t.task_id]">
        <span class="text">{{ t.text }}</span>
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
