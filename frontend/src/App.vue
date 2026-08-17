<script setup>
import { ref, onMounted } from 'vue'
import LoginPage from './pages/LoginPage.vue'
import WorkbenchPage from './pages/WorkbenchPage.vue'
import AppLayout from './components/AppLayout.vue'
import UserPanel from './components/UserPanel.vue'
import ChatDock from './components/ChatDock.vue'
import { listPending } from './api/confirmation'
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
const userPanelOpen = ref(false)
const pendingCount = ref(0)

async function refreshPending() {
  try {
    const items = await listPending()
    pendingCount.value = items.length
  } catch {
    pendingCount.value = 0
  }
}

onMounted(refreshPending)

function logout() {
  clearStoredUser()
  user.value = null
}
</script>

<template>
  <LoginPage v-if="!user" />
  <AppLayout
    v-else
    :user="user"
    :pending-count="pendingCount"
    @logout="logout"
    @open-user="userPanelOpen = true"
  >
    <WorkbenchPage @pending-change="refreshPending" />
  </AppLayout>
  <UserPanel
    v-if="userPanelOpen && user"
    :user="user"
    @close="userPanelOpen = false"
    @logout="logout"
  />
  <ChatDock v-if="user" :user="user" @pending-change="refreshPending" />
</template>
