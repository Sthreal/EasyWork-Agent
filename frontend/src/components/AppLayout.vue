<script setup>
const props = defineProps({
  user: { type: Object, default: null },
  pendingCount: { type: Number, default: 0 },
})
const emit = defineEmits(['logout', 'open-user'])

function userName() {
  return (props.user && props.user.name) || ''
}
</script>

<template>
  <div class="layout">
    <header class="topbar">
      <div class="brand-title">🤖 办公自动化 Agent</div>
      <div class="brand-user" title="个人中心" @click="emit('open-user')">
        <img v-if="user && user.avatar_url" :src="user.avatar_url" class="avatar" alt="" />
        <span v-else class="avatar avatar-fallback">{{ userName().slice(0, 1) }}</span>
        <span class="user-name">{{ userName() }}</span>
      </div>
    </header>
    <main class="main">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: var(--color-bg);
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 20px;
  background: var(--color-card);
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}
.brand-title {
  font-size: 16px;
  font-weight: 700;
  white-space: nowrap;
}
.brand-user {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px 4px 4px;
  border-radius: 20px;
  cursor: pointer;
  transition: background 0.15s ease;
}
.brand-user:hover {
  background: var(--color-bg);
}
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}
.avatar-fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-size: 15px;
  font-weight: 600;
}
.user-name {
  font-size: 13px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}
.main {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
</style>
