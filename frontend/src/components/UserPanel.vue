<script setup>
const props = defineProps({ user: { type: Object, default: null } })
const emit = defineEmits(['close', 'logout', 'navigate'])

function userName() {
  return (props.user && props.user.name) || ''
}
</script>

<template>
  <div class="overlay" @click.self="emit('close')">
    <div class="panel">
      <div class="panel-head">
        <h2>个人中心</h2>
        <button class="close" @click="emit('close')">✕</button>
      </div>
      <div class="user-head">
        <img v-if="user && user.avatar_url" :src="user.avatar_url" class="avatar-lg" alt="" />
        <span v-else class="avatar-lg avatar-fallback">{{ userName().slice(0, 1) }}</span>
        <div>
          <div class="u-name">{{ userName() }}</div>
          <div class="u-id">open_id: {{ (user && user.open_id) || '-' }}</div>
        </div>
        <span class="tag">普通用户</span>
      </div>

      <div class="sec">
        <h4>账号与安全</h4>
        <div class="row"><span>QQ 邮箱</span><span class="muted">已绑定</span></div>
        <div class="row"><span>API Key</span><span class="muted">已配置</span></div>
      </div>

      <div class="sec">
        <h4>权限 <span class="hint">（预留：多用户/角色权限）</span></h4>
        <div class="row"><span>角色</span><span class="tag">普通用户</span></div>
        <div class="row"><span>数据范围</span><span class="muted">仅本人</span></div>
      </div>

      <button class="btn-logout" @click="emit('logout')">退出登录</button>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
}
.panel {
  width: min(520px, 92vw);
  max-height: 84vh;
  overflow-y: auto;
  background: var(--color-card);
  border-radius: var(--radius-lg);
  padding: 22px 24px;
  box-shadow: var(--shadow-pop);
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.panel-head h2 {
  margin: 0;
  font-size: 17px;
}
.close {
  border: none;
  background: none;
  font-size: 16px;
  cursor: pointer;
  color: var(--color-text-muted);
}
.user-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--color-border-light);
  margin-bottom: 14px;
}
.avatar-lg {
  width: 46px;
  height: 46px;
  border-radius: 50%;
  object-fit: cover;
}
.avatar-fallback {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-size: 18px;
  font-weight: 600;
}
.u-name {
  font-weight: 600;
  font-size: 15px;
}
.u-id {
  font-size: 12px;
  color: var(--color-text-muted);
}
.tag {
  margin-left: auto;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: var(--color-primary-light);
  color: var(--color-primary);
}
.sec {
  margin-bottom: 16px;
}
.sec h4 {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0 0 6px;
}
.hint {
  font-weight: 400;
  color: var(--color-text-muted);
}
.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 0;
  border-bottom: 1px solid var(--color-border-light);
  font-size: 13px;
}
.row:last-child {
  border-bottom: none;
}
.muted {
  color: var(--color-text-secondary);
  font-size: 12px;
}
.btn-logout {
  width: 100%;
  margin-top: 6px;
  padding: 9px;
  border: 1px solid var(--color-danger);
  border-radius: var(--radius-md);
  background: var(--color-danger-light);
  color: var(--color-danger);
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
}
.btn-logout:hover {
  background: var(--color-danger);
  color: #fff;
}
</style>
