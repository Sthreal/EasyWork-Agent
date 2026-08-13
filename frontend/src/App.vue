<script setup>
import { ref } from 'vue'
import LoginPage from './pages/LoginPage.vue'
import ChatPage from './pages/ChatPage.vue'
import { getStoredUser, clearStoredUser } from './api/auth'

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