<script setup>
import { ref, onMounted, watch } from 'vue'
import LoginPage from './pages/LoginPage.vue'
import WorkbenchPage from './pages/WorkbenchPage.vue'
import ChatPage from './pages/ChatPage.vue'
import ConfirmationPage from './pages/ConfirmationPage.vue'
import HistoryPage from './pages/HistoryPage.vue'
import SettingsPage from './pages/SettingsPage.vue'
import AppLayout from './components/AppLayout.vue'
import UserPanel from './components/UserPanel.vue'
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
const view = ref('workbench')
const pendingCount = ref(0)
const userPanelOpen = ref(false)

async function refreshPending() {
  try {
    const items = await listPending()
    pendingCount.value = items.length
  } catch {
    pendingCount.value = 0
  }
}

onMounted(refreshPending)
watch(view, refreshPending)

function logout() {
  clearStoredUser()
  user.value = null
}
</script>

<template>
  <LoginPage v-if="!user" />
  <AppLayout
    v-else
    :view="view"
    :user="user"
    :pending-count="pendingCount"
    @navigate="view = $event"
    @logout="logout"
    @open-user="userPanelOpen = true"
  >
    <WorkbenchPage v-if="view === 'workbench'" @pending-change="refreshPending" />
    <ChatPage
      v-else-if="view === 'chat'"
      :user="user"
      @logout="logout"
      @openConfirm="view = 'confirm'"
      @openHistory="view = 'history'"
      @openSettings="view = 'settings'"
    />
    <ConfirmationPage v-else-if="view === 'confirm'" @back="view = 'chat'" />
    <HistoryPage v-else-if="view === 'history'" :user="user" @back="view = 'chat'" />
    <SettingsPage v-else-if="view === 'settings'" :user="user" @back="view = 'chat'" />
  </AppLayout>
  <UserPanel
    v-if="userPanelOpen && user"
    :user="user"
    @close="userPanelOpen = false"
    @logout="logout"
  />
</template>