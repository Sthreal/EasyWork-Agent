<script setup>
defineProps({ disabled: { type: Boolean, default: false } })
const emit = defineEmits(['submit'])
import { ref } from 'vue'
const text = ref('')

function send() {
  const t = text.value.trim()
  if (!t) return
  emit('submit', t)
  text.value = ''
}
</script>

<template>
  <div class="input-row">
    <input
      v-model="text"
      :disabled="disabled"
      placeholder="输入任务，例如：给项目组发邮件，说明明天会议改到3点"
      @keyup.enter="send"
    />
    <button :disabled="disabled" @click="send">发送</button>
  </div>
</template>

<style scoped>
.input-row { display: flex; gap: 8px; padding: 12px 16px; border-top: 1px solid #eee; }
.input-row input { flex: 1; padding: 10px 12px; border: 1px solid #ddd; border-radius: 8px; }
.input-row button { padding: 10px 20px; border: none; border-radius: 8px; background: #3370ff; color: #fff; cursor: pointer; }
.input-row button:disabled, .input-row input:disabled { opacity: .6; cursor: not-allowed; }
</style>