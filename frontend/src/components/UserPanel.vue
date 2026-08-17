<script setup>
import { ref, onMounted } from 'vue'
import { getMail, saveMail, testMail } from '../api/user'
import { listTasks } from '../api/task'

const props = defineProps({ user: { type: Object, default: null } })
const emit = defineEmits(['close', 'logout', 'navigate'])

const mailStatus = ref('未绑定')
const editOpen = ref(false)
const address = ref('')
const code = ref('')
const masked = ref('')
const msg = ref('')
const msgOk = ref(false)
const busy = ref(false)
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
    address.value = cfg.qq_mail_address
    masked.value = cfg.qq_mail_auth_code_masked
    mailStatus.value = cfg.qq_mail_address ? cfg.qq_mail_address + '（已绑定）' : '未绑定'
  } catch {
    mailStatus.value = '未绑定'
  }
}

function toggleEdit() {
  editOpen.value = !editOpen.value
  msg.value = ''
}

async function onSave() {
  busy.value = true
  msg.value = ''
  try {
    const cfg = await saveMail(props.user.user_id, address.value.trim(), code.value.trim())
    masked.value = cfg.qq_mail_auth_code_masked
    mailStatus.value = address.value.trim() + '（已绑定）'
    msg.value = '已保存（授权码已加密显示）'
    msgOk.value = true
  } catch (e) {
    msg.value = `保存失败：${e.message || e}`
    msgOk.value = false
  } finally {
    busy.value = false
  }
}

async function onTest() {
  busy.value = true
  msg.value = ''
  try {
    const r = await testMail(props.user.user_id, address.value.trim(), code.value.trim())
    msg.value = r.message
    msgOk.value = !!r.ok
  } catch (e) {
    msg.value = `测试失败：${e.message || e}`
    msgOk.value = false
  } finally {
    busy.value = false
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
        <div class="row">
          <span>QQ 邮箱</span>
          <span class="muted">{{ mailStatus }}</span>
          <button class="link-btn" @click="toggleEdit">{{ editOpen ? '收起' : '修改' }}</button>
        </div>
        <div v-if="editOpen" class="mail-form">
          <p class="tip">绑定后发邮件使用你的邮箱；不绑定则用系统默认邮箱。</p>
          <label class="field">
            <span class="label">QQ 邮箱</span>
            <input v-model="address" class="input" placeholder="yourname@qq.com" />
          </label>
          <label class="field">
            <span class="label">授权码（IMAP/SMTP，16 位）</span>
            <input v-model="code" type="password" class="input" :placeholder="masked || '填新的授权码'" />
          </label>
          <p v-if="msg" class="msg" :class="{ ok: msgOk }">{{ msg }}</p>
          <div class="btns">
            <button class="btn btn-primary" :disabled="busy" @click="onSave">保存</button>
            <button class="btn" :disabled="busy" @click="onTest">发送测试邮件</button>
          </div>
        </div>
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
.link-btn {
  border: none;
  background: none;
  color: var(--color-primary);
  font-size: 12px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 6px;
}
.link-btn:hover {
  background: var(--color-primary-light);
}
.mail-form {
  margin-top: 8px;
  padding: 12px 14px;
  background: var(--color-bg);
  border-radius: var(--radius-md);
}
.tip {
  color: var(--color-text-secondary);
  font-size: 12px;
  margin: 0 0 12px;
}
.field {
  display: block;
  margin-bottom: 12px;
}
.label {
  display: block;
  margin-bottom: 5px;
  font-size: 12px;
  font-weight: 500;
}
.input {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  outline: none;
  font-family: inherit;
  background: var(--color-card);
}
.msg {
  margin: 10px 0 0;
  color: var(--color-danger);
  font-size: 12px;
}
.msg.ok {
  color: var(--color-success);
}
.btns {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
.btn {
  border: 1px solid var(--color-border);
  background: var(--color-card);
  color: var(--color-text);
  border-radius: 8px;
  padding: 7px 14px;
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
}
.btn-primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
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
