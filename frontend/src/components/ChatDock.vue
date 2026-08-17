<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import ResultCard from './ResultCard.vue'
import { createTask } from '../api/task'

const props = defineProps({ user: { type: Object, default: null } })
const emit = defineEmits(['pending-change'])

const open = ref(false)
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const pendingContext = ref(null)
const listEl = ref(null)
const panelEl = ref(null)
const dockEl = ref(null)

async function scrollBottom() {
  await nextTick()
  if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight
}

async function send() {
  const text = inputText.value.trim()
  if (!text || sending.value) return
  let submitText = text
  let round = 1
  if (pendingContext.value) {
    submitText = `${pendingContext.value.text}，补充：${text}`
    round = pendingContext.value.round + 1
    pendingContext.value = null
  }
  messages.value.push({ role: 'user', text: submitText })
  inputText.value = ''
  sending.value = true
  try {
    const result = await createTask(submitText, round, props.user?.user_id)
    messages.value.push({ role: 'agent', ...(result || {}) })
    if (result && result.status === 'need_clarify') {
      pendingContext.value = { text: submitText, round }
    }
  } catch (e) {
    messages.value.push({
      role: 'agent',
      task_id: '',
      status: 'error',
      message: `提交失败：${e.message || e}`,
    })
  } finally {
    sending.value = false
    scrollBottom()
  }
}

function onPendingChange() {
  emit('pending-change')
}

// ===== 打开/关闭：点击输入框展开，点空白关闭，草稿保留 =====
function openChat() {
  open.value = true
  scrollBottom()
}
function closeChat() {
  open.value = false
}
function onDocClick(e) {
  if (dockEl.value && !e.target.closest('.chat-dock')) {
    closeChat()
  }
}
function onKey(e) {
  if (e.key === 'Escape') closeChat()
}

// ===== 拖拽调大小：宽/高分开 + 左上/右上斜向（v16 逻辑）=====
let resizing = null
function startResize(e, mode) {
  e.preventDefault()
  e.stopPropagation()
  if (!panelEl.value || !dockEl.value) return
  const r = panelEl.value.getBoundingClientRect()
  resizing = { mode, startX: e.clientX, startY: e.clientY, startW: r.width, startH: r.height }
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
}
function onResize(e) {
  if (!resizing || !panelEl.value || !dockEl.value) return
  const { mode, startX, startY, startW, startH } = resizing
  const dx = e.clientX - startX
  const dy = e.clientY - startY
  let w = startW
  let h = startH
  if (mode === 'e') w = startW + dx
  if (mode === 'n') h = startH - dy
  if (mode === 'tr') { w = startW + dx; h = startH - dy }
  if (mode === 'tl') { w = startW - dx; h = startH - dy }
  w = Math.max(400, Math.min(1200, w))
  h = Math.max(260, Math.min(window.innerHeight - 160, h))
  dockEl.value.style.width = w + 'px'
  panelEl.value.style.height = h + 'px'
}
function stopResize() {
  resizing = null
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
}

// ===== 滚动条：滚动时才显示 =====
function flashScrollbar(e) {
  const el = e.currentTarget
  el.classList.add('scrolling')
  clearTimeout(el._scrollTimer)
  el._scrollTimer = setTimeout(() => el.classList.remove('scrolling'), 400)
}

onMounted(() => {
  document.addEventListener('click', onDocClick)
  document.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('keydown', onKey)
})
</script>

<template>
  <div ref="dockEl" class="chat-dock">
    <div ref="panelEl" v-show="open" class="chat-panel">
      <div class="resize-tl" @mousedown.prevent="startResize($event, 'tl')" title="拖拽调整大小"></div>
      <div class="resize-tr" @mousedown.prevent="startResize($event, 'tr')" title="拖拽调整大小"></div>
      <div class="resize-e" @mousedown.prevent="startResize($event, 'e')" title="拖拽调整宽度"></div>
      <div class="resize-n" @mousedown.prevent="startResize($event, 'n')" title="拖拽调整高度"></div>
      <div class="panel-head">💬 与 Agent 对话（点击空白处关闭，草稿保留）</div>
      <div ref="listEl" class="msgs" @scroll="flashScrollbar">
        <div class="msgs-inner">
          <template v-for="(m, i) in messages" :key="i">
            <div v-if="m.role === 'user'" class="msg-user">{{ m.text }}</div>
            <ResultCard v-else :message="m" @pending-change="onPendingChange" />
          </template>
          <div v-if="sending" class="msg-typing">⏳ 处理中…</div>
        </div>
      </div>
    </div>
    <div class="input-wrap">
      <input
        v-model="inputText"
        placeholder="输入任务，回车发送…（点击展开聊天）"
        @focus="openChat"
        @keydown.enter="send"
      />
      <button @click="send">发送</button>
    </div>
  </div>
</template>

<style scoped>
.chat-dock {
  position: fixed;
  left: 50%;
  transform: translateX(-50%);
  bottom: 24px;
  width: 840px;
  z-index: 100;
}
.chat-panel {
  position: absolute;
  bottom: 74px;
  left: 0;
  width: 100%;
  height: 420px;
  display: flex;
  flex-direction: column;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  box-shadow: var(--shadow-pop);
  overflow: hidden;
}
.resize-tl {
  position: absolute;
  top: 0;
  left: 0;
  width: 16px;
  height: 16px;
  cursor: nwse-resize;
  z-index: 6;
  background: radial-gradient(circle at 3px 3px, var(--color-text-muted) 0 2px, transparent 2.5px);
}
.resize-tr {
  position: absolute;
  top: 0;
  right: 0;
  width: 16px;
  height: 16px;
  cursor: nesw-resize;
  z-index: 6;
  background: radial-gradient(circle at 13px 3px, var(--color-text-muted) 0 2px, transparent 2.5px);
}
.resize-e {
  position: absolute;
  top: 0;
  right: 0;
  width: 10px;
  height: 100%;
  cursor: ew-resize;
  z-index: 6;
}
.resize-n {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 10px;
  cursor: ns-resize;
  z-index: 6;
}
.panel-head {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-border-light);
  font-size: 13px;
  color: var(--color-text-secondary);
}
.msgs {
  flex: 1;
  min-height: 100px;
  overflow-y: scroll;
  overscroll-behavior: contain;
  padding: 14px 16px;
  scrollbar-width: thin;
  scrollbar-color: transparent transparent;
}
.msgs::-webkit-scrollbar { width: 6px; }
.msgs::-webkit-scrollbar-track { background: transparent; }
.msgs::-webkit-scrollbar-thumb { background: transparent; border-radius: 3px; }
.msgs.scrolling::-webkit-scrollbar-thumb { background: rgba(134, 144, 156, 0.55); }
.msgs.scrolling { scrollbar-color: rgba(134, 144, 156, 0.55) transparent; }
.msgs-inner {
  min-height: 100%;
  padding-bottom: 40px;
}
.msg-user {
  width: fit-content;
  max-width: 80%;
  margin-left: auto;
  margin-bottom: 10px;
  background: var(--color-primary);
  color: #fff;
  border-radius: 10px 10px 4px 10px;
  padding: 8px 12px;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}
.msg-typing {
  color: var(--color-text-secondary);
  font-size: 13px;
  padding: 8px 0;
}
.input-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: 28px;
  padding: 14px 12px 14px 24px;
  box-shadow: var(--shadow-pop);
}
.input-wrap input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 15px;
  background: transparent;
  font-family: inherit;
}
.input-wrap button {
  border: none;
  background: var(--color-primary);
  color: #fff;
  border-radius: 22px;
  padding: 12px 24px;
  font-size: 14px;
  font-family: inherit;
  cursor: pointer;
}
.input-wrap button:hover {
  background: var(--color-primary-hover);
}
</style>
