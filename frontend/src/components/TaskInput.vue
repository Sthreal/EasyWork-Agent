<script setup>
import { ref } from 'vue'

defineProps({ disabled: { type: Boolean, default: false } })
const emit = defineEmits(['submit'])

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
    <button class="send-btn" :disabled="disabled" @click="send">发送</button>
  </div>
</template>

<style scoped>
.input-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 24px;
  border-top: 1px solid var(--color-border);
  background: var(--color-card);
}
.input-row input {
  flex: 1;
  padding: 11px 14px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.input-row input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(51, 112, 255, 0.12);
}
.input-row input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.send-btn {
  padding: 11px 26px;
  border: none;
  border-radius: var(--radius-md);
  background: var(--color-primary);
  color: #fff;
  font-size: 14px;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s ease;
}
.send-btn:hover:not(:disabled) {
  background: var(--color-primary-hover);
}
.send-btn:active:not(:disabled) {
  background: var(--color-primary-active);
}
.send-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
