<script setup>
defineProps({ item: { type: Object, required: true } })
const emit = defineEmits(['confirm', 'close'])
</script>

<template>
  <div class="overlay" @click.self="emit('close')">
    <div class="modal">
      <h3>确认执行高危动作？</h3>
      <p>{{ item.action }} {{ item.target }}</p>
      <div class="btns">
        <button class="ok" @click="emit('confirm')">确认执行</button>
        <button @click="emit('close')">取消</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overlay { position: fixed; inset: 0; background: rgba(0,0,0,.4); display: flex; align-items: center; justify-content: center; }
.modal { background: #fff; border-radius: 10px; padding: 24px; width: 320px; }
.btns { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
.ok { padding: 6px 16px; border: none; border-radius: 6px; background: #e64340; color: #fff; cursor: pointer; }
</style>