<script setup>
import { ref } from 'vue'
import LoginPage from './pages/LoginPage.vue'
import ChatPage from './pages/ChatPage.vue'
import { getStoredUser, clearStoredUser, saveStoredUser } from './api/auth'

// 登录成功后回调页会带上 ?user=...，这里读取并存到当前端口的 localStorage
const params = new URLSearchParams(window.location.search)
const userParam = params.get('user')
if (userParam) {
  try {
    saveStoredUser(JSON.parse(userParam))
    history.replaceState(null, '', window.location.pathname)
  } catch {
    // URL 参数解析失败则忽略，走正常登录
  }
}

const user = ref(getStoredUser())

function logout() {
  clearStoredUser()
  user.value = null
}
</script>

<template>
  <LoginPage v-if="!user" />
  <ChatPage v-else :user="user" @logout="logout" />
</template>