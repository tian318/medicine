<template>
  <div class="page-container">
    <AppSidebar />

    <main class="main-content">
      <!-- 页面标题 -->
      <div class="mb-6">
        <h1 class="text-2xl font-bold text-gray-800">价格数据统计分析</h1>
      </div>
      <!-- 1. 价格涨幅排行榜部分 -->
      <div class="bg-[#f6f8f6] rounded-xl card-shadow p-6 mb-6 shadow-lg">
        <div class="card-header mb-4">
          <h2 class="font-bold text-lg">药材价格涨幅排行榜</h2>
        </div>
        <div class="filter-section mb-4">
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-600">涨幅类型：</span>
              <div class="flex border rounded-md overflow-hidden">
                <button
                  v-for="type in rankingTypes"
                  :key="type.value"
                  class="px-4 py-2 text-sm font-medium"
                  :class="rankingType === type.value ? 'bg-herbal-green text-white' : 'bg-white text-gray-700 hover:bg-gray-50 transition-all'"
                  @click="rankingType = type.value; fetchPriceRanking()"
                >
                  {{ type.label }}
                </button>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-600">显示数量：</span>
              <select
                v-model="rankingLimit"
                class="px-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-herbal-green focus:border-transparent transition-all"
                @change="fetchPriceRanking()"
              >
                <option :value="5">Top 5</option>
                <option :value="10">Top 10</option>
                <option :value="20">Top 20</option>
                <option :value="50">Top 50</option>
              </select>
            </div>
            <button
              class="px-5 py-2 bg-herbal-green text-white rounded-md text-sm font-medium hover:bg-herbal-lightGreen transition-all transform hover:scale-105"
              @click="fetchPriceRanking"
            >
              刷新
            </button>
          </div>
        </div>
        <div class="ranking-table-container" style="overflow-x: auto; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);">
          <table class="min-w-full border-collapse" style="table-layout: fixed; width: 100%;">
            <colgroup>
              <col style="width: 8%;">
              <col style="width: 16%;">
              <col style="width: 14%;">
              <col style="width: 16%;">
              <col style="width: 16%;">
              <col style="width: 14%;">
              <col style="width: 16%;">
            </colgroup>
            <thead class="bg-herbal-green text-white">
              <tr>
                <th class="px-4 py-3 text-center align-middle text-sm font-semibold" style="width: 8%; border-top-left-radius: 8px;">排名</th>
                <th class="px-4 py-3 text-center align-middle text-sm font-semibold" style="width: 16%;">药材名称</th>
                <th class="px-4 py-3 text-center align-middle text-sm font-semibold" style="width: 14%;">规格</th>
                <th class="px-4 py-3 text-center align-middle text-sm font-semibold" style="width: 16%;">产地/市场</th>
                <th class="px-4 py-3 text-center align-middle text-sm font-semibold" style="width: 16%;">当前价格(元/kg)</th>
                <th class="px-4 py-3 text-center align-middle text-sm font-semibold" style="width: 14%;">{{ getRankingTypeLabel() }}</th>
                <th class="px-4 py-3 text-center align-middle text-sm font-semibold" style="width: 16%; border-top-right-radius: 8px;">记录时间</th>
              </tr>
            </thead>
            <tbody v-if="!rankingLoading">
              <tr v-for="(item, index) in priceRanking" :key="index" class="transition-all duration-200 hover:bg-gray-50 hover:shadow-sm" :class="index % 2 === 1 ? 'bg-gray-50/30' : 'bg-white'">
                <td class="px-4 py-3 text-center align-middle text-sm font-medium border-b border-gray-100" style="width: 8%; text-align: center;">{{ index + 1 }}</td>
                <td class="px-4 py-3 text-center align-middle text-sm font-medium text-gray-800 border-b border-gray-100" style="width: 16%; text-align: center;">{{ item.herb_name }}</td>
                <td class="px-4 py-3 text-center align-middle text-sm text-gray-600 border-b border-gray-100" style="width: 14%; text-align: center;">{{ item.specification }}</td>
                <td class="px-4 py-3 text-center align-middle text-sm text-gray-600 border-b border-gray-100" style="width: 16%; text-align: center;">{{ item.location }}</td>
                <td class="px-4 py-3 text-center align-middle text-sm font-semibold text-herbal-green border-b border-gray-100" style="width: 16%; text-align: center;">{{ item.price.toFixed(2) }}</td>
                <td class="px-4 py-3 text-center align-middle text-sm font-semibold text-green-600 border-b border-gray-100" style="width: 14%; text-align: center;">{{ getRankingValue(item, rankingType) }}%</td>
                <td class="px-4 py-3 text-center align-middle text-sm text-gray-600 border-b border-gray-100" style="width: 16%; text-align: center;">{{ formatDate(item.recorded_at) }}</td>
              </tr>
            </tbody>
            <tbody v-else>
              <tr>
                <td colspan="7" class="px-6 py-12 text-center bg-white">
                  <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-herbal-green mx-auto"></div>
                  <p class="mt-4 text-gray-500 text-sm">加载中...</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <!-- 2. 价格分布分析部分 -->
      <div class="bg-[#f6f8f6] rounded-xl card-shadow p-6 mb-6 shadow-lg">
        <div class="card-header mb-4">
          <h2 class="font-bold text-lg title1">药材价格分布</h2>
        </div>
        <div class="filter-section mb-4">
          <div class="flex items-center gap-4 flex-nowrap">
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-600">药材名称：</span>
              <select
                v-model="filterForm.herbName"
                class="px-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-herbal-green focus:border-transparent transition-all"
                @change="(e) => handleHerbChange((e.target as HTMLSelectElement).value)"
              >
                <option value="">请选择药材</option>
                <option v-for="herb in herbs" :key="herb" :value="herb">{{ herb }}</option>
              </select>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-600">规格：</span>
              <select
                v-model="filterForm.specification"
                class="px-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-herbal-green focus:border-transparent transition-all"
              >
                <option value="">请选择规格</option>
                <option v-for="spec in specifications" :key="spec" :value="spec">{{ spec }}</option>
              </select>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-600">时间范围：</span>
              <div class="flex gap-2 items-center">
                <input
                  type="date"
                  v-model="filterForm.dateRange[0]"
                  class="w-36 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-herbal-green focus:border-transparent transition-all"
                >
                <span class="text-gray-500">至</span>
                <input
                  type="date"
                  v-model="filterForm.dateRange[1]"
                  class="w-36 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-herbal-green focus:border-transparent transition-all"
                >
              </div>
            </div>
            <div class="flex gap-3 ml-auto shrink-0">
              <button
                class="px-5 py-2 bg-herbal-green text-white rounded-md text-sm font-medium hover:bg-herbal-lightGreen transition-colors"
                @click="fetchPriceDistribution"
              >
                分析
              </button>
              <button
                class="px-5 py-2 border border-gray-300 rounded-md text-sm text-gray-600 hover:bg-gray-50 transition-colors"
                @click="resetForm"
              >
                重置
              </button>
            </div>
          </div>
        </div>

        <!-- 价格分布图表 -->
        <div class="chart-container mt-4 mb-4">
          <div class="price-distribution-chart" ref="priceDistributionChart"></div>
        </div>

        <!-- 价格统计信息 -->
        <div class="price-stats p-4 bg-[#f6f8f6] rounded-xl shadow-md" v-if="priceStats.count > 0">
          <h3 class="font-bold text-md mb-3 text-gray-800 border-b pb-2 border-gray-100">价格统计信息</h3>
          <div class="overflow-x-auto">
            <table class="min-w-full border-collapse rounded-lg overflow-hidden">
              <tbody>
                <tr class="bg-gray-50/50">
                  <td class="px-4 py-3 text-gray-600 font-medium">数据量</td>
                  <td class="px-4 py-3 font-semibold text-gray-800">{{ priceStats.count }}</td>
                  <td class="px-4 py-3 text-gray-600 font-medium">最低价格</td>
                  <td class="px-4 py-3 font-semibold text-herbal-green">{{ priceStats.min.toFixed(2) }} 元/kg</td>
                  <td class="px-4 py-3 text-gray-600 font-medium">最高价格</td>
                  <td class="px-4 py-3 font-semibold text-herbal-green">{{ priceStats.max.toFixed(2) }} 元/kg</td>
                </tr>
                <tr class="bg-white">
                  <td class="px-4 py-3 text-gray-600 font-medium">平均价格</td>
                  <td class="px-4 py-3 font-semibold text-herbal-green">{{ priceStats.avg.toFixed(2) }} 元/kg</td>
                  <td class="px-4 py-3 text-gray-600 font-medium">中位数价格</td>
                  <td class="px-4 py-3 font-semibold text-herbal-green">{{ priceStats.median.toFixed(2) }} 元/kg</td>
                  <td class="px-4 py-3 text-gray-600 font-medium">标准差</td>
                  <td class="px-4 py-3 font-semibold text-gray-800">{{ priceStats.stdDev.toFixed(2) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 3. 价格热力图分析部分 -->
      <div class="bg-[#f6f8f6] rounded-xl card-shadow p-6 mb-6 shadow-lg">
        <div class="card-header mb-4">
          <h2 class="font-bold text-lg title1">价格地区时间热力图</h2>
        </div>

        <div class="filter-section mb-4">
          <div class="flex flex-nowrap items-center gap-4">
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-600">药材名称：</span>
              <select
                v-model="heatmapForm.herbName"
                class="w-36 px-3 py-1 border rounded-md text-sm"
                @change="(e) => handleHeatmapHerbChange((e.target as HTMLSelectElement).value)"
              >
                <option value="">请选择药材</option>
                <option v-for="herb in herbs" :key="herb" :value="herb">{{ herb }}</option>
              </select>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-600">规格：</span>
              <select
                v-model="heatmapForm.specification"
                class="px-3 py-1 border rounded-md text-sm"
              >
                <option value="">请选择规格</option>
                <option v-for="spec in heatmapSpecifications" :key="spec" :value="spec">{{ spec }}</option>
              </select>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-600">时间范围：</span>
              <div class="flex gap-1">
                <input
                  type="date"
                  v-model="heatmapForm.dateRange[0]"
                  class="px-2 py-1 border rounded-md text-sm"
                >
                <span class="text-gray-500">至</span>
                <input
                  type="date"
                  v-model="heatmapForm.dateRange[1]"
                  class="w-36 px-2 py-1 border rounded-md text-sm"
                >
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <span class="text-sm text-gray-600">时间间隔：</span>
              <div class="flex border rounded-md overflow-hidden">
                <button
                  v-for="interval in timeIntervals"
                  :key="interval.value"
                  class="px-3 py-1 text-sm"
                  :class="heatmapForm.timeInterval === interval.value ? 'bg-herbal-green text-white' : 'bg-white text-gray-600 hover:bg-gray-50'"
                  @click="heatmapForm.timeInterval = interval.value as 'week' | 'month'"
                >
                  {{ interval.label }}
                </button>
              </div>
            </div>
            <button
              class="px-4 py-1 bg-herbal-green text-white rounded-md text-sm"
              @click="fetchHeatmapData"
            >
              分析
            </button>
            <button
              class="px-4 py-1 border rounded-md text-sm text-gray-600 hover:bg-gray-50"
              @click="resetHeatmapForm"
            >
              重置
            </button>
          </div>
        </div>

        <!-- 热力图图表 -->
        <div class="chart-container mt-4 mb-4">
          <div class="price-heatmap-chart" ref="priceHeatmapChart"></div>
        </div>

        <div class="heatmap-info p-4 bg-[#f6f8f6] rounded-md" v-if="heatmapData.locations && heatmapData.locations.length > 0">
          <p class="text-gray-600">
            热力图显示了 {{ heatmapForm.herbName }} {{ heatmapForm.specification ? '(' + heatmapForm.specification + ')' : '' }} 在不同地区和时间段的价格变化情况。颜色越深表示价格越高。
          </p>
        </div>
      </div>

      <!-- 自定义弹窗 -->
      <CustomAlert
        v-if="alertVisible"
        :visible="alertVisible"
        :title="alertTitle"
        :message="alertMessage"
      />
    </main>

    <footer class="footer">
      <p>© 2026 灵汐药策 版权所有</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import AppSidebar from '@/components/AppSidebar.vue'
import CustomAlert from '@/components/CustomAlert.vue'
import * as echarts from 'echarts'
import api from '@/services/api'

defineOptions({ name: 'PricePreviewPage' })

// 类型定义
interface RankingItem {
  id: number
  rank: number
  herbName: string
  spec: string
  origin: string
  price: number
  weeklyIncrease: number
  recordTime: string
  herb_name?: string
  specification?: string
  location?: string
  week_change?: number | string
  month_change?: number | string
  year_change?: number | string
  recorded_at?: string
  icon?: string
}

interface LocationPriceItem {
  price: string | number
  location?: string
  date?: string
  herb_name?: string
  specification?: string
}

// 图表引用
const priceDistributionChart = ref<HTMLElement | null>(null)
const priceHeatmapChart = ref<HTMLElement | null>(null)
let priceDistributionChartInstance: echarts.ECharts | null = null
let priceHeatmapChartInstance: echarts.ECharts | null = null

// 数据状态
const herbs = ref<string[]>([])
const specifications = ref<string[]>([])
const heatmapSpecifications = ref<string[]>([])
const priceData = ref<number[]>([])
const priceStats = reactive({
  count: 0,
  min: 0,
  max: 0,
  avg: 0,
  median: 0,
  stdDev: 0
})
const heatmapData = reactive({
  locations: [] as string[],
  time_periods: [] as string[],
  data: [] as [number, number, number][]
})

// 排行榜相关状态
const rankingType = ref<'week_change' | 'month_change' | 'year_change'>('week_change')
const rankingLimit = ref<number>(10)
const priceRanking = ref<RankingItem[]>([])
const rankingLoading = ref<boolean>(false)

// 弹窗相关状态
const alertVisible = ref(false)
const alertTitle = ref('提示')
const alertMessage = ref('')

// 显示弹窗
const showAlert = (title: string, message: string) => {
  alertTitle.value = title
  alertMessage.value = message
  alertVisible.value = true
  // 3秒后自动关闭
  setTimeout(() => {
    alertVisible.value = false
  }, 3000)
}

// 筛选表单
const filterForm = reactive({
  herbName: '金银花',
  specification: '白花一级',
  dateRange: [
    new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 90天前
    new Date().toISOString().split('T')[0] // 今天
  ] as [string, string]
})

// 热力图筛选表单
const heatmapForm = reactive({
  herbName: '丹参',
  specification: '统个 山东',
  dateRange: [
    new Date(Date.now() - 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 180天前
    new Date().toISOString().split('T')[0] // 今天
  ] as [string, string],
  timeInterval: 'month' as 'week' | 'month' // 默认按月
})

// 排名类型选项
const rankingTypes: Array<{ value: 'week_change' | 'month_change' | 'year_change'; label: string }> = [
  { value: 'week_change', label: '周涨幅' },
  { value: 'month_change', label: '月涨幅' },
  { value: 'year_change', label: '年涨幅' }
]

// 时间间隔选项
const timeIntervals = [
  { value: 'week', label: '按周' },
  { value: 'month', label: '按月' }
]

// 初始化
onMounted(async () => {
  // 并行加载初始数据
  await Promise.all([
    fetchHerbs(),
    fetchPriceRanking() // 初始加载排行榜数据
  ])

  // 并行加载价格分布和热力图数据
  await Promise.all([
    // 价格分布数据
    (async () => {
      if (filterForm.herbName) {
        await fetchSpecifications(filterForm.herbName)
        // 自动获取价格分布数据
        await fetchPriceDistribution()
      }
    })(),
    // 热力图数据
    (async () => {
      if (heatmapForm.herbName) {
        await fetchHeatmapSpecifications(heatmapForm.herbName)
        // 自动获取热力图数据
        await fetchHeatmapData()
      }
    })()
  ])

  window.addEventListener('resize', handleResize)
})

// 在组件卸载时移除事件监听
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  // 清理图表实例
  if (priceDistributionChartInstance) {
    priceDistributionChartInstance.dispose()
  }
  if (priceHeatmapChartInstance) {
    priceHeatmapChartInstance.dispose()
  }
})

// 监听窗口大小变化，优化图表显示
const handleResize = () => {
  nextTick(() => {
    if (priceDistributionChartInstance) {
      priceDistributionChartInstance.resize()
    }
    if (priceHeatmapChartInstance) {
      priceHeatmapChartInstance.resize()
    }
  })
}

// 获取涨幅类型标签
const getRankingTypeLabel = () => {
  const labels = {
    'week_change': '周涨幅',
    'month_change': '月涨幅',
    'year_change': '年涨幅'
  }
  return labels[rankingType.value]
}

// 格式化日期
const formatDate = (dateString: string | null | undefined) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

// 获取排名值显示
const getRankingValue = (item: RankingItem, rankingType: 'week_change' | 'month_change' | 'year_change') => {
  const value = item[rankingType];
  if (value === undefined || value === null) {
    return '0';
  }
  const valueStr = String(value);
  if (valueStr.includes('%')) {
    return valueStr.replace('%', '');
  }
  return String(value);
}

// 获取价格涨幅排行榜数据
const fetchPriceRanking = async () => {
  rankingLoading.value = true
  try {
    const response = await api.getPriceRanking({
      ranking_type: rankingType.value,
      limit: rankingLimit.value,
      positive_only: true // 只获取正的涨幅
    })

    // 定义接口类型
    interface PriceRankingItem {
      id: number;
      herb_name: string;
      specification: string;
      location: string;
      price: number;
      week_change: string | number;
      month_change: string | number;
      year_change: string | number;
      recorded_at: string;
    }

    // 处理返回的数据，确保涨幅值是数字或百分比字符串
    priceRanking.value = response.map((item: PriceRankingItem, index: number) => {
      // 如果涨幅是百分比字符串，保持原样
      // 如果是数字字符串，转换为数字
      const fields: Array<'week_change' | 'month_change' | 'year_change'> = ['week_change', 'month_change', 'year_change'];
      fields.forEach((field) => {
        if (item[field] && typeof item[field] === 'string') {
          // 如果已经是百分比格式，不做处理
          if (!item[field].includes('%')) {
            // 尝试转换为数字
            const numValue = parseFloat(item[field]);
            if (!isNaN(numValue)) {
              item[field] = numValue;
            }
          }
        }
      });

      // 为每个药材分配一个图标
      const icons = ['🌿', '🌱', '🪴', '🎍', '🌾', '🪨', '🍃', '🌸', '🌺', '🌻'];
      const icon = icons[index % icons.length];

      return {
        id: item.id,
        rank: index + 1, // 计算排名
        herbName: item.herb_name,
        spec: item.specification,
        origin: item.location,
        price: item.price,
        weeklyIncrease: typeof item.week_change === 'string' ? parseFloat(item.week_change) || 0 : item.week_change || 0,
        recordTime: formatDate(item.recorded_at),
        herb_name: item.herb_name,
        specification: item.specification,
        location: item.location,
        week_change: item.week_change,
        month_change: item.month_change,
        year_change: item.year_change,
        recorded_at: item.recorded_at,
        icon: icon
      };
    });
  } catch (error) {
    console.error('获取价格涨幅排行榜失败:', error)
    priceRanking.value = []
  } finally {
    rankingLoading.value = false
  }
}

// 获取所有药材
const fetchHerbs = async () => {
  try {
    const response = await api.getHerbs()
    herbs.value = response
  } catch (error) {
    console.error('获取药材列表失败:', error)
    herbs.value = []
  }
}

// 获取药材规格
const fetchSpecifications = async (herbName: string) => {
  try {
    const response = await api.getSpecifications(herbName)
    specifications.value = response
  } catch (error) {
    console.error('获取规格列表失败:', error)
    specifications.value = []
  }
}

// 获取热力图药材规格
const fetchHeatmapSpecifications = async (herbName: string) => {
  try {
    const response = await api.getSpecifications(herbName)
    heatmapSpecifications.value = response
  } catch (error) {
    console.error('获取规格列表失败:', error)
    heatmapSpecifications.value = []
  }
}

// 获取价格分布数据
const fetchPriceDistribution = async () => {
  if (!filterForm.herbName) {
      showAlert('提示', '请选择药材名称')
      return
    }

  if (!filterForm.specification) {
      showAlert('提示', '请选择规格')
      return
    }

  try {
    // 首先获取所有地点的价格数据
    const locationParams = {
      location: '', // 空字符串表示获取所有地点
      herb_name: filterForm.herbName,
      specification: filterForm.specification,
      start_date: filterForm.dateRange[0],
      end_date: filterForm.dateRange[1]
    }

    const locationResponse = await api.getLocationPrices(locationParams)

    // 提取所有价格数据
    const prices = locationResponse.map((item: LocationPriceItem) => parseFloat(String(item.price))).filter((price: number) => !isNaN(price))
    priceData.value = prices

    // 计算价格统计信息
    calculatePriceStats(prices)

    // 绘制价格分布图
    drawPriceDistribution(prices)
  } catch (error) {
    console.error('获取价格分布数据失败:', error)
    showAlert('错误', '获取价格分布数据失败，请检查网络连接或参数设置')
  }
}

// 计算价格统计信息
const calculatePriceStats = (prices: number[]) => {
  if (!prices || prices.length === 0) {
    Object.assign(priceStats, { count: 0, min: 0, max: 0, avg: 0, median: 0, stdDev: 0 })
    return
  }

  // 排序价格数组用于计算中位数
  const sortedPrices = [...prices].sort((a, b) => a - b)

  // 计算基本统计量
  const count = prices.length
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const sum = prices.reduce((acc: number, price: number) => acc + price, 0)
  const avg = sum / count

  // 计算中位数
  const middle = Math.floor(count / 2)
  const median = count % 2 === 0
    ? ((sortedPrices[middle - 1] as number) + (sortedPrices[middle] as number)) / 2
    : sortedPrices[middle] as number

  // 计算标准差
  const squaredDiffs = prices.map((price: number) => Math.pow(price - avg, 2))
  const variance = squaredDiffs.reduce((acc: number, val: number) => acc + val, 0) / count
  const stdDev = Math.sqrt(variance)

  // 更新统计信息
  Object.assign(priceStats, { count, min, max, avg, median, stdDev })
}

// 绘制价格分布图
const drawPriceDistribution = (prices: number[]) => {
  if (!priceDistributionChart.value) return

  if (priceDistributionChartInstance) {
    priceDistributionChartInstance.dispose()
  }

  priceDistributionChartInstance = echarts.init(priceDistributionChart.value)

  if (!prices || prices.length === 0) {
    priceDistributionChartInstance.setOption({
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center'
      }
    })
    return
  }

  // 计算直方图的区间
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min

  // 根据数据量确定区间数量，最少5个，最多20个
  const binCount = Math.min(20, Math.max(5, Math.ceil(Math.sqrt(prices.length))))
  const binWidth = range / binCount

  // 创建区间
  const bins = Array(binCount).fill(0).map((_, i) => ({
    min: min + i * binWidth,
    max: min + (i + 1) * binWidth,
    count: 0
  }))

  // 统计每个区间的数量
  prices.forEach((price: number) => {
    const binIndex = Math.min(binCount - 1, Math.floor((price - min) / binWidth))
    if (bins[binIndex]) {
      bins[binIndex].count++
    }
  })

  // 准备图表数据
  const xAxisData = bins.map(bin => `${bin.min.toFixed(2)}-${bin.max.toFixed(2)}`)
  const seriesData = bins.map(bin => bin.count)

  // 设置图表选项
  const option = {
    title: {
      text: `${filterForm.herbName}${filterForm.specification ? ' (' + filterForm.specification + ')' : ''} 价格分布`,
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: function(params: { dataIndex: number }) {
        const bin = bins[params.dataIndex]
        if (bin) {
          return `价格区间: ${bin.min.toFixed(2)}-${bin.max.toFixed(2)} 元/kg<br/>数量: ${bin.count}<br/>占比: ${(bin.count / prices.length * 100).toFixed(2)}%`
        }
        return ''
      }
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      name: '价格区间 (元/kg)',
      axisLabel: {
        rotate: 45,
        interval: 0
      }
    },
    yAxis: {
      type: 'value',
      name: '数量'
    },
    series: [{
      name: '价格分布',
      type: 'bar',
      data: seriesData,
      itemStyle: {
        color: '#409EFF'
      }
    }],
    grid: {
      left: '5%',
      right: '5%',
      bottom: '15%',
      containLabel: true
    }
  }

  priceDistributionChartInstance.setOption(option)
}

// 处理药材变化
const handleHerbChange = async (value: string) => {
  filterForm.specification = ''
  if (value) {
    await fetchSpecifications(value)
  } else {
    specifications.value = []
  }
}

// 处理热力图药材变化
const handleHeatmapHerbChange = async (value: string) => {
  heatmapForm.specification = ''
  if (value) {
    await fetchHeatmapSpecifications(value)
  } else {
    heatmapSpecifications.value = []
  }
}

// 重置表单
const resetForm = () => {
  filterForm.herbName = ''
  filterForm.specification = ''
  filterForm.dateRange = [
    new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    new Date().toISOString().split('T')[0]
  ] as [string, string]
  specifications.value = []
  priceData.value = []
  Object.assign(priceStats, { count: 0, min: 0, max: 0, avg: 0, median: 0, stdDev: 0 })

  if (priceDistributionChartInstance) {
    priceDistributionChartInstance.dispose()
    priceDistributionChartInstance = null
  }
}

// 重置热力图表单
const resetHeatmapForm = () => {
  heatmapForm.herbName = ''
  heatmapForm.specification = ''
  heatmapForm.dateRange = [
    new Date(Date.now() - 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    new Date().toISOString().split('T')[0]
  ] as [string, string]
  heatmapForm.timeInterval = 'month' as const
  heatmapSpecifications.value = []

  // 清空热力图数据
  heatmapData.locations = []
  heatmapData.time_periods = []
  heatmapData.data = []

  if (priceHeatmapChartInstance) {
    priceHeatmapChartInstance.dispose()
    priceHeatmapChartInstance = null
  }
}

// 获取热力图数据
const fetchHeatmapData = async () => {
  if (!heatmapForm.herbName) {
      showAlert('提示', '请选择药材名称')
      return
    }

  try {
    const params = {
      herb_name: heatmapForm.herbName,
      specification: heatmapForm.specification,
      start_date: (heatmapForm.dateRange[0] || new Date(Date.now() - 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]) as string,
      end_date: (heatmapForm.dateRange[1] || new Date().toISOString().split('T')[0]) as string
    }

    const response = await api.getPriceHeatmap(params)

    // 更新热力图数据
    heatmapData.locations = response.locations
    heatmapData.time_periods = response.time_periods
    heatmapData.data = response.data

    // 绘制热力图
    drawHeatmap()
  } catch (error) {
    console.error('获取热力图数据失败:', error)
  }
}

// 绘制热力图
const drawHeatmap = () => {
  if (!priceHeatmapChart.value) return

  if (priceHeatmapChartInstance) {
    priceHeatmapChartInstance.dispose()
  }

  priceHeatmapChartInstance = echarts.init(priceHeatmapChart.value)

  if (!heatmapData.locations || heatmapData.locations.length === 0) {
    priceHeatmapChartInstance.setOption({
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center'
      }
    })
    return
  }

  // 计算数据的最大值和最小值，用于设置颜色范围
  let minValue = Infinity
  let maxValue = -Infinity

  heatmapData.data.forEach((item: [number, number, number]) => {
    const value = item[2]
    minValue = Math.min(minValue, value)
    maxValue = Math.max(maxValue, value)
  })

  // 设置热力图选项
  const option = {
    title: {
      text: `${heatmapForm.herbName}${heatmapForm.specification ? ' (' + heatmapForm.specification + ')' : ''} 价格热力图`,
      left: 'center'
    },
    tooltip: {
      position: 'top',
      formatter: function(params: { data: [number, number, number] }) {
        const location = heatmapData.locations[params.data[1]]
        const timePeriod = heatmapData.time_periods[params.data[0]]
        const price = params.data[2]
        return `地点: ${location}<br>` +
               `时间: ${timePeriod}<br>` +
               `价格: ${price.toFixed(2)} 元/kg`
      }
    },
    grid: {
      top: '60px',
      bottom: '15%',
      left: '10%',
      right: '10%'
    },
    xAxis: {
      type: 'category',
      data: heatmapData.time_periods,
      splitArea: {
        show: true
      },
      axisLabel: {
        rotate: 45,
        interval: 0
      },
      name: heatmapForm.timeInterval === 'week' ? '周' : '月',
      nameLocation: 'end'
    },
    yAxis: {
      type: 'category',
      data: heatmapData.locations,
      splitArea: {
        show: true
      },
      name: '地点',
      nameLocation: 'end'
    },
    visualMap: {
      min: minValue,
      max: maxValue,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '0',
      inRange: {
        color: ['#e0f3f8', '#abd9e9', '#74add1', '#4575b4', '#313695']
      }
    },
    series: [{
      name: '价格热力图',
      type: 'heatmap',
      data: heatmapData.data as [number, number, number][],
      label: {
        show: false
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }

  priceHeatmapChartInstance.setOption(option)
}
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  background-color: #f0f8f0;
  padding: 24px;
  margin-top: 70px;
}

.title1{
  padding: 10px;
}

.card-shadow {
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1), 0 2px 8px rgba(0, 0, 0, 0.1);
  /* border: 1px solid #aea6a6; */
  border-radius: 8px;
}

.shadow-lg {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

/* 表格行悬停效果 */
tbody tr:hover {
  background-color: #f9fafb;
}

/* 表格样式 */
table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #d0d0d0;
  border-radius: 0;
  overflow: hidden;
}

/* 表头样式 */
thead {
  background-color: #f8f9fa;
}

/* 表头单元格 */
th {
  font-weight: 600;
  font-size: 14px;
  letter-spacing: 0.05em;
  background-color: #f8f9fa;
  border: 1px solid #d0d0d0;
  padding: 8px 12px;
}

/* 表格单元格 */
td {
  font-size: 14px;
  line-height: 1.5;
  border: 1px solid #d0d0d0;
  padding: 8px 12px;
}

/* 表格行 */
tr {
  transition: background-color 0.2s ease;
}

/* 交替行背景色 */
tbody tr:nth-child(even) {
  background-color: #f8f9fa;
}

/* 表格行悬停效果 */
tbody tr:hover {
  background-color: #e9ecef;
}

.card-header {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 15px;
}

.card-header h3 {
  color: #000;
  margin: 0;
}

.filter-section {
  margin-bottom: 20px;
  padding: 16px;
  background-color: #f6f8f6;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow-x: auto;
}

.filter-section > div {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: nowrap;
  min-width: max-content;
}

.filter-section .flex.items-center {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-section select,
.filter-section button,
.filter-section input[type="date"] {
  height: 36px;
  box-sizing: border-box;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  padding: 0 12px;
  font-size: 14px;
  transition: all 0.2s ease;
}

.filter-section select:focus,
.filter-section input[type="date"]:focus {
  outline: none;
  border-color: #2d5d2b;
  box-shadow: 0 0 0 3px rgba(45, 93, 43, 0.1);
}

.filter-section button {
  padding: 0 16px;
  font-weight: 500;
  cursor: pointer;
}

.filter-section button.bg-herbal-green {
  background-color: #2d5d2b;
  color: white;
  border: none;
}

.filter-section button.bg-herbal-green:hover {
  background-color: #3a7a36;
}

.filter-section button.border {
  background-color: white;
  color: #4b5563;
  border: 1px solid #e5e7eb;
}

.filter-section button.border:hover {
  background-color: #f3f4f6;
}

.chart-container {
  margin-top: 20px;
  margin-bottom: 20px;
}

.price-distribution-chart,
.price-heatmap-chart {
  width: 100%;
  height: 400px;
}

.price-stats table {
  width: 100%;
  border-collapse: collapse;
}

.price-stats td {
  padding: 8px 12px;
  border-bottom: 1px solid #e5e7eb;
}

.price-stats tr:last-child td {
  border-bottom: none;
}

.price-stats,
.heatmap-info {
  margin-top: 20px;
  padding: 15px;
  background-color: #f6f8f6;
  border-radius: 4px;
}

.price-stats h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #000;
}

.heatmap-info p {
  margin: 0;
  color: #606266;
}

/* 新增样式 */
.ranking-table-container {
  margin-top: 20px;
}

.price-increase {
  color: #67c23a;
  font-weight: bold;
}

.empty-data {
  margin: 40px 0;
  text-align: center;
}

/* 自定义按钮样式 */
button {
  cursor: pointer;
  transition: all 0.2s ease;
}

button:hover {
  opacity: 0.9;
}

/* 加载动画 */
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

:root {
  --herbal-green: #2d5d2b;
  --herbal-lightGreen: #3a7a36;
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
</style>
