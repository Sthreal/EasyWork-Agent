<script setup>
const props = defineProps({
  view: { type: String, default: 'workbench' },
  user: { type: Object, default: null },
  pendingCount: { type: Number, default: 0 },
})
const emit = defineEmits(['navigate', 'logout', 'open-user'])

const navs = [
  { key: 'workbench', icon: '📊', label: '工作台' },
  { key: 'chat', icon: '💬', label: '对话' },
  { key: 'confirm', icon: '⚠️', label: '待确认' },
  { key: 'history', icon: '📋', label: '历史' },
  { key: 'settings', icon: '⚙️', label: '设置' },
]

function userName() {
  return (props.user && props.user.name) || ''
}
</script>

<template>
  <div class="layout">
    <header class="topbar">
      <div class="brand">
        <div class="brand-title">🤖 办公自动化 Agent</div>
        <div class="brand-user" title="个人中心" @click="emit('open-user')">
          <img v-if="user && user.avatar_url" :src="user.avatar_url" class="avatar" alt="" />
          <span v-else class="avatar avatar-fallback">{{ userName().slice(0, 1) }}</span>
          <span class="user-name">{{ userName() }}</span>
        </div>
      </div>
      <nav class="tabs">
        <button
          v-for="n in navs"
          :key="n.key"
          class="tab"
          :class="{ active: view === n.key }"
          @click="emit('navigate', n.key)"
        >
          <span>{{ n.icon }}</span>
          <span>{{ n.label }}</span>
          <span v-if="n.key === 'confirm' && pendingCount" class="tab-badge">{{ pendingCount }}</span>
        </button>
      </nav>
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
.brand {
  display: flex;
  align-items: center;
  gap: 18px;
  min-width: 0;
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

.tabs {
  display: flex;
  gap: 4px;
}
.tab {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}
.tab:hover {
  background: var(--color-bg);
}
.tab.active {
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: 600;
}
.tab-badge {
  min-width: 16px;
  height: 16px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--color-danger);
  color: #fff;
  font-size: 11px;
  line-height: 16px;
  text-align: center;
}

.main {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

@media (max-width: 900px) {
  .brand-title {
    display: none;
  }
  .tabs {
    overflow-x: auto;
  }
}
</style>
