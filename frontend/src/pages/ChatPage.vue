<script setup>
import { ref } from 'vue'
import TaskInput from '../components/TaskInput.vue'
import ResultCard from '../components/ResultCard.vue'
import { createTask } from '../api/task'

const props = defineProps({ user: { type: Object, required: true } })
const emit = defineEmits(['logout', 'openConfirm'])

const messages = ref([])
const pendingContext = ref(null) // { text, round }
const sending = ref(false)

async function handleSubmit(text) {
  let submitText = text
  let round = 1
  if (pendingContext.value) {
    submitText = `${pendingContext.value.text}，补充：${text}`
    round = pendingContext.value.round + 1
    pendingContext.value = null
  }
  sending.value = true
  try {
    const result = await createTask(submitText, round)
    messages.value.push({ text: submitText, ...(result || {}) })
    if (result && result.status === 'need_clarify') {
      pendingContext.value = { text: submitText, round }
    }
  } catch (e) {
    messages.value.push({
      text: submitText,
      task_id: '',
      status: 'error',
      message: `提交失败：${e.message || e}`,
    })
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <main class="chat">
    <header class="top">
      <img v-if="user.avatar_url" :src="user.avatar_url" class="avatar" alt="" />
      <span class="name">{{ user.name }}</span>
      <button class="logout" @click="emit('openConfirm')">待确认</button>
      <button class="logout" @click="emit('logout')">退出</button>
    </header>
    <section class="messages">
      <div class="welcome">
        <p>👋 你好，{{ user.name }}</p>
        <p>输入任务，我来帮你执行。例如：</p>
        <ul>
          <li>给项目组发邮件，说明明天会议改到3点</li>
          <li>帮我约明天下午和HR的会议</li>
          <li>把报名表里张三的电话更新为138xxxx</li>
        </ul>
      </div>
      <ResultCard v-for="(m, i) in messages.filter(Boolean)" :key="i" :message="m" />
      <div v-if="sending" class="card sending">⏳ 处理中…</div>
    </section>
    <TaskInput @submit="handleSubmit" :disabled="sending" />
  </main>
</template>

<style scoped>
.chat { max-width: 720px; margin: 0 auto; display: flex; flex-direction: column; height: 100vh; }
.top { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border-bottom: 1px solid #eee; }
.avatar { width: 32px; height: 32px; border-radius: 50%; }
.name { flex: 1; }
.logout { border: none; background: none; color: #999; cursor: pointer; }
.messages { flex: 1; overflow-y: auto; padding: 16px; }
.welcome { background: #f7f8fa; border-radius: 8px; padding: 16px; margin-bottom: 12px; }
.welcome p { margin: 0 0 8px; }
.welcome ul { margin: 0; padding-left: 20px; color: #555; }
.welcome li { margin-bottom: 4px; }
.card { background: #f7f8fa; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px; }
.sending { color: #999; }
</style>