<script setup>
import { ref, nextTick } from 'vue'
import TaskInput from '../components/TaskInput.vue'
import ResultCard from '../components/ResultCard.vue'
import { createTask } from '../api/task'

const props = defineProps({ user: { type: Object, required: true } })
const emit = defineEmits(['logout', 'openConfirm', 'openHistory', 'openSettings'])

const messages = ref([])
const pendingContext = ref(null)
const sending = ref(false)
const listEl = ref(null)

async function scrollToBottom() {
  await nextTick()
  if (listEl.value) listEl.value.scrollTop = listEl.value.scrollHeight
}

async function handleSubmit(text) {
  let submitText = text
  let round = 1
  if (pendingContext.value) {
    submitText = `${pendingContext.value.text}，补充：${text}`
    round = pendingContext.value.round + 1
    pendingContext.value = null
  }
  messages.value.push({ role: 'user', text: submitText })
  await scrollToBottom()
  sending.value = true
  try {
    const result = await createTask(submitText, round, props.user.user_id)
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
    await scrollToBottom()
  }
}
</script>

<template>
  <section class="chat">
    <div class="messages" ref="listEl">
      <div class="welcome">
        <p class="welcome-title">👋 你好，{{ user.name }}</p>
        <p class="welcome-sub">输入任务，我来帮你执行。例如：</p>
        <ul class="welcome-examples">
          <li>给项目组发邮件，说明明天会议改到3点</li>
          <li>帮我约明天下午和HR的会议</li>
          <li>把报名表里张三的电话更新为138xxxx</li>
        </ul>
      </div>
      <template v-for="(m, i) in messages.filter(Boolean)" :key="i">
        <div v-if="m.role === 'user'" class="bubble-user">{{ m.text }}</div>
        <ResultCard v-else :message="m" />
      </template>
      <div v-if="sending" class="bubble-user bubble-typing">⏳ 处理中…</div>
    </div>
    <TaskInput @submit="handleSubmit" :disabled="sending" />
  </section>
</template>

<style scoped>
.chat {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* 欢迎卡 */
.welcome {
  max-width: 720px;
  margin: 0 auto 24px;
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 20px 24px;
  box-shadow: var(--shadow-card);
}
.welcome-title {
  font-size: 17px;
  font-weight: 600;
  margin: 0 0 6px;
}
.welcome-sub {
  color: var(--color-text-secondary);
  margin: 0 0 10px;
}
.welcome-examples {
  padding: 0;
  color: var(--color-text-secondary);
}
.welcome-examples li {
  position: relative;
  padding-left: 16px;
  margin-bottom: 4px;
}
.welcome-examples li::before {
  content: '';
  position: absolute;
  left: 2px;
  top: 9px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
}

/* 用户消息气泡 */
.bubble-user {
  width: fit-content;
  max-width: 640px;
  margin-left: auto;
  margin-bottom: 14px;
  background: var(--color-primary);
  color: #fff;
  border-radius: var(--radius-md) var(--radius-md) var(--radius-sm) var(--radius-md);
  padding: 10px 14px;
  box-shadow: var(--shadow-card);
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}
.bubble-typing {
  background: var(--color-primary-light);
  color: var(--color-primary);
}
</style>
