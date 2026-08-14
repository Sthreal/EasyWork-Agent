<template>
  <main class="login">
    <div class="card">
      <div class="logo-mark">OA</div>
      <h1>办公自动化 Agent</h1>
      <p class="subtitle">员工用自然语言提需求，Agent 帮你执行</p>
      <a class="btn btn-primary btn-login" href="/api/v1/auth/login">
        <span>🪶</span> 使用飞书登录
      </a>
      <p class="hint">登录后即可发起任务 · 发邮件 / 建日程 / 改表格</p>
    </div>
  </main>
</template>

<style scoped>
.login {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
  background: linear-gradient(135deg, #eef2ff 0%, #f5f6f7 55%, #f5f6f7 100%);
}
.card {
  width: 100%;
  max-width: 420px;
  background: var(--color-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-pop);
  padding: 40px 36px 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 4px;
}
.logo-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: var(--color-primary);
  color: #fff;
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 14px;
}
h1 {
  font-size: 22px;
  margin: 0;
}
.subtitle {
  color: var(--color-text-secondary);
  margin: 0 0 24px;
}
.btn-login {
  padding: 12px 32px;
  font-size: 15px;
  border-radius: var(--radius-md);
}
.hint {
  color: var(--color-text-muted);
  font-size: 12px;
  margin-top: 18px;
}
</style>
