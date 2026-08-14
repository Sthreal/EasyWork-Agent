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
    <header class="page-header">
      <h2>待确认动作</h2>
      <button class="btn btn-sm" @click="load">刷新</button>
    </header>
    <p v-if="!loading && items.length === 0" class="empty">🎉 暂无待确认动作</p>
    <div v-for="item in items" :key="item.id" class="item">
      <div class="item-head">
        <span class="badge badge-danger">高危</span>
        <span class="line"><b>{{ item.action }}</b> {{ item.target }}</span>
      </div>
      <p v-if="item.params" class="preview">📋 {{ item.params }}</p>
      <p class="meta">任务 #{{ item.task_id }} · {{ item.created_at }}</p>
      <div class="btns">
        <button class="btn btn-danger" @click="target = item">确认执行</button>
        <button class="btn" @click="onReject(item)">拒绝</button>
      </div>
    </div>
    <ConfirmModal v-if="target" :item="target" @confirm="onApprove" @close="target = null" />
  </main>
</template>

<style scoped>
.confirm-page {
  padding: 24px;
  max-width: var(--content-max-width);
  margin: 0 auto;
}
.item {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 16px 20px;
  margin-bottom: 14px;
  box-shadow: var(--shadow-card);
}
.item-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}
.line {
  flex: 1;
  margin: 0;
  font-size: 15px;
}
.preview {
  margin: 0 0 8px;
  padding: 8px 12px;
  background: var(--color-warning-light);
  color: var(--color-warning);
  border-radius: var(--radius-sm);
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-word;
}
.meta {
  margin: 0 0 12px;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.btns {
  display: flex;
  gap: 10px;
}
</style>
