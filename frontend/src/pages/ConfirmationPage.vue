<script setup>
import { ref, onMounted } from 'vue'
import ConfirmModal from '../components/ConfirmModal.vue'
import { listPending, decide } from '../api/confirmation'

const emit = defineEmits(['back'])

const items = ref([])
const loading = ref(false)
const target = ref(null)

async function load() {
  loading.value = true
  try {
    items.value = await listPending()
  } finally {
    loading.value = false
  }
}

async function onApprove() {
  await decide(target.value.id, true)
  target.value = null
  await load()
}

async function onReject(item) {
  await decide(item.id, false)
  await load()
}

onMounted(load)
</script>

<template>
  <main class="confirm-page">
    <header class="top">
      <button class="link" @click="emit('back')">← 返回</button>
      <h2>待确认动作</h2>
      <button class="link" @click="load">刷新</button>
    </header>
    <p v-if="!loading && items.length === 0" class="empty">暂无待确认动作</p>
    <div v-for="item in items" :key="item.id" class="item">
      <p class="line"><b>{{ item.action }}</b> {{ item.target }}（高危，需确认）</p>
      <p v-if="item.params" class="preview">📋 {{ item.params }}</p>
      <p class="meta">任务 #{{ item.task_id }} · {{ item.created_at }}</p>
      <div class="btns">
        <button class="ok" @click="target = item">确认执行</button>
        <button class="no" @click="onReject(item)">拒绝</button>
      </div>
    </div>
    <ConfirmModal v-if="target" :item="target" @confirm="onApprove" @close="target = null" />
  </main>
</template>

<style scoped>
.confirm-page { max-width: 720px; margin: 0 auto; padding: 16px; }
.top { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.top h2 { flex: 1; margin: 0; }
.link { border: none; background: none; color: #3370ff; cursor: pointer; }
.empty { color: #999; }
.item { border: 1px solid #eee; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px; }
.line { margin: 0 0 6px; }
.preview { margin: 0 0 6px; color: #b25000; font-size: 13px; }
.meta { margin: 0 0 10px; font-size: 12px; color: #999; }
.btns { display: flex; gap: 8px; }
.ok { padding: 6px 16px; border: none; border-radius: 6px; background: #e64340; color: #fff; cursor: pointer; }
.no { padding: 6px 16px; border: 1px solid #ddd; border-radius: 6px; background: #fff; cursor: pointer; }
</style>