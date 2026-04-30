<template>
  <div class="login-page">
    <!-- <div class="login-container"> -->

      <form @submit.prevent="handleLogin" class="login-form">
<h1 class="login-title">灵汐药策</h1>
<h1 class="login-title2">中药材价格智能分析与预测系统</h1>        
        <div class="form-group">
          <div class="input-wrapper">
            <i class="fa-solid fa-user"></i>
            <input
              type="text"
              id="username"
              v-model="form.username"
              required
              placeholder="请输入用户名"
            />
          </div>
        </div>
        <div class="form-group">
          <div class="input-wrapper">
            <svg class="input-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
            </svg>
            <input
              :type="showPassword ? 'text' : 'password'"
              id="password"
              v-model="form.password"
              required
              placeholder="请输入密码"
            />
            <button type="button" @click="togglePassword" class="password-toggle">
              <i :class="showPassword ? 'fa-solid fa-eye' : 'fa-solid fa-eye-slash'" />
            </button>
          </div>
        </div>
        <div class="register-right">
          <span class="register-text">还没有账号?</span>
          <router-link to="/register" class="register-link">注册</router-link>
        </div>
        <button type="submit" :disabled="loading" class="btn">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </form>
      <CustomAlert
        v-if="alertVisible"
        :visible="alertVisible"
        :title="alertTitle"
        :message="alertMessage"
        @close="closeAlert"
      />
    <!-- </div> -->
  </div>
</template>
<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import CustomAlert from '@/components/CustomAlert.vue'
import { api } from '@/services/api'
defineOptions({ name: 'UserLogin' })

const router = useRouter()
const loading = ref(false)
const showPassword = ref(false)
const alertVisible = ref(false)
const alertTitle = ref('提示')
const alertMessage = ref('')

// 页面加载时执行new5.py
onMounted(async () => {
  try {
    console.log('执行new5.py脚本...')
    const response = await fetch('http://localhost:5002/api/run-new5')
    const result = await response.json()
    console.log('new5.py执行结果:', result)
    if (result.code !== 200) {
      console.warn('new5.py执行失败:', result.message)
    }
  } catch (error) {
    console.error('执行new5.py时出错:', error)
  }
})

const form = reactive({
  username: '',
  password: '',
  remember: false,
})

const togglePassword = () => {
  showPassword.value = !showPassword.value
}

const showAlert = (title: string, message: string) => {
  alertTitle.value = title
  alertMessage.value = message
  alertVisible.value = true
}

const closeAlert = () => {
  alertVisible.value = false
}

//在script部分添加类型定义和类型守卫
interface ApiError {
  response?: {
    data?: {
      message?: string;
      error?: string;
    };
  };
  message?: string;
}

function isApiError(error: unknown): error is ApiError {
  return typeof error === 'object' && error !== null;
}
const handleLogin = async () => {
  if (!form.username.trim() || !form.password.trim()) {
    showAlert('提示', '请输入用户名和密码')
    return
  }

  loading.value = true

  try {
    const res = await api.login({
      username: form.username.trim(),
      password: form.password.trim(),
    })

    if (res.code !== 200) {
      showAlert('登录失败', res.message || '用户名或密码错误')
      loading.value = false
      return
    }

    // 写入登录标记，路由守卫会据此放行
    localStorage.setItem('herb_price_token', 'db-user')
    localStorage.setItem('herb_price_username', res.data?.username || form.username.trim())

    showAlert('登录成功', '欢迎使用中药材价格信息系统')
    setTimeout(() => {
      closeAlert()
      router.replace('/index')
    }, 1000)
  } catch (error: unknown) {
  console.error('登录请求失败:', error);
  let msg = '登录失败，请稍后重试';
  if (isApiError(error)) {
    msg = error.response?.data?.message ||
          error.response?.data?.error ||
          error.message ||
          msg;
  }
  showAlert('登录失败', msg);
} finally {
  loading.value = false;
}
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-image: url('../../img/1.webp');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  position: relative;
}


.login-container {
  max-width: 400px;
  width: 100%;
  background: transparent;
  backdrop-filter: blur(10px);
  border: none;
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  position: relative;
  z-index: 2;
  text-align: center;
  padding: 2rem;
}

.login-header {
  padding: 2rem;
  text-align: center;
}

.logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  background-color: white;
  color: var(--herbal-green);
  border-radius: 50%;
  margin-bottom: 1rem;
  font-size: 1.5rem;
}

.login-header h1 {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.login-header p {
  margin: 0;
  font-size: 0.875rem;
  opacity: 0.9;
  color: rgba(255, 255, 255, 0.8);
}

.login-card {
  max-width: 500px;   /* 原表单的宽度限制上提 */
  width: 100%;
  text-align: center;
  /* 可添加原表单的透明背景或模糊效果 */
  background: transparent;
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 2rem;
}

.login-form {
  /* 固定最大宽度，限制表单宽度 */
  max-width: 100%;
  ;
}

.form-group {
  margin-bottom: 1rem;
}

.input-wrapper {
  position: relative;
  width: 375px;
  /* margin-bottom: 1.5rem */
  margin: 0 auto 1.5rem;
}

.input-wrapper i,
.input-wrapper .input-icon-svg {
  position: absolute;
  left: 15px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 2;
  color: var(--herbal-green);
  font-size: 1rem;
}

.input-wrapper .input-icon-svg {
  width: 1rem;
  height: 1rem;
}
.input-wrapper input {
  width: 100%;
  padding: 1rem 50px 1rem 45px;
  background: transparent;
  border: 1px solid var(--herbal-green);
  border-radius: 25px;
  font-size: 1rem;
  color: white;
  transition: all 0.3s ease;
  backdrop-filter: blur(5px);
  box-shadow: 0 0 10px #43e295;
}

.input-wrapper input::placeholder {
  color: rgba(255, 255, 255, 0.8);
}

.input-wrapper input:focus {
  outline: none;
  border-color: #4ade80;
  box-shadow: 0 0 15px rgba(74, 222, 128, 0.5);
  background: transparent;
}

.password-toggle {
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--herbal-green);
  padding: 8px;
  font-size: 1rem;
  z-index: 10;
  transition: color 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
}

.password-toggle:hover {
  color: #4ade80;
}

.register-right {
  text-align: right;
  margin-bottom: 1.5rem;
  margin-right: 50px;
}

.register-text {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.875rem;
}

.register-link {
  color: #43e29a;
  text-decoration: none;
  font-size: 0.875rem;
  transition: color 0.3s ease;
  margin-left: 5px;
}

.register-link:hover {
  color: #4ade80;
  text-decoration: underline;
}

.btn {
  width: 375px;
  padding: 1rem;
  background: linear-gradient(90deg, var(--herbal-green), #3a7a36);
  color: white;
  border: none;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(45, 93, 43, 0.4);
  display: block;      /* 确保按钮为块级元素 */
  margin: 0 auto; 
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(45, 93, 43, 0.6);
  background: linear-gradient(90deg, #3a7a36, var(--herbal-green));
}

.btn:disabled {
  background: rgba(255, 255, 255, 0.3);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.copyright {
  text-align: center;
  padding: 1.5rem;
  background-color: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(45, 93, 43, 0.3);
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}
.logo-image {
  width: 62px;
  height: 62px;
  object-fit: contain;
  border-radius: 50%;
}

.login-title {
  font-size: 2.2rem;            /* 大号字体 */
  font-weight: 700;
  color: white;
  text-align: center;
  margin-top: 0;
  margin-bottom: 0rem;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
  letter-spacing: 2px;
}

.login-title2{
  font-size: 1.8rem;            /* 大号字体 */
  font-weight: 700;
  color: white;
  text-align: center;
  margin-top: 0;
  margin-bottom: 2rem;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.6);
  letter-spacing: 2px;
}
</style>
