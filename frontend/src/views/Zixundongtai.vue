<template>
  <div class="page-container">
    <AppSidebar />
    <!-- 主内容区域 -->
    <main class="main-content">
      <!-- 选项卡导航栏 - 菱形切换样式 -->
      <div class="tab-container mb-6">
        <div class="diamond-tabs">
          <div
            class="diamond-tab"
            :class="{ active: activeTab === 'news' }"
            @click="activeTab = 'news'"
          >
            <span class="diamond-text">新闻资讯</span>
          </div>
          <div
            class="diamond-tab"
            :class="{ active: activeTab === 'weekly' }"
            @click="activeTab = 'weekly'"
          >
            <span class="diamond-text">新闻周报</span>
          </div>
        </div>
      </div>
      <!-- 根据激活的选项卡显示不同内容 -->
      <div v-if="activeTab === 'news'" class="tab-content">
          <!-- 标签筛选区域 -->
          <div v-if="!loading && news.length > 0" class="mb-12">
            <div class="tag-filter-container">
              <button
                v-for="tag in allTags"
                :key="tag"
                :class="['tag-filter-btn', selectedTags.includes(tag) ? 'tag-filter-btn-active' : '']"
                @click="toggleTag(tag)"
              >
                {{ tag }}
              </button>
              <div class="ml-auto flex gap-3">
                <button
                  v-if="selectedTags.length > 0"
                  class="clear-filter-btn"
                  @click="clearTags"
                >
                  清除筛选
                </button>
                <button
                  class="btn-primary"
                  @click="refreshNews"
                >
                  实时更新
                </button>
              </div>
            </div>
          </div>
          <div v-if="loading" class="loading-container">
            <div class="flex flex-col items-center justify-center py-8">
              <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-herbal-green"></div>
              <p class="mt-4 text-gray-600">加载中...</p>
            </div>
          </div>
          <div v-else-if="filteredNews.length === 0" class="empty-container">
            <div class="flex flex-col items-center justify-center py-12">
              <p class="text-gray-500">暂无符合条件的新闻资讯</p>
            </div>
          </div>
          <div v-else class="news-list-scrollable">
            <div
              v-for="newsItem in filteredNews"
              :key="newsItem.id"
              class="news-item-scrollable mb-4"
            >
              <div class="news-header mb-3">
                <h4 class="font-medium text-gray-800 mb-2">{{ newsItem.title }}</h4>
                <div class="news-meta flex gap-4 text-sm text-gray-500">
                  <span>{{ formatDate(newsItem.publish_time) }}</span>
                  <span>{{ newsItem.market_name }}</span>
                </div>
              </div>
              <!-- 标签展示 -->
              <div v-if="newsItem.tags && newsItem.tags.length > 0" class="news-tags mb-3 flex flex-wrap gap-2">
                <span
                  v-for="tag in newsItem.tags"
                  :key="tag"
                  :class="['tag', getTagType(tag)]"
                >
                  {{ tag }}
                </span>
              </div>
              <div class="news-content mb-3 text-gray-600">
                <p>{{ truncateContent(newsItem.content, 100) }}</p>
              </div>
              <div class="news-footer flex justify-between items-center">
                <span v-if="newsItem.herb_name" class="news-herb text-sm bg-blue-50 text-blue-600 px-2 py-1 rounded">
                  相关药材: {{ newsItem.herb_name }}
                </span>
                <button
                  class="text-herbal-green hover:underline text-sm"
                  @click="toggleNewsDetail(newsItem)"
                >
                  {{ expandedNewsId === newsItem.id ? '收起详情' : '查看详情' }}
                </button>
              </div>
              <!-- 新闻详情展开区域 -->
              <div v-if="expandedNewsId === newsItem.id" class="news-detail-expanded mt-4 pt-4 border-t border-gray-100">
                <div class="news-detail-meta flex flex-wrap gap-4 mb-4 text-sm text-gray-500">
                  <span>{{ formatDate(newsItem.publish_time) }}</span>
                  <span>{{ newsItem.market_name }}</span>
                  <span v-if="newsItem.herb_name" class="bg-blue-50 text-blue-600 px-2 py-1 rounded">
                    相关药材: {{ newsItem.herb_name }}
                  </span>
                </div>
                <div class="news-detail-content text-gray-600 leading-relaxed text-base p-4 bg-gray-50 rounded-lg">
                  <p class="whitespace-pre-wrap leading-relaxed">
                    {{ newsItem.content }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'weekly'" class="tab-content p-6">
          <!-- 生成中：显示加载状态 -->
          <div v-if="generatingReport" class="flex flex-col items-center justify-center min-h-[500px]">
            <el-skeleton :rows="10" animated />
          </div>

          <!-- 生成后：显示完整周报 -->
          <div v-else-if="weeklyReport" class="el-row" :gutter="20">
            <!-- 周报内容 -->
            <div class="el-col" :span="24">
              <el-card class="el-card report-card" ref="reportCard">
                <template #header>
                  <div class="card-header">
                    <h2>中药材周报智能体</h2>
                    <button
                      class="btn-primary"
                      @click="generateWeeklyReport"
                    >
                      重新生成
                    </button>
                  </div>
                </template>

                <!-- 周报内容 -->
                <div class="report-content">
                  <!-- 标题和日期 -->
                  <div class="report-header">
                    <h3>{{ weeklyReport.title }}</h3>
                    <p class="date-range">{{ weeklyReport.date_range }}</p>
                  </div>

                  <!-- 总体概况 -->
                  <div class="section">
                    <h4 class="section-title">📊 本周概况</h4>
                    <div class="overview-box">
                      <p><strong>{{ weeklyReport.summary.overview }}</strong></p>
                      <p>{{ weeklyReport.summary.sentiment }}</p>
                      <p>价格走势：{{ weeklyReport.summary.price_trend }}</p>
                    </div>
                  </div>

                  <!-- 市场情绪 -->
                  <div class="section">
                    <h4 class="section-title">📈 市场情绪分析</h4>
                    <div class="sentiment-box" :class="weeklyReport.sentiment_analysis.sentiment">
                      <div class="el-row" :gutter="20">
                        <div class="el-col" :span="8">
                          <div class="sentiment-item">
                            <div class="label">整体情绪</div>
                            <div class="value">{{ weeklyReport.sentiment_analysis.summary }}</div>
                          </div>
                        </div>
                        <div class="el-col" :span="8">
                          <div class="sentiment-item">
                            <div class="label">积极占比</div>
                            <div class="value positive">{{ (weeklyReport.sentiment_analysis.positive_ratio * 100).toFixed(1) }}%</div>
                          </div>
                        </div>
                        <div class="el-col" :span="8">
                          <div class="sentiment-item">
                            <div class="label">消极占比</div>
                            <div class="value negative">{{ (weeklyReport.sentiment_analysis.negative_ratio * 100).toFixed(1) }}%</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 热门药材 -->
                  <div class="section" v-if="weeklyReport.news_summary.hot_herbs.length > 0">
                    <h4 class="section-title">🔥 热门药材关注</h4>
                    <div class="herb-tags">
                      <span
                        v-for="herb in weeklyReport.news_summary.hot_herbs"
                        :key="herb.name"
                        class="el-tag el-tag--warning el-tag--dark herb-tag"
                      >
                        {{ herb.name }} ({{ herb.count }}条)
                      </span>
                    </div>
                  </div>

                  <!-- 价格走势 -->
                  <div class="section" v-if="weeklyReport.price_analysis.up_herbs.length > 0 || weeklyReport.price_analysis.down_herbs.length > 0">
                    <h4 class="section-title">💰 价格走势分析</h4>

                    <div v-if="weeklyReport.price_analysis.up_herbs.length > 0" class="price-section">
                      <h5 class="sub-title up">📈 上涨品种</h5>
                      <div class="el-table" :data="weeklyReport.price_analysis.up_herbs" size="small" style="width: 100%">
                        <div class="el-table__header-wrapper">
                          <table>
                            <thead>
                              <tr>
                                <th width="120">药材名称</th>
                                <th width="120">现价(元/公斤)</th>
                                <th>规格</th>
                                <th>产地/市场</th>
                              </tr>
                            </thead>
                          </table>
                        </div>
                        <div class="el-table__body-wrapper">
                          <table>
                            <tbody>
                              <tr v-for="herb in weeklyReport.price_analysis.up_herbs" :key="herb.name">
                                <td width="120">{{ herb.name }}</td>
                                <td width="120"><span class="price-up">{{ herb.price }}</span></td>
                                <td>{{ herb.specification || '统货' }}</td>
                                <td>{{ herb.location || '-' }}</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>

                    <div v-if="weeklyReport.price_analysis.down_herbs.length > 0" class="price-section">
                      <h5 class="sub-title down">📉 下跌品种</h5>
                      <div class="el-table" :data="weeklyReport.price_analysis.down_herbs" size="small" style="width: 100%">
                        <div class="el-table__header-wrapper">
                          <table>
                            <thead>
                              <tr>
                                <th width="120">药材名称</th>
                                <th width="120">现价(元/公斤)</th>
                                <th>规格</th>
                                <th>产地/市场</th>
                              </tr>
                            </thead>
                          </table>
                        </div>
                        <div class="el-table__body-wrapper">
                          <table>
                            <tbody>
                              <tr v-for="herb in weeklyReport.price_analysis.down_herbs" :key="herb.name">
                                <td width="120">{{ herb.name }}</td>
                                <td width="120"><span class="price-down">{{ herb.price }}</span></td>
                                <td>{{ herb.specification || '统货' }}</td>
                                <td>{{ herb.location || '-' }}</td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 关键事件 -->
                  <div class="section" v-if="weeklyReport.news_summary.key_events.length > 0">
                    <h4 class="section-title">📰 本周关键事件</h4>
                    <div class="el-timeline">
                      <div
                        v-for="event in weeklyReport.news_summary.key_events"
                        :key="event.title"
                        class="el-timeline-item"
                        :class="'el-timeline-item--' + getEventType(event.type)"
                      >
                        <div class="el-timeline-item__timestamp">{{ event.date }}</div>
                        <div class="el-timeline-item__content">
                          {{ event.title }}
                          <span class="el-tag el-tag--small event-tag">{{ event.type }}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 种植户建议 -->
                  <div class="section advice-section">
                    <h4 class="section-title">🌱 对种植户的建议</h4>
                    <div
                      v-for="(advice, index) in weeklyReport.grower_advice"
                      :key="index"
                      class="el-alert advice-alert"
                      :title="getAdviceTitle(advice)"
                      :type="getAdviceType(advice)"
                      :closable="false"
                    >
                      <div>{{ getAdviceContent(advice) }}</div>
                    </div>
                  </div>

                  <!-- 买家建议 -->
                  <div class="section advice-section">
                    <h4 class="section-title">🛒 对采购商/买家的建议</h4>
                    <div
                      v-for="(advice, index) in weeklyReport.buyer_advice"
                      :key="index"
                      class="el-alert advice-alert"
                      :title="getAdviceTitle(advice)"
                      :type="getAdviceType(advice)"
                      :closable="false"
                    >
                      <div>{{ getAdviceContent(advice) }}</div>
                    </div>
                  </div>

                  <!-- 关键词 -->
                  <div class="section" v-if="weeklyReport.keywords.length > 0">
                    <h4 class="section-title">🔑 本周关键词</h4>
                    <div class="keyword-cloud">
                      <span
                        v-for="keyword in weeklyReport.keywords"
                        :key="keyword.word"
                        :class="['el-tag', 'el-tag--' + getKeywordType(keyword.weight), 'el-tag--plain', 'keyword-tag']"
                        :style="{ fontSize: getKeywordSize(keyword.weight) + 'px' }"
                      >
                        {{ keyword.word }}
                      </span>
                    </div>
                  </div>

                  <!-- 下载按钮 -->
                  <div class="download-section">
                    <el-button type="success" @click="downloadReport" size="large">
                      <el-icon><Download /></el-icon>
                      下载周报
                    </el-button>
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </div>
    </main>

    <footer class="footer">
      <p>© 2026 灵汐药策 版权所有</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onActivated, computed, watch } from 'vue'
import axios from 'axios'
import AppSidebar from '@/components/AppSidebar.vue'
import { Download } from '@element-plus/icons-vue'
import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'


// 类型定义
interface NewsItem {
  id: number
  title: string
  content: string
  publish_time: string
  market_name: string
  herb_name?: string
  tags?: string[]
}

interface HotHerb {
  name: string
  count: number
}

interface KeyEvent {
  date: string
  title: string
  type: string
}

interface NewsSummary {
  hot_herbs: HotHerb[]
  key_events: KeyEvent[]
  total_count?: number
}

interface PriceAnalysis {
  up_herbs: Array<{ name: string; price: string; specification?: string; location?: string }>
  down_herbs: Array<{ name: string; price: string; specification?: string; location?: string }>
}

interface SentimentAnalysis {
  summary: string
  sentiment: string
  positive_ratio: number
  negative_ratio: number
}

interface Summary {
  overview: string
  sentiment: string
  price_trend: string
}

interface Keyword {
  word: string
  weight: number
}

interface WeeklyReport {
  title: string
  date_range: string
  summary: Summary
  sentiment_analysis: SentimentAnalysis
  news_summary: NewsSummary
  price_analysis: PriceAnalysis
  grower_advice: string[]
  buyer_advice: string[]
  keywords: Keyword[]
}

// 缓存对象
const cache = {
  weeklyReport: null as WeeklyReport | null,
  isFirstLoad: true
}

// 状态管理
const loading = ref(false)
const news = ref<NewsItem[]>([])
const expandedNewsId = ref<number | null>(null)
const generatingReport = ref(false)
const weeklyReport = ref<WeeklyReport | null>(cache.weeklyReport)
const selectedTags = ref<string[]>([])
const activeTab = ref('news')
// const reportCard = ref<HTMLElement | null>(null)

onMounted(() => {
  // 先获取当天新闻（不等待爬虫）
  fetchTodayNews()

  // 在后台启动爬虫
  axios.get(`/api/run-new5`)
    .then(response => {
      console.log('爬虫已启动:', response.data)

      // 如果返回了task_id，可以轮询检查状态
      if (response.data.task_id) {
        checkTaskStatus(response.data.task_id)
      }
    })
    .catch(error => {
      console.error('启动爬虫失败:', error)
      // 不要显示错误提示，因为不影响查看已有新闻
    })
  
  // 从缓存恢复周报数据
  if (cache.weeklyReport) {
    weeklyReport.value = cache.weeklyReport
  }
})

// 当组件被激活时（从其他页面切换回来时）
onActivated(() => {
  // 从缓存恢复周报数据
  if (cache.weeklyReport) {
    weeklyReport.value = cache.weeklyReport
  }
})

// 检查后台任务状态
const checkTaskStatus = async (taskId: string) => {
  try {
    // 每30秒检查一次状态，最多检查10次
    let checkCount = 0
    const checkInterval = setInterval(async () => {
      checkCount++
      if (checkCount > 10) {
        clearInterval(checkInterval)
        return
      }

      try {
        const response = await axios.get(`/api/run-new5/status/${taskId}`)
        const status = response.data.status

        if (status === 'completed') {
          clearInterval(checkInterval)
          console.log('爬虫任务完成:', response.data)
          // 刷新新闻列表
          fetchTodayNews()
        } else if (status === 'failed' || status === 'error' || status === 'timeout') {
          clearInterval(checkInterval)
          console.error('爬虫任务失败:', response.data)
          // 静默失败，不打扰用户
        }
      } catch {
        // 状态检查失败，继续尝试
      }
    }, 30000)
  } catch (e) {
    console.error('检查任务状态失败:', e)
  }
}

// 获取当天新闻
const fetchTodayNews = async () => {
  loading.value = true
  try {
    const response = await axios.get(`/api/today-news`)

    if (response.data && Array.isArray(response.data)) {
      news.value = response.data
      selectedTags.value = [] // 清除筛选
    } else {
      news.value = []
    }
  } catch (error) {
    console.error('获取当天新闻失败:', error)
    news.value = []
  } finally {
    loading.value = false
  }
}

// 刷新新闻
const refreshNews = () => {
  // 启动爬虫
  axios.get(`/api/run-new5`)
    .then(response => {
      console.log('爬虫已启动:', response.data)

      // 如果返回了task_id，可以轮询检查状态
      if (response.data.task_id) {
        checkTaskStatus(response.data.task_id)
      }
    })
    .catch(error => {
      console.error('启动爬虫失败:', error)
      // 不要显示错误提示，因为不影响查看已有新闻
    })

  // 获取新闻
  fetchTodayNews()
}

// 切换新闻详情展开状态
const toggleNewsDetail = (newsItem: NewsItem) => {
  if (expandedNewsId.value === newsItem.id) {
    expandedNewsId.value = null
  } else {
    expandedNewsId.value = newsItem.id
  }
}

// 生成周报
const generateWeeklyReport = async () => {
  generatingReport.value = true
  try {
    // 使用正确的API地址，后端运行在5002端口
    const response = await axios.get('/api/herb-weekly-report')
    if (response.data && response.data.success) {
      weeklyReport.value = response.data.report
      // 保存到缓存
      cache.weeklyReport = response.data.report
    } else {
      console.error('生成失败:', response.data.error || '未知错误')
    }
  } catch (error) {
    console.error('生成周报失败:', error)
  } finally {
    generatingReport.value = false
  }
}

// 计算所有标签（限制数量并过滤掉"药材-"开头的标签）
const allTags = computed(() => {
  const tags = new Set<string>()
  news.value.forEach(item => {
    if (item.tags && Array.isArray(item.tags)) {
      item.tags.forEach((tag: string) => {
        if (!tag.startsWith('药材-')) {
          tags.add(tag)
        }
      })
    }
  })
  return Array.from(tags).slice(0, 5)
})

// 筛选后的新闻
const filteredNews = computed(() => {
  if (selectedTags.value.length === 0) {
    return news.value
  }
  return news.value.filter(item => {
    if (!item.tags || !Array.isArray(item.tags)) {
      return false
    }
    return selectedTags.value.some(tag => item.tags?.includes(tag))
  })
})

// 切换标签选择
const toggleTag = (tag: string) => {
  const index = selectedTags.value.indexOf(tag)
  if (index === -1) {
    selectedTags.value.push(tag)
  } else {
    selectedTags.value.splice(index, 1)
  }
}

// 清除筛选
const clearTags = () => {
  selectedTags.value = []
}

// 获取标签类型
const getTagType = (tag: string) => {
  if (tag.includes('价格上涨')) return 'tag-danger'
  if (tag.includes('价格下跌')) return 'tag-success'
  if (tag.includes('价格稳定')) return 'tag-info'
  if (tag.includes('走货') || tag.includes('库存') || tag.includes('供需')) return 'tag-warning'
  if (tag.includes('药材-')) return 'tag-primary'
  return 'tag-default'
}

// 下载周报
const downloadReport = async () => {
  console.log('下载周报按钮被点击')
  console.log('weeklyReport.value:', weeklyReport.value)
  
  if (!weeklyReport.value) {
    console.log('weeklyReport.value 为 null')
    return
  }
  
  try {
    // 尝试使用 html2canvas 生成 PDF
    console.log('使用 html2canvas 生成 PDF')
    
    // 创建一个临时的 DOM 元素来渲染周报内容
    const tempElement = document.createElement('div')
    tempElement.style.position = 'absolute'
    tempElement.style.top = '-9999px'
    tempElement.style.left = '-9999px'
    tempElement.style.width = '800px'
    tempElement.style.backgroundColor = '#ffffff'
    tempElement.style.padding = '20px'
    
    // 构建周报内容
    const report = weeklyReport.value
    tempElement.innerHTML = `
      <div style="font-family: Arial, 'Microsoft YaHei', sans-serif; font-size: 11px;">
        <h1 style="text-align: center; margin-bottom: 15px; font-size: 16px;">${report.title}</h1>
        
        <h2 style="margin-top: 15px; margin-bottom: 8px; font-size: 13px;">【本周概况】</h2>
        <p style="margin-bottom: 8px; line-height: 1.3;">${report.summary.overview}</p>
        <p style="margin-bottom: 8px; line-height: 1.3;">${report.summary.sentiment}</p>
        <p style="margin-bottom: 15px; line-height: 1.3;">价格走势：${report.summary.price_trend}</p>
        
        <h2 style="margin-top: 15px; margin-bottom: 8px; font-size: 13px;">【热门药材】</h2>
        <ul style="margin-bottom: 15px; line-height: 1.3; padding-left: 20px;">
          ${report.news_summary.hot_herbs.map(herb => `
            <li style="margin-bottom: 4px;">${herb.name}：${herb.count}条相关资讯</li>
          `).join('')}
        </ul>
        
        <h2 style="margin-top: 15px; margin-bottom: 8px; font-size: 13px;">【本周关键事件】</h2>
        <ul style="margin-bottom: 15px; line-height: 1.3; padding-left: 20px;">
          ${report.news_summary.key_events.map(event => `
            <li style="margin-bottom: 4px;">[${event.date}] ${event.title}</li>
          `).join('')}
        </ul>
        
        <h2 style="margin-top: 15px; margin-bottom: 8px; font-size: 13px;">【对种植户的建议】</h2>
        <ul style="margin-bottom: 15px; line-height: 1.3; padding-left: 20px;">
          ${report.grower_advice.map(advice => `
            <li style="margin-bottom: 4px;">${advice}</li>
          `).join('')}
        </ul>
        
        <h2 style="margin-top: 15px; margin-bottom: 8px; font-size: 13px;">【对采购商/买家的建议】</h2>
        <ul style="margin-bottom: 15px; line-height: 1.3; padding-left: 20px;">
          ${report.buyer_advice.map(advice => `
            <li style="margin-bottom: 4px;">${advice}</li>
          `).join('')}
        </ul>
        
        <h2 style="margin-top: 15px; margin-bottom: 8px; font-size: 13px;">【本周关键词】</h2>
        <p style="margin-bottom: 15px; line-height: 1.3;">${report.keywords.map(k => k.word).join('、')}</p>
        
        <p style="margin-top: 20px; text-align: right; font-size: 10px;">报告生成时间：${new Date().toLocaleString('zh-CN')}</p>
      </div>
    `
    
    // 将临时元素添加到文档中
    document.body.appendChild(tempElement)
    
    // 使用 html2canvas 捕获内容
    console.log('开始捕获内容')
    const canvas = await html2canvas(tempElement, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff'
    })
    console.log('捕获成功')
    
    // 从文档中移除临时元素
    document.body.removeChild(tempElement)
    
    // 创建 PDF 实例
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pdfWidth = pdf.internal.pageSize.getWidth()
    const pdfHeight = pdf.internal.pageSize.getHeight()
    
    // 计算图片在 PDF 中的尺寸
    const imgWidth = pdfWidth - 20
    const imgHeight = (canvas.height * imgWidth) / canvas.width
    
    // 如果图片高度超过 PDF 页面高度，需要分页
    if (imgHeight > pdfHeight - 20) {
      const pages = Math.ceil(imgHeight / (pdfHeight - 20))
      
      for (let i = 0; i < pages; i++) {
        if (i > 0) {
          pdf.addPage()
        }
        
        const yOffset = i * (pdfHeight - 20)
        const imgPartHeight = Math.min(pdfHeight - 20, imgHeight - yOffset)
        
        const pageCanvas = document.createElement('canvas')
        pageCanvas.width = canvas.width
        pageCanvas.height = (canvas.width * imgPartHeight) / imgWidth
        const ctx = pageCanvas.getContext('2d')
        
        if (ctx) {
          ctx.drawImage(
            canvas,
            0, yOffset * (canvas.height / imgHeight),
            canvas.width, pageCanvas.height,
            0, 0,
            canvas.width, pageCanvas.height
          )
          
          const imgData = pageCanvas.toDataURL('image/png')
          pdf.addImage(imgData, 'PNG', 10, 10, imgWidth, imgPartHeight)
        }
      }
    } else {
      const imgData = canvas.toDataURL('image/png')
      pdf.addImage(imgData, 'PNG', 10, 10, imgWidth, imgHeight)
    }
    
    // 保存 PDF 文件
    const filename = `中药材周报_${new Date().toISOString().split('T')[0]}.pdf`
    console.log('准备保存 PDF 文件:', filename)
    pdf.save(filename)
    console.log('PDF 文件保存命令已执行')

    // 显示下载成功提示
    console.log('周报下载成功')
  } catch (error: any) {
    console.error('下载周报失败:', error)
    console.error('错误详情:', error?.message)
    console.error('错误堆栈:', error?.stack)
  }
}

// 获取事件类型
const getEventType = (type: string) => {
  const typeMap: Record<string, string> = {
    '产新': 'success',
    '涨价': 'danger',
    '跌价': 'warning',
    '天气': 'info',
    '政策': 'primary',
    '库存': ''
  }
  return typeMap[type] || ''
}

// 解析建议标题
const getAdviceTitle = (advice: string) => {
  const match = advice.match(/【(.+?)】/)
  return match ? match[1] : '建议'
}

// 解析建议内容
const getAdviceContent = (advice: string) => {
  return advice.replace(/【.+?】/, '').trim()
}

// 获取建议类型
const getAdviceType = (advice: string) => {
  if (advice.includes('种植决策')) return 'success'
  if (advice.includes('采购策略')) return 'warning'
  if (advice.includes('价格')) return 'info'
  if (advice.includes('质量')) return 'primary'
  return 'info'
}

// 获取关键词类型
const getKeywordType = (weight: number) => {
  if (weight > 0.3) return 'success'
  if (weight > 0.2) return 'primary'
  if (weight > 0.1) return 'info'
  return 'info'
}

// 获取关键词大小
const getKeywordSize = (weight: number) => {
  const baseSize = 12
  return baseSize + weight * 20
}

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC'
  })
}

// 截断内容
const truncateContent = (content: string, length: number) => {
  if (!content) return ''
  if (content.length <= length) return content
  return content.substring(0, length) + '...'
}

// 监听activeTab变化，当切换到周报标签时自动生成周报
watch(activeTab, (newTab) => {
  if (newTab === 'weekly' && !weeklyReport.value && !generatingReport.value) {
    generateWeeklyReport()
  }
})

defineOptions({ name: 'NewsPage' })
</script>

<style scoped>
:root {
  --herbal-green: #2d5d2b;
  --herbal-lightGreen: #3a7a36;
}

/* 菱形标签 */
.tab-container {
  background: linear-gradient(135deg, var(--herbal-green) 0%, var(--herbal-lightGreen) 100%) !important;
  padding: 20px 30px !important;
  border-radius: 0 !important;
  position: relative !important;
  overflow: hidden !important;
  width: flex;
  margin-bottom: 24px !important;
}

.diamond-tabs {
  display: flex !important;
  align-items: center !important;
  gap: 0 !important;
  position: relative !important;
  width: 100% !important;
}

.diamond-tab {
  position: relative !important;
  padding: 15px 40px !important;
  cursor: pointer !important;
  transition: all 0.3s ease !important;
  background-color: rgba(255, 255, 255, 0.15) !important;
  clip-path: polygon(15% 0%, 100% 0%, 85% 100%, 0% 100%) !important;
  margin-right: -20px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  min-width: 160px !important;
  z-index: 10 !important;
}

.diamond-tab:first-child {
  clip-path: polygon(0% 0%, 100% 0%, 85% 100%, 0% 100%) !important;
  padding-left: 30px !important;
}

.diamond-tab:last-child {
  clip-path: polygon(15% 0%, 100% 0%, 100% 100%, 0% 100%) !important;
  padding-right: 30px !important;
  margin-right: 0 !important;
}

.diamond-tab:hover {
  background-color: rgba(255, 255, 255, 0.25) !important;
}

.diamond-tab.active {
  background-color: rgba(255, 255, 255, 0.9) !important;
}

.diamond-tab.active .diamond-text {
  color: #2d5d2b !important;
  font-weight: 600 !important;
}

.diamond-text {
  color: rgba(255, 255, 255, 0.9) !important;
  font-size: 16px !important;
  font-weight: 500 !important;
  white-space: nowrap !important;
  z-index: 11 !important;
  position: relative !important;
}

.page-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  background-color: #f0f8f0;
  padding: 24px 70px;
  margin-top: 70px;
}

.tab-content {
  padding: 0;
}

/* 资讯卡片 */
.news-item-scrollable {
  transition: all 0.3s ease;
  background: #f0f8f0;
  padding: 20px;
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  margin-bottom: 16px;
}
.news-item-scrollable:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  transform: translateY(-3px);
}

.news-header h4 {
  font-size: 18px;
  font-weight: 600;
  color: #f0f8f0;
  margin-bottom: 12px;
  line-height: 1.4;
}
.news-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 16px;
}

/* 标签 */
.news-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}
.tag {
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}
.tag-default { background: #e5e7eb; color: #374151; }
.tag-primary { background: #dbeafe; color: #1e40af; }
.tag-success { background: #dcfce7; color: #15803d; }
.tag-warning { background: #fef3c7; color: #d97706; }
.tag-danger { background: #fee2e2; color: #dc2626; }
.tag-info { background: #e0f2fe; color: #0284c7; }

.news-content p {
  color: #4b5563;
  line-height: 1.6;
  font-size: 14px;
}

.news-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f3f4f6;
}
.news-herb {
  background-color: #eff6ff;
  color: #1d4ed8;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
}
.news-footer button {
  color: #2d5d2b;
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 6px;
}
.news-footer button:hover {
  background-color: #f0fdf4;
}

/* 新闻详情展开区域 */
.news-detail-expanded {
  animation: slideDown 0.3s ease-out;
}

.news-detail-content {
  line-height: 1.8;
  font-size: 15px;
  background-color: #f0f8f0;
}

.news-detail-content p {
  margin: 0;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 周报样式 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f0f8f0;
}

.card-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.report-header {
  text-align: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e4e7ed;
}

.report-header h3 {
  margin: 0 0 10px 0;
  font-size: 24px;
  color: #303133;
}

.date-range {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

.section {
  margin-bottom: 30px;
}

.section-title {
  font-size: 18px;
  color: #303133;
  margin-bottom: 15px;
  padding-left: 10px;
  border-left: 4px solid #409eff;
  background: #f0f8f0;
}

.overview-box {
  background: #f0f8f0;
  padding: 20px;
  border-radius: 8px;
  line-height: 2;
}

.sentiment-box {
  background: #f0f8f0;
  padding: 20px;
  border-radius: 8px;
}

.sentiment-box.positive {
  background: #f0f9ff;
  border: 1px solid #b3e0ff;
}

.sentiment-box.negative {
  background: #fff5f5;
  border: 1px solid #ffccc7;
}

.sentiment-item {
  text-align: center;
  padding: 10px;
}

.sentiment-box .el-row {
  display: flex;
  justify-content: space-between;
}

.sentiment-box .el-col {
  flex: 1;
  margin: 0 10px;
}

.sentiment-box .el-col:first-child {
  margin-left: 0;
}

.sentiment-box .el-col:last-child {
  margin-right: 0;
}

.sentiment-item .label {
  color: #909399;
  font-size: 14px;
  margin-bottom: 8px;
}

.sentiment-item .value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.sentiment-item .value.positive {
  color: #67c23a;
}

.sentiment-item .value.negative {
  color: #f56c6c;
}

.herb-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.herb-tag {
  font-size: 14px;
}

.price-section {
  margin-bottom: 20px;
}

.sub-title {
  font-size: 16px;
  margin-bottom: 10px;
  padding: 5px 10px;
  border-radius: 4px;
}

.sub-title.up {
  color: #f56c6c;
  background: #fff5f5;
}

.sub-title.down {
  color: #67c23a;
  background: #f0f9ff;
}

.price-up {
  color: #f56c6c;
  font-weight: bold;
}

.price-down {
  color: #67c23a;
  font-weight: bold;
}

.event-tag {
  margin-left: 10px;
}

.advice-section .advice-alert {
  margin-bottom: 10px;
}

.keyword-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 20px;
  background: #f0f8f0;
  border-radius: 8px;
  box-sizing: border-box;
  width: 100%;
}

.keyword-tag {
  margin: 2px;
  box-sizing: border-box;
  padding: 12px 16px;
  border-width: 2px;
  line-height: 1.5;
  /* height: 10px;; */
}

.download-section {
  text-align: center;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.loading-container {
  padding: 40px;
}

.empty-container {
  padding: 60px 0;
}

.stats-card .stats-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.stat-item {
  text-align: center;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.empty-stats {
  padding: 40px 0;
}

.tips-content {
  font-size: 14px;
  line-height: 1.8;
  color: #606266;
}

.tips-content ul {
  padding-left: 20px;
  margin: 10px 0;
}

.tips-content li {
  margin-bottom: 5px;
}

/* 滚动 */
.news-list-scrollable {
  margin-top: 40px;
}

/* 按钮 */
.btn-primary {
  padding: 8px 20px;
  background-color: var(--herbal-green);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}
.btn-primary:hover {
  background-color: var(--herbal-lightGreen);
}

.tag-filter-btn {
  padding: 8px 20px;
  background-color: #f3f4f6;
  color: #374151;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
}
.tag-filter-btn-active {
  background-color: #2d5d2b;
  color: white;
}
.clear-filter-btn {
  padding: 8px 16px;
  background-color: #f3f4f6;
  color: #2d5d2b;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
}

.tag-filter-container {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.footer {
  background-color: var(--secondary);
  color: var(--text-dark);
  padding: 20px 0;
  text-align: center;
  font-size: 14px;
  width: 100%;
  margin: 0;
}

/* 自定义弹窗样式 - 符合项目主体风格 */
:global(.custom-message-box) {
  border-radius: 8px !important;
  box-shadow: none !important;
  border: none !important;
  overflow: hidden !important;
  outline: none !important;
  background: transparent !important;
  padding: 0 !important;
}

:global(.custom-message-box .el-message-box) {
  border: none !important;
  border-radius: 8px !important;
  overflow: hidden !important;
  background: transparent !important;
  box-shadow: none !important;
}

:global(.custom-message-box .el-message-box__wrapper) {
  background: transparent !important;
  box-shadow: none !important;
  padding: 0 !important;
}

:global(.custom-message-box .el-message-box__container) {
  background: transparent !important;
  box-shadow: none !important;
  padding: 0 !important;
}

:global(.custom-message-box .el-message-box__content) {
  background: white !important;
  border: none !important;
}

:global(.custom-message-box .el-message-box__btns) {
  background: #f9fafb !important;
  border: none !important;
  border-top: 1px solid #e4e7ed !important;
}

:global(.custom-message-box .el-message-box__header) {
  background: var(--herbal-green) !important;
  padding: 12px 16px !important;
  border-radius: 0 !important;
  border-bottom: 2px solid var(--herbal-lightGreen) !important;
}

:global(.custom-message-box .el-message-box__title) {
  color: white !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  margin: 0 !important;
}

:global(.custom-message-box .el-message-box__headerbtn .el-message-box__close) {
  color: white !important;
  font-size: 14px !important;
}

:global(.custom-message-box .el-message-box__headerbtn .el-message-box__close:hover) {
  color: rgba(255, 255, 255, 0.8) !important;
}

:global(.custom-message-box .el-message-box__content) {
  padding: 20px 16px !important;
  font-size: 14px !important;
  color: #303133 !important;
  background-color: white !important;
  position: relative !important;
  min-height: 80px !important;
}

:global(.custom-message-box .el-message-box__content::before) {
  content: '' !important;
  position: absolute !important;
  bottom: -10px !important;
  right: -10px !important;
  width: 80px !important;
  height: 80px !important;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path d="M50 5c-15 0-27 12-27 27v36c0 15 12 27 27 27s27-12 27-27V32c0-15-12-27-27-27zM35 40c-3 0-5 2-5 5s2 5 5 5 5-2 5-5-2-5-5-5zm30 0c-3 0-5 2-5 5s2 5 5 5 5-2 5-5-2-5-5-5zm-30 20c-3 0-5 2-5 5s2 5 5 5 5-2 5-5-2-5-5-5zm30 0c-3 0-5 2-5 5s2 5 5 5 5-2 5-5-2-5-5-5z" fill="%23e8f5e8" opacity="0.3"/></svg>') !important;
  background-repeat: no-repeat !important;
  background-size: contain !important;
  z-index: 0 !important;
  pointer-events: none !important;
}

:global(.custom-message-box .el-message-box__btns) {
  padding: 12px 16px !important;
  background-color: #f9fafb !important;
  border-top: 1px solid #e4e7ed !important;
  display: flex !important;
  justify-content: flex-end !important;
}

:global(.custom-message-box .el-button--primary) {
  background-color: var(--herbal-green) !important;
  border-color: var(--herbal-green) !important;
  padding: 8px 16px !important;
  font-size: 14px !important;
  border-radius: 4px !important;
  min-width: 80px !important;
  text-align: center !important;
}

:global(.custom-message-box .el-button--primary:hover) {
  background-color: var(--herbal-lightGreen) !important;
  border-color: var(--herbal-lightGreen) !important;
}

:global(.custom-message-box .el-message-box__status) {
  display: none !important;
}

:global(.custom-message-box .el-message-box__content p) {
  margin: 0 !important;
  z-index: 1 !important;
  position: relative !important;
}
</style>
