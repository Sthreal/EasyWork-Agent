<script setup>
import { ref } from 'vue'
import TaskInput from '../components/TaskInput.vue'
import ResultCard from '../components/ResultCard.vue'
import { createTask } from '../api/task'

const props = defineProps({ user: { type: Object, required: true } })
const emit = defineEmits(['logout'])

const messages = ref([])

async function handleSubmit(text) {
  const result = await createTask(text)
  messages.value.push({ text, ...result })
}
</script>

<template>
  <main class="chat">
    <header class="top">
      <img v-if="user.avatar_url" :src="user.avatar_url" class="avatar" alt="" />
      <span class="name">{{ user.name }}</span>
      <button class="logout" @click="emit('logout')">退出</button>
    </header>
    <section class="messages">
      <ResultCard v-for="(m, i) in messages" :key="i" :message="m" />
    </section>
    <TaskInput @submit="handleSubmit" />
  </main>
</template>

<style scoped>
.chat { max-width: 720px; margin: 0 auto; display: flex; flex-direction: column; height: 100vh; }
.top { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border-bottom: 1px solid #eee; }
.avatar { width: 32px; height: 32px; border-radius: 50%; }
.name { flex: 1; }
.logout { border: none; background: none; color: #999; cursor: pointer; }
.messages { flex: 1; overflow-y: auto; padding: 16px; }
</style>