<script setup>
import { ref, onMounted } from 'vue'
import { getMail, saveMail, testMail } from '../api/user'

const props = defineProps({ user: { type: Object, required: true } })
const emit = defineEmits(['back'])

const address = ref('')
const code = ref('')
const masked = ref('')
const msg = ref('')
const msgOk = ref(false)
const busy = ref(false)

async function load() {
  try {
    const cfg = await getMail(props.user.user_id)
    address.value = cfg.qq_mail_address
    masked.value = cfg.qq_mail_auth_code_masked
  } catch (e) {
    msg.value = `读取失败：${e.message || e}`
  }
}

async function onSave() {
  busy.value = true
  msg.value = ''
  try {
    const cfg = await saveMail(props.user.user_id, address.value.trim(), code.value.trim())
    masked.value = cfg.qq_mail_auth_code_masked
    msg.value = '已保存（授权码已加密显示）'
    msgOk.value = true
  } catch (e) {
    msg.value = `保存失败：${e.message || e}`
    msgOk.value = false
  } finally {
    busy.value = false
  }
}

async function onTest() {
  busy.value = true
  msg.value = ''
  try {
    const r = await testMail(props.user.user_id, address.value.trim(), code.value.trim())
    msg.value = r.message
    msgOk.value = !!r.ok
  } catch (e) {
    msg.value = `测试失败：${e.message || e}`
    msgOk.value = false
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="settings">
    <header class="page-header">
      <h2>我的邮箱</h2>
    </header>
    <div class="card">
      <p class="tip">绑定后，发邮件会使用你自己的邮箱；不绑定则使用系统默认邮箱。</p>
      <label class="field">
        <span class="label">QQ 邮箱</span>
        <input v-model="address" class="input" placeholder="yourname@qq.com" />
      </label>
      <label class="field">
        <span class="label">授权码（IMAP/SMTP，16 位）</span>
        <input v-model="code" type="password" class="input" :placeholder="masked || '填新的授权码'" />
      </label>
      <p v-if="msg" class="msg" :class="{ ok: msgOk }">{{ msg }}</p>
      <div class="btns">
        <button class="btn btn-primary" :disabled="busy" @click="onSave">保存</button>
        <button class="btn" :disabled="busy" @click="onTest">发送测试邮件</button>
      </div>
    </div>
  </main>
</template>

<style scoped>
.settings {
  padding: 24px;
  max-width: 640px;
  margin: 0 auto;
}
.card {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 24px 28px;
  box-shadow: var(--shadow-card);
}
.tip {
  color: var(--color-text-secondary);
  font-size: 13px;
  margin: 0 0 18px;
}
.field {
  display: block;
  margin-bottom: 16px;
}
.label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
}
.msg {
  margin: 12px 0 0;
  color: var(--color-danger);
  font-size: 13px;
}
.msg.ok {
  color: var(--color-success);
}
.btns {
  display: flex;
  gap: 10px;
  margin-top: 18px;
}
</style>
