<template>
  <div class="page-container">
    <AppSidebar />
    
    <main class="main-content">
      <!-- 首屏Banner -->
      <section class="banner">
        <h1>一站式中药材产业数据服务平台</h1>
        <p>整合全国药材资源，提供实时行情、专业资讯与智能价格分析服务</p>
        <div class="stats-row">
          <div class="stat-item">
            <div class="stat-number">100万+</div>
            <div class="stat-label">平台数据量</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">800+</div>
            <div class="stat-label">药材品种数</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">10,000+</div>
            <div class="stat-label">市场资讯数</div>
          </div>
        </div>
        <div class="banner-buttons">
          <button class="btn btn-green" @click="handleViewPrice">查看价格</button>
          <button class="btn btn-green" @click="handlePricePredict">价格预测</button>
        </div>
      </section>

      <!-- 平台服务模块 -->
      <section class="service-section">
        <h2 class="section-title">服务功能</h2>
        <p class="section-subtitle">中药材价格智能分析与预测系统，助力行业高效发展</p>
        <div class="service-cards">
          <div class="service-card" v-for="(service, index) in serviceList" :key="index">
            <div class="icon-title-container">
              <div class="service-icon">{{ service.icon }}</div>
              <h3>{{ service.title }}</h3>
            </div>
            <p>{{ service.desc }}</p>
            <ul class="service-list">
              <li v-for="(item, idx) in service.list" :key="idx">{{ item }}</li>
            </ul>
            <a 
              href="#" 
              class="more-link" 
              :class="{ 'more-link-active': hoveredServiceIndex === index }"
              @click.prevent="handleServiceMore(service)"
              @mouseenter="hoveredServiceIndex = index"
              @mouseleave="hoveredServiceIndex = -1"
            >
              查看更多 →
            </a>
          </div>
        </div>
      </section>

      <!-- 热门药材模块 -->
      <section class="hot-herbs-section">
        <h2 class="section-title">热门药材</h2>
        <p class="section-subtitle">热门药材价格实时更新，行情一目了然</p>
        <div class="herbs-grid">
          <div class="herb-card" v-for="(herb, index) in hotHerbsList" :key="index">
            <div class="herb-icon">{{ herb.icon }}</div>
            <div class="herb-name">{{ herb.name }}</div>
            <div class="herb-price">¥{{ herb.price }}/kg</div>
            <div :class="['herb-change', getChangeClass(herb.change)]">
              {{ herb.change > 0 ? '↑' : herb.change < 0 ? '↓' : '' }} {{ Math.abs(herb.change) }}%
            </div>
            <div class="herb-info">
              <span>产地: {{ herb.origin }}</span>
            </div>
          </div>
        </div>
        <button class="btn btn-outline-green" @click="handleViewAllMarket">查看全部行情</button>
      </section>

      <!-- 页脚 -->
      <!-- <footer class="footer">
        <div class="footer-content">
          <div class="footer-col">
            <div class="footer-logo">
              <span>🌿</span> 中药材产业服务平台
            </div>
            <p class="footer-desc">
              汇聚全国优质药材资源，提供实时行情、权威资讯与安全的交易服务，助力中药材行业数字化发展。
            </p>
          </div>
          <div class="footer-col">
            <h4 class="footer-title">快速链接</h4>
            <ul class="footer-links">
              <li><a href="#">系统首页</a></li>
              <li><a href="#">药材产地</a></li>
              <li><a href="#">价格预览</a></li>
              <li><a href="#">价格走势</a></li>
              <li><a href="#">药材库</a></li>
            </ul>
          </div>
          <div class="footer-col">
            <h4 class="footer-title">联系我们</h4>
            <ul class="contact-info">
              <li><span>📞</span> 400-123-4567</li>
              <li><span>📧</span> contact@yaocai.com</li>
              <li><span>📍</span> 北京市朝阳区药材大厦</li>
            </ul>
          </div>
        </div>
        <div class="footer-bottom">
          © 2026 中药材产业服务平台 版权所有
        </div>
      </footer> -->
      <footer class="footer">
        <p>© 2026 灵汐药策 版权所有</p>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
// 确保AppSidebar导入路径正确
import AppSidebar from '@/components/AppSidebar.vue'

const router = useRouter()

// 记录当前悬停和点击的服务索引
const hoveredServiceIndex = ref(-1)
const clickedServiceIndex = ref(-1)

// 服务列表数据
const serviceList = ref([
  {
    icon: '📰',
    title: '资讯动态',
    desc: '及时了解药材行业最新消息，不落后市场一步',
    list: ['市场动态', '资讯周报', '技术创新'],
    path: '/zixundongtai'
  },
  {
    icon: '🏪',
    title: '市场行情',
    desc: '地图展示药材产地与市场，支持筛选，可查看药材价格、走势及涨跌数据',
    list: ['实时价格', '市场分布', '产地分布'],
    path: '/yaocaichandi'
  },
  {
    icon: '🤝',
    title: '市场预测',
    desc: '集成了多模型价格预测与市场情绪分析两大核心功能',
    list: ['价格预测', '情绪分析'],
    path: '/shichangfenxi'
  },
  {
    icon: '📊',
    title: '价格预览',
    desc: '实时更新药材价格走势与市场分析，数据权威精准',
    list: ['价格展示', '价格分析', '价格分布'],
    path: '/jiageyulan'
  },
  {
    icon: '📈',
    title: '价格走势',
    desc: '筛选药材、规格与时间范围，用于分析药材价格趋势并进行市场价格比较',
    list: ['价格趋势', '价格比较', '相关性分析'],
    path: '/jiagezoushi'
  },
  {
    icon: '🌿',
    title: '药材展示',
    desc: '首字母快速筛选中药材，可查看各类中药材的详细性状与功效信息',
    list: ['药材检索', '信息查询', '功效展示'],
    path: '/zhongyaoku'
  }
])

// 热门药材数据
const hotHerbsList = ref([
  { icon: '🎍', name: '青葙子', price: 100, change: 100.0, origin: '亳州' },
  { icon: '🌿', name: '当归', price: 45, change: -2.1, origin: '甘肃', volume: '89吨' },
  { icon: '🌱', name: '款冬花', price: 120, change: 71.43, origin: '甘肃陇西县' },
  { icon: '🪴', name: '大风子', price: 40, change: 66.67, origin: '安国' },
  { icon: '🪨', name: '鱼脑石', price: 200, change: 66.67, origin: '安国' },
  { icon: '🌾', name: '芒硝', price: 2, change: 66.67, origin: '亳州' }
])

// 按钮点击事件
const handleViewPrice = () => {
  router.push('/jiageyulan')
}

const handlePricePredict = () => {
  router.push('/shichangfenxi')
}

const handleViewAllMarket = () => {
  router.push('/yaocaichandi')
}

const handleServiceMore = (service, index) => {
  clickedServiceIndex.value = index
  if (service.path) {
    router.push(service.path)
  }
}

// 获取价格变动样式类名
const getChangeClass = (change) => {
  if (change > 0) return 'change-up'
  if (change < 0) return 'change-down'
  return 'change-zero'
}
</script>

<style scoped>
/* 定义AppSidebar需要的CSS变量（关键！） */
:root {
  --primary-green: #28a745;
  --dark-green: #1e7e34;
  --light-bg: #f5f7f9;
  --text-dark: #212529;
  --text-light: #6c757d;
  --success-green: #28a745;
  --danger-red: #dc3545;
  --white: #ffffff;
  --herbal-green: #2d5d2b; /* 新增：和AppSidebar一致的绿色变量 */
}

/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: "Microsoft YaHei", sans-serif;
}

.page-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  background-color: #f9fafb;
  margin-top: 70px;
}

/* 首屏Banner样式：移除min-height:100vh，避免覆盖 */
.banner {
  background-color: var(--herbal-green);
  color: var(--white);
  text-align: center;
  padding: 190px 5%; /* 用padding撑高，替代100vh */
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}

.banner h1 {
  font-size: clamp(2.5rem, 5vw, 4rem);
  margin-bottom: 25px;
  line-height: 1.2;
  color: white;
}

.banner p {
  font-size: clamp(1rem, 2vw, 1.5rem);
  margin-bottom: 40px;
  opacity: 0.9;
  max-width: 800px;
  line-height: 1.5;
  color: white;
}

.stat-number {
  font-size: clamp(1.8rem, 4vw, 2.8rem);
  font-weight: bold;
  margin-bottom: 10px;
  color: white;
}

.stat-label {
  font-size: clamp(0.9rem, 1.5vw, 1.2rem);
  opacity: 0.8;
  color: white;
}

.stats-row {
  display: flex;
  justify-content: center;
  gap: 3vw;
  margin-bottom: 50px;
  flex-wrap: wrap;
}

.stat-item {
  background-color: rgba(255,255,255,0.1);
  padding: clamp(1.5rem, 3vw, 2.5rem) clamp(2rem, 4vw, 3.5rem);
  border-radius: 8px;
  /* 👇 核心修改：固定宽度，替换原来的min-width */
  width: 350px; /* 可根据需求调整数值，比如200px/250px */
  min-width: unset; /* 清除原有自适应min-width */
  backdrop-filter: blur(5px);
}

.banner-buttons {
  display: flex;
  justify-content: center;
  gap: clamp(1rem, 2vw, 2rem);
  flex-wrap: wrap;
}

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

.btn-green {
  background-color: var(--herbal-green);
  /* 用!important强制覆盖，彻底解决文字颜色异常 */
  color: #ffffff !important;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.btn-green:hover {
  background-color: var(--herbal-dark);
}

/* 平台服务模块 */
.service-section {
  background-color:#f0f8f0;
  padding: 50px 15%;
  text-align: center;
}

.section-title {
  font-size:35px;
  color: var(--text-dark);
  margin-bottom: 4px;
}

.section-subtitle {
  font-size: 15px;
  color: var(--text-light);
  margin-bottom: 40px;
}

.service-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 30px;
}

.service-card {
  background-color: rgba(45, 93, 43, 0.1);
  padding: 30px 25px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  text-align: left;
  display: flex;
  flex-direction: column;
  height: 100%;
  transition: all 0.3s ease;
}

.service-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
  background-color: rgba(45, 93, 43, 0.15);
}

.icon-title-container {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.service-icon {
  font-size: 40px;
  color: var(--primary-green);
  margin-bottom: 0;
}

.service-card h3 {
  font-size: 25px;
  color: var(--text-dark);
  margin-bottom: 0;
}

.service-card p {
  font-size: 14px;
  color: var(--text-light);
  margin-bottom: 15px;
  line-height: 1.5;
}

.service-list {
  list-style: none;
  margin-bottom: 20px;
  flex-grow: 1;
}

.service-list li {
  font-size: 14px;
  color: var(--text-dark);
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.service-list li::before {
  content: "✓";
  color: var(--success-green);
  font-weight: bold;
}

.more-link {
  font-size: 14px;
  color: var(--success-green);
  text-decoration: none;
  font-weight: bold;
  transition: all 0.3s ease;
  outline: none;
  background: transparent;
}

.more-link:hover,
.more-link-active {
  color: var(--dark-green);
  text-decoration: underline;
  transform: translateX(5px);
  display: inline-block;
}

.more-link:focus,
.more-link:active {
  outline: none;
  background: transparent;
  box-shadow: none;
}

/* 热门药材模块 */
.hot-herbs-section {
  padding: 50px 15%;
  text-align: center;
  background-color:#f0f8f0;
}

.herbs-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 25px;
  margin-bottom: 30px;
}

.herb-card {
  background-color:  #f9fcfd;
  padding: 25px 20px;
  border-radius: 4px;
}

.herb-icon {
  font-size: 40px;
  color: var(--primary-green);
  margin-bottom: 10px;
}

.herb-name {
  font-size: 15px;
  font-weight: bold;
  color: var(--text-dark);
  margin-bottom: 10px;
}

.herb-price {
  font-size: 18px;
  font-weight: bold;
  color: var(--success-green);
  margin-bottom: 8px;
}

.herb-change {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 3px;
  display: inline-block;
  margin-bottom: 15px;
}

.change-up {
  background-color: #d4edda;
  color: var(--success-green);
}

.change-down {
  background-color: #f8d7da;
  color: var(--danger-red);
}

.change-zero {
  background-color: #e9ecef;
  color: var(--text-light);
}

.herb-info {
  display: flex;
  justify-content: space-between;
  font-size: 15px;
  color: var(--text-light);
}

.btn-outline-green {
  border: 1px solid var(--herbal-green);
  color: #ffffff;
  background-color: var(--herbal-green);
}

.btn-outline-green:hover {
  background-color: var(--herbal-dark);
  color: #ffffff;
}

/* 页脚样式 */
.footer {
  background-color: var(--secondary); /* 与服务功能部分一致的背景色 */
  color: var(--text-dark); /* 修正：改用深色文字，否则白色背景+白色文字看不见 */
  padding: 40px 15% 20px;
  text-align: center; /* 核心：让页脚内所有行内/行内块元素居中 */
}

.footer-content {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: 30px;
  margin-bottom: 30px;
}

.footer-logo {
  font-weight: bold;
  font-size: 14px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.footer-desc {
  font-size: 12px;
  line-height: 1.6;
  opacity: 0.8;
}

.footer-title {
  font-size: 13px;
  font-weight: bold;
  margin-bottom: 15px;
  padding-bottom: 5px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.footer-links {
  list-style: none;
}

.footer-links li {
  margin-bottom: 8px;
}

.footer-links a {
  color: #eef0f3;
  text-decoration: none;
  font-size: 12px;
  opacity: 0.8;
  transition: opacity 0.3s;
}

.footer-links a:hover {
  opacity: 1;
}

.contact-info {
  list-style: none;
  font-size: 12px;
  line-height: 1.8;
  opacity: 0.8;
}

.contact-info li {
  display: flex;
  align-items: center;
  gap: 6px;
}

.footer-bottom {
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid rgba(255,255,255,0.1);
  font-size: 10px;
  opacity: 0.6;
}

/* 响应式适配 */
@media (max-width: 992px) {
  .service-cards, .herbs-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .footer-content {
    grid-template-columns: 1fr 1fr;
  }
  .stats-row {
    gap: 2vw;
  }
}

@media (max-width: 768px) {
  .banner {
    padding: 50px 5%;
  }
  .service-section, .hot-herbs-section {
    padding: 30px 5%;
  }
  .stats-row {
    flex-direction: column;
    gap: 15px;
    width: 100%;
  }
  .stat-item {
    width: 100%;
    min-width: unset;
  }
  .service-cards, .herbs-grid {
    grid-template-columns: 1fr;
  }
  .footer-content {
    grid-template-columns: 1fr;
  }
  .banner-buttons {
    flex-direction: column;
    width: 100%;
    max-width: 300px;
  }
  .btn {
    width: 100%;
  }
  .footer {
    padding: 40px 5% 20px;
  }
}
</style>