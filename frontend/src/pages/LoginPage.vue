<template>
  <main class="login">
    <h1>办公自动化 Agent</h1>
    <p>员工用自然语言提需求，Agent 帮你执行</p>
    <a class="btn" href="/api/v1/auth/login">飞书登录</a>
  </main>
</template>

<style scoped>
.login {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 100px 20px;
}
.btn {
  display: inline-block;
  padding: 10px 32px;
  border-radius: 8px;
  background: #3370ff;
  color: #fff;
  text-decoration: none;
}
</style>