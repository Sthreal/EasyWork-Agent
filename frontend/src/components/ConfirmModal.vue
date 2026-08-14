<script setup>
defineProps({ item: { type: Object, required: true } })
const emit = defineEmits(['confirm', 'close'])
</script>

<template>
  <div class="overlay" @click.self="emit('close')">
    <div class="modal">
      <h3>确认执行高危动作？</h3>
      <p class="action">{{ item.action }} {{ item.target }}</p>
      <p v-if="item.params" class="preview">📋 {{ item.params }}</p>
      <div class="btns">
        <button class="btn btn-danger" @click="emit('confirm')">确认执行</button>
        <button class="btn" @click="emit('close')">取消</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  animation: fade-in 0.15s ease;
}
.modal {
  width: min(480px, 90vw);
  background: var(--color-card);
  border-radius: var(--radius-lg);
  padding: 24px 26px;
  box-shadow: var(--shadow-pop);
  animation: pop-in 0.18s ease;
}
.modal h3 {
  margin: 0 0 12px;
  font-size: 17px;
}
.action {
  margin: 0 0 8px;
}
.preview {
  margin: 0;
  padding: 8px 12px;
  background: var(--color-warning-light);
  color: var(--color-warning);
  border-radius: var(--radius-sm);
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-word;
}
.btns {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes pop-in {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
</style>
