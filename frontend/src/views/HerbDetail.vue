<template>
  <div class="page-container">
    <AppSidebar />
    <main class="main-content">
        <div class="herb-intro-container">
    <div class="herb-intro-card">
      <!-- 左侧：药材图片 -->
      <div class="herb-image-section">
        <div class="herb-image-wrapper">
          <img
            v-if="matchedImageUrl"
            :src="matchedImageUrl"
            :alt="herbData.name"
            class="herb-image"
          >
          <div v-else class="herb-image-placeholder">
            <p class="text-gray-500 mt-2">暂无图片</p>
          </div>
        </div>
      </div>


      <!-- 右侧：药材信息 -->
      <div class="herb-info-section">


        <!-- 品名 -->
        <div class="info-item">
          <span class="info-label">药材名称：</span>
          <span class="info-value">{{ herbData.name || '请填写药材名称' }}</span>
        </div>

        <!-- 产区分布 -->
        <div class="info-item">
          <span class="info-label">分布区域：</span>
          <span class="info-value">{{ herbData.distribution || '无' }}</span>
        </div>

        <div class="info-item">
          <span class="info-label">采集时间：</span>
          <span class="info-value">{{ herbData.harvest_season || '无' }}</span>
        </div>

        <!-- 品种特点 -->
        <div class="info-item">
          <span class="info-label">用法：</span>
          <span class="info-value">{{ herbData.usage_method || '无' }}</span>
        </div>

        <div class="info-item">
          <span class="info-label">品种特点：</span>
          <span class="info-value">{{ herbData.characteristics || '无' }}</span>
        </div>
        <!-- 查看详情链接 -->
        <!-- <div class="detail-link">
          <a href="#" class="detail-link-text">查看详情>></a>
        </div> -->
      </div>


    </div>


  </div>

        <div class="symptoms-section">
        <div class="symptoms-card">
          <h2 class="symptoms-title">毒性</h2>
          <div class="symptoms-content">
            <!-- 症状列表 -->
             <div class="info-item">
          <!-- <span class="info-label">针对症状：</span> -->
                <span class="info-value">{{ herbData.taboo || '无' }}</span>
            </div>
          </div>
        </div>
        </div>


        <div class="symptoms-section">
        <div class="symptoms-card">
          <h2 class="symptoms-title">针对症状</h2>
          <div class="symptoms-content">
            <!-- 症状列表 -->
             <div class="info-item">
          <!-- <span class="info-label">针对症状：</span> -->
                <span class="info-value">{{ herbData.medicinal_effects || '无' }}</span>
            </div>
          </div>
        </div>
        </div>
        <div class="symptoms-section">
        <div class="symptoms-card">
          <h2 class="symptoms-title">形态特征</h2>
          <div class="symptoms-content">
            <!-- 症状列表 -->
             <div class="info-item">
          <!-- <span class="info-label">针对症状：</span> -->
                <span class="info-value">{{ herbData.xingtaitezheng || '无' }}</span>
            </div>
          </div>
        </div>
        </div>
        <div class="symptoms-section">
        <div class="symptoms-card">
          <h2 class="symptoms-title">生长环境</h2>
          <div class="symptoms-content">
            <!-- 症状列表 -->
             <div class="info-item">
          <!-- <span class="info-label">针对症状：</span> -->
                <span class="info-value">{{ herbData.shengzhanghuanjing || '无' }}</span>
            </div>
          </div>
        </div>
        </div>

        <div class="symptoms-section">
        <div class="symptoms-card">
          <h2 class="symptoms-title">栽培技术</h2>
          <div class="symptoms-content">
            <!-- 症状列表 -->
             <div class="info-item">
          <!-- <span class="info-label">针对症状：</span> -->
                <span class="info-value">{{ herbData.zaipeijishu || '无' }}</span>
            </div>
          </div>
        </div>
        </div>

          <!-- 返回按钮 -->
          <div class="back-button-container">
            <button @click="goBack" class="btn-custom">
               返回药材库
            </button>
          </div>

          <!-- 页脚 -->
          <footer class="footer">
            <p>© 2026 中药材价格智能分析与预测系统 版权所有</p>
         </footer>
</main>
</div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppSidebar from '@/components/AppSidebar.vue'
import axios from 'axios'

defineOptions({ name: 'HerbDetailPage' })

const route = useRoute()
const router = useRouter()
const herbName = route.query.herb_name as string

const loading = ref(true)
const error = ref('')
const herbData = ref({
  "initial": '',
  "name": '',
  "characteristics":'',
  "distribution": '',
  "harvest_season": '',
  "usage_method": '',
  "taboo":'',
  "medicinal_effects":'',
  "shengzhanghuanjing":'',
  "xingtaitezheng": '',
  "zaipeijishu": ''

})

// 1. 动态读取本地图片文件夹（@/ 对应 src/ 目录，Vite自动解析）
const herbImages = import.meta.glob('@/img/HerbImage/*.{png,jpg,jpeg,webp,gif}', { eager: true, import: 'default' })

// 2. 计算属性：根据药材名称自动匹配图片
const matchedImageUrl = computed(() => {
  if (!herbData.value.name) return ''

  // 遍历所有图片，匹配文件名（不含后缀）和药材名称
  for (const [path, url] of Object.entries(herbImages)) {
    // 提取文件名（比如 "@/img/HerbImage/艾叶.png" → "艾叶"）
    const fileName = path.split('/').pop()?.split('.')[0] || ''
    if (fileName === herbData.value.name) {
      console.log('找到匹配图片:', path, url)
      return url as string
    }
  }
  console.log('未找到匹配图片，药材名称:', herbData.value.name)
  return '' // 无匹配返回空，显示占位符
})

// 3. 补充缺失的herbCategories定义

// 新增：计算当前药材所属板块

const fetchHerbDetail = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await axios.get('/api/herb-detail', {
      params: { herb_name: herbName }
    })
    herbData.value = response.data
  } catch (err: unknown) {
    error.value = err instanceof Error ? err.message : '获取中药材详情失败'

  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push('/zhongyaoku')
}

onMounted(() => {
  if (herbName) {
    fetchHerbDetail()
  } else {
    // 无参数时默认显示艾叶数据
    // herbData.value = {
    //   name: '艾叶',
    //   initial: '菊科蒿属',
    //   scientific_name: 'Artemisia argyi Levl. et Vant.',
    //   image: 'https://picsum.photos/id/152/200/200',
    //   category: '叶类',
    //   taste: '辛、苦，温；有小毒。归肝、脾、肾经',
    //   distribution: '河南,湖北',
    //   harvest_season: '五月、六月、七月',
    //   storage_method: '阴凉干燥处，防潮，防蛀'
    // }
    error.value = ''
    loading.value = false
  }
})



</script>

<style scoped>
.herb-intro-container {
  width: 100%;
  padding: 50px;
}

.herb-intro-card {
  display: flex;
  gap: 40px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  background-color: #f0f8f0;
  padding: 60px;
  border-radius: 8px;
}

/* 左侧图片区域 */
.herb-image-section {
  flex-shrink: 0;
  height: 300px;
  width: 400px;
}

.herb-image-wrapper {
  width: 100%;
  height: 300px;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.herb-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.herb-image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  background-color: #f9fafb;
}

/* 右侧信息区域 */
.herb-info-section {
  flex: 1;
  padding-top: 20px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 16px;
  line-height: 1.6;
}

.info-label {
  width: 100px;
  flex-shrink: 0;
  color: #666;
  font-size: 16px;
}

.info-value {
  flex: 1;
  color: #333;
  font-size: 16px;
}

/* 查看详情链接 */
.detail-link {
  margin-top: 24px;
}

.detail-link-text {
  color: white;
  font-size: 18px;
  font-weight: 500;
  text-decoration: none;
}

.detail-link-text:hover {
  text-decoration: underline;
}

.back-button-container {
  display: flex;
  justify-content: center;
  margin: 32px 0 48px 0;
}

/* 新增：返回按钮的自定义类选择器 - 可以调整颜色、长宽等参数 */
.btn-custom {
  /* 尺寸参数 */
  padding: 12px 32px;
  min-width: 160px;
  height: 48px;

  /* 颜色参数 */
  background-color: #2d5d2b;
  color: #ffffff;
  border: 2px solid #2d5d2b;

  /* 字体参数 */
  font-size: 16px;
  font-weight: 500;

  /* 边框和圆角 */
  border-radius: 8px;

  /* 鼠标样式 */
  cursor: pointer;

  /* 过渡动画 */
  transition: all 0.3s ease;

  /* 阴影 */
  box-shadow: 0 2px 8px rgba(45, 93, 43, 0.2);
}

.btn-custom:hover {
  background-color: #43a359;
  border-color: #43a359;
  box-shadow: 0 4px 12px rgba(45, 93, 43, 0.3);
  transform: translateY(-2px);
}

.btn-custom:active {
  transform: translateY(0);
  box-shadow: 0 1px 4px rgba(45, 93, 43, 0.2);
}

/* 新增：统一的按钮样式（和查看全部行情按钮保持一致） */
.btn {
  padding: clamp(0.8rem, 2vw, 1.2rem) clamp(1.5rem, 3vw, 2.5rem);
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: clamp(1rem, 1.8vw, 1.2rem);
  transition: background 0.3s, transform 0.2s;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
  transition: background 0.3s, transform 0.2s, box-shadow 0.3s;
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
}

.btn-outline-green {
  border: 1px solid #28a745;
  color: #eef0f3;
  background-color: #2d5d2b;
}

.btn-outline-green:hover {
  background-color: #43a359;
  color: #eef0f3;
}


/* 第二个模块：毒性等级（独立模块，增加间距和分割） */
.toxicity-section {
  max-width: 1500px; /* 控制模块最大长度（宽度），可按需调整 */
  margin: 0 auto 2rem auto; /* 模块上下间距，与其他内容分割 */
  width: 100%;
}

/* 毒性等级卡片（控制模块整体尺寸+内边距） */
.toxicity-card {
  background-color: #ffffff; /* 卡片背景色 */
  border-radius: 12px; /* 圆角 */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); /* 阴影 */
  padding: 24px 32px; /* 👈 核心：文字与边框的距离（上下24px，左右32px），可按需调整 */
  min-height: 180px; /* 👈 控制模块最小高度，可按需调整 */
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 毒性等级标题 */
.toxicity-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

/* 毒性等级内容容器 */
.toxicity-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 毒性程度行（修复文字重叠，左右分布） */
.toxicity-level-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.toxicity-label {
  font-size: 0.875rem;
  color: #4b5563;
}
.toxicity-value {
  font-size: 0.875rem;
  font-weight: 600;
}

/* 进度条容器 */
.toxicity-bar-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.toxicity-bar {
  height: 12px; /* 进度条高度，可按需调整 */
  background: linear-gradient(to right, #6A994E, #F59E0B, #EF4444); /* 进度条渐变 */
  border-radius: 9999px;
  overflow: hidden;
  position: relative;
}
.toxicity-progress {
  height: 100%;
  border-radius: 9999px;
  background-color: transparent;
  border-right: 3px solid #ffffff; /* 进度标记线 */
  transition: width 0.3s ease;
}
/* 不同毒性等级的进度位置 */
.toxic-small { width: 25%; }
.toxic-medium { width: 50%; }
.toxic-high { width: 75%; }
.toxic-strong { width: 100%; }

/* 进度条标签（无毒/剧毒） */
.toxicity-bar-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #6b7280;
}

/* 提示文字 */
.toxicity-tip {
  font-size: 0.875rem;
  color: #374151;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb; /* 分割线 */
  margin-top: 8px;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .herb-intro-card { flex-direction: column; padding: 1.5rem; }
  .herb-image-section { flex: 0 0 auto; }
  .herb-image-wrapper { height: 250px; }
  .info-label { flex: 0 0 90px; }

  /* 移动端适配毒性模块 */
  .toxicity-card {
    padding: 16px 20px; /* 移动端缩小内边距 */
    min-height: 160px;
  }
}


.symptoms-section {
  max-width: 1470px; /* 和毒性模块保持一致的宽度 */
  margin: 0 auto 2rem auto; /* 上下间距，与其他模块分割 */
  width: 100%;
}

/* 针对症状卡片（和毒性模块样式统一） */
.symptoms-card {
  background-color: #f0f8f0; /* 统一的背景色 */
  border-radius: 12px; /* 统一的圆角 */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); /* 统一的阴影 */
  padding: 24px 32px; /* 和毒性模块一致的内边距（文字离边框距离） */
  min-height: 160px; /* 模块最小高度，可按需调整 */
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 针对症状标题（和毒性模块标题样式统一） */
.symptoms-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
  margin: 0;
}

/* 症状内容容器 */
.symptoms-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 症状列表 */
.symptoms-list {
  display: flex;
  flex-direction: column;
  gap: 12px; /* 每个症状之间的间距 */
  padding: 0;
  margin: 0;
}

/* 单个症状项 */
.symptom-item {
  display: flex;
  align-items: center;
  font-size: 0.875rem;
  color: #374151;
  line-height: 1.6;
}

/* 无症状数据占位 */
.no-symptoms {
  font-size: 0.875rem;
  color: #6b7280;
  padding: 8px 0;
}

/* 功效说明（可选补充） */
.symptoms-tip {
  font-size: 0.875rem;
  color: #374151;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb; /* 分割线，和毒性模块统一 */
  margin-top: 8px;
  margin-bottom: 8px;
}

/* 主题色定义（统一管理） */
:root {
  --primary: #6A994E; /* 中药主题绿色 */
}
.text-primary {
  color: var(--primary);
}

/* 响应式适配（和其他模块统一） */
@media (max-width: 768px) {
  .herb-intro-card { flex-direction: column; padding: 1.5rem; }
  .herb-image-section { flex: 0 0 auto; }
  .herb-image-wrapper { height: 250px; }
  .info-label { flex: 0 0 90px; }

  /* 移动端适配毒性模块 */
  .toxicity-card {
    padding: 16px 20px;
    min-height: 160px;
  }

  /* 移动端适配针对症状模块 */
  .symptoms-card {
    padding: 16px 20px; /* 移动端缩小内边距 */
    min-height: 140px;
  }
}
</style>

<style scoped>
.page-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  background-color: #f0f8f0;
  padding: 40px;
  margin-top: 0; /* 移除顶部margin，保持布局一致 */
}

.main-content1 {
  width:100%;
  flex: 1;
  overflow-y: auto;
  background-color: white;
  padding: 20px;
  margin-top: 0; /* 移除顶部margin，保持布局一致 */
}

.footer {
  background-color: #f0f8f0;
  color: var(--text-dark);
  padding: 20px 15% !important; /* 缩小上下内边距，更紧凑 */
  text-align: center;
  margin-top: auto !important; /* 关键：自动推到容器底部 */
  width: 100%;
  box-sizing: border-box;
}

/* 自定义样式 */
.card-shadow {
  box-shadow: 0 4px 12px rgba(92, 64, 51, 0.1);
}

.toxic-level {
  background: linear-gradient(90deg, #2D5D2B 0%, #E53E3E 100%);
  border-radius: 999px;
  height: 8px;
}

/* 新增：板块分类样式优化 */
:deep(.hover\:bg-gray-50:hover) {
  background-color: #f9fafb;
}

:deep(.bg-herbal-green\/5) {
  background-color: rgba(45, 93, 43, 0.05);
}

/* 颜色变量 */
:deep(.text-herbal-green) {
  color: #2D5D2B;
}

:deep(.bg-herbal-green) {
  background-color: #2D5D2B;
}

:deep(.bg-herbal-lightGreen) {
  background-color: #4A7A48;
}

:deep(.bg-herbal-dark) {
  background-color: #5C4033;
}

:deep(.border-herbal-green) {
  border-color: #2D5D2B;
}

:deep(.hover\:bg-herbal-green:hover) {
  background-color: #2D5D2B;
}

:deep(.hover\:bg-herbal-dark:hover) {
  background-color: #5C4033;
}

:deep(.hover\:text-herbal-green:hover) {
  color: #2D5D2B;
}
</style>
