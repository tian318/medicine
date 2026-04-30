<template>
  <div class="page-container">
    <AppSidebar />

    <main class="main-content">
      <div class="container">
        <!-- 面包屑导航 -->
        <div class="flex items-center justify-center text-sm text-gray-500 mb-6 breadcrumb-container">
          <span class="text-herbal-green font-medium breadcrumb-title">个人中心</span>
        </div>

        <!-- 三盒布局 -->
        <div class="three-box-layout">
          <!-- 左侧第一个小盒子：个人信息 -->
          <div class="box box-left-top bg-white rounded-xl card-shadow p-4 hover:shadow-lg transition-shadow">
            <div class="flex flex-col items-center mb-4">
              <!-- 头像区域（保持不变） -->
              <div class="avatar-container">
                <label class="avatar-wrapper">
                  <img :src="user.avatar" alt="用户头像" class="avatar-image" id="profileAvatar">
                  <input type="file" accept="image/*" class="file-input-hidden" @change="handleAvatarUpload">
                </label>
                <label class="avatar-upload-btn">
                  <i class="fas fa-camera"></i>
                  <input type="file" accept="image/*" class="file-input-hidden" @change="handleAvatarUpload">
                </label>
              </div>

              <h3 class="text-base font-bold text-gray-800 nickname-title">{{ user.nickname }}</h3>
            </div>

            <!-- 【优化】收藏/浏览 间距可配置 -->
            <div class="flex justify-center items-center collection-history-container py-3 border-t border-b border-gray-100 mb-3">
              <!-- 收藏模块 -->
              <div class="collection-item">
                <i class="fas fa-star collect-history-icon"></i>
                <div>
                  <span class="collect-history-text">收藏{{ collections.length }}</span>
                </div>
              </div>

              <!-- 浏览模块 -->
              <div class="history-item">
                <i class="fas fa-eye collect-history-icon"></i>
                <div>
                  <span class="collect-history-text">浏览{{ history.length }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 左侧第二个小盒子：功能导航 -->
          <div class="box box-left-bottom bg-white rounded-xl card-shadow p-6 hover:shadow-lg transition-shadow">
            <h3 class="function-nav-title">
              <!-- <i class="fas fa-sliders-h text-herbal-green mr-2"></i> -->
              功能导航
            </h3>
            <nav class="space-y-3">
              <button @click="switchTab('profile')" class="tab-btn text-left px-4 py-3 rounded-lg transition-all flex items-center" :class="activeTab === 'profile' ? 'bg-herbal-green/10 text-herbal-green font-medium' : 'text-gray-700 hover:bg-gray-50'">
                个人资料
              </button>
              <button @click="switchTab('collection')" class="tab-btn text-left px-4 py-3 rounded-lg transition-all flex items-center" :class="activeTab === 'collection' ? 'bg-herbal-green/10 text-herbal-green font-medium' : 'text-gray-700 hover:bg-gray-50'">
                我的收藏
              </button>
              <button @click="switchTab('history')" class="tab-btn text-left px-4 py-3 rounded-lg transition-all flex items-center" :class="activeTab === 'history' ? 'bg-herbal-green/10 text-herbal-green font-medium' : 'text-gray-700 hover:bg-gray-50'">
                浏览记录
              </button>
              <button @click="switchTab('settings')" class="tab-btn text-left px-4 py-3 rounded-lg transition-all flex items-center" :class="activeTab === 'settings' ? 'bg-herbal-green/10 text-herbal-green font-medium' : 'text-gray-700 hover:bg-gray-50'">
                系统设置
              </button>
            </nav>
          </div>

          <!-- 右侧大盒子：内容区域 -->
          <div class="box box-right bg-white rounded-xl card-shadow p-6 hover:shadow-lg transition-shadow">
            <!-- 个人资料 Tab -->
           <div v-show="activeTab === 'profile'" class="profile-container">
  <h3 class="profile-title">个人资料</h3>

  <!-- 个人信息卡片 -->
  <div class="profile-info-card">
    <!-- 头像和基本信息 -->
    <div class="profile-header">
      <div class="profile-avatar">
        <img :src="user.avatar" alt="用户头像" class="avatar-image">
        <div class="role-badge">系统管理员</div>
      </div>
      <div class="profile-info">
        <h4 class="profile-name">{{ user.nickname }}</h4>
        <p class="profile-role">中药材管理员</p>
        <button class="edit-profile-btn" @click="editProfile">
          <i class="fas fa-edit mr-2"></i>编辑个人资料
        </button>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="profile-stats">
      <div class="stat-item">
        <i class="fas fa-star stat-icon"></i>
        <div class="stat-content">
          <div class="stat-number">{{ collections.length }}</div>
          <div class="stat-label">收藏药材</div>
        </div>
      </div>
      <div class="stat-item">
        <i class="fas fa-eye stat-icon"></i>
        <div class="stat-content">
          <div class="stat-number">{{ history.length }}</div>
          <div class="stat-label">浏览记录</div>
        </div>
      </div>
    </div>
  </div>

  <!-- 编辑表单 -->
  <div v-if="isEditing" class="profile-form">
    <div class="form-row">
      <div class="form-item">
        <label>用户名</label>
        <input type="text" v-model="user.username" readonly>
      </div>
      <div class="form-item">
        <label>昵称</label>
        <input type="text" v-model="user.nickname">
      </div>
    </div>
    <div class="form-row">
      <div class="form-item">
        <label>手机号码</label>
        <input type="text" v-model="user.phone" placeholder="请输入手机号码">
      </div>
      <div class="form-item">
        <label>电子邮箱</label>
        <input type="email" v-model="user.email">
      </div>
    </div>
    <div class="form-row full-width">
      <div class="form-item">
        <label>个人简介</label>
        <textarea v-model="user.introduction" placeholder="请输入个人简介（选填）"></textarea>
      </div>
    </div>
    <div class="form-actions">
      <button type="button" class="save-btn" @click="saveProfile">
        <i class="fas fa-save mr-2"></i>保存修改
      </button>
      <button type="button" class="cancel-btn" @click="cancelEdit">
        <i class="fas fa-times mr-2"></i>取消
      </button>
    </div>
  </div>

  <!-- 查看模式 -->
  <div v-else class="profile-view">
    <div class="form-row">
      <div class="form-item">
        <label>用户名</label>
        <div class="form-value">{{ user.username }}</div>
      </div>
      <div class="form-item">
        <label>昵称</label>
        <div class="form-value">{{ user.nickname }}</div>
      </div>
    </div>
    <div class="form-row">
      <div class="form-item">
        <label>手机号码</label>
        <div class="form-value">{{ user.phone || '请输入手机号码' }}</div>
      </div>
      <div class="form-item">
        <label>电子邮箱</label>
        <div class="form-value">{{ user.email }}</div>
      </div>
    </div>
    <div class="form-row full-width">
      <div class="form-item">
        <label>个人简介</label>
        <div class="form-value">{{ user.introduction || '请输入个人简介（选填）' }}</div>
      </div>
    </div>
  </div>
</div>

            <!-- 我的收藏 Tab -->
            <div v-show="activeTab === 'collection'" class="collection-container">
              <h3 class="collection-title">
                <!-- <i class="fas fa-star text-herbal-green mr-2"></i> -->
                我的收藏
              </h3>
              <div class="collection-header">
                <span class="collection-count">共 {{ collections.length }} 个收藏</span>
                <button @click="clearCollections" class="clear-collection-btn">
                  <!-- <i class="fas fa-trash-alt mr-1"></i> -->
                  清空收藏
                </button>
              </div>
              <div class="collection-list">
                <div v-for="(item, index) in collections" :key="index" class="collection-item">
                  <div class="collection-item-info">
                    <h4 class="collection-item-name">{{ item.name }}</h4>
                    <p class="collection-item-category">{{ item.category }}</p>
                  </div>
                  <div class="collection-item-actions">
                    <a :href="`/herb-detail?herb_name=${item.name}`" class="view-btn">
                      查看
                    </a>
                    <button @click="removeCollection(index)" class="remove-btn">
                      取消
                    </button>
                  </div>
                </div>
                <div v-if="collections.length === 0" class="empty-collection">
                  <i class="fas fa-star-half-alt text-herbal-green/30 text-6xl mb-4"></i>
                  <p class="text-gray-500">暂无收藏的中药材，快去药材库收藏吧！</p>
                  <a href="/zhongyaoku" class="go-to-herb-btn">
                    <i class="fas fa-arrow-right mr-2"></i>
                    前往药材库
                  </a>
                </div>
              </div>
            </div>

            <!-- 浏览记录 Tab -->
            <div v-show="activeTab === 'history'" class="history-container">
              <h3 class="history-title">
                <!-- <i class="fas fa-history text-herbal-green mr-2"></i> -->
                浏览记录
              </h3>
              <div class="history-header">
                <span class="history-count">共 {{ history.length }} 条记录</span>
                <button @click="clearHistory" class="clear-history-btn">
                  <!-- <i class="fas fa-trash-alt mr-1"></i> -->
                  清空记录
                </button>
              </div>
              <div class="history-list">
                <div v-for="(item, index) in history" :key="index" class="history-item">
                  <div class="history-item-info">
                    <h4 class="history-item-name">{{ item.name }}</h4>
                    <p class="history-item-time">{{ item.time }}</p>
                  </div>
                  <div class="history-item-actions">
                    <a :href="`/herb-detail?herb_name=${item.name}`" class="view-btn">
                      查看
                    </a>
                  </div>
                </div>
                <div v-if="history.length === 0" class="empty-history">
                  <i class="fas fa-clock text-herbal-green/30 text-6xl mb-4"></i>
                  <p class="text-gray-500">暂无浏览记录，快去探索中药材吧！</p>
                  <a href="/zhongyaoku" class="go-to-herb-btn">
                    <i class="fas fa-arrow-right mr-2"></i>
                    前往药材库
                  </a>
                </div>
              </div>
            </div>

            <!-- 系统设置 Tab -->
            <div v-show="activeTab === 'settings'" class="settings-container">
              <h3 class="settings-title">
                <!-- <i class="fas fa-cog text-herbal-green mr-2"></i> -->
                系统设置
              </h3>
              <div class="settings-content">
                <!-- 密码修改 -->
                <div class="settings-section">
                  <h4 class="section-title">修改密码</h4>
                  <div class="password-form">
                    <div class="form-group">
                      <label class="form-label">当前密码</label>
                      <input
                        type="password"
                        v-model="passwordForm.oldPassword"
                        class="form-input"
                        placeholder="请输入当前密码"
                      >
                    </div>
                    <div class="form-group">
                      <label class="form-label">新密码</label>
                      <input
                        type="password"
                        v-model="passwordForm.newPassword"
                        class="form-input"
                        placeholder="请输入新密码"
                      >
                    </div>
                    <div class="form-group">
                      <label class="form-label">确认新密码</label>
                      <input
                        type="password"
                        v-model="passwordForm.confirmPassword"
                        class="form-input"
                        placeholder="请确认新密码"
                      >
                    </div>
                    <button @click="changePassword" class="btn btn-primary">
                      <!-- <i class="fas fa-key mr-2"></i> -->
                      修改密码
                    </button>
                  </div>
                </div>


                <!-- 账号安全 -->
                <div class="settings-section">
                  <!-- <h4 class="section-title">账号安全</h4> -->
                  <div class="security-settings">
                    <div class="security-item">
                      <div class="security-info">
                        <p class="security-title">登录密码</p>
                        <p class="security-desc">上次修改：2026-01-15</p>
                      </div>
                      <button class="btn btn-secondary">修改</button>
                    </div>

                    <!-- <div class="settings-section"> -->
                  <button @click="logout" class="btn btn-danger w-full">
                    <!-- <i class="fas fa-sign-out-alt mr-2"></i> -->
                    退出登录
                  </button>
                <!-- </div> -->
                  </div>
                </div>

                <!-- 退出登录 -->

              </div>
            </div>
          </div>
        </div>

        <!-- 页脚 -->
        <footer class="footer">
          <p>© 2026 中药材价格信息系统 版权所有 | 本网站信息仅供参考，不作为用药依据</p>
        </footer>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import AppSidebar from '@/components/AppSidebar.vue'

defineOptions({
  name: 'UserProfilePage',
})

const router = useRouter()

// 从本地存储加载头像，如果没有则使用默认头像
const savedAvatar = localStorage.getItem('userAvatar')
const user = ref({
  username: 'admin',
  email: 'admin@herbal.com',
  nickname: '中药材管理员',
  phone: '',
  introduction: '',
  avatar: savedAvatar || 'https://via.placeholder.com/150'
})

const uploading = ref(false)
const uploadSuccess = ref(false)

// 激活的标签页
const activeTab = ref('profile')

// 编辑模式状态
const isEditing = ref(false)

// 收藏和历史记录数据
const collections = ref([
  { name: '艾叶', category: '叶类', image: 'https://picsum.photos/id/152/100/100' },
  { name: '当归', category: '根及根茎类', image: 'https://picsum.photos/id/106/100/100' },
  { name: '金银花', category: '花类', image: 'https://picsum.photos/id/116/100/100' }
])

const history = ref([
  { name: '黄芪', image: 'https://picsum.photos/id/126/100/100', time: '2026-03-18 14:30' },
  { name: '甘草', image: 'https://picsum.photos/id/136/100/100', time: '2026-03-17 09:15' },
  { name: '枸杞', image: 'https://picsum.photos/id/146/100/100', time: '2026-03-16 16:45' }
])

// 密码修改表单
const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 通知设置
// 暂时注释掉未使用的变量
/* const notificationSettings = ref({
  price: true,
  product: true,
  system: true
}) */

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const response = await axios.get('/api/user-info')
    if (response.data) {
      user.value = {
        ...user.value,
        username: response.data.username,
        email: response.data.email,
        nickname: response.data.nickname || '中药材管理员',
        phone: response.data.phone || '',
        introduction: response.data.introduction || ''
      }
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

// 组件挂载时获取用户信息
onMounted(() => {
  fetchUserInfo()
  // 删除冗余的原生DOM事件绑定（改用label原生机制）
})

// 切换标签页
const switchTab = (tab: string) => {
  activeTab.value = tab
}

// 滚动到个人资料表单
// 暂时注释掉未使用的函数
/* const scrollToProfileForm = () => {
  const profileSection = document.querySelector('form')
  if (profileSection) {
    profileSection.scrollIntoView({ behavior: 'smooth' })
  }
} */

// 保存个人资料
const saveProfile = () => {
  alert('个人资料保存成功！')
  isEditing.value = false
}

// 进入编辑模式
const editProfile = () => {
  isEditing.value = true
}

// 取消编辑
const cancelEdit = () => {
  isEditing.value = false
}

// 修改密码
const changePassword = () => {
  if (!passwordForm.value.oldPassword) {
    alert('请输入当前密码！')
    return
  }
  if (!passwordForm.value.newPassword) {
    alert('请输入新密码！')
    return
  }
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    alert('两次输入的密码不一致！')
    return
  }

  alert('密码修改成功！请重新登录')
  passwordForm.value = {
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
}

// 移除收藏
const removeCollection = (index: number) => {
  collections.value.splice(index, 1)
}

// 清空收藏
const clearCollections = () => {
  if (confirm('确定要清空所有收藏吗？')) {
    collections.value = []
  }
}

// 清空浏览记录
const clearHistory = () => {
  if (confirm('确定要清空所有浏览记录吗？')) {
    history.value = []
  }
}

const logout = () => {
  console.log('退出登录')
  router.replace('/')
}

// 头像上传处理
const handleAvatarUpload = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    const file = input.files[0]
    // 校验文件类型
    if (!file.type.startsWith('image/')) {
      alert('请选择图片文件（JPG/PNG等）')
      return
    }
    // 校验文件大小（5MB）
    if (file.size > 5 * 1024 * 1024) {
      alert('图片大小不能超过5MB，请选择更小的图片')
      return
    }

    uploading.value = true
    uploadSuccess.value = false

    // 使用Canvas压缩裁剪图片
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()

    // 解决跨域问题（可选）
    img.crossOrigin = 'anonymous'

    img.onload = () => {
      // 目标尺寸：200x200圆形头像
      const targetSize = 200
      canvas.width = targetSize
      canvas.height = targetSize

      // 计算缩放比例，居中显示
      const scale = Math.max(targetSize / img.width, targetSize / img.height)
      const scaledWidth = img.width * scale
      const scaledHeight = img.height * scale
      const offsetX = (targetSize - scaledWidth) / 2
      const offsetY = (targetSize - scaledHeight) / 2

      if (ctx) {
        // 填充白色背景（解决透明图片显示问题）
        ctx.fillStyle = '#ffffff'
        ctx.fillRect(0, 0, targetSize, targetSize)
        // 绘制缩放后的图片
        ctx.drawImage(img, offsetX, offsetY, scaledWidth, scaledHeight)
        // 转换为base64（80%质量）
        const avatarUrl = canvas.toDataURL('image/jpeg', 0.8)

        // 更新头像并保存到本地存储
        user.value.avatar = avatarUrl
        localStorage.setItem('userAvatar', avatarUrl)

        // 通知其他组件更新头像（如导航栏）
        window.dispatchEvent(new CustomEvent('avatar-updated', {
          detail: { avatar: avatarUrl }
        }))

        // 结束上传状态
        uploading.value = false
        uploadSuccess.value = true
        setTimeout(() => {
          uploadSuccess.value = false
        }, 3000)
      }
    }

    img.onerror = () => {
      alert('图片加载失败，请重试或选择其他图片')
      uploading.value = false
    }

    // 读取本地图片文件
    img.src = URL.createObjectURL(file)
  }
}
</script>

<style scoped>
:root {
  --herbal-green: #2D5D2B;
  --herbal-lightGreen: #4A7A48;
  --herbal-dark: #5C4033;
}

.page-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* 个人资料 */
.profile-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 24px;
  text-align: center;
  color: #1f2937;
}

.profile-container {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
}
/* 个人信息卡片 */
.profile-info-card {
  background-color: #f8f9fa;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 32px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 24px;
}

.profile-avatar {
  position: relative;
  width: 100px;
  height: 100px;
}

.profile-avatar .avatar-image {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #2d5d2b;
}

.role-badge {
  position: absolute;
  bottom: 0;
  right: 0;
  background-color: #2d5d2b;
  color: white;
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 12px;
  border: 2px solid white;
}

.profile-info {
  flex: 1;
}

.profile-name {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 4px;
}

.profile-role {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 16px;
}

.edit-profile-btn {
  background-color: #2d5d2b;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: background-color 0.3s ease;
}

.edit-profile-btn:hover {
  background-color: #43a359;
}

/* 统计信息 */
.profile-stats {
  display: flex;
  gap: 48px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-icon {
  font-size: 24px;
  color: #2d5d2b;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
}

/* 表单样式 */
.profile-form {
  background-color: white;
  border-radius: 12px;
  padding: 21px;
  min-height: 400x;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.profile-view {
  background-color: white;
  border-radius: 12px;
  padding: 24px;
  min-height: 420px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.form-row {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
}

.form-row.full-width {
  flex-direction: column;
}

.form-item {
  flex: 1;
}

.form-item label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
  margin-bottom: 8px;
}

.form-item input,
.form-item textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s ease;
}

.form-item input:focus,
.form-item textarea:focus {
  outline: none;
  border-color: #2d5d2b;
  box-shadow: 0 0 0 3px rgba(45, 93, 43, 0.1);
}

.form-item textarea {
  resize: vertical;
  min-height: 100px;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
}

.save-btn {
  background-color: #2d5d2b;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: background-color 0.3s ease;
}

.save-btn:hover {
  background-color: #43a359;
}

.cancel-btn {
  background-color: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
}

.cancel-btn:hover {
  background-color: #e5e7eb;
}

/* 查看模式 */


.form-value {
  width: 100%;
  padding: 10px 12px;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 14px;
  color: #374151;
  min-height: 40px;
  display: flex;
  align-items: center;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .profile-header {
    flex-direction: column;
    text-align: center;
  }

  .profile-stats {
    justify-content: center;
    gap: 32px;
  }

  .form-row {
    flex-direction: column;
  }

  .form-actions {
    flex-direction: column;
  }

  .save-btn,
  .cancel-btn {
    justify-content: center;
  }
}

/* 我的收藏 */
.collection-container {
  background-color: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  height: 100%;
  /* overflow-y: auto; */
}

.collection-title {
  width: 750px;
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.collection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.collection-count {
  font-size: 14px;
  color: #6b7280;
}

.clear-collection-btn {
  background-color: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
}

.clear-collection-btn:hover {
  background-color: #e5e7eb;
}

.collection-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.collection-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  border-bottom: 1px solid #f3f4f6;
}

.collection-item:last-child {
  border-bottom: none;
}

.collection-item-info {
  flex: 1;
}

.collection-item-name {
  font-size: 16px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
}

.collection-item-category {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 12px;
}

.collection-item-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.view-btn {
  background-color: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  text-decoration: none;
  transition: all 0.3s ease;
}

.view-btn:hover {
  background-color: #e5e7eb;
}

.remove-btn {
  background-color: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
}

.remove-btn:hover {
  background-color: #fee2e2;
}

.empty-collection {
  text-align: center;
  padding: 48px 24px;
}

.go-to-herb-btn {
  display: inline-flex;
  align-items: center;
  background-color: #2d5d2b;
  color: white;
  padding: 10px 20px;
  border-radius: 6px;
  text-decoration: none;
  font-size: 14px;
  margin-top: 16px;
  transition: background-color 0.3s ease;
}

.go-to-herb-btn:hover {
  background-color: #43a359;
}

/* 浏览记录 */
.history-container {
  background-color: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
}

.history-title {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.history-count {
  font-size: 14px;
  color: #6b7280;
}

.clear-history-btn {
  background-color: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
}

.clear-history-btn:hover {
  background-color: #e5e7eb;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  border-bottom: 1px solid #f3f4f6;
}

.history-item:last-child {
  border-bottom: none;
}

.history-item-info {
  flex: 1;
}

.history-item-name {
  font-size: 16px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
}

.history-item-time {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 12px;
}

.history-item-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 系统设置 */
.settings-container {
  background-color: white;
  border-radius: 12px;
  padding: 24px;
  height: 762px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  max-width: 800px;
  margin: 0 auto;
  width: 800px;
  display: flex;
  flex-direction: column;
}

.settings-title {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
}

/* 系统设置内容 */
.settings-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* 设置区块 */
.settings-section {
  background-color: #f8f9fa;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 区块标题 */
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

/* 密码表单 */
.password-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 14px;
  font-weight: 500;
  color: #4b5563;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: #2d5d2b;
  box-shadow: 0 0 0 3px rgba(45, 93, 43, 0.1);
}

/* 按钮样式 */
.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.btn-primary {
  background-color: #2d5d2b;
  color: white;
}

.btn-primary:hover {
  background-color: #43a359;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(45, 93, 43, 0.2);
}

.btn-secondary {
  background-color: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  background-color: #e5e7eb;
  transform: translateY(-1px);
}

.btn-danger {
  background-color: #dc2626;
  color: white;
  width: 100%;
  text-align: center;
}

.btn-danger:hover {
  background-color: #b91c1c;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(220, 38, 38, 0.2);
}

/* 通知设置 */
.notification-settings {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.notification-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background-color: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
}

.notification-item:hover {
  border-color: #d1d5db;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.notification-info {
  flex: 1;
}

.notification-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
}

.notification-desc {
  font-size: 13px;
  color: #6b7280;
}

/* 开关样式 */
.toggle-switch {
  position: relative;
  width: 50px;
  height: 24px;
}

.toggle-checkbox {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-label {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #e5e7eb;
  border-radius: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.toggle-label:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  border-radius: 50%;
  transition: all 0.3s ease;
}

.toggle-checkbox:checked + .toggle-label {
  background-color: #2d5d2b;
}

.toggle-checkbox:checked + .toggle-label:before {
  transform: translateX(26px);
}

/* 账号安全 */
.security-settings {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background-color: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  transition: all 0.3s ease;
}

.security-item:hover {
  border-color: #d1d5db;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.security-info {
  flex: 1;
}

.security-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
}

.security-desc {
  font-size: 13px;
  color: #6b7280;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .settings-section {
    padding: 20px;
  }

  .notification-item,
  .security-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .toggle-switch {
    align-self: flex-end;
  }

  .btn {
    width: 100%;
  }
}

.function-nav-title {
  margin-top: 10px ;
  padding: 5px 20px;
  font-size: 18px; /* 对应原 text-lg (18px)，可直接修改 */
  font-weight: 700; /* 对应原 font-bold */
  margin-bottom: 16px; /* 对应原 mb-4 (16px) */
  display: flex; /* 对应原 flex */
  align-items: center; /* 对应原 items-center */
  color: #1f2937; /* 对应原 text-gray-800 */
}

/* 新增核心样式：收藏/浏览间距控制 */
.collection-history-container {
  --item-gap: 60px; /* 核心控制：收藏和浏览的间隔宽度，可直接修改 */
  gap: var(--item-gap) !important;
  display: flex !important;
  flex-direction: row !important;
  padding: 20px 0 !important;

}

.collect-history-text {
  font-size: 20px; /* 👉 只需改这个数值就能调整字体大小 */
  color: #6b7280; /* 保持和原有一致的灰色 */
  margin-left: 4px; /* 替代 ml-1，等价于 0.25rem */
  line-height: 1.2; /* 保证和数字对齐 */
  width: 30px;
}

.collect-history-icon {
  font-size: 20px; /* 👉 改这个数值调整图标大小 */
  color: var(--herbal-green);
}

/* 收藏/浏览子项样式 */
.collection-item, .history-item {
  display: flex;
  align-items: center;
  gap: 8px; /* 图标和文字的间距，可单独调整 */
  padding: 30px 35px;

}

/* 间距预设变体（可选） */
.collection-history-container.small-gap {
  --item-gap: 40px; /* 小间距 */
}

.collection-history-container.large-gap {
  --item-gap: 120px; /* 大间距 */
}

/* 昵称居中 */
.nickname-title {
  text-align: center;
  width: 100%; /* 确保宽度占满父容器，居中效果更完整 */
  font-size: 22px;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  background-color: #f9fafb;
  padding: 24px;
  margin-left: 0;
  margin-top: 70px;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.card-shadow {
  box-shadow: 0 4px 12px rgba(92, 64, 51, 0.1);
}

/* 开关样式优化 */
.toggle-checkbox {
  z-index: 1;
}

.toggle-checkbox:checked {
  right: 0;
  border-color: var(--herbal-green);
}

.toggle-checkbox:checked + .toggle-label {
  background-color: var(--herbal-green);
}

.toggle-label {
  position: relative;
  background-color: #e5e7eb;
  transition: background-color 0.2s ease;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 16px;
}

.modal-content {
  background-color: white;
  border-radius: 0.75rem;
  width: 100%;
  max-width: 480px;
  padding: 24px;
}

/* 页脚样式 */
.footer {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
  text-align: center;
  font-size: 14px;
  color: #6b7280;
}

/* 响应式布局：屏幕较小时允许横向滚动 */
@media screen and (max-width: 1200px) {
  .filter-row {
    overflow-x: auto;
    padding-bottom: 8px;
  }

  .cluster-filter-row {
    overflow-x: auto;
    padding-bottom: 8px;
  }
}

/* 三盒布局 */
.three-box-layout {
  display: grid;
  grid-template-columns: 1fr 1fr 2fr;
  grid-template-rows: 1fr 1fr;
  grid-template-areas:
    "left-top right right"
    "left-bottom right right";
  gap: 24px;
  margin-bottom: 32px;
  min-height: 700px;
}

/* 头像区域核心样式 - 核心修改：调高头像高度 */
.avatar-container {
  position: relative;
  width: 120px;   /* 从80px改为120px，宽度调高 */
  height: 120px;  /* 从80px改为120px，高度调高（核心修改） */
  margin: 40px auto 16px auto; /* 底部间距从12px改为16px，保持比例协调 */
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-wrapper {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background-color: rgba(45, 93, 43, 0.1);
  border: 2px solid rgba(45, 93, 43, 0.2);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer; /* 提示可点击 */
  transition: border-color 0.2s ease;
}

.avatar-wrapper:hover {
  border-color: var(--herbal-green);
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover; /* 裁剪适配，不拉伸 */
  border-radius: 50%;
}

/* 右下角相机按钮 - 同步放大，保持比例 */
.avatar-upload-btn {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 30px;    /* 从24px改为30px，同步放大 */
  height: 30px;   /* 从24px改为30px，同步放大 */
  border-radius: 50%;
  background-color: var(--herbal-green);
  color: white;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 10; /* 确保在头像上层 */
}

.avatar-upload-btn:hover {
  background-color: var(--herbal-dark);
  transform: scale(1.1);
}

.avatar-upload-btn i {
  font-size: 12px; /* 从10px改为12px，图标同步放大 */
}

/* 隐藏文件选择框 - 核心：只保留功能，不显示原生样式 */
.file-input-hidden {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  opacity: 0;
  visibility: hidden;
  cursor: pointer;
  z-index: -1;
}

/* 盒子通用样式 */
.box {
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  /* justify-content: center; */
  flex-direction: column;
}

.box-left-top {
  grid-area: left-top;
  height: 350px;
  width: 400px;
}

.box-left-bottom {
  grid-area: left-bottom;
  height: 368px;
  width: 400px;
}

.box-right {
  grid-area: right;
  height: 100%;
  position: relative;
}

/* 面包屑标题样式 */
/* .breadcrumb-container {
  text-sm: unset;
} */

.breadcrumb-title {
  font-size: 35px !important;
  color: #000 !important;
  font-weight: 700 !important;
  text-align: center;
  width: 100%;
}

/* 功能导航标题 */
.function-nav-title {
  margin-top: 10px;
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  color: #1f2937;
}

/* 按钮样式：统一控制宽度，让按钮变窄 */
.tab-btn {
  border: 1px solid #28a745;
  background-color: #346d32;
  width: 300px !important;
  height: 40px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition: all 0.2s ease;
  margin: 0 auto;
  padding: 0 16px !important;
  font-size: 16px !important;
  color: white;
  /* 核心：椭圆圆角（高度的一半，完美椭圆） */
  border-radius: 10px !important;
}

.tab-btn:hover {
  background-color: #43a359;
  /* border-radius: 20px !important; 保持hover时圆角一致 */
}

/* 导航容器强制垂直排列 */
nav {
  display: flex;
  flex-direction: column !important;
  gap: 12px;
}

/* 响应式布局适配 - 移动端同步调整头像大小 */
@media screen and (max-width: 1024px) {
  .three-box-layout {
    grid-template-columns: 1fr 2fr;
    grid-template-rows: 1fr 1fr;
    grid-template-areas:
      "left-top right"
      "left-bottom right";
  }

  /* 平板端头像尺寸适配 */
  .avatar-container {
    width: 100px;
    height: 100px;
  }

  .avatar-upload-btn {
    width: 28px;
    height: 28px;
  }
}

@media screen and (max-width: 768px) {
  .main-content {
    margin-left: 0;
    padding: 20px;
  }

  .three-box-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto auto;
    grid-template-areas:
      "left-top"
      "left-bottom"
      "right";
  }

  /* 移动端头像尺寸适配 */
  .avatar-container {
    width: 90px;
    height: 90px;
  }

  .avatar-upload-btn {
    width: 26px;
    height: 26px;
  }

  .breadcrumb-title {
    font-size: 20px !important;
  }
}

/* 统计模块样式 */
.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.stat-icon {
  font-size: 20px;
  color: #2e7d32; /* 主题绿色，和你的词云图匹配 */
}
.stat-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.stat-number {
  font-size: 20px;
  font-weight: bold;
  color: #2e7d32;
  line-height: 1.2;
}
.stat-label {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.2;
}
</style>
