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

function taskStatusText(t) {
  if (t.status === 'executed') return '✅ 已完成'
  if (t.status === 'failed') return '❌ 失败'
  if (t.status === 'pending_confirm') return '⏳ 待确认'
  return ''
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
    <header class="top">
      <button class="link" @click="emit('back')">← 返回</button>
      <h2>任务历史</h2>
      <button class="link" @click="load">刷新</button>
    </header>
    <p v-if="!loading && items.length === 0" class="empty">暂无任务</p>
    <div v-for="t in items" :key="t.task_id" class="item">
      <div class="row" @click="expanded[t.task_id] = !expanded[t.task_id]">
        <span class="text">{{ t.text }}</span>
        <span class="meta">{{ t.status }} · {{ fmt(t.created_at) }}</span>
      </div>
      <div v-if="expanded[t.task_id]" class="detail">
        <p v-if="t.question" class="q">❓ {{ t.question }}</p>
        <ul v-if="t.tasks && t.tasks.length">
          <li v-for="(s, i) in t.tasks" :key="i">
            {{ i + 1 }}. {{ s.action }}<template v-if="s.target"> {{ s.target }}</template>
            <span v-if="s.high_risk" class="risk">（高危）</span>
            <span class="st">{{ taskStatusText(s) }}</span>
            <span v-if="taskResult(s)" class="r">{{ taskResult(s) }}</span>
          </li>
        </ul>
      </div>
    </div>
  </main>
</template>

<style scoped>
.history { max-width: 720px; margin: 0 auto; padding: 16px; }
.top { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.top h2 { flex: 1; margin: 0; }
.link { border: none; background: none; color: #3370ff; cursor: pointer; }
.empty { color: #999; }
.item { border: 1px solid #eee; border-radius: 8px; margin-bottom: 10px; }
.row { display: flex; justify-content: space-between; gap: 10px; padding: 10px 14px; cursor: pointer; }
.text { flex: 1; }
.meta { color: #999; font-size: 12px; white-space: nowrap; }
.detail { padding: 0 14px 10px; border-top: 1px solid #f0f0f0; }
.q { color: #b25000; }
.detail ul { margin: 8px 0 0; padding-left: 20px; }
.risk { color: #e64340; font-size: 12px; }
.st { margin-left: 6px; font-size: 12px; color: #3370ff; }
.r { margin-left: 6px; font-size: 12px; color: #666; }
</style>