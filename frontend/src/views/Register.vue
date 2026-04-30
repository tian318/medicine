<template>
  <div class="register-page">
    <form @submit.prevent="handleRegister" class="register-form">
      <div class="form-group">
        <div class="input-wrapper">
          <i class="fa-solid fa-user"></i>
          <input
            type="text"
            id="username"
            v-model="form.username"
            required
            placeholder="请输入用户名（4-16位字母/数字）"
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
            type="password"
            id="password"
            v-model="form.password"
            required
            placeholder="请输入密码（6-20位，含字母和数字）"
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
            type="password"
            id="confirmPassword"
            v-model="form.confirmPassword"
            required
            placeholder="请再次输入密码"
          />
        </div>
      </div>
      <div class="form-group">
        <div class="input-wrapper">
          <i class="fa-solid fa-phone"></i>
          <input
            type="text"
            id="phone"
            v-model="form.phone"
            required
            placeholder="请输入11位手机号码"
          />
        </div>
      </div>
      <div class="form-group agree-group">
        <input type="checkbox" id="agree" v-model="form.agree" />
        <label for="agree">我已阅读并同意《用户协议》和《隐私政策》</label>
      </div>
      <button type="submit" :disabled="loading || !form.agree" class="btn">
        {{ loading ? '注册中...' : '完成注册' }}
      </button>
      <p class="login-link">已有账号？<router-link to="/">立即登录</router-link></p>
    </form>
    <CustomAlert
      v-if="alertVisible"
      :visible="alertVisible"
      :title="alertTitle"
      :message="alertMessage"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import CustomAlert from '@/components/CustomAlert.vue'
import { api } from '@/services/api'

defineOptions({ name: 'UserRegister' })

const router = useRouter()
const loading = ref(false)
const alertVisible = ref(false)
const alertTitle = ref('提示')
const alertMessage = ref('')

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  phone: '',
  code: '',
  agree: false,
})

const showAlert = (title: string, message: string) => {
  alertTitle.value = title
  alertMessage.value = message
  alertVisible.value = true
}

const handleRegister = async () => {
  if (
    !form.username.trim() ||
    !form.password.trim() ||
    !form.confirmPassword.trim()
  ) {
    showAlert('提示', '请填写用户名和密码')
    return
  }

  if (form.password !== form.confirmPassword) {
    showAlert('提示', '两次输入的密码不一致')
    return
  }

  if (!form.agree) {
    showAlert('提示', '请阅读并同意用户协议和隐私政策')
    return
  }

  loading.value = true

  try {
    const res = await api.register({
      username: form.username.trim(),
      password: form.password.trim(),
      phone: form.phone.trim()
    })

    if (res.code !== 200) {
      showAlert('注册失败', res.message || '注册失败，请稍后重试')
      loading.value = false
      return
    }

    showAlert('注册成功', '请登录')
    // 延迟跳转，让用户看到弹窗
    setTimeout(() => {
      alertVisible.value = false
      router.replace('/')
    }, 1500)
  } catch (error: unknown) {
    console.error('注册请求失败:', error)
    interface ApiError {
      response?: {
        data?: {
          error?: string
        }
      }
      message?: string
    }
    const isApiError = (err: unknown): err is ApiError => {
      return typeof err === 'object' && err !== null
    }
    let msg = '注册失败，请稍后重试'
    if (isApiError(error)) {
      msg = error.response?.data?.error || error.message || msg
    }
    showAlert('注册失败', msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
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

.register-form {
  padding: 0 2rem 2rem;
  max-width: 400px; /* 限制表单最大宽度，输入框会继承这个宽度 */
  width: 100%;  
}

.form-group {
  margin-bottom: 1rem;
}

.input-wrapper {
  position: relative;
  width: 100%;
  margin-bottom: 1.5rem;
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
  padding: 1rem 45px 1rem 45px;
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

.code-btn {
  position: absolute;
  right: 15px;
  top: 50%;
  transform: translateY(-50%);
  background: var(--herbal-green);
  color: white;
  border: none;
  border-radius: 20px;
  padding: 8px 16px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: background-color 0.3s ease;
  z-index: 10;
}

.code-btn:hover {
  background: #4ade80;
}

.agree-group {
  display: flex;
  align-items: center;
  margin-bottom: 1.5rem;
}

.agree-group input[type='checkbox'] {
  width: auto;
  height: auto;
  margin: 0 8px 0 0;
  cursor: pointer;
}

.agree-group label {
  margin: 0;
  font-weight: normal;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  flex: 1;
}

.agree-group label a {
  color: var(--herbal-green);
  text-decoration: none;
}

.agree-group label a:hover {
  text-decoration: underline;
}

.btn {
  width: 100%;
  padding: 1rem;
  background: var(--herbal-green);
  color: white;
  border: none;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 1rem;
  box-shadow: 0 4px 15px rgba(45, 93, 43, 0.3);
}

.btn:hover {
  background: #4ade80;
  box-shadow: 0 6px 20px rgba(74, 222, 128, 0.4);
}

.btn:disabled {
  background: #cccccc;
  cursor: not-allowed;
  box-shadow: none;
}

.login-link {
  text-align: center;
  font-size: 0.875rem;
}

.login-link {
  color: rgba(255, 255, 255, 0.8);
}

.login-link a {
  color: #43e29a;
  text-decoration: none;
  transition: color 0.3s ease;
}

.login-link a:hover {
  text-decoration: underline;
  color: #4ade80;
}
</style>
