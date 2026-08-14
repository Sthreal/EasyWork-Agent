<script setup>
import { ref, onMounted } from 'vue'
import { getMail, saveMail, testMail } from '../api/user'

const props = defineProps({ user: { type: Object, required: true } })
const emit = defineEmits(['back'])

const address = ref('')
const code = ref('')
const masked = ref('')
const msg = ref('')
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
    msg.value = '✅ 已保存（授权码已加密显示）'
  } catch (e) {
    msg.value = `保存失败：${e.message || e}`
  } finally {
    busy.value = false
  }
}

async function onTest() {
  busy.value = true
  msg.value = ''
  try {
    const r = await testMail(props.user.user_id, address.value.trim(), code.value.trim())
    msg.value = r.ok ? `✅ ${r.message}` : `❌ ${r.message}`
  } catch (e) {
    msg.value = `测试失败：${e.message || e}`
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="settings">
    <header class="top">
      <button class="link" @click="emit('back')">← 返回</button>
      <h2>我的邮箱</h2>
    </header>
    <p class="tip">绑定后，发邮件会使用你自己的邮箱；不绑定则使用系统默认邮箱。</p>
    <label>
      QQ 邮箱
      <input v-model="address" placeholder="yourname@qq.com" />
    </label>
    <label>
      授权码（IMAP/SMTP，16 位）
      <input v-model="code" type="password" :placeholder="masked || '填新的授权码'" />
    </label>
    <p v-if="msg" class="msg">{{ msg }}</p>
    <div class="btns">
      <button :disabled="busy" @click="onSave">保存</button>
      <button :disabled="busy" @click="onTest">发送测试邮件</button>
    </div>
  </main>
</template>

<style scoped>
.settings { max-width: 480px; margin: 0 auto; padding: 16px; }
.top { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.top h2 { flex: 1; margin: 0; }
.link { border: none; background: none; color: #3370ff; cursor: pointer; }
.tip { color: #999; font-size: 13px; }
label { display: block; margin: 12px 0; }
input { width: 100%; padding: 8px 10px; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; margin-top: 4px; }
.msg { color: #b25000; }
.btns { display: flex; gap: 8px; }
.btns button { padding: 8px 18px; border: none; border-radius: 8px; background: #3370ff; color: #fff; cursor: pointer; }
.btns button:disabled { opacity: .6; cursor: not-allowed; }
</style>