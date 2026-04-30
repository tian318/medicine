<template>
  <div class="herb-intro-container">
    <div class="herb-intro-card">
      <!-- 左侧：药材图片 -->
      <div class="herb-image-section">
        <div class="herb-image-wrapper">
          <img 
            v-if="herbData.image" 
            :src="herbData.image" 
            :alt="herbData.name"
            class="herb-image"
          >
          <div v-else class="herb-image-placeholder">
            <i class="fas fa-seedling text-4xl text-gray-400"></i>
            <p class="text-gray-500 mt-2">暂无图片</p>
          </div>
        </div>
      </div>

      <!-- 右侧：药材信息 -->
      <div class="herb-info-section">
        <!-- 品名 -->
        <div class="info-item">
          <span class="info-label">品名：</span>
          <span class="info-value">{{ herbData.name || '请填写品名' }}</span>
        </div>

        <!-- 别名 -->
        <div class="info-item">
          <span class="info-label">别名：</span>
          <span class="info-value">{{ herbData.alias || '请填写别名' }}</span>
        </div>

        <!-- 产新时间 -->
        <div class="info-item">
          <span class="info-label">产新时间：</span>
          <span class="info-value">{{ herbData.harvestTime || '请填写产新时间' }}</span>
        </div>

        <!-- 产区分布 -->
        <div class="info-item">
          <span class="info-label">产区分布：</span>
          <span class="info-value">{{ herbData.distribution || '请填写产区分布' }}</span>
        </div>

        <!-- 品种特点 -->
        <div class="info-item">
          <span class="info-label">品种特点：</span>
          <span class="info-value">{{ herbData.characteristics || '请填写品种特点' }}</span>
        </div>

        <!-- 查看详情链接 -->
        <div class="detail-link">
          <a href="#" class="detail-link-text">查看详情>></a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// 药材数据结构
interface HerbData {
  name: string
  alias: string
  harvestTime: string
  distribution: string
  characteristics: string
  image: string
}

// 药材数据 - 您可以在这里填写内容
const herbData = ref<HerbData>({
  name: '',
  alias: '',
  harvestTime: '',
  distribution: '',
  characteristics: '',
  image: ''
})

// 示例数据（可直接使用）
// const herbData = ref<HerbData>({
//   name: '白术',
//   alias: '冬术,冬白术,杨枪蓟,种术,浙术,干术,山芥,山连,山蓟,山精,乞力伽,天蓟,术',
//   harvestTime: '九月,十月,十一月',
//   distribution: '安徽,河北,河南,湖南,陕西,四川,浙江,重庆',
//   characteristics: '易变色走油,易掺假,易受旱情影响,易受雨涝影响,生长期1年,生长期易受行情影响,种植费工时,采挖（摘）加工费工时,常用大宗,家种主供,滋补',
//   image: ''
// })
</script>

<style scoped>
.herb-intro-container {
  width: 100%;
  padding: 20px;
}

.herb-intro-card {
  display: flex;
  gap: 40px;
  background-color: white;
  padding: 24px;
  border-radius: 8px;
}

/* 左侧图片区域 */
.herb-image-section {
  flex-shrink: 0;
  width: 400px;
}

.herb-image-wrapper {
  width: 100%;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.herb-image {
  width: 100%;
  height: auto;
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
  padding-top: 8px;
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
  color: #2D5D2B;
  font-size: 18px;
  font-weight: 500;
  text-decoration: none;
}

.detail-link-text:hover {
  text-decoration: underline;
}
</style>
