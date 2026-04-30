<template>
  <div class="page-container">
    <AppSidebar />
    <!-- 主内容区域 -->
    <main class="main-content">
      <!-- 顶部信息栏 -->
      <div class="mb-6">
        <div class="flex items-center justify-center mb-4">
          <h2 class="text-2xl font-bold text-gray-800 wenzi">药材价格走势</h2>
        </div>
      </div>
      <!-- 图表筛选区域（已调整为第二张图片风格） -->
<div class="filter-section mb-8 border border-gray-200 rounded-md p-4 bg-white">
  <div class="filter-row">
    <!-- 药材名称 -->
    <div class="filter-item">
      <span class="filter-label">药材名称：</span>
      <select
        v-model="chartFilterForm.herbName"
        class="filter-select"
        @change="(e) => handleChartHerbChange((e.target as HTMLSelectElement).value)"
      >
        <option value="">请选择药材</option>
        <option v-for="herb in herbs" :key="herb" :value="herb">{{ herb }}</option>
      </select>
    </div>

    <!-- 规格 -->
    <div class="filter-item">
      <span class="filter-label">规格：</span>
      <select
        v-model="chartFilterForm.specification"
        class="filter-select"
        :disabled="!chartFilterForm.herbName"
      >
        <option value="">请选择规格</option>
        <option v-for="spec in chartSpecifications" :key="spec" :value="spec">{{ spec }}</option>
      </select>
    </div>

    <!-- 时间范围 -->
    <div class="filter-item">
      <span class="filter-label">时间范围：</span>
      <div class="date-range-wrapper">
        <input
          type="date"
          v-model="chartFilterForm.dateRange[0]"
          class="filter-date"
          @change="handleChartDateRangeChange"
        />
        <span class="date-separator">至</span>
        <input
          type="date"
          v-model="chartFilterForm.dateRange[1]"
          class="filter-date"
          @change="handleChartDateRangeChange"
        />
      </div>
    </div>

    <!-- 按钮区 -->
    <div class="filter-buttons">
      <button
        class="btn-primary"
        @click="loadChartData"
      >
        分析
      </button>
      <button
        class="btn-secondary"
        @click="resetChartForm"
      >
        重置
      </button>
    </div>
  </div>
</div>

      <!-- 价格趋势图 -->
      <div class="bg-white rounded-xl card-shadow p-6 mb-6 shadow-lg">
        <h3 class="font-bold text-lg mb-2 title1 text-center">药材价格趋势</h3>
        <div class="chart-container" ref="priceTrendChart"></div>
      </div>

      <!-- 市场价格比较和天气与价格相关性 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <!-- 市场价格比较 -->
        <div class="bg-white rounded-xl card-shadow p-6 shadow-lg">
          <h3 class="font-bold text-lg mb-2 title1">药材市场价格比较</h3>
          <div class="chart-container" ref="marketComparisonChart"></div>
        </div>
        <!-- 天气与价格相关性 -->
        <div class="bg-white rounded-xl card-shadow p-6 shadow-lg">
          <h3 class="font-bold text-lg mb-2 title1">天气与药材价格相关性</h3>
          <div class="chart-container" ref="weatherCorrelationChart"></div>
        </div>
      </div>

      <!-- 价格趋势聚类分析 -->
      <!-- 价格趋势聚类分析 -->
      <div class="bg-white rounded-xl card-shadow p-6 mb-6 shadow-lg">
        <div class="card-header mb-2">
          <h3 class="font-bold text-lg title1">药材价格趋势聚类分析</h3>
          <p class="text-gray-600 mt-2">
            本功能通过机器学习算法对药材价格趋势进行聚类分析，将具有相似价格变动模式的药材归为同一类别。
            您可以选择不同的趋势类型查看代表性药材的价格变动情况。
          </p>
        </div>

        <div
          class="filter-section mb-4"
          style="padding: 16px; background-color: #f8f9fa; border-radius: 8px"
        >
          <div class="cluster-filter-row">
            <div class="cluster-filter-item">
              <span class="cluster-filter-label">时间范围：</span>
              <div class="cluster-date-range">
                <input
                  type="date"
                  v-model="dateRange[0]"
                  class="cluster-filter-date"
                />
                <span class="cluster-date-separator">至</span>
                <input
                  type="date"
                  v-model="dateRange[1]"
                  class="cluster-filter-date"
                />
              </div>
            </div>
            <div class="cluster-filter-buttons">
              <button
                class="cluster-btn-primary"
                @click="fetchClusteringData"
                :disabled="loading"
              >
                分析
              </button>
              <button
                class="cluster-btn-success"
                @click="saveClusteringResult"
                :disabled="!clusteringData"
              >
                保存结果
              </button>
              <button
                class="cluster-btn-primary"
                @click="showHistoryDialog"
              >
                加载历史聚类
              </button>
            </div>
          </div>
        </div>

        <div v-if="loading" class="flex items-center justify-center py-12">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-herbal-green"></div>
        </div>

        <template v-else-if="clusteringData">
          <div
            class="analysis-info p-4 bg-gray-50 rounded-md mb-4"
            v-if="clusteringData.analysis_time"
          >
            <p class="text-sm text-gray-600">分析时间: {{ clusteringData.analysis_time }}</p>
            <p class="text-sm text-gray-600" v-if="clusteringData.date_range">
              数据范围: {{ clusteringData.date_range.start_date || '未指定' }} 至
              {{ clusteringData.date_range.end_date || '未指定' }}
            </p>
          </div>

          <div class="trend-selection mb-4">
            <h4 class="font-medium mb-2">选择趋势类型：</h4>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="(trendType, clusterId) in clusteringData.trend_types"
                :key="clusterId"
                class="px-4 py-2 rounded-md text-sm font-medium transition-all"
                :class="
                  selectedCluster === parseInt(clusterId)
                    ? 'bg-herbal-green text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                "
                :disabled="!clusteringData.clusters[clusterId]"
                @click="selectedCluster = parseInt(clusterId); handleClusterChange()"
              >
                {{ trendType }} ({{
                  clusteringData.clusters[clusterId]
                    ? clusteringData.clusters[clusterId].total_herbs
                    : 0
                }})
              </button>
            </div>
          </div>

          <div
            v-if="selectedCluster !== null && clusteringData?.clusters?.[selectedCluster as number]"
            class="cluster-details"
          >
            <h4 class="font-medium mb-4">
              {{ clusteringData.trend_types[selectedCluster] }}类药材
            </h4>

            <div class="chart-container mb-6" ref="clusteringChart"></div>

            <div class="table-container">
              <table class="w-full border-collapse" style="border: 1px solid #e0e0e0; table-layout: fixed;">
                <colgroup>
                  <col style="width: 8%;">
                  <col style="width: 18%;">
                  <col style="width: 18%;">
                  <col style="width: 28%;">
                  <col style="width: 28%;">
                </colgroup>
                <thead>
                  <tr class="bg-gray-50 border-b border-gray-200">
                    <th
                      class="px-4 py-3 text-center text-sm font-medium text-gray-700 border border-gray-200"
                    >
                      序号
                    </th>
                    <th
                      class="px-4 py-3 text-center text-sm font-medium text-gray-700 border border-gray-200"
                    >
                      药材名称
                    </th>
                    <th
                      class="px-4 py-3 text-center text-sm font-medium text-gray-700 border border-gray-200"
                    >
                      规格
                    </th>
                    <th
                      class="px-4 py-3 text-center text-sm font-medium text-gray-700 border border-gray-200"
                    >
                      产地/市场
                    </th>
                    <th
                      class="px-4 py-3 text-center text-sm font-medium text-gray-700 border border-gray-200"
                    >
                      价格变动
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(herb, index) in clusteringData?.clusters?.[selectedCluster as number]
                      ?.herbs || []"
                    :key="index"
                    class="border-b border-gray-200"
                    :class="index % 2 === 1 ? 'bg-gray-50' : ''"
                  >
                    <td class="px-4 py-3 text-sm text-gray-900 border border-gray-200 text-center">
                      {{ index + 1 }}
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-900 border border-gray-200 text-center">
                      {{ herb.herb_name }}
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-500 border border-gray-200 text-center">
                      {{ herb.specification }}
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-500 border border-gray-200 text-center">
                      {{ herb.location }}
                    </td>
                    <td class="px-4 py-3 text-sm border border-gray-200 text-center">
                      <button
                        class="text-herbal-green hover:text-herbal-lightGreen font-medium"
                        @click="showHerbDetail(herb)"
                      >
                        查看详情
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div v-else-if="selectedCluster !== null" class="empty-cluster py-12 text-center">
            <p class="text-gray-500">该类别暂无药材数据</p>
          </div>
        </template>

        <div v-else class="empty-data py-12 text-center"></div>
      </div>
    </main>

    <footer class="footer">
      <p>© 2026 灵汐药策 版权所有</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import AppSidebar from '@/components/AppSidebar.vue'
import * as api from '@/api/price'

defineOptions({ name: 'PriceTrendPage' })

// 图表引用和实例
const priceTrendChart = ref<HTMLElement | null>(null)
const marketComparisonChart = ref<HTMLElement | null>(null)
const weatherCorrelationChart = ref<HTMLElement | null>(null)
const clusteringChart = ref<HTMLElement | null>(null)
let priceTrendChartInstance: echarts.ECharts | null = null
let marketComparisonChartInstance: echarts.ECharts | null = null
let weatherCorrelationChartInstance: echarts.ECharts | null = null
let clusteringChartInstance: echarts.ECharts | null = null

// 数据状态
const herbs = ref<string[]>([])
const chartSpecifications = ref<string[]>([])

// 图表筛选表单
const chartFilterForm = reactive({
  herbName: '柴胡',
  specification: '统根',
  dateRange: [
    new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] as string, // 30天前
    new Date().toISOString().split('T')[0] as string, // 今天
  ] as [string, string],
})

// 聚类分析相关状态
const dateRange = ref<[string, string]>([
  new Date(Date.now() - 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] as string, // 6个月前
  new Date().toISOString().split('T')[0] as string, // 今天
])
const loading = ref<boolean>(false)
interface ClusteringData {
  analysis_time?: string
  date_range?: {
    start_date: string
    end_date: string
  }
  trend_types: Record<number, string>
  clusters: Record<
    number,
    {
      total_herbs: number
      all_herb_names: string[]
      herbs: Array<{
        herb_name: string
        specification: string
        location: string
        prices: number[]
        dates: string[]
      }>
    }
  >
}

interface Herb {
  herb_name: string
  specification: string
  location: string
  prices: number[]
  dates: string[]
}

interface HistoryFile {
  filename: string
  date: string
  size: string
}

const clusteringData = ref<ClusteringData | null>(null)
const selectedCluster = ref<number | null>(null)
const selectedHerb = ref<Herb>({} as Herb)
const herbDetailVisible = ref<boolean>(false)
const saveSuccessVisible = ref<boolean>(false)
const savedFilePath = ref<string>('')
const isLocalFile = ref<boolean>(false)
const historyDialogVisible = ref<boolean>(false)
const historyFiles = ref<HistoryFile[]>([])
const loadingHistory = ref<boolean>(false)

// 弹窗相关状态
const alertVisible = ref<boolean>(false)
const alertTitle = ref<string>('提示')
const alertMessage = ref<string>('')

// 监听窗口大小变化，优化图表显示
const handleResize = () => {
  nextTick(() => {
    const charts = [
      priceTrendChartInstance,
      marketComparisonChartInstance,
      weatherCorrelationChartInstance,
      clusteringChartInstance,
    ]
    charts.forEach((chart) => {
      if (chart) {
        chart.resize()
      }
    })
  })
}

// 监听图表药材名称选择变化
watch(
  () => chartFilterForm.herbName,
  (newHerbName) => {
    // 清空规格选择
    chartFilterForm.specification = ''

    if (newHerbName) {
      // 获取该药材的规格列表
      fetchChartSpecifications(newHerbName)
    } else {
      // 清空规格列表
      chartSpecifications.value = []
    }
  },
)

// 初始化
onMounted(async () => {
  await fetchHerbs()
  initCharts()
  
  // 如果有默认的药材选择，自动获取该药材的规格列表并选择默认规格
  if (chartFilterForm.herbName) {
    await fetchChartSpecifications(chartFilterForm.herbName)
    // 自动获取价格趋势数据
    await loadChartData()
  }
  
  window.addEventListener('resize', handleResize)
})

// 在组件卸载时移除事件监听
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

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

// API请求函数
const fetchHerbs = async () => {
  try {
    const response = await api.getHerbs()
    herbs.value = response
  } catch (error) {
    console.error('获取药材列表失败:', error)
    showAlert('错误', '获取药材列表失败')
  }
}

// 获取图表筛选用的规格列表
const fetchChartSpecifications = async (herbName: string) => {
  try {
    const response = await api.getSpecifications(herbName)
    chartSpecifications.value = response
  } catch (error) {
    console.error('获取规格列表失败:', error)
    showAlert('错误', '获取规格列表失败')
  }
}

// 初始化图表通用函数
const initChart = (
  chartRef: { value: HTMLElement | null },
  chartInstance: echarts.ECharts | null,
) => {
  if (!chartRef.value) return null

  if (chartInstance) {
    chartInstance.dispose()
  }

  return echarts.init(chartRef.value, null, {
    renderer: 'canvas',
    useDirtyRect: true,
    devicePixelRatio: window.devicePixelRatio,
  })
}

// 设置空数据图表选项
const getEmptyChartOption = () => ({
  title: {
    text: '暂无数据',
    left: 'center',
    top: 'center',
    textStyle: { opacity: 0.2 },
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true,
  },
})

// 初始化图表函数
const initCharts = () => {
  nextTick(() => {
    // 初始化价格趋势图表
    if (priceTrendChart.value) {
      priceTrendChartInstance = initChart(priceTrendChart, priceTrendChartInstance)
      priceTrendChartInstance!.setOption(getEmptyChartOption())
    }

    // 初始化市场比较图表
    if (marketComparisonChart.value) {
      marketComparisonChartInstance = initChart(
        marketComparisonChart,
        marketComparisonChartInstance,
      )
      marketComparisonChartInstance!.setOption(getEmptyChartOption())
    }

    // 初始化天气相关性图表
    if (weatherCorrelationChart.value) {
      weatherCorrelationChartInstance = initChart(
        weatherCorrelationChart,
        weatherCorrelationChartInstance,
      )
      weatherCorrelationChartInstance!.setOption(getEmptyChartOption())
    }
  })
}

// 加载图表数据
const loadChartData = async () => {
  // 检查是否已选择药材和规格
  if (!chartFilterForm.herbName) {
    showAlert('提示', '请选择药材')
    return
  }

  if (!chartFilterForm.specification) {
    showAlert('提示', '请选择规格')
    return
  }

  // 确保图表已初始化
  if (!priceTrendChartInstance && priceTrendChart.value) {
    priceTrendChartInstance = initChart(priceTrendChart, priceTrendChartInstance)
  }

  if (!marketComparisonChartInstance && marketComparisonChart.value) {
    marketComparisonChartInstance = initChart(marketComparisonChart, marketComparisonChartInstance)
  }

  if (!weatherCorrelationChartInstance && weatherCorrelationChart.value) {
    weatherCorrelationChartInstance = initChart(
      weatherCorrelationChart,
      weatherCorrelationChartInstance,
    )
  }

  loading.value = true
  try {
    // 加载价格趋势
    if (priceTrendChartInstance) {
      await loadPriceTrendData()
    }

    // 加载市场比较
    if (marketComparisonChartInstance) {
      await loadMarketComparisonData()
    }

    // 加载天气相关性
    if (weatherCorrelationChartInstance) {
      await loadWeatherCorrelationData()
    }

    showAlert('成功', '数据加载成功')
  } catch (error) {
    console.error('数据加载失败:', error)
    showAlert('错误', '数据加载失败')
  } finally {
    loading.value = false
  }
}

// 价格趋势数据加载函数
const loadPriceTrendData = async () => {
  if (!priceTrendChartInstance) {
    console.error('价格趋势图表未初始化')
    return
  }

  try {
    const params = {
      herbName: chartFilterForm.herbName,
      specification: chartFilterForm.specification,
      startDate: chartFilterForm.dateRange[0],
      endDate: chartFilterForm.dateRange[1],
    }

    const response = await api.getPriceTrend(params)
    const data = response

    // 更新价格趋势图表
    priceTrendChartInstance.setOption({
      title: {
        text: `${chartFilterForm.herbName} ${chartFilterForm.specification} 价格趋势`,
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
      },
      legend: {
        data: ['平均价格', '最低价格', '最高价格'],
        bottom: 55,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '18%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: data.dates,
        axisLabel: { rotate: 45 },
      },
      yAxis: {
        type: 'value',
        name: '价格 (元/kg)',
        nameLocation: 'middle',
        nameGap: 40,
      },
      series: [
        {
          name: '平均价格',
          type: 'line',
          data: data.avg_prices,
          smooth: true,
          lineStyle: { width: 3 },
          itemStyle: { color: '#409EFF' },
        },
        {
          name: '最低价格',
          type: 'line',
          data: data.min_prices,
          smooth: true,
          lineStyle: { width: 2 },
          itemStyle: { color: '#67C23A' },
        },
        {
          name: '最高价格',
          type: 'line',
          data: data.max_prices,
          smooth: true,
          lineStyle: { width: 2 },
          itemStyle: { color: '#F56C6C' },
        },
      ],
      dataZoom: [
        { type: 'inside', start: 0, end: 100 },
        { start: 0, end: 100 },
      ],
    })
  } catch (error) {
    console.error('加载价格趋势数据失败:', error)
    showAlert('错误', '加载价格趋势数据失败')
    throw error
  }
}

// 市场比较数据加载函数
const loadMarketComparisonData = async () => {
  if (!marketComparisonChartInstance) {
    console.error('市场比较图表未初始化')
    return
  }

  try {
    const params = {
      herbName: chartFilterForm.herbName,
      specification: chartFilterForm.specification,
    }

    const response = await api.getMarketComparison(params)
    const data = response

    // 更新市场比较图表
    marketComparisonChartInstance.setOption({
      title: {
        text: `${chartFilterForm.herbName} ${chartFilterForm.specification} 市场价格比较`,
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: data.locations,
        axisLabel: {
          rotate: 45,
          interval: 0,
        },
      },
      yAxis: {
        type: 'value',
        name: '平均价格 (元/kg)',
        nameLocation: 'middle',
        nameGap: 40,
      },
      series: [
        {
          name: '平均价格',
          type: 'bar',
          data: data.prices,
          itemStyle: {
            color: function (params: { dataIndex: number }) {
              // 根据价格高低设置不同颜色
              const colorList = ['#91cc75', '#fac858', '#ee6666', '#73c0de', '#5470c6', '#9a60b4']
              return colorList[params.dataIndex % colorList.length]
            },
          },
          label: {
            show: true,
            position: 'top',
            formatter: function(params: any) { return params.value.toFixed(2) + ' 元/kg' },
          },
        },
      ],
      dataZoom: [
        { type: 'inside', start: 0, end: 100 },
        { start: 0, end: 100 },
      ],
    })
  } catch (error) {
    console.error('加载市场比较数据失败:', error)
    showAlert('错误', '加载市场比较数据失败')
    throw error
  }
}

// 天气相关性数据加载函数
const loadWeatherCorrelationData = async () => {
  if (!weatherCorrelationChartInstance) {
    console.error('天气相关性图表未初始化')
    return
  }

  try {
    const params = {
      herbName: chartFilterForm.herbName,
      specification: chartFilterForm.specification,
      startDate: chartFilterForm.dateRange[0],
      endDate: chartFilterForm.dateRange[1],
    }

    const response = await api.getWeatherPriceCorrelation(params)
    const data = response

    // 更新天气相关性图表
    weatherCorrelationChartInstance.setOption({
      title: {
        text: `${chartFilterForm.herbName} ${chartFilterForm.specification} 天气与价格相关性`,
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
      },
      legend: {
        data: ['价格', '温度', '降水量'],
        bottom: 55,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '18%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: data.dates,
        axisLabel: { rotate: 45 },
      },
      yAxis: [
        {
          type: 'value',
          name: '价格 (元/kg)',
          position: 'left',
          axisLine: { lineStyle: { color: '#409EFF' } },
          axisLabel: { formatter: '{value} 元' },
        },
        {
          type: 'value',
          name: '温度 (°C)',
          position: 'right',
          offset: 0,
          axisLine: { lineStyle: { color: '#F56C6C' } },
          axisLabel: { formatter: '{value} °C' },
        },
        {
          type: 'value',
          name: '降水量 (mm)',
          position: 'right',
          offset: 80,
          axisLine: { lineStyle: { color: '#67C23A' } },
          axisLabel: { formatter: '{value} mm' },
        },
      ],
      series: [
        {
          name: '价格',
          type: 'line',
          data: data.prices,
          yAxisIndex: 0,
          smooth: true,
          itemStyle: { color: '#409EFF' },
        },
        {
          name: '温度',
          type: 'line',
          data: data.temperatures,
          yAxisIndex: 1,
          smooth: true,
          itemStyle: { color: '#F56C6C' },
        },
        {
          name: '降水量',
          type: 'bar',
          data: data.precipitations,
          yAxisIndex: 2,
          itemStyle: { color: '#67C23A', opacity: 0.5 },
        },
      ],
      dataZoom: [
        { type: 'inside', start: 0, end: 100 },
        { start: 0, end: 100 },
      ],
    })
  } catch (error) {
    console.error('加载天气相关性数据失败:', error)
    showAlert('错误', '加载天气相关性数据失败')
    throw error
  }
}

// 图表日期范围变化处理
const handleChartDateRangeChange = () => {
  // 如果已经选择了药材和规格，则自动刷新图表
  if (chartFilterForm.herbName && chartFilterForm.specification) {
    loadChartData()
  }
}

// 图表药材选择变化处理
const handleChartHerbChange = async (value: string) => {
  chartFilterForm.specification = ''
  if (value) {
    await fetchChartSpecifications(value)
  } else {
    chartSpecifications.value = []
  }
}

// 重置图表表单
const resetChartForm = () => {
  Object.assign(chartFilterForm, {
    herbName: '',
    specification: '',
    dateRange: [
      new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0] as string,
      new Date().toISOString().split('T')[0] as string,
    ] as [string, string],
  })
  chartSpecifications.value = []

  // 重置图表
  const emptyOption = getEmptyChartOption()
  const charts = [
    priceTrendChartInstance,
    marketComparisonChartInstance,
    weatherCorrelationChartInstance,
  ]
  charts.forEach((chart) => {
    if (chart) {
      chart.setOption({
        ...emptyOption,
        series: [],
      })
    }
  })
}

// 聚类分析相关函数
const fetchClusteringData = async () => {
  loading.value = true
  isLocalFile.value = false
  try {
    const response = await api.getPriceTrendClustering({
      startDate: dateRange.value[0],
      endDate: dateRange.value[1],
      saveResult: false,
    })

    clusteringData.value = response

    // 优先选择"先稳后涨"的聚类，否则选择第一个有数据的聚类
    if (clusteringData.value && clusteringData.value.clusters) {
      let targetClusterId: string | null = null
      // 遍历所有聚类，寻找"先稳后涨"的聚类
      for (const clusterId in clusteringData.value.trend_types) {
        if (clusteringData.value.trend_types[parseInt(clusterId)] === '先稳后涨') {
          targetClusterId = clusterId
          break
        }
      }
      // 如果没有找到"先稳后涨"的聚类，选择第一个
      if (!targetClusterId) {
        targetClusterId = Object.keys(clusteringData.value.clusters)[0]
      }
      if (targetClusterId) {
        selectedCluster.value = parseInt(targetClusterId)
        // 等待DOM更新，确保图表容器已经渲染
        setTimeout(() => {
          nextTick(() => {
            console.log('DOM更新后调用renderTrendChart')
            renderTrendChart()
          })
        }, 100)
      }
    }
  } catch (error) {
    console.error('获取聚类数据失败:', error)
    showAlert('错误', '获取聚类数据失败')
  } finally {
    loading.value = false
  }
}

const handleClusterChange = () => {
  nextTick(() => {
    renderTrendChart()
  })
}

const renderTrendChart = () => {
  if (!selectedCluster.value || !clusteringData.value || !clusteringData.value.clusters) {
    console.log('聚类数据不完整')
    return
  }

  const data = clusteringData.value
  const cluster = data.clusters[selectedCluster.value]
  if (!cluster) {
    console.log('未找到指定聚类')
    return
  }

  const herbs = cluster.herbs
  if (!herbs || herbs.length === 0) {
    console.log('聚类中没有药材数据')
    return
  }

  // 初始化图表
  console.log('clusteringChart.value:', clusteringChart.value)
  if (clusteringChart.value) {
    console.log('图表容器存在，宽高:', clusteringChart.value.clientWidth, 'x', clusteringChart.value.clientHeight)
    if (!clusteringChartInstance) {
      console.log('初始化聚类图表')
      clusteringChartInstance = initChart(clusteringChart, clusteringChartInstance)
      console.log('图表实例创建:', clusteringChartInstance)
    }
  } else {
    console.log('图表容器不存在')
    return
  }

  if (!clusteringChartInstance) {
    console.log('图表实例创建失败')
    return
  }
  console.log('图表实例创建成功')

  // 检查数据格式
  console.log('聚类数据:', herbs)
  console.log('第一个药材的dates:', herbs[0]?.dates)
  console.log('第一个药材的prices:', herbs[0]?.prices)

  // 准备数据
  const series = herbs.map((herb: Herb) => {
    return {
      name: `${herb.herb_name} (${herb.specification}) - ${herb.location}`,
      type: 'line',
      data: herb.prices || [],
      smooth: true,
      showSymbol: false,
    }
  })

  // 设置图表选项
  const option = {
    title: {
      text: `${data.trend_types?.[selectedCluster.value] || '未知'}类药材价格趋势`,
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      formatter: function (
        params: Array<{
          axisValue: string
          marker: string
          seriesName: string
          value: number | string
        }>,
      ) {
        if (!params || params.length === 0) return ''
        let result = params[0]?.axisValue + '<br/>' || ''
        params.forEach(
          (param: {
            axisValue: string
            marker: string
            seriesName: string
            value: number | string
          }) => {
            result +=
              param.marker + param.seriesName + ': ' + Number(param.value).toFixed(2) + '元/kg<br/>'
          },
        )
        return result
      },
    },
    legend: {
      data: series.map((s: { name: string }) => s.name),
      type: 'scroll',
      orient: 'horizontal',
      bottom: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: herbs[0]?.dates || [],
      axisLabel: {
        rotate: 45,
      },
    },
    yAxis: {
      type: 'value',
      name: '价格 (元/kg)',
    },
    series: series,
    toolbox: {
      feature: {
        saveAsImage: {},
      },
    },
  }

  // 渲染图表
  console.log('设置图表选项')
  clusteringChartInstance.setOption(option)
  console.log('图表渲染完成')
  // 强制图表 resize
  clusteringChartInstance.resize()
}

const showHerbDetail = (herb: Herb) => {
  selectedHerb.value = herb
  herbDetailVisible.value = true

  nextTick(() => {
    renderHerbDetailChart()
  })
}

const renderHerbDetailChart = () => {
  if (!selectedHerb.value || !selectedHerb.value.prices) {
    return
  }

  // 这里可以实现药材详情图表的渲染
  console.log('Rendering herb detail chart for:', selectedHerb.value)
}

const saveClusteringResult = async () => {
  if (!clusteringData.value) {
    showAlert('提示', '没有可保存的聚类数据')
    return
  }

  try {
    // 如果是本地文件加载的数据，直接提示用户
    if (isLocalFile.value) {
      showAlert('提示', '当前数据已经是从本地文件加载的，无需再次保存')
      return
    }

    // 添加日期范围信息
    if (!clusteringData.value.date_range) {
      clusteringData.value.date_range = {
        start_date: dateRange.value[0],
        end_date: dateRange.value[1],
      }
    }

    // 添加分析时间
    if (!clusteringData.value.analysis_time) {
      clusteringData.value.analysis_time = new Date().toLocaleString()
    }

    const response = await api.saveClusteringResult(clusteringData.value)

    if (response.success) {
      savedFilePath.value = response.file_path || ''
      saveSuccessVisible.value = true
      showAlert('成功', '聚类分析结果已成功保存')
    } else {
      showAlert('错误', '保存失败: ' + (response.error || '未知错误'))
    }
  } catch (error) {
    console.error('保存聚类结果失败:', error)
    showAlert('错误', '保存聚类结果失败')
  }
}

const showHistoryDialog = () => {
  historyDialogVisible.value = true
  fetchHistoryFiles()
}

const fetchHistoryFiles = async () => {
  loadingHistory.value = true
  try {
    const response = await api.getClusteringHistory()
    historyFiles.value = response
  } catch (error) {
    console.error('获取历史聚类文件列表失败:', error)
    showAlert('错误', '获取历史聚类文件列表失败')
  } finally {
    loadingHistory.value = false
  }
}

const loadHistoryFile = async (fileInfo: HistoryFile) => {
  loading.value = true
  historyDialogVisible.value = false
  try {
    const response = await api.loadClusteringHistory(fileInfo.filename)
    clusteringData.value = response
    isLocalFile.value = true

    // 优先选择"先稳后涨"的聚类，否则选择第一个有数据的聚类
    if (clusteringData.value && clusteringData.value.clusters) {
      let targetClusterId: string | null = null
      // 遍历所有聚类，寻找"先稳后涨"的聚类
      for (const clusterId in clusteringData.value.trend_types) {
        if (clusteringData.value.trend_types[parseInt(clusterId)] === '先稳后涨') {
          targetClusterId = clusterId
          break
        }
      }
      // 如果没有找到"先稳后涨"的聚类，选择第一个
      if (!targetClusterId) {
        targetClusterId = Object.keys(clusteringData.value.clusters)[0]
      }
      if (targetClusterId) {
        selectedCluster.value = parseInt(targetClusterId)
        nextTick(() => {
          renderTrendChart()
        })
      }
    }

    showAlert('成功', `成功加载历史聚类文件: ${fileInfo.filename}`)
  } catch (error) {
    console.error('加载历史聚类文件失败:', error)
    showAlert('错误', '加载历史聚类文件失败')
  } finally {
    loading.value = false
  }
}

// 暴露给父组件的方法
defineExpose({
  loadChartData,
  resetChartForm,
  loadHistoryFile,
})
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.wenzi{
  font-size: 30px;
}
.main-content {
  flex: 1;
  background-color: #f0f8f0;
  padding: 24px;
  margin-top: 70px;
}

.title1{
  padding: 10px;
  font-size: 25px;;
  text-align: center;
}

.card-shadow {
  padding :5px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;
}

.card-shadow:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.shadow-lg {
  box-shadow:
    0 10px 15px -3px rgba(0, 0, 0, 0.1),
    0 4px 6px -2px rgba(0, 0, 0, 0.05);
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

.filter-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16px;
  flex-wrap: nowrap;
  white-space: nowrap;
  padding-bottom: 16px;
  
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.filter-label {
  font-size: 14px;
  color: #4b5563;
  white-space: nowrap;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  background-color: white;
  min-width: 120px;
}

.filter-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.date-range-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
}

.filter-date {
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  width: 130px;
}

.filter-date:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.date-separator {
  color: #6b7280;
  font-size: 14px;
}

.filter-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
  flex-shrink: 0;
}

.btn-primary {
  padding: 8px 20px;
  background-color: var(--herbal-green);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary:hover {
  background-color: var(--herbal-lightGreen);
}

.btn-secondary {
  padding: 8px 20px;
  background-color: white;
  color: #4b5563;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-secondary:hover {
  background-color: #f3f4f6;
}

.cluster-filter-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16px;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.cluster-filter-item {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.cluster-filter-label {
  font-size: 14px;
  color: #4b5563;
  white-space: nowrap;
}

.cluster-date-range {
  display: flex;
  align-items: center;
  gap: 4px;
}

.cluster-filter-date {
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  width: 130px;
  background-color: white;
}

.cluster-filter-date:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}

.cluster-date-separator {
  color: #6b7280;
  font-size: 14px;
}

.cluster-filter-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
  flex-shrink: 0;
}

.cluster-btn-primary {
  padding: 8px 16px;
  background-color: var(--herbal-green);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.cluster-btn-primary:hover {
  background-color: var(--herbal-lightGreen);
}

.cluster-btn-success {
  padding: 8px 16px;
  background-color: var(--herbal-green);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.cluster-btn-success:hover {
  background-color: var(--herbal-lightGreen);
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

.chart-container {
  width: 100%;
  height: 450px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

@media screen and (max-width: 768px) {
  .chart-container {
    height: 300px;
  }
}

.card-header {
  margin-bottom: 20px;
}

.description {
  color: #666;
  margin-top: 10px;
}

.trend-selection {
  margin-bottom: 20px;
}

.all-herbs-container {
  margin-bottom: 20px;
}

.herb-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.analysis-info {
  background-color: #f8f9fa;
  padding: 10px 15px;
  border-radius: 4px;
  margin-bottom: 15px;
  font-size: 14px;
  color: #606266;
}

.analysis-info p {
  margin: 5px 0;
}

.empty-data,
.empty-cluster {
  margin-top: 20px;
  text-align: center;
}

:root {
  --herbal-green: #2d5d2b;
  --herbal-lightGreen: #3a7a36;
}

.table-container {
  width: 100%;
  margin: 0 auto;
  border: 2px solid #d0d0d0;
  border-radius: 8px;
  overflow: hidden;
}

.table-container table {
  width: 100%;
  border-collapse: collapse;
}

.table-container th,
.table-container td {
  text-align: center;
  vertical-align: middle;
  border: 1px solid #d0d0d0;
}

.table-container th {
  border-bottom: 2px solid #d0d0d0;
}

.table-container tr:last-child td {
  border-bottom: none;
}
</style>
