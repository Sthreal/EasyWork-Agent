<script setup>
import { ref, onMounted } from 'vue'
import { getMail } from '../api/user'
import { listTasks } from '../api/task'

const props = defineProps({ user: { type: Object, default: null } })
const emit = defineEmits(['close', 'logout', 'navigate'])

const mail = ref('未绑定')
const historyOpen = ref(false)
const historyItems = ref([])
const historyLoading = ref(false)

function userName() {
  return (props.user && props.user.name) || ''
}

function taskBadge(status) {
  switch (status) {
    case 'executed': return { text: '✅ 已完成', cls: 'badge-success' }
    case 'failed': return { text: '❌ 失败', cls: 'badge-danger' }
    case 'pending_confirm': return { text: '⏳ 待确认', cls: 'badge-warning' }
    case 'need_clarify': return { text: '❓ 待澄清', cls: 'badge-warning' }
    case 'rejected': return { text: '🚫 已拒绝', cls: 'badge-muted' }
    default: return { text: '已提交', cls: 'badge-muted' }
  }
}

function fmtTime(iso) {
  if (!iso) return ''
  return iso.replace('T', ' ').slice(0, 16)
}

async function loadMail() {
  if (!props.user || props.user.user_id == null) return
  try {
    const cfg = await getMail(props.user.user_id)
    mail.value = cfg.qq_mail_address ? cfg.qq_mail_address + '（已绑定）' : '未绑定'
  } catch {
    mail.value = '未绑定'
  }
}

async function toggleHistory() {
  if (historyOpen.value) {
    historyOpen.value = false
    return
  }
  historyOpen.value = true
  if (!historyItems.value.length) {
    historyLoading.value = true
    try {
      const res = await listTasks({ limit: 20 })
      historyItems.value = res.items
    } catch {
      historyItems.value = []
    } finally {
      historyLoading.value = false
    }
  }
}

onMounted(loadMail)
</script>

<template>
  <div class="overlay" @click.self="emit('close')">
    <div class="panel">
      <div class="panel-head">
        <h2>个人中心</h2>
        <button class="close" @click="emit('close')">✕</button>
      </div>
      <div class="user-head">
        <img v-if="user && user.avatar_url" :src="user.avatar_url" class="avatar-lg" alt="" />
        <span v-else class="avatar-lg avatar-fallback">{{ userName().slice(0, 1) }}</span>
        <div>
          <div class="u-name">{{ userName() }}</div>
          <div class="u-id">open_id: {{ (user && user.open_id) || '-' }}</div>
        </div>
        <span class="tag">普通用户</span>
      </div>

      <div class="sec">
        <h4>账号与安全</h4>
        <div class="row"><span>QQ 邮箱</span><span class="muted">{{ mail }}</span></div>
        <div class="row"><span>API Key</span><span class="muted">已配置</span></div>
      </div>

      <div class="sec">
        <h4>权限 <span class="hint">（预留：多用户/角色权限）</span></h4>
        <div class="row"><span>角色</span><span class="tag">普通用户</span></div>
        <div class="row"><span>高危确认权限</span><span class="muted">可确认 / 拒绝 / 稍后</span></div>
        <div class="row"><span>数据范围</span><span class="muted">仅本人</span></div>
      </div>

      <div class="sec">
        <h4>历史记录</h4>
        <div class="row clickable" @click="toggleHistory">
          <span>📜 历史任务记录</span>
          <span class="muted">{{ historyOpen ? '▾ 收起' : '▸ 点击展开' }}</span>
        </div>
        <div v-if="historyOpen" class="history-box">
          <div v-if="historyLoading" class="history-empty">加载中…</div>
          <div v-else-if="!historyItems.length" class="history-empty">暂无任务记录</div>
          <div v-for="t in historyItems" :key="t.task_id" class="history-item">
            <span class="h-text">#{{ t.task_id }} {{ t.text }}</span>
            <span class="badge" :class="taskBadge(t.status).cls">{{ taskBadge(t.status).text }}</span>
            <span class="h-time">{{ fmtTime(t.created_at) }}</span>
          </div>
        </div>
      </div>

      <button class="btn-logout" @click="emit('logout')">退出登录</button>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
}
.panel {
  width: min(520px, 92vw);
  max-height: 84vh;
  overflow-y: auto;
  background: var(--color-card);
  border-radius: var(--radius-lg);
  padding: 22px 24px;
  box-shadow: var(--shadow-pop);
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.panel-head h2 {
  margin: 0;
  font-size: 17px;
}
.close {
  border: none;
  background: none;
  font-size: 16px;
  cursor: pointer;
  color: var(--color-text-muted);
}
.user-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--color-border-light);
  margin-bottom: 14px;
}
.avatar-lg {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  object-fit: cover;
}
.avatar-fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-size: 18px;
  font-weight: 600;
}
.u-name {
  font-weight: 600;
  font-size: 15px;
}
.u-id {
  font-size: 12px;
  color: var(--color-text-muted);
}
.tag {
  margin-left: auto;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--color-primary-light);
  color: var(--color-primary);
}
.sec {
  margin-bottom: 16px;
}
.sec h4 {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0 0 6px;
}
.hint {
  font-weight: 400;
  color: var(--color-text-muted);
}
.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 0;
  border-bottom: 1px solid var(--color-border-light);
  font-size: 13px;
}
.row:last-child {
  border-bottom: none;
}
.row.clickable {
  cursor: pointer;
}
.row.clickable:hover {
  background: var(--color-bg);
}
.muted {
  color: var(--color-text-secondary);
  font-size: 12px;
}
.history-box {
  margin-top: 6px;
  max-height: 220px;
  overflow-y: auto;
  overscroll-behavior: contain;
  border: 1px solid var(--color-border-light);
  border-radius: 8px;
  padding: 4px 10px;
}
.history-empty {
  color: var(--color-text-muted);
  font-size: 12px;
  padding: 12px 0;
  text-align: center;
}
.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-border-light);
  font-size: 12px;
}
.history-item:last-child {
  border-bottom: none;
}
.h-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.h-time {
  color: var(--color-text-muted);
  font-size: 11px;
  white-space: nowrap;
}
.badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
}
.badge-danger { background: var(--color-danger-light); color: var(--color-danger); }
.badge-warning { background: var(--color-warning-light); color: var(--color-warning); }
.badge-success { background: var(--color-success-light); color: var(--color-success); }
.badge-muted { background: var(--color-bg); color: var(--color-text-secondary); }
.btn-logout {
  width: 100%;
  margin-top: 6px;
  padding: 9px;
  border: 1px solid var(--color-danger);
  border-radius: var(--radius-md);
  background: var(--color-danger-light);
  color: var(--color-danger);
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
}
.btn-logout:hover {
  background: var(--color-danger);
  color: #fff;
}
</style>
