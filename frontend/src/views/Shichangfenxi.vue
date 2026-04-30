<template>
  <div class="page-container">
    <AppSidebar />
    <!-- 主内容区域 -->
    <main class="main-content">
      <!-- 顶部信息栏 -->
      <div class="mb-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-2xl font-bold text-gray-80 wenzi">市场分析</h2>
        </div>
      </div>

      <!-- 数据预测部分 -->
      <div class="bg-[#f0f8f0] rounded-xl card-shadow p-6 mb-6">
        <h3 class="font-bold text-lg mb-4 title1">药材价格预测</h3>

        <!-- 预测参数设置 -->
        <div class="filter-section mb-6">
          <div class="prediction-filter-row">
            <div class="prediction-filter-item">
              <select
                v-model="predictionForm.herbName"
                @change="handleHerbChange()"
                class="prediction-filter-select"
              >
                <option value="">药材名称</option>
                <option v-for="herb in herbs" :key="herb" :value="herb">{{ herb }}</option>
              </select>
            </div>
            <div class="prediction-filter-item">
              <select
                v-model="predictionForm.specification"
                :disabled="!predictionForm.herbName"
                class="prediction-filter-select"
              >
                <option value="">规格</option>
                <option v-for="spec in specifications" :key="spec" :value="spec">{{ spec }}</option>
              </select>
            </div>
            <div class="prediction-filter-item">
              <label class="text-sm mr-2">历史数据范围：</label>
            </div>
            <div class="prediction-filter-item">
              <input
                type="date"
                v-model="predictionForm.startDate"
                class="prediction-filter-select"
              >
            </div>
            <div class="prediction-filter-item">
              <span class="text-sm mx-2">至</span>
            </div>
            <div class="prediction-filter-item">
              <input
                type="date"
                v-model="predictionForm.endDate"
                class="prediction-filter-select"
              >
            </div>
            <div class="prediction-filter-item">
              <label class="text-sm mr-2">预测天数：</label>
            </div>
            <div class="prediction-filter-item">
              <div class="prediction-days-wrapper">
                <button @click="decreaseForecastDays" class="prediction-days-btn">-</button>
                <input
                  type="number"
                  v-model.number="predictionForm.forecastDays"
                  min="7"
                  max="90"
                  step="7"
                  class="prediction-days-input"
                >
                <button @click="increaseForecastDays" class="prediction-days-btn">+</button>
              </div>
            </div>
            <div class="prediction-filter-buttons">
              <button
                @click="runPrediction"
                :disabled="loading"
                class="prediction-btn-primary"
              >
                开始预测
              </button>
              <button
                @click="resetPredictionForm"
                class="prediction-btn-secondary"
              >
                重置
              </button>
              <button
                @click="showPredictionHistory"
                class="prediction-btn-secondary"
              >
                加载历史预测
              </button>
            </div>
          </div>
        </div>

        <!-- 预测进度 -->
        <div v-if="loading" class="prediction-progress mb-6 py-6 flex flex-col items-center justify-center p-6">
          <div class="w-full bg-gray-200 rounded-full h-2.5 mb-4">
            <div class="bg-herbal-green h-2.5 rounded-full" :style="{ width: predictionProgress + '%' }"></div>
          </div>
          <p class="text-sm text-gray-600 text-center">正在进行预测计算，请稍候...</p>
        </div>

        <!-- 预测结果展示 -->
        <div class="prediction-results mb-6">
          <!-- <h4 class="font-semibold text-md mb-3">预测结果</h4> -->

          <!-- 有数据时显示的内容 -->
          <template v-if="predictionResults && !loading">
            <!-- 市场选择 (仅在按市场预测时显示) -->
            <div v-if="predictionResults.by_market" class="market-selector mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">选择市场</label>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="market in availableMarkets"
                  :key="market"
                  @click="selectedMarket = market; handleMarketChange()"
                  :class="[
                    'px-3 py-1 rounded-md text-sm',
                    selectedMarket === market
                      ? 'bg-herbal-green text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  ]"
                >
                  {{ market }}
                </button>
              </div>
            </div>

            <!-- 模型选择 -->
            <div class="model-selector mb-6">
              <label class="block text-sm font-medium text-gray-700 mb-3">选择预测模型</label>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="model in availableModels"
                  :key="model"
                  @click="selectedModel = model; updateChartData()"
                  :class="[
                    'px-4 py-2 rounded-xl text-sm transition-colors duration-200',
                    selectedModel === model
                      ? 'bg-[#2d5d2b] text-white'
                      : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
                  ]"
                >
                  {{ getModelName(model) }}
                </button>
              </div>
            </div>
            <!-- 价格预测图表 -->
            <div class="chart-container mb-6 min-h-[400px]" ref="pricePredictionChart">
              
            </div>
            <!-- 模型评估指标 -->
            <div v-if="modelMetrics" class="model-metrics mb-6">
              <h4 class="font-semibold text-md mb-2">模型评估指标</h4>
              <div style="display: flex; gap: 16px; overflow-x: auto; padding-bottom: 8px; width: 100%;">
                <div style="background-color: #f9fafb; padding: 12px; border-radius: 8px; display: flex; align-items: center; white-space: nowrap; flex-shrink: 0;">
                  <p style="font-size: 14px; color: #4b5563; margin-right: 8px;">平均绝对误差 (MAE):</p>
                  <p style="font-weight: 500;">{{ formatNumber(modelMetrics.mae) }}</p>
                </div>
                <div style="background-color: #f9fafb; padding: 12px; border-radius: 8px; display: flex; align-items: center; white-space: nowrap; flex-shrink: 0;">
                  <p style="font-size: 14px; color: #4b5563; margin-right: 8px;">均方根误差 (RMSE):</p>
                  <p style="font-weight: 500;">{{ formatNumber(modelMetrics.rmse) }}</p>
                </div>
                <div style="background-color: #f9fafb; padding: 12px; border-radius: 8px; display: flex; align-items: center; white-space: nowrap; flex-shrink: 0;">
                  <p style="font-size: 14px; color: #4b5563; margin-right: 8px;">决定系数 (R²):</p>
                  <p style="font-weight: 500;">{{ formatNumber(modelMetrics.r2) }}</p>
                </div>
              </div>
            </div>

            <!-- 真实数据与预测数据比对 -->
            <div v-if="actualVsPredicted.hasData" class="actual-vs-predicted mb-6">
              <h4 class="font-semibold text-md mb-3">预测准确性评估</h4>
              <div class="chart-container mb-4 min-h-[300px]" ref="actualVsPredictedChart"></div>
              
              <div v-if="actualVsPredicted.metrics" class="accuracy-metrics mb-4">
                <div style="display: flex; gap: 16px; overflow-x: auto; padding-bottom: 8px;">
                  <div style="background-color: #f9fafb; padding: 12px 16px; border-radius: 6px; display: flex; align-items: center; white-space: nowrap; flex-shrink: 0;">
                    <p style="font-size: 14px; color: #4b5563; margin-right: 8px;">预测准确率:</p>
                    <p style="font-weight: 500;">{{ formatPercent(actualVsPredicted.metrics.accuracy) }}</p>
                  </div>
                  <div style="background-color: #f9fafb; padding: 12px 16px; border-radius: 6px; display: flex; align-items: center; white-space: nowrap; flex-shrink: 0;">
                    <p style="font-size: 14px; color: #4b5563; margin-right: 8px;">平均误差:</p>
                    <p style="font-weight: 500;">{{ formatNumber(actualVsPredicted.metrics.mean_error) }}</p>
                  </div>
                  <div style="background-color: #f9fafb; padding: 12px 16px; border-radius: 6px; display: flex; align-items: center; white-space: nowrap; flex-shrink: 0;">
                    <p style="font-size: 14px; color: #4b5563; margin-right: 8px;">最大误差:</p>
                    <p style="font-weight: 500;">{{ formatNumber(actualVsPredicted.metrics.max_error) }}</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- 多市场比较 (仅在按市场预测时显示) -->
            <div v-if="predictionResults && predictionResults.by_market" class="comparison-chart-container mb-6">
              <h4 class="font-semibold text-md mb-3">多市场预测比较</h4>
              <div class="chart-container min-h-[300px]" ref="marketComparisonChart"></div>
            </div>
          </template>

          <!-- 无数据时显示空白占位区域 -->
          <div v-else class="bg-[#f0f8f0] rounded-lg border border-gray-200 py-6 flex items-center justify-center p-6">
            <p class="text-gray-400 text-sm">暂无预测数据，请点击"开始预测"按钮生成数据</p>
          </div>
        </div>


      </div>

      <!-- 历史预测记录对话框 -->
      <div v-if="historyDialogVisible" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[80vh] overflow-y-auto">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-bold">历史预测记录</h3>
            <button @click="historyDialogVisible = false" class="text-gray-500 hover:text-gray-700">
              ×
            </button>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full border-collapse">
              <thead>
                <tr class="bg-gray-100">
                  <th class="border p-2 text-left">药材名称</th>
                  <th class="border p-2 text-left">规格</th>
                  <th class="border p-2 text-left">预测天数</th>
                  <th class="border p-2 text-left">创建时间</th>
                  <th class="border p-2 text-left">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in predictionHistory" :key="item.filename">
                  <td class="border p-2">{{ item.herb_name }}</td>
                  <td class="border p-2">{{ item.specification || '-' }}</td>
                  <td class="border p-2">{{ item.forecast_days }}</td>
                  <td class="border p-2">{{ item.created_at }}</td>
                  <td class="border p-2">
                    <button
                      @click="loadPredictionFile(item.filename)"
                      class="px-3 py-1 bg-herbal-green text-white rounded-md text-sm hover:bg-herbal-green/90"
                    >
                      加载
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 市场情绪分析 -->
      <div class="mt-10 bg-[#f0f8f0] rounded-xl card-shadow p-6 mb-6">
        <h2 class="text-2xl font-bold mb-6 text-gray-800 title1">相关市场情绪分析</h2>

        <!-- 分析表单 -->
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 24px; flex-wrap: nowrap; padding-left: 20px; padding-right: 20px;">
          <div style="display: flex; align-items: center; gap: 8px; flex-shrink: 0;">
            <span style="font-size: 14px; color: #4b5563; white-space: nowrap;">药材名称：</span>
            <select
              v-model="sentimentForm.herbName"
              style="padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; width: 150px;"
            >
              <option value="">药材名称</option>
              <option v-for="herb in herbs" :key="herb" :value="herb">
                {{ herb }}
              </option>
            </select>
          </div>
          <div style="display: flex; align-items: center; gap: 8px; flex-shrink: 0;">
            <span style="font-size: 14px; color: #4b5563; white-space: nowrap;">时间范围：</span>
            <select
              v-model="sentimentForm.timeRange"
              style="padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; width: 150px;"
            >
              <option v-for="option in timeRangeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
          <div style="flex-shrink: 0;">
            <button
              @click="analyzeSentiment"
              :disabled="sentimentLoading"
              style="padding: 8px 20px; background-color: #2d5d2b; color: white; border-radius: 6px; font-size: 14px; font-weight: 500; border: none; cursor: pointer;"
            >
              分析市场情绪
            </button>
          </div>
        </div>

        <!-- 显示选择的时间范围 -->
        <div v-if="sentimentAnalysisResult" class="mt-2 mb-6 text-center text-sm text-gray-600" style="padding-left: 20px; padding-right: 20px;">
          分析时间范围: {{ getTimeRangeLabel(sentimentForm.timeRange) }}
        </div>

        <!-- 情绪分析进度 -->
        <div v-if="sentimentLoading" class="py-6 flex flex-col items-center justify-center p-6">
          <div class="w-full bg-gray-200 rounded-full h-2.5 mb-4">
            <div class="bg-herbal-green h-2.5 rounded-full" style="width: 50%"></div>
          </div>
          <p class="text-sm text-gray-600 text-center">正在进行情绪分析，请稍候...</p>
        </div>

        <!-- 分析结果 -->
        <div v-else>
          <!-- 有数据时显示的内容 -->
          <template v-if="sentimentAnalysisResult">
            <div class="space-y-6">
              <!-- 热门关键词 -->
              <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 24px; margin-bottom: 24px; box-sizing: border-box; background-color: #f0f8f0;">
                <h3 style="font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1f2937;">热门关键词</h3>
                <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                  <span
                    v-for="(keyword, index) in sentimentAnalysisResult.sentiment_analysis.keywords"
                    :key="index"
                    :style="{ 
                      fontSize: getKeywordSize(keyword.weight) + 'px',
                      color: getKeywordColor(index),
                      border: '1px solid ' + getKeywordColor(index),
                      borderRadius: '12px',
                      padding: '2px 8px',
                      marginRight: '8px',
                      marginBottom: '8px'
                    }"
                  >
                    {{ keyword.word }}
                  </span>
                </div>
              </div>

              <!-- 情绪概览 -->
              <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 24px; margin-bottom: 24px; box-sizing: border-box; background-color: #f0f8f0;">
                <h3 style="font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1f2937;">情绪概览</h3>
                <div style="margin-bottom: 24px;">
                  <p style="font-size: 14px; color: #4b5563; margin-bottom: 8px;">平均情绪分数</p>
                  <p :class="getSentimentClass(sentimentAnalysisResult.sentiment_analysis.avg_sentiment)" style="font-size: 30px; line-height: 1;">
                    {{ formatSentiment(sentimentAnalysisResult.sentiment_analysis.avg_sentiment) }}
                  </p>
                </div>
                <div style="display: flex; flex-direction: column; gap: 16px;">
                  <div style="box-sizing: border-box;">
                    <div style="display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 4px;">
                      <span>积极</span>
                      <span>{{ sentimentAnalysisResult.sentiment_analysis.sentiment_counts.positive }}</span>
                    </div>
                    <div style="width: 100%; background-color: #e5e7eb; border-radius: 9999px; height: 10px; overflow: hidden;">
                      <div
                        style="background-color: #16a34a; height: 10px; border-radius: 9999px; transition: width 0.3s ease;"
                        :style="{ width: getSentimentPercentage('positive') + '%' }"
                      ></div>
                    </div>
                  </div>
                  <div style="box-sizing: border-box;">
                    <div style="display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 4px;">
                      <span>中性</span>
                      <span>{{ sentimentAnalysisResult.sentiment_analysis.sentiment_counts.neutral }}</span>
                    </div>
                    <div style="width: 100%; background-color: #e5e7eb; border-radius: 9999px; height: 10px; overflow: hidden;">
                      <div
                        style="background-color: #6b7280; height: 10px; border-radius: 9999px; transition: width 0.3s ease;"
                        :style="{ width: getSentimentPercentage('neutral') + '%' }"
                      ></div>
                    </div>
                  </div>
                  <div style="box-sizing: border-box;">
                    <div style="display: flex; justify-content: space-between; font-size: 14px; margin-bottom: 4px;">
                      <span>消极</span>
                      <span>{{ sentimentAnalysisResult.sentiment_analysis.sentiment_counts.negative }}</span>
                    </div>
                    <div style="width: 100%; background-color: #e5e7eb; border-radius: 9999px; height: 10px; overflow: hidden;">
                      <div
                        style="background-color: #dc2626; height: 10px; border-radius: 9999px; display: block;"
                        :style="{ width: getSentimentPercentage('negative') > 0 ? Math.max(2, getSentimentPercentage('negative')) + '%' : '0%' }"
                      ></div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 价格趋势预测 -->
              <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 24px; margin-bottom: 24px; box-sizing: border-box; background-color: #f0f8f0;">
                <h3 style="font-size: 18px; font-weight: 600; margin-bottom: 16px; color: #1f2937;">价格趋势预测</h3>
                <div style="display: flex; align-items: flex-start; gap: 12px; margin-bottom: 24px;">
                  <div style="font-size: 32px; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 4px;">
                    <span v-if="sentimentAnalysisResult.trend_prediction.trend === 'up'" style="color: #16a34a; line-height: 1;">↑</span>
                    <span v-else-if="sentimentAnalysisResult.trend_prediction.trend === 'down'" style="color: #dc2626; line-height: 1;">↓</span>
                    <span v-else style="color: #4b5563; line-height: 1;">→</span>
                  </div>
                  <div style="flex: 1; min-width: 0;">
                    <h4 style="font-size: 18px; font-weight: 500; margin-bottom: 4px; line-height: 1.4;">
                      {{ getTrendLabel(sentimentAnalysisResult.trend_prediction.trend) }}
                    </h4>
                    <p style="font-size: 14px; color: #4b5563; margin-bottom: 4px; line-height: 1.4;">
                      置信度: {{ (sentimentAnalysisResult.trend_prediction.confidence * 100).toFixed(0) }}%
                    </p>
                    <p style="color: #374151; font-size: 14px; line-height: 1.4;">
                      {{ sentimentAnalysisResult.trend_prediction.explanation }}
                    </p>
                  </div>
                </div>
                <!-- 情绪趋势图 -->
                <div style="border-top: 1px solid #e5e7eb; padding-top: 16px;">
                  <h4 style="font-size: 16px; font-weight: 500; margin-bottom: 12px; color: #374151;">情绪趋势分析</h4>
                  <div style="min-height: 500px; width: 100%;" ref="sentimentTrendChart"></div>
                </div>
              </div>
            </div>
          </template>

          <!-- 无数据时显示空白占位区域 -->
          <div v-else class="bg-[#f0f8f0] rounded-lg border border-gray-200 py-6 flex items-center justify-center p-6">
            <p class="text-gray-400 text-sm">暂无分析数据，请点击"分析市场情绪"按钮生成数据</p>
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
import { ref, reactive, onMounted, onUnmounted, nextTick, computed } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import AppSidebar from '@/components/AppSidebar.vue'
import {ElMessage } from 'element-plus'

defineOptions({ name: 'MarketAnalysisPage' })

// 类型定义
interface ModelMetrics {
  mae: number
  rmse: number
  r2: number
}

interface PredictionHistoryItem {
  filename: string
  herb_name: string
  specification: string
  forecast_days: number
  created_at: string
}

// 情绪分析相关类型定义
interface SentimentCounts {
  positive: number
  negative: number
  neutral: number
}

interface SentimentAnalysis {
  avg_sentiment: number
  sentiment_counts: SentimentCounts
  keywords: Array<{word: string, weight: number}>
  sentiment_trend: {
    dates: string[]
    scores: number[]
  }
}

interface TrendPrediction {
  trend: 'up' | 'down' | 'stable'
  confidence: number
  explanation: string
}

interface SentimentAnalysisResult {
  success: boolean
  herb_name: string
  date_range: {
    start_date: string
    end_date: string
  }
  news_count: number
  sentiment_analysis: SentimentAnalysis
  trend_prediction: TrendPrediction
}

// 设置API基础URL（使用相对路径以利用Vite代理）
const API_BASE_URL = ''

// 图表引用和实例
const pricePredictionChart = ref<HTMLElement | null>(null)
const actualVsPredictedChart = ref<HTMLElement | null>(null)
const marketComparisonChart = ref<HTMLElement | null>(null)
const sentimentTrendChart = ref<HTMLElement | null>(null)
let pricePredictionChartInstance: echarts.ECharts | null = null
let actualVsPredictedChartInstance: echarts.ECharts | null = null
let marketComparisonChartInstance: echarts.ECharts | null = null
let sentimentTrendChartInstance: echarts.ECharts | null = null

// 类型定义
interface ActualMarketData {
  dates: string[]
  prices: number[]
}

interface MarketMetrics {
  accuracy: number
  mean_error: number
  max_error: number
  comparisons: number
}

interface ActualVsPredictedMetrics {
  accuracy: number
  mean_error: number
  max_error: number
  comparisons: number
  markets: Record<string, MarketMetrics>
}

interface ActualVsPredictedState {
  hasData: boolean
  data: Record<string, ActualMarketData> | null
  metrics: ActualVsPredictedMetrics | null
}

interface MarketPrediction {
  predictions: Record<string, {
    forecast: {
      date: string[]
      predicted_price: number[]
      lower_bound?: number[]
      upper_bound?: number[]
    }
    metrics?: ModelMetrics
  }>
  historical_data: {
    date: string[]
    price: number[]
  }
}

interface PredictionResults {
  herb_name: string
  specification?: string
  forecast_days: number
  by_market: boolean
  predictions: Record<string, {
    forecast: {
      date: string[]
      predicted_price: number[]
      lower_bound?: number[]
      upper_bound?: number[]
    }
    metrics?: ModelMetrics
  }>
  historical_data: {
    date: string[]
    price: number[]
  }
  market_predictions?: Record<string, MarketPrediction>
}

interface SeriesData {
  name: string
  type: 'line'
  smooth?: boolean
  symbol?: string
  symbolSize?: number
  lineStyle?: {
    width: number
    type?: 'solid' | 'dashed' | 'dotted'
  }
  itemStyle?: {
    color: string
  }
  data: Array<[string, number | null]>
}

// 数据状态
const herbs = ref<string[]>([])
const specifications = ref<string[]>([])
const loading = ref(false)
const predictionProgress = ref(0)
const predictionResults = ref<PredictionResults | null>(null)
const historyDialogVisible = ref(false)
const predictionHistory = ref<PredictionHistoryItem[]>([])
const selectedModel = ref('Ensemble')
const selectedMarket = ref('')
const modelMetrics = ref<ModelMetrics | null>(null)
const availableModels = ref<string[]>([])
const availableMarkets = ref<string[]>([])
const actualVsPredicted = reactive<ActualVsPredictedState>({
  hasData: false,
  data: null,
  metrics: null
})

// 情绪分析相关状态
const sentimentForm = reactive({
  herbName: '丹参',
  timeRange: '30d'
})
const timeRangeOptions = ref([
  { value: '7d', label: '近7天' },
  { value: '30d', label: '近30天' },
  { value: '90d', label: '近90天' },
  { value: '180d', label: '近半年' }
])
const sentimentLoading = ref(false)
const sentimentAnalysisResult = ref<SentimentAnalysisResult | null>(null)

// 预测表单
const predictionForm = reactive({
  herbName: '丹参',
  specification: '三级',
  forecastDays: 30,
  startDate: '2026-02-01',
  endDate: '2026-03-01'
})

// 计算当前使用的预测结果
const currentPredictions = computed(() => {
  if (!predictionResults.value) return null
  
  if (predictionResults.value.by_market) {
    if (!selectedMarket.value || !predictionResults.value.market_predictions || !predictionResults.value.market_predictions[selectedMarket.value]) return null
    return predictionResults.value.market_predictions[selectedMarket.value].predictions
  } else {
    return predictionResults.value.predictions
  }
})

// 计算当前使用的历史数据
const currentHistoricalData = computed(() => {
  if (!predictionResults.value) return null
  
  if (predictionResults.value.by_market) {
    if (!selectedMarket.value || !predictionResults.value.market_predictions || !predictionResults.value.market_predictions[selectedMarket.value]) return null
    return predictionResults.value.market_predictions[selectedMarket.value].historical_data
  } else {
    return predictionResults.value.historical_data
  }
})

// 模型名称映射
const modelNames = {
  'ARIMA': 'ARIMA模型',
  'Prophet': 'Prophet模型',
  'LSTM': 'LSTM神经网络',
  'XGBoost': 'XGBoost模型',
  'Ensemble': '集成模型'
}

// 获取模型名称
const getModelName = (modelId: string): string => {
  return modelNames[modelId as keyof typeof modelNames] || modelId
}

// 格式化数字
const formatNumber = (value: number | undefined | null): string => {
  if (value === undefined || value === null) return 'N/A'
  return value.toFixed(4)
}

// 格式化百分比
const formatPercent = (value: number | undefined | null): string => {
  if (value === undefined || value === null) return 'N/A'
  return (parseFloat(value.toString()) * 100).toFixed(2) + '%'
}

// 市场变更处理
const handleMarketChange = () => {
  // 更新可用模型列表
  if (predictionResults.value && predictionResults.value.by_market && selectedMarket.value && predictionResults.value.market_predictions) {
    const marketData = predictionResults.value.market_predictions[selectedMarket.value]
    if (marketData) {
      availableModels.value = Object.keys(marketData.predictions)
      
      // 默认选择集成模型，如果有的话
      if (availableModels.value.includes('Ensemble')) {
        selectedModel.value = 'Ensemble'
      } else if (availableModels.value.length > 0) {
        selectedModel.value = availableModels.value[0]
      }
      
      // 更新模型评估指标
      updateModelMetrics()
      
      // 更新图表
      updateChartData()
      
      // 获取真实数据与预测数据比对
      fetchActualVsPredicted()
    }
  }
}

// 获取药材列表
// 获取药材列表
const fetchHerbs = async () => {
  try {
    console.log('Fetching herbs from:', API_BASE_URL) // 添加日志
    const response = await axios.get(`${API_BASE_URL}/api/herbs`)
    console.log('Herbs response:', response.data) // 查看返回数据
    herbs.value = response.data
  } catch (error) {
    console.error('获取药材列表失败:', error) // 详细错误信息
    ElMessage({
      message: '获取药材列表失败: ' + (error instanceof Error ? error.message : '未知错误'),
      type: 'error',
      offset: 80,
      duration: 3000
    })
  }
}

// 药材变更处理
const handleHerbChange = async () => {
  predictionForm.specification = ''
  specifications.value = []

  if (!predictionForm.herbName) return

  try {
    const response = await axios.get(`${API_BASE_URL}/api/specifications`, {
      params: { herb_name: predictionForm.herbName }
    })
    specifications.value = response.data
  } catch (error) {
    console.error('获取规格列表失败:', error)
    ElMessage({
      message: '获取规格列表失败',
      type: 'error',
      offset: 80,
      duration: 3000
    })
  }
}

// 增加预测天数
const increaseForecastDays = () => {
  if (predictionForm.forecastDays < 90) {
    predictionForm.forecastDays += 7
  }
}

// 减少预测天数
const decreaseForecastDays = () => {
  if (predictionForm.forecastDays > 7) {
    predictionForm.forecastDays -= 7
  }
}

// 重置预测表单
const resetPredictionForm = () => {
  predictionForm.herbName = ''
  predictionForm.specification = ''
  predictionForm.forecastDays = 30
  predictionForm.startDate = ''
  predictionForm.endDate = ''
  specifications.value = []
}

// 情绪分析相关方法
const analyzeSentiment = async () => {
  if (!sentimentForm.herbName) {
    ElMessage({
      message: '请选择药材名称',
      type: 'warning',
      offset: 80,
      duration: 3000
    })
    return
  }

  sentimentLoading.value = true

  try {
    // 计算日期范围
    const endDate = new Date()
    const startDate = new Date()

    switch (sentimentForm.timeRange) {
      case '7d':
        startDate.setDate(endDate.getDate() - 7)
        break
      case '30d':
        startDate.setDate(endDate.getDate() - 30)
        break
      case '90d':
        startDate.setDate(endDate.getDate() - 90)
        break
      case '180d':
        startDate.setDate(endDate.getDate() - 180)
        break
    }

    const response = await axios.get(`${API_BASE_URL}/api/sentiment-analysis`, {
      params: {
        herb_name: sentimentForm.herbName,
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0]
      }
    })

    sentimentAnalysisResult.value = response.data

    // 初始化情绪趋势图表
    nextTick(() => {
      initSentimentTrendChart()
    })
  } catch (error) {
    console.error('情绪分析失败:', error)
    ElMessage({
      message: '情绪分析失败: ' + (error instanceof Error ? error.message : '未知错误'),
      type: 'error',
      offset: 80,
      duration: 3000
    })
  } finally {
    sentimentLoading.value = false
  }
}





// 初始化情绪趋势图表
const initSentimentTrendChart = () => {
  if (!sentimentAnalysisResult.value || !sentimentTrendChart.value) return
  
  sentimentTrendChartInstance = echarts.init(sentimentTrendChart.value)
  
  const { dates, scores } = sentimentAnalysisResult.value.sentiment_analysis.sentiment_trend
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value',
      min: -1,
      max: 1,
      interval: 0.2
    },
    series: [
      {
        data: scores,
        type: 'line',
        smooth: true,
        lineStyle: {
          width: 3
        },
        itemStyle: {
          color: function(params: any) {
            const value = params.value
            if (value > 0.1) return '#67C23A'
            if (value < -0.1) return '#F56C6C'
            return '#909399'
          }
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            {
              offset: 0,
              color: 'rgba(103, 194, 58, 0.5)'
            },
            {
              offset: 0.5,
              color: 'rgba(144, 147, 153, 0.3)'
            },
            {
              offset: 1,
              color: 'rgba(245, 108, 108, 0.5)'
            }
          ])
        }
      }
    ]
  }
  
  sentimentTrendChartInstance.setOption(option)
  
  // 强制图表重新计算大小并渲染
  nextTick(() => {
    if (sentimentTrendChartInstance) {
      sentimentTrendChartInstance.resize()
    }
  })
  
  // 再次调用resize确保图表完全适应容器
  setTimeout(() => {
    if (sentimentTrendChartInstance) {
      sentimentTrendChartInstance.resize()
    }
  }, 100)
}



// 获取时间范围标签
const getTimeRangeLabel = (timeRange: string): string => {
  const option = timeRangeOptions.value.find(opt => opt.value === timeRange)
  return option ? option.label : timeRange
}

// 获取情绪类名
const getSentimentClass = (sentiment: number): string => {
  if (sentiment > 0.1) {
    return 'text-green-600 font-bold'
  } else if (sentiment < -0.1) {
    return 'text-red-600 font-bold'
  } else {
    return 'text-gray-600 font-bold'
  }
}

// 格式化情绪分数
const formatSentiment = (sentiment: number): string => {
  return sentiment.toFixed(2)
}

// 获取情绪百分比
const getSentimentPercentage = (type: 'positive' | 'negative' | 'neutral'): number => {
  if (!sentimentAnalysisResult.value) return 0

  const counts = sentimentAnalysisResult.value.sentiment_analysis.sentiment_counts
  const total = counts.positive + counts.negative + counts.neutral

  if (total === 0) return 0

  switch (type) {
    case 'positive':
      return (counts.positive / total) * 100
    case 'negative':
      return (counts.negative / total) * 100
    case 'neutral':
      return (counts.neutral / total) * 100
    default:
      return 0
  }
}

// 获取趋势标签
const getTrendLabel = (trend: string): string => {
  switch (trend) {
    case 'up':
      return '价格看涨'
    case 'down':
      return '价格看跌'
    case 'stable':
      return '价格稳定'
    default:
      return '趋势不明'
  }
}

// 获取关键词标签类型
// const getKeywordTagType = (index: number): string => {
//   const types = [
//     'bg-blue-100 text-blue-800',
//     'bg-green-100 text-green-800',
//     'bg-yellow-100 text-yellow-800',
//     'bg-purple-100 text-purple-800',
//     'bg-red-100 text-red-800'
//   ]
//   return types[index % types.length]
// }

// 获取关键词大小
const getKeywordSize = (weight: number): number => {
  // 根据权重计算字体大小，范围12-20px
  return Math.max(12, Math.min(20, 12 + weight * 8))
}

// 获取关键词颜色
const getKeywordColor = (index: number): string => {
  const colors = [
    '#3b82f6', // 蓝色
    '#10b981', // 绿色
    '#f59e0b', // 黄色
    '#8b5cf6', // 紫色
    '#ef4444', // 红色
    '#06b6d4', // 青色
    '#84cc16', // 浅绿色
    '#f97316', // 橙色
    '#a855f7', // 淡紫色
    '#ec4899'  // 粉色
  ]
  return colors[index % colors.length]
}

// 显示历史预测记录
const showPredictionHistory = async () => {
  try {
    historyDialogVisible.value = true
    const response = await axios.get(`${API_BASE_URL}/api/prediction-history`)
    predictionHistory.value = response.data
  } catch (error) {
    console.error('获取预测历史失败:', error)
    ElMessage({
      message: '获取预测历史失败',
      type: 'error',
      offset: 80,
      duration: 3000
    })
  }
}

// 加载预测文件
const loadPredictionFile = async (filename: string) => {
  try {
    loading.value = true
    const response = await axios.get(`${API_BASE_URL}/api/prediction-result/${filename}`)
    predictionResults.value = response.data
    
    // 处理按市场预测的结果
    if (predictionResults.value && predictionResults.value.by_market) {
      // 获取所有可用市场
      availableMarkets.value = Object.keys(predictionResults.value.market_predictions || {})
      
      // 默认选择第一个市场
      if (availableMarkets.value.length > 0) {
        selectedMarket.value = availableMarkets.value[0]
        
        // 设置当前市场的可用模型
        if (predictionResults.value.market_predictions) {
          const marketData = predictionResults.value.market_predictions[selectedMarket.value]
          if (marketData && marketData.predictions) {
            availableModels.value = Object.keys(marketData.predictions)
            
            // 默认选择集成模型，如果有的话
            if (availableModels.value.includes('Ensemble')) {
              selectedModel.value = 'Ensemble'
            } else if (availableModels.value.length > 0) {
              selectedModel.value = availableModels.value[0]
            }
          }
        }
      }
      
      // 确保DOM已更新
      await nextTick()
      
      // 延迟一点时间再绘制图表，确保DOM已完全渲染
      setTimeout(() => {
        drawMarketComparisonChart()
      }, 300)
    } else {
      // 设置可用模型
      if (predictionResults.value && predictionResults.value.predictions) {
        availableModels.value = Object.keys(predictionResults.value.predictions)
        
        // 默认选择集成模型，如果有的话
          if (availableModels.value.includes('Ensemble')) {
            selectedModel.value = 'Ensemble'
          } else if (availableModels.value.length > 0) {
            selectedModel.value = availableModels.value[0]
          }
      }
    }
    
    // 更新图表数据
    await nextTick()
    setTimeout(() => {
      updateChartData()
    }, 300)
    
    // 更新表单数据，与加载的预测结果保持一致
    if (predictionResults.value) {
      predictionForm.herbName = predictionResults.value.herb_name
      predictionForm.specification = predictionResults.value.specification || ''
      predictionForm.forecastDays = predictionResults.value.forecast_days
    }
    
    historyDialogVisible.value = false
    ElMessage({
      message: '预测结果加载成功',
      type: 'success',
      offset: 80,
      duration: 3000
    })
  } catch (error) {
    console.error('加载预测结果失败:', error)
    ElMessage({
      message: '加载预测结果失败',
      type: 'error',
      offset: 80,
      duration: 3000
    })
  } finally {
    loading.value = false
  }
}

// 执行预测
const runPrediction = async () => {
  if (!predictionForm.herbName) {
    ElMessage({
      message: '请选择药材名称',
      type: 'warning',
      offset: 80,
      duration: 3000
    })
    return
  }

  loading.value = true
  predictionProgress.value = 0

  // 模拟进度
  const progressInterval = setInterval(() => {
    if (predictionProgress.value < 90) {
      predictionProgress.value += 5
    }
  }, 1000)

  try {
    const params = {
      herb_name: predictionForm.herbName,
      specification: predictionForm.specification || null,
      forecast_days: predictionForm.forecastDays,
      start_date: predictionForm.startDate || null,
      end_date: predictionForm.endDate || null
    }

    const response = await axios.post(`${API_BASE_URL}/api/price-prediction`, params)
    predictionResults.value = response.data
    
    // 打印后端返回的预测数据
    console.log('Backend prediction results:', response.data)

    // 处理按市场预测的结果
    if (predictionResults.value && predictionResults.value.by_market) {
      // 获取所有可用市场
      availableMarkets.value = Object.keys(predictionResults.value.market_predictions || {})
      
      // 默认选择第一个市场
      if (availableMarkets.value.length > 0) {
        selectedMarket.value = availableMarkets.value[0]
        
        // 设置当前市场的可用模型
        if (predictionResults.value.market_predictions) {
          const marketData = predictionResults.value.market_predictions[selectedMarket.value]
          if (marketData && marketData.predictions) {
            availableModels.value = Object.keys(marketData.predictions)
            
            // 默认选择集成模型，如果有的话
            if (availableModels.value.includes('Ensemble')) {
              selectedModel.value = 'Ensemble'
            } else if (availableModels.value.length > 0) {
              selectedModel.value = availableModels.value[0]
            }
          }
        }
      }
      
      // 绘制多市场比较图表
      await nextTick()
      drawMarketComparisonChart()
    } else {
      // 设置可用模型
      if (predictionResults.value && predictionResults.value.predictions) {
        availableModels.value = Object.keys(predictionResults.value.predictions)
        
        // 默认选择集成模型，如果有的话
          if (availableModels.value.includes('Ensemble')) {
            selectedModel.value = 'Ensemble'
          } else if (availableModels.value.length > 0) {
            selectedModel.value = availableModels.value[0]
          }
      }
    }
    
    // 更新图表数据
    await nextTick()
    setTimeout(() => {
      updateChartData()
    }, 300)

    predictionProgress.value = 100
    ElMessage({
      message: '预测完成',
      type: 'success',
      offset: 80,
      duration: 3000
    })
  } catch (error) {
    console.error('预测失败:', error)
    ElMessage({
      message: '预测失败: ' + (error instanceof Error ? error.message : '未知错误'),
      type: 'error',
      offset: 80,
      duration: 3000
    })
  } finally {
    clearInterval(progressInterval)
    loading.value = false
  }
}

// 更新模型评估指标
const updateModelMetrics = () => {
  const predictions = currentPredictions.value
  if (!predictions || !selectedModel.value) {
    modelMetrics.value = null
    return
  }

  const modelData = predictions[selectedModel.value]
  if (modelData && modelData.metrics) {
    modelMetrics.value = modelData.metrics
  } else {
    modelMetrics.value = null
  }
}

// 更新图表数据
const updateChartData = async () => {
  if (!predictionResults.value) return

  // 获取当前使用的预测数据
  const predictions = currentPredictions.value
  const historicalData = currentHistoricalData.value

  if (!predictions || !historicalData || !selectedModel.value) return

  const modelData = predictions[selectedModel.value]
  if (!modelData) return

  // 打印当前选择的模型和对应的预测数据
  console.log('Selected model:', selectedModel.value)
  console.log('Prediction prices:', modelData.forecast.predicted_price)

  // 打印所有模型的预测数据
  console.log('All models predictions:')
  for (const model in predictions) {
    console.log(`${model}:`, predictions[model].forecast.predicted_price)
  }

  // 更新评估指标
  updateModelMetrics()

  // 绘制预测图表
  await nextTick()
  drawPredictionChart(historicalData, modelData)
  
  // 获取真实数据与预测数据比对
  fetchActualVsPredicted()
}

// 获取真实数据与预测数据比对
const fetchActualVsPredicted = async () => {
  if (!predictionResults.value) return
  
  try {
    // 打印调试信息
    console.log('开始获取真实数据与预测数据比对')
    
    // 获取预测的第一个日期
    let firstPredictionDate
    
    if (predictionResults.value.by_market) {
      if (!selectedMarket.value || !predictionResults.value.market_predictions) {
        console.log('缺少市场数据')
        return
      }
      
      const marketData = predictionResults.value.market_predictions[selectedMarket.value]
      if (!marketData || !marketData.predictions || !marketData.predictions[selectedModel.value]) {
        console.log('缺少市场预测数据')
        return
      }
      
      const modelData = marketData.predictions[selectedModel.value]
      if (!modelData || !modelData.forecast || !modelData.forecast.date || modelData.forecast.date.length === 0) {
        console.log('缺少模型预测日期数据')
        return
      }
      
      firstPredictionDate = modelData.forecast.date[0]
    } else {
      if (!predictionResults.value.predictions || !predictionResults.value.predictions[selectedModel.value]) {
        console.log('缺少预测数据')
        return
      }
      
      const modelData = predictionResults.value.predictions[selectedModel.value]
      if (!modelData || !modelData.forecast || !modelData.forecast.date || modelData.forecast.date.length === 0) {
        console.log('缺少模型预测日期数据')
        return
      }
      
      firstPredictionDate = modelData.forecast.date[0]
    }
    
    console.log('第一个预测日期:', firstPredictionDate)
    
    // 查询从预测开始日期的实际价格数据
    const params: {
      herb_name: string
      prediction_date: string
      specification?: string
    } = {
      herb_name: predictionResults.value.herb_name,
      prediction_date: firstPredictionDate
    }
    
    if (predictionResults.value.specification) {
      params.specification = predictionResults.value.specification
    }
    
    console.log('请求参数:', params)
    
    const response = await axios.get(`${API_BASE_URL}/api/actual-vs-predicted`, { params })
    
    console.log('API响应:', response.data)
    
    if (response.data && response.data.success && response.data.actual_data && Object.keys(response.data.actual_data).length > 0) {
      console.log('获取到真实数据')
      actualVsPredicted.data = response.data.actual_data
      actualVsPredicted.hasData = true
      
      // 计算预测准确性指标
      calculatePredictionAccuracy()
      
      // 绘制真实数据与预测数据比对图表
      await nextTick()
      drawActualVsPredictedChart()
    } else {
      console.log('没有获取到真实数据')
      actualVsPredicted.hasData = false
      actualVsPredicted.data = null
      actualVsPredicted.metrics = null
    }
  } catch (error) {
    console.error('获取真实数据与预测数据比对失败:', error)
    actualVsPredicted.hasData = false
    actualVsPredicted.data = null
    actualVsPredicted.metrics = null
  }
}

// 计算预测准确性指标
const calculatePredictionAccuracy = () => {
  if (!actualVsPredicted.data || !predictionResults.value) return
  
  // 获取预测数据
  let predictionData: {
    dates: string[]
    prices: number[]
  }
  
  if (predictionResults.value.by_market) {
    if (!selectedMarket.value || !predictionResults.value.market_predictions) return
    
    const marketData = predictionResults.value.market_predictions[selectedMarket.value]
    if (!marketData || !marketData.predictions[selectedModel.value]) return
    
    predictionData = {
      dates: marketData.predictions[selectedModel.value].forecast.date,
      prices: marketData.predictions[selectedModel.value].forecast.predicted_price
    }
  } else {
    if (!predictionResults.value.predictions[selectedModel.value]) return
    
    predictionData = {
      dates: predictionResults.value.predictions[selectedModel.value].forecast.date,
      prices: predictionResults.value.predictions[selectedModel.value].forecast.predicted_price
    }
  }
  
  // 计算各市场的预测准确性
  const marketMetrics: Record<string, MarketMetrics> = {}
  const totalErrors: number[] = []
  let totalComparisons = 0
  
  for (const market in actualVsPredicted.data) {
    const actualMarketData = actualVsPredicted.data[market]
    const marketErrors = []
    
    // 对每个日期进行比较
    for (let i = 0; i < actualMarketData.dates.length; i++) {
      const actualDate = actualMarketData.dates[i]
      const actualPrice = actualMarketData.prices[i]
      
      // 在预测数据中查找对应日期
      const predIndex = predictionData.dates.indexOf(actualDate)
      
      if (predIndex !== -1) {
        const predPrice = predictionData.prices[predIndex]
        const error = Math.abs(predPrice - actualPrice)
        const relativeError = error / actualPrice
        
        marketErrors.push(relativeError)
        totalErrors.push(relativeError)
        totalComparisons++
      }
    }
    
    // 计算市场指标
    if (marketErrors.length > 0) {
      const meanError = marketErrors.reduce((sum, err) => sum + err, 0) / marketErrors.length
      const maxError = Math.max(...marketErrors)
      const accuracy = 1 - meanError
      
      marketMetrics[market] = {
        accuracy,
        mean_error: meanError,
        max_error: maxError,
        comparisons: marketErrors.length
      }
    }
  }
  
  // 计算总体指标
  if (totalErrors.length > 0) {
    const meanError = totalErrors.reduce((sum, err) => sum + err, 0) / totalErrors.length
    const maxError = Math.max(...totalErrors)
    const accuracy = 1 - meanError
    
    actualVsPredicted.metrics = {
      accuracy,
      mean_error: meanError,
      max_error: maxError,
      comparisons: totalComparisons,
      markets: marketMetrics
    }
  } else {
    actualVsPredicted.metrics = null
  }
}

// 绘制预测图表
const drawPredictionChart = (historicalData: {
  date: string[]
  price: number[]
}, modelData: {
  forecast: {
    date: string[]
    predicted_price: number[]
    lower_bound?: number[]
    upper_bound?: number[]
  }
}) => {
  if (!pricePredictionChart.value || !predictionResults.value) return

  if (pricePredictionChartInstance) {
    pricePredictionChartInstance.dispose()
  }

  pricePredictionChartInstance = echarts.init(pricePredictionChart.value)

  // 准备数据
  const dates = historicalData.date
  const prices = historicalData.price
  const predictionDates = modelData.forecast.date
  const predictionPrices = modelData.forecast.predicted_price

  // 设置图表标题
  let title = `${predictionResults.value.herb_name}`
  if (predictionResults.value.specification) {
    title += ` (${predictionResults.value.specification})`
  }
  if (predictionResults.value.by_market && selectedMarket.value) {
    title += ` - ${selectedMarket.value}市场`
  }
  title += ' 价格预测'

  // 构建系列数据
  const seriesData: echarts.SeriesOption[] = [
    {
      name: '历史价格',
      type: 'line' as const,
      data: [...prices, ...Array(predictionDates.length).fill(null)],
      smooth: true,
      symbol: 'circle' as const,
      symbolSize: 5,
      lineStyle: {
        width: 2
      }
    },
    {
      name: '预测价格',
      type: 'line' as const,
      data: [...Array(dates.length).fill(null), ...predictionPrices],
      smooth: true,
      symbol: 'circle' as const,
      symbolSize: 5,
      lineStyle: {
        width: 2,
        type: 'dashed' as const
      },
      itemStyle: {
        color: '#91cc75'
      }
    }
  ]

  // 如果是Prophet模型，添加置信区间
  if (selectedModel.value === 'Prophet' && modelData.forecast.lower_bound && modelData.forecast.upper_bound) {
    seriesData.push(
      {
        name: '置信区间',
        type: 'line' as const,
        data: [...Array(dates.length).fill(null), ...modelData.forecast.upper_bound],
        lineStyle: {
          width: 0
        },
        symbol: 'none' as const
      },
      {
        name: '置信区间',
        type: 'line' as const,
        data: [...Array(dates.length).fill(null), ...modelData.forecast.lower_bound],
        lineStyle: {
          width: 0
        },
        areaStyle: {
          color: '#91cc75',
          opacity: 0.2
        },
        symbol: 'none' as const
      }
    )
  }

  // 如果有真实数据，添加到图表中
  if (actualVsPredicted.hasData) {
    // 合并所有市场的真实数据
    const allActualDates: string[] = []
    const allActualPrices: number[] = []
    
    for (const market in actualVsPredicted.data) {
      const marketData = actualVsPredicted.data[market]
      
      for (let i = 0; i < marketData.dates.length; i++) {
        const date = marketData.dates[i]
        const price = marketData.prices[i]
        
        // 只添加预测日期范围内的数据
        if (predictionDates.includes(date)) {
          const index = allActualDates.indexOf(date)
          
          if (index === -1) {
            allActualDates.push(date)
            allActualPrices.push(price)
          } else {
            // 如果日期已存在，取平均值
            allActualPrices[index] = (allActualPrices[index] + price) / 2
          }
        }
      }
    }
    
    // 按日期排序
    const sortedIndices = allActualDates.map((date, index) => ({ date, index }))
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .map(item => item.index)
    
    const sortedDates = sortedIndices.map(i => allActualDates[i])
    const sortedPrices = sortedIndices.map(i => allActualPrices[i])
    
    // 创建真实价格数据系列
    const actualSeries = {
      name: '真实价格',
      type: 'line' as const,
      data: Array(dates.length + predictionDates.length).fill(null),
      smooth: true,
      symbol: 'diamond' as const,
      symbolSize: 8,
      lineStyle: {
        width: 2
      },
      itemStyle: {
        color: '#ee6666'
      }
    }
    
    // 填充真实价格数据
    for (let i = 0; i < sortedDates.length; i++) {
      const date = sortedDates[i]
      const price = sortedPrices[i]
      
      const dateIndex = [...dates, ...predictionDates].indexOf(date)
      if (dateIndex !== -1) {
        actualSeries.data[dateIndex] = price
      }
    }
    
    seriesData.push(actualSeries)
  }

  // 设置图表选项
  const option: echarts.EChartsOption = {
    title: {
      text: title,
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params: unknown) {
        const typedParams = params as Array<{
          axisValue: string | number
          seriesName: string
          value: [string | number, number | null | undefined]
        }>
        const date = typedParams[0].axisValue
        let result = `${date}<br/>`

        typedParams.forEach((param) => {
          if (param.value && param.value[1] !== null && param.value[1] !== undefined) {
            result += `${param.seriesName}: ${param.value[1].toFixed(2)} 元/kg<br/>`
          }
        })

        return result
      }
    },
    legend: {
      data: ['历史价格', '预测价格', '真实价格'],
      bottom: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category' as const,
      boundaryGap: false,
      data: [...dates, ...predictionDates],
      axisLabel: {
        rotate: 45,
        interval: Math.floor((dates.length + predictionDates.length) / 15)
      }
    },
    yAxis: {
      type: 'value' as const,
      name: '价格 (元/kg)',
      axisLabel: {
        formatter: '{value} 元'
      }
    },
    series: seriesData
  }

  pricePredictionChartInstance.setOption(option)

  // 添加窗口大小变化时的自适应
  window.addEventListener('resize', () => {
    pricePredictionChartInstance?.resize()
  })
}

// 绘制真实数据与预测数据比对图表
const drawActualVsPredictedChart = () => {
  if (!actualVsPredictedChart.value || !actualVsPredicted.hasData || !predictionResults.value) return
  
  if (actualVsPredictedChartInstance) {
    actualVsPredictedChartInstance.dispose()
  }
  
  actualVsPredictedChartInstance = echarts.init(actualVsPredictedChart.value)
  
  // 获取预测数据
  let predictionData: {
    dates: string[]
    prices: number[]
  }
  
  if (predictionResults.value.by_market) {
    if (!selectedMarket.value || !predictionResults.value.market_predictions) return
    
    const marketData = predictionResults.value.market_predictions[selectedMarket.value]
    if (!marketData || !marketData.predictions[selectedModel.value]) return
    
    predictionData = {
      dates: marketData.predictions[selectedModel.value].forecast.date,
      prices: marketData.predictions[selectedModel.value].forecast.predicted_price
    }
  } else {
    if (!predictionResults.value.predictions[selectedModel.value]) return
    
    predictionData = {
      dates: predictionResults.value.predictions[selectedModel.value].forecast.date,
      prices: predictionResults.value.predictions[selectedModel.value].forecast.predicted_price
    }
  }
  
  // 准备数据
  const series: SeriesData[] = []
  const allDates: string[] = []
  
  // 添加预测数据系列
  series.push({
    name: '预测价格',
    type: 'line' as const,
    smooth: true,
    symbol: 'circle' as const,
    symbolSize: 6,
    lineStyle: {
      width: 2,
      type: 'dashed' as const
    },
    itemStyle: {
      color: '#91cc75'
    },
    data: []
  })
  
  // 添加各市场的真实数据系列
  const marketColors = ['#ee6666', '#5470c6', '#fac858', '#73c0de', '#3ba272', '#fc8452', '#9a60b4']
  let colorIndex = 0
  
  for (const market in actualVsPredicted.data) {
    series.push({
      name: `${market}真实价格`,
      type: 'line' as const,
      smooth: true,
      symbol: 'diamond' as const,
      symbolSize: 8,
      lineStyle: {
        width: 2
      },
      itemStyle: {
        color: marketColors[colorIndex % marketColors.length]
      },
      data: []
    })
    
    colorIndex++
  }
  
  // 收集所有日期
  for (const date of predictionData.dates) {
    if (!allDates.includes(date)) {
      allDates.push(date)
    }
  }
  
  for (const market in actualVsPredicted.data) {
    for (const date of actualVsPredicted.data[market].dates) {
      if (!allDates.includes(date)) {
        allDates.push(date)
      }
    }
  }
  
  // 按日期排序
  allDates.sort((a, b) => new Date(a).getTime() - new Date(b).getTime())
  
  // 填充数据
  for (const date of allDates) {
    // 预测数据
    const predIndex = predictionData.dates.indexOf(date)
    if (predIndex !== -1) {
      series[0].data.push([date, predictionData.prices[predIndex]])
    } else {
      series[0].data.push([date, null])
    }
    
    // 各市场真实数据
    let marketIndex = 1
    for (const market in actualVsPredicted.data) {
      const marketData = actualVsPredicted.data[market]
      const dateIndex = marketData.dates.indexOf(date)
      
      if (dateIndex !== -1) {
        series[marketIndex].data.push([date, marketData.prices[dateIndex]])
      } else {
        series[marketIndex].data.push([date, null])
      }
      
      marketIndex++
    }
  }
  
  // 设置图表选项
  const option: echarts.EChartsOption = {
    title: {
      text: '预测价格与真实价格比对',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params: unknown) {
        const typedParams = params as Array<{
          axisValue: string | number
          seriesName: string
          value: [string | number, number | null | undefined]
        }>
        const date = typedParams[0].axisValue
        let result = `${date}<br/>`
        
        typedParams.forEach((param) => {
          if (param.value && param.value[1] !== null && param.value[1] !== undefined) {
            result += `${param.seriesName}: ${param.value[1].toFixed(2)} 元/kg<br/>`
          }
        })
        
        return result
      }
    },
    legend: {
      data: series.map(s => s.name).filter(Boolean) as string[],
      bottom: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'time',
      boundaryGap: ['5%', '5%'],
      axisLabel: {
        formatter: '{yyyy}-{MM}-{dd}',
        rotate: 45
      }
    },
    yAxis: {
      type: 'value' as const,
      name: '价格 (元/kg)',
      axisLabel: {
        formatter: '{value} 元'
      }
    },
    series: series
  }
  
  actualVsPredictedChartInstance.setOption(option)
  
  // 添加窗口大小变化时的自适应
  window.addEventListener('resize', () => {
    actualVsPredictedChartInstance?.resize()
  })
}

// 绘制多市场比较图表
const drawMarketComparisonChart = () => {
  if (!marketComparisonChart.value || !predictionResults.value || !predictionResults.value.by_market || !predictionResults.value.market_predictions) return
  
  if (marketComparisonChartInstance) {
    marketComparisonChartInstance.dispose()
  }
  
  marketComparisonChartInstance = echarts.init(marketComparisonChart.value)
  
  // 准备数据
  const series: SeriesData[] = []
  const allDates: string[] = []
  const marketColors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4']
  
  // 收集所有市场的预测数据
  let colorIndex = 0
  
  for (const market of availableMarkets.value) {
    if (!predictionResults.value.market_predictions || 
        !predictionResults.value.market_predictions[market] || 
        !predictionResults.value.market_predictions[market].predictions || 
        !predictionResults.value.market_predictions[market].predictions[selectedModel.value]) {
      continue
    }
    
    const marketData = predictionResults.value.market_predictions[market]
    const modelData = marketData.predictions[selectedModel.value]
    
    if (!modelData.forecast || !modelData.forecast.date || !modelData.forecast.predicted_price) {
      continue
    }
    
    // 添加系列
    series.push({
      name: `${market}预测价格`,
      type: 'line' as const,
      smooth: true,
      symbol: 'circle' as const,
      symbolSize: 6,
      lineStyle: {
        width: 2
      },
      itemStyle: {
        color: marketColors[colorIndex % marketColors.length]
      },
      data: []
    })
    
    // 收集日期
    for (const date of modelData.forecast.date) {
      if (!allDates.includes(date)) {
        allDates.push(date)
      }
    }
    
    colorIndex++
  }
  
  // 按日期排序
  allDates.sort((a, b) => new Date(a).getTime() - new Date(b).getTime())
  
  // 填充数据
  for (const date of allDates) {
    let seriesIndex = 0
    
    for (const market of availableMarkets.value) {
      if (!predictionResults.value.market_predictions || 
          !predictionResults.value.market_predictions[market] || 
          !predictionResults.value.market_predictions[market].predictions || 
          !predictionResults.value.market_predictions[market].predictions[selectedModel.value] ||
          !predictionResults.value.market_predictions[market].predictions[selectedModel.value].forecast ||
          !predictionResults.value.market_predictions[market].predictions[selectedModel.value].forecast.date ||
          !predictionResults.value.market_predictions[market].predictions[selectedModel.value].forecast.predicted_price) {
        continue
      }
      
      const modelData = predictionResults.value.market_predictions[market].predictions[selectedModel.value]
      const dateIndex = modelData.forecast.date.indexOf(date)
      
      if (dateIndex !== -1 && seriesIndex < series.length) {
        series[seriesIndex].data.push([date, modelData.forecast.predicted_price[dateIndex]])
      } else if (seriesIndex < series.length) {
        series[seriesIndex].data.push([date, null])
      }
      
      seriesIndex++
    }
  }
  
  // 设置图表选项
  const option: echarts.EChartsOption = {
    title: {
      text: `${predictionResults.value.herb_name}${predictionResults.value.specification ? ' (' + predictionResults.value.specification + ')' : ''} - 多市场预测比较`,
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params: unknown) {
        const typedParams = params as Array<{
          axisValue: string | number
          seriesName: string
          value: [string | number, number | null | undefined]
        }>
        const date = typedParams[0].axisValue
        let result = `${date}<br/>`
        
        typedParams.forEach((param) => {
          if (param.value && param.value[1] !== null && param.value[1] !== undefined) {
            result += `${param.seriesName}: ${param.value[1].toFixed(2)} 元/kg<br/>`
          }
        })
        
        return result
      }
    },
    legend: {
      data: series.map(s => s.name).filter(Boolean) as string[],
      bottom: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'time',
      boundaryGap: ['5%', '5%'],
      axisLabel: {
        formatter: '{yyyy}-{MM}-{dd}',
        rotate: 45
      }
    },
    yAxis: {
      type: 'value' as const,
      name: '价格 (元/kg)',
      axisLabel: {
        formatter: '{value} 元'
      }
    },
    series: series
  }
  
  marketComparisonChartInstance.setOption(option)
  
  // 添加窗口大小变化时的自适应
  window.addEventListener('resize', () => {
    marketComparisonChartInstance?.resize()
  })
}

// 监听窗口大小变化，优化图表显示
const handleResize = () => {
  nextTick(() => {
    pricePredictionChartInstance?.resize()
    sentimentTrendChartInstance?.resize()
  })
}

// 初始化
onMounted(async () => {
  await fetchHerbs()
  
  // 自动为三七获取规格列表
  if (predictionForm.herbName) {
    await handleHerbChange()
  }
  
  // 自动执行预测
  if (predictionForm.herbName) {
    await runPrediction()
  }
  
  // 自动执行情绪分析
  if (sentimentForm.herbName) {
    await analyzeSentiment()
  }

  window.addEventListener('resize', handleResize)
})

// 在组件卸载时移除事件监听
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  // 清理图表实例
  if (pricePredictionChartInstance) {
    pricePredictionChartInstance.dispose()
  }
  if (actualVsPredictedChartInstance) {
    actualVsPredictedChartInstance.dispose()
  }
  if (marketComparisonChartInstance) {
    marketComparisonChartInstance.dispose()
  }
})
</script>

<style scoped>
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
  border: none !important;
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
  border: none !important;
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

:root {
  --herbal-green: #2d5d2b;
  --herbal-lightGreen: #3a7a36;
}
/* 价格预测筛选区域样式 */
.prediction-filter-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
  flex-wrap: nowrap;
  white-space: nowrap;
  padding-left: 20px;
  padding-right: 20px;
}

.prediction-filter-item {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.prediction-filter-select {
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  background-color: white;
  min-width: 120px;
  width: 150px;
}

.prediction-filter-select:focus {
  outline: none;
  border-color: #2d5d2b;
  box-shadow: 0 0 0 2px rgba(45, 93, 43, 0.2);
}

.prediction-days-wrapper {
  display: flex;
  align-items: center;
  gap: 2px;
}

.prediction-days-btn {
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  background-color: white;
  cursor: pointer;
  transition: background-color 0.2s;
}

.prediction-days-btn:hover {
  background-color: #f3f4f6;
}

.prediction-days-input {
  padding: 6px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  width: 60px;
  text-align: center;
}

.prediction-days-input:focus {
  outline: none;
  border-color: #2d5d2b;
  box-shadow: 0 0 0 2px rgba(45, 93, 43, 0.2);
}

.prediction-date-input {
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  background-color: white;
  min-width: 140px;
  width: 140px;
}

.wenzi{
  font-size: 30px;
}

.title1{
  padding: 10px;
  font-size: 25px;;
  text-align: center;
}

.prediction-date-input:focus {
  outline: none;
  border-color: #2d5d2b;
  box-shadow: 0 0 0 2px rgba(45, 93, 43, 0.2);
}

.prediction-filter-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
  flex-shrink: 0;
}

.prediction-btn-primary {
  padding: 6px 14px;
  background-color: #2d5d2b;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.prediction-btn-primary:hover {
  background-color: #3a7a36;
}

.prediction-btn-primary:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}

.prediction-btn-secondary {
  padding: 6px 14px;
  background-color: white;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.prediction-btn-secondary:hover {
  background-color: #f3f4f6;
}

/* 市场情绪分析筛选区域样式 */
.sentiment-filter-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.sentiment-filter-item {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sentiment-filter-select {
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  background-color: white;
  min-width: 120px;
  width: 180px;
}

.sentiment-filter-select:focus {
  outline: none;
  border-color: #2d5d2b;
  box-shadow: 0 0 0 2px rgba(45, 93, 43, 0.2);
}

/* 图表容器样式 */
.chart-container {
  width: 100%;
  overflow: hidden;
  transition: all 0.3s ease;
}

/* 数据展示区域样式 */
.prediction-results,
.model-metrics,
.actual-vs-predicted,
.comparison-chart-container {
  width: 100%;
  overflow: hidden;
  transition: all 0.3s ease;
}

.sentiment-filter-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
  flex-shrink: 0;
}

.sentiment-btn-primary {
  padding: 6px 18px;
  background-color: #2d5d2b;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.sentiment-btn-primary:hover {
  background-color: #3a7a36;
}

.sentiment-btn-primary:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}

/* 响应式布局 */
@media screen and (max-width: 1200px) {
  .prediction-filter-row {
    overflow-x: auto;
    padding-bottom: 8px;
  }
  
  .sentiment-filter-row {
    overflow-x: auto;
    padding-bottom: 8px;
  }
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
}/* 适配顶部导航栏 */

.card-shadow {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

.chart-container {
  width: 100%;
  height: 400px;
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

.prediction-progress {
  margin: 20px 0;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.model-selector {
  margin: 20px 0;
}

.model-metrics {
  margin: 20px 0;
}

.model-info {
  margin-top: 30px;
}

@media screen and (max-width: 768px) {
  .chart-container {
    height: 300px;
  }

  .main-content {
    padding: 16px;
  }
}

.prediction-results {
  padding-left: 20px;
}

.prediction-results h4,
.prediction-results label,
.prediction-results .model-selector {
  margin-left: 0;
}
</style>
