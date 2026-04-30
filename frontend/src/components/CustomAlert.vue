<template>
  <div v-if="visible" class="alert-container">
    <div class="alert-header">
      <h3>{{ title }}</h3>
      <button class="close-btn" @click="handleClose">×</button>
    </div>
    <div class="alert-body">
      <p>{{ message }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted, onMounted } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '提示',
  },
  message: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['close'])
const timer = ref<number | null>(null)

const handleClose = () => {
  if (timer.value) {
    clearTimeout(timer.value)
    timer.value = null
  }
  emit('close')
}

// 设置自动关闭定时器
const setupAutoClose = () => {
  // 清除之前的定时器
  if (timer.value) {
    clearTimeout(timer.value)
  }
  // 设置新的定时器，3秒后关闭
  timer.value = window.setTimeout(() => {
    handleClose()
  }, 3000)
}

// 监听visible变化，当visible为true时，设置3秒后自动关闭
watch(() => props.visible, (newValue) => {
  if (newValue) {
    setupAutoClose()
  }
})

// 组件挂载时，如果visible为true，设置自动关闭定时器
onMounted(() => {
  if (props.visible) {
    setupAutoClose()
  }
})

// 组件卸载时清除定时器
onUnmounted(() => {
  if (timer.value) {
    clearTimeout(timer.value)
  }
})
</script>

<style scoped>
.alert-container {
  position: fixed;
  top: 20px;
  right: 20px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  max-width: 300px;
  width: 90%;
  overflow: hidden;
  z-index: 1000;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.alert-header {
  background-color: var(--herbal-green);
  color: white;
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.alert-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 500;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.3s ease;
}

.close-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.alert-body {
  padding: 1.5rem;
}



.alert-body p {
  margin: 0;
  color: #333;
  line-height: 1.5;
}
</style>
