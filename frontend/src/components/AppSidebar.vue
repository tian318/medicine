<template>
  <aside class="sidebar">
    <!-- 系统Logo -->
    <div class="sidebar-header">
      <div class="sidebar-logo">
        <h1 class="text-xs font-bold">灵汐药策</h1>
      </div>
    </div>

    <!-- 导航菜单 -->
    <nav class="sidebar-nav">
      <div class="sidebar-menu">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="sidebar-link"
          :class="[$route.path === item.path ? 'sidebar-item-active' : '']"
          replace
        >
        <template v-if="item.path === '/index'">
          
        </template>
        <template v-else-if="item.path === '/yaocaichandi'">
           
          </template>
          <template v-else-if="item.path === '/jiageyulan'">
           
          </template>
          <template v-else-if="item.path === '/jiagezoushi'">
            
          </template>
          <template v-else-if="item.path === '/zhongyaoku'">
           
          </template>
          <template v-else-if="item.path === '/shichangfenxi'">
            <!-- <div class="icon-container-transparent">
              <img src="/logo/scfx.png" alt="市场分析" class="w-2 h-2" />
            </div> -->
          </template>
          <template v-else-if="item.path === '/zixundongtai'">
            <!-- <div class="icon-container-transparent">
              <img src="/logo/zxdt.png" alt="资讯动态" class="w-2 h-2" />
            </div> -->
          </template>

          <i v-else :class="[item.icon, 'sidebar-icon']"></i>
          <span>{{ item.name }}</span>
        </router-link>
      </div>
    </nav>

    <!-- 用户信息区域 -->
    <div class="sidebar-footer">
      <div class="user-info-container">
        <div class="user-avatar" @click="goToPersonalCenter">
          <div v-if="userAvatar" class="avatar-image-container">
            <img :src="userAvatar" alt="用户头像" class="w-full h-full object-contain" />
          </div>
          <i v-else class="fa-solid fa-user"></i>
        </div>
      </div>
    </div>
  </aside>

  <!-- 小助手按钮 -->
  <div v-if="!agentChatActive" class="agent-toggle" id="agentToggle" @click="agentChatActive = true">
    <img src="http://zhangzetian.me/logo/logo.png" alt="中药材AI助手" class="w-6 h-6" />
  </div>

  <!-- 小助手聊天窗口 -->
  <div v-if="agentChatActive" class="agent-chat" id="agentChat">
    <div class="agent-header">
      <span>中药材AI助手</span>
      <button class="agent-close" id="agentClose" @click="agentChatActive = false">×</button>
    </div>
    <div class="agent-messages" id="agentMessages" ref="agentMessages">
      <div v-for="(message, index) in agentMessagesList" :key="index" :class="['agent-msg', message.role]">
        <div v-html="message.content"></div>
      </div>
    </div>
    <div class="agent-input">
      <input type="text" id="agentInput" ref="agentInput" v-model="agentInputValue" placeholder="问点药材问题..." @keydown.enter="sendAgentMsg" />
        <button id="agentSend" @click="sendAgentMsg"><i class="fas fa-paper-plane"></i></button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 用户头像状态
const userAvatar = ref<string | null>(null)
import axios from 'axios'
// AI助手相关状态
const agentChatActive = ref(false)
const agentInputValue = ref('')
const agentMessages = ref<HTMLElement | null>(null)
const agentMessagesList = ref([
  {
    role: 'ai',
    content: '你好！我是中药材AI助手，可查询药材功效、配伍、禁忌~'
  }
])

// 从本地存储加载头像
const loadAvatar = () => {
  const savedAvatar = localStorage.getItem('userAvatar')
  if (savedAvatar) {
    userAvatar.value = savedAvatar
    console.log('加载头像成功:', savedAvatar)
  } else {
    console.log('本地存储中没有头像')
  }
}

// 监听头像更新事件
const handleAvatarUpdate = (event: CustomEvent) => {
  if (event.detail && event.detail.avatar) {
    userAvatar.value = event.detail.avatar
    console.log('接收到头像更新事件:', event.detail.avatar)
  } else {
    console.log('接收到头像更新事件，但没有头像数据')
  }
}

const menuItems = [
  { path: '/index', name: '系统首页' },
  { path: '/yaocaichandi', name: '药材产地', icon: 'fa-solid fa-home' },
  { path: '/jiageyulan', name: '价格预览', icon: 'fa-solid fa-magnifying-glass' },
  { path: '/jiagezoushi', name: '价格走势', icon: 'fa-solid fa-chart-line' },
  { path: '/zhongyaoku', name: '药材库', icon: 'fa-solid fa-database' },
  { path: '/shichangfenxi', name: '市场分析', icon: 'fa-solid fa-chart-pie' },
  { path: '/zixundongtai', name: '资讯动态', icon: 'fa-solid fa-newspaper' },
]

const goToPersonalCenter = () => {
  router.replace('/gerenzhongxin')
}

// 生命周期钩子
onMounted(() => {
  // 加载头像
  loadAvatar()
  // 添加事件监听器
  window.addEventListener('avatar-updated', handleAvatarUpdate as EventListener)
  console.log('导航栏组件已挂载，添加了头像更新事件监听器')
})

// AI助手发送消息
const sendAgentMsg = async () => {
  const content = agentInputValue.value.trim()
  if (!content) return
  
  // 显示用户消息
  agentMessagesList.value.push({
    role: 'user',
    content: content
  })
  agentInputValue.value = ''
  
  // 滚动到底部
  setTimeout(() => {
    if (agentMessages.value) {
      agentMessages.value.scrollTop = agentMessages.value.scrollHeight
    }
  }, 100)
  
  // 加载提示
  const loadingIndex = agentMessagesList.value.length
  agentMessagesList.value.push({
    role: 'ai',
    content: '思考中...'
  })
  
  // 滚动到底部
  setTimeout(() => {
    if (agentMessages.value) {
      agentMessages.value.scrollTop = agentMessages.value.scrollHeight
    }
  }, 100)
  
  try {
  // 调用后端接口
  const { data } = await axios.post('http://59.110.216.114:8000/chat', {
    content
  }, {
    headers: {
      'Content-Type': 'application/json'
    }
  })
  // 替换加载提示为AI回复
  agentMessagesList.value[loadingIndex] = {
    role: 'ai',
    content: data.reply.replace(/\n/g, '<br>')
  }
}catch (err) {
    // 替换加载提示为错误信息
    agentMessagesList.value[loadingIndex] = {
      role: 'ai',
      content: '❌ 连接失败，请稍后再试'
    }
  }
  
  // 滚动到底部
  setTimeout(() => {
    if (agentMessages.value) {
      agentMessages.value.scrollTop = agentMessages.value.scrollHeight
    }
  }, 100)
}

onUnmounted(() => {
  // 移除事件监听器
  window.removeEventListener('avatar-updated', handleAvatarUpdate as EventListener)
})
</script>

<style scoped>
.sidebar {
  width: 100%;
  background-color: var(--herbal-green);
  color: white;
  height: 70px;
  display: flex;
  flex-direction: row;
  align-items: center;
  overflow-x: auto;
  position: fixed;
  left: 0;
  top: 0;
  right: 0;
  z-index: 100;
  overflow-y: visible;

  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15); /* 底部柔和阴影，提升悬浮感 */
  border-bottom: 1px solid rgba(255, 255, 255, 0.1); /* 底部白色半透明分割线 */
}

.sidebar-header {
  padding: 0 16px;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  height: 100%;
  display: flex;
  align-items: center;
  position: relative;
  overflow: visible;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  font-size: 14px;
  position: relative;
}

/* 小助手按钮 */
.agent-toggle {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #2A5F48;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
  border: 3px solid white !important;
  outline: none !important;
  z-index: 9999;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.agent-toggle:hover {
  transform: scale(1.1);
  box-shadow: 0 0 15px rgba(42, 95, 72, 0.5);
  background: rgba(255, 255, 255, 0.9);
  border: 3px solid white !important;
}

.agent-toggle i {
  font-size: 16px;
}

/* 小助手聊天窗口 */
.agent-chat {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 320px;
  height: 480px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 10000;
  pointer-events: auto;
}

.agent-chat.active {
  display: flex;
}

/* 聊天窗口头部 */
.agent-header {
  background: var(--herbal-green);
  color: white;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.agent-close {
  background: none;
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
}

/* 消息区 */
.agent-messages {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
  background: #F9F6F0;
  color: black !important;
  display: flex;
  flex-direction: column;
  gap: 10px;
  * {
    color: black !important;
  }
}

.agent-msg {
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.5;
  max-width: 85%;
  color: black !important;
  border-radius: 16px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.agent-msg.ai {
  background: white !important;
  border: 1px solid #000 !important;
  align-self: flex-start !important;
  color: black !important;
}

.agent-msg.user {
  background: #E1F0EC !important;
  border: 1px solid #409eff !important;
  align-self: flex-end !important;
  margin-left: auto !important;
  color: black !important;
}

/* 输入框 */
.agent-input {
  display: flex;
  padding: 10px;
  border-top: 1px solid #D1C7B8;
}

#agentInput {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #D1C7B8;
  border-radius: 20px;
  outline: none;
  font-size: 13px;
}

#agentSend {
  margin-left: 8px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--herbal-green);
  color: white;
  border: none;
  cursor: pointer;
}

.sidebar-nav {
  flex: 1;
  padding: 0 16px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin-left: 20px;
}

.sidebar-menu {
  display: flex;
  flex-direction: row;
  gap: 8px;
  height: 100%;
  align-items: center;
}

.sidebar-link {
  display: flex;
  align-items: center;
  padding: 3px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
  text-decoration: none;
  color: white;
  white-space: nowrap;
}

.sidebar-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.sidebar-item-active {
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  /* border-bottom: 3px solid white; */
  border-left: none;
}

.sidebar-icon {
  width: 20px;
  text-align: center;
  margin-right: 12px;
}

.icon-container {
  width: 20px;
  height: 20px;
  text-align: center;
  margin-right: 12px;
  background-color: var(--herbal-green);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.icon-container-transparent {
  width: 20px;
  height: 20px;
  text-align: center;
  margin-right: 12px;
  background-color: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.sidebar-link:hover .icon-container {
  background-color: rgba(255, 255, 255, 0.2);
}

.sidebar-item-active .icon-container {
  background-color: rgba(255, 255, 255, 0.2);
}

.sidebar-link:hover .icon-container-transparent {
  background-color: transparent;
}

.sidebar-item-active .icon-container-transparent {
  background-color: transparent;
}

.icon-container {
  width: 20px;
  height: 20px;
  text-align: center;
  margin-right: 12px;
  background-color: var(--herbal-green);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.sidebar-link:hover .icon-container {
  background-color: rgba(255, 255, 255, 0.2);
}

.sidebar-item-active .icon-container {
  background-color: rgba(255, 255, 255, 0.2);
}

.sidebar-footer {
  padding: 0 16px;
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  height: 100%;
  display: flex;
  align-items: center;
}

.user-info-container {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 100%;
}

.user-info {
  display: flex;
  align-items: center;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: white;
  color: var(--herbal-green);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
  border: 2px solid rgba(255, 255, 255, 0.8);
}

.avatar-image-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: white;
}

.avatar-image-container img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.user-avatar:hover {
  background-color: rgba(255, 255, 255, 0.9);
  transform: scale(1.15);
  box-shadow: 0 0 15px rgba(255, 255, 255, 0.7);
}




</style>
