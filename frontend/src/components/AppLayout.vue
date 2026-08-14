<script setup>
const props = defineProps({
  view: { type: String, default: 'chat' },
  user: { type: Object, default: null },
  pendingCount: { type: Number, default: 0 },
})
const emit = defineEmits(['navigate', 'logout'])

const navs = [
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
    <aside class="sidebar">
      <div class="logo">
        <span class="logo-mark">OA</span>
        <span class="logo-text">办公自动化</span>
      </div>
      <nav class="nav">
        <button
          v-for="n in navs"
          :key="n.key"
          class="nav-item"
          :class="{ active: view === n.key }"
          @click="emit('navigate', n.key)"
        >
          <span class="nav-icon">{{ n.icon }}</span>
          <span class="nav-label">{{ n.label }}</span>
          <span v-if="n.key === 'confirm' && pendingCount" class="nav-badge">{{ pendingCount }}</span>
        </button>
      </nav>
      <div class="user-box">
        <img v-if="user && user.avatar_url" :src="user.avatar_url" class="avatar" alt="" />
        <span v-else class="avatar avatar-fallback">{{ userName().slice(0, 1) }}</span>
        <span class="user-name">{{ userName() }}</span>
        <button class="logout" title="退出登录" @click="emit('logout')">退出</button>
      </div>
    </aside>
    <main class="main">
      <slot />
    </main>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ---------- 侧边栏 ---------- */
.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--color-card);
  border-right: 1px solid var(--color-border);
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--color-border-light);
}
.logo-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: var(--color-primary);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}
.logo-text {
  font-size: 15px;
  font-weight: 600;
}

.nav {
  flex: 1;
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text);
  font-size: 14px;
  font-family: inherit;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s ease, color 0.15s ease;
}
.nav-item:hover {
  background: var(--color-bg);
}
.nav-item.active {
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: 500;
}
.nav-icon {
  font-size: 16px;
  width: 22px;
  text-align: center;
}
.nav-label {
  flex: 1;
}
.nav-badge {
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 999px;
  background: var(--color-danger);
  color: #fff;
  font-size: 12px;
  line-height: 20px;
  text-align: center;
}

.user-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-top: 1px solid var(--color-border-light);
}
.avatar {
  width: 34px;
  height: 34px;
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
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}
.logout {
  border: none;
  background: none;
  color: var(--color-text-secondary);
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: color 0.15s ease, background 0.15s ease;
}
.logout:hover {
  color: var(--color-danger);
  background: var(--color-danger-light);
}

/* ---------- 主区 ---------- */
.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background: var(--color-bg);
}

/* ---------- 窄屏回退：侧边栏收成顶部横条 ---------- */
@media (max-width: 768px) {
  .layout {
    flex-direction: column;
  }
  .sidebar {
    width: 100%;
    flex-shrink: 0;
  }
  .logo {
    display: none;
  }
  .nav {
    flex-direction: row;
    padding: 6px 8px;
    overflow-x: auto;
  }
  .nav-item {
    flex: 1;
    justify-content: center;
    padding: 8px 6px;
  }
  .user-box {
    display: none;
  }
  .main {
    overflow-y: auto;
  }
}
</style>
