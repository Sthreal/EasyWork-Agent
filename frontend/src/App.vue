<script setup>
import { ref } from 'vue'
import LoginPage from './pages/LoginPage.vue'
import ChatPage from './pages/ChatPage.vue'
import ConfirmationPage from './pages/ConfirmationPage.vue'
import { getStoredUser, clearStoredUser, saveStoredUser } from './api/auth'

const params = new URLSearchParams(window.location.search)
const userParam = params.get('user')
if (userParam) {
  try {
    saveStoredUser(JSON.parse(userParam))
    history.replaceState(null, '', window.location.pathname)
  } catch {
  }
}

const user = ref(getStoredUser())
const view = ref('chat')

function logout() {
  clearStoredUser()
  user.value = null
}
</script>

<template>
  <LoginPage v-if="!user" />
  <template v-else>
    <ChatPage v-if="view === 'chat'" :user="user" @logout="logout" @openConfirm="view = 'confirm'" />
    <ConfirmationPage v-else-if="view === 'confirm'" @back="view = 'chat'" />
  </template>
</template>