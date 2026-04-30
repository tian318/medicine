import axios from 'axios'

// 后端基础地址（使用相对路径）
const API_BASE_URL = '/api'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 增加超时时间到60秒
  headers: {
    'Content-Type': 'application/json',
  },
})

// ===== 参数类型定义 =====

export interface PriceTrendParams {
  herb_name: string
  specification: string
  location?: string
  start_date?: string
  end_date?: string
  days?: number
}

export interface MarketComparisonParams {
  herb_name: string
  specification: string
}

export interface WeatherPriceCorrelationParams {
  herb_name: string
  specification: string
  location?: string
  start_date?: string
  end_date?: string
}

export interface LocationPricesParams {
  location: string
  herb_name?: string
  specification?: string
  start_date?: string
  end_date?: string
}

export interface PriceHeatmapParams {
  herb_name: string
  specification?: string
  start_date: string
  end_date: string
}

export interface PricePredictionParams {
  herb_name: string
  specification: string | null
  forecast_days: number
  by_market: boolean
  start_date?: string
  end_date?: string
}

export interface ActualVsPredictedParams {
  herb_name: string
  prediction_date: string
  specification?: string
}

export interface PriceRankingParams {
  ranking_type?: string
  limit?: number
  positive_only?: boolean
}

export interface SentimentAnalysisParams {
  herb_name: string
  start_date?: string
  end_date?: string
}

export interface PriceTrendClusteringParams {
  start_date: string
  end_date: string
  save_result?: boolean
}

export interface LoginParams {
  username: string
  password: string
}

export interface RegisterParams {
  username: string
  password: string
  phone?: string
}

// ===== 统一 API 封装：对应 app.py 中的接口 =====

export const api = {
  // 基础数据
  async getHerbs() {
    const res = await apiClient.get('/herbs')
    return res.data
  },

  async getSpecifications(herbName: string) {
    const res = await apiClient.get('/specifications', {
      params: { herb_name: herbName },
    })
    return res.data
  },

  // 价格趋势 & 分析
  async getPriceTrend(params: PriceTrendParams) {
    const res = await apiClient.get('/price-trend', { params })
    return res.data
  },

  async getMarketComparison(params: MarketComparisonParams) {
    const res = await apiClient.get('/market-comparison', { params })
    return res.data
  },

  async getWeatherPriceCorrelation(params: WeatherPriceCorrelationParams) {
    const res = await apiClient.get('/weather-price-correlation', { params })
    return res.data
  },

  // 价格热力图
  async getPriceHeatmap(params: PriceHeatmapParams) {
    const res = await apiClient.get('/price-heatmap', { params })
    return res.data
  },

  async getPriceRanking(params: PriceRankingParams = {}) {
    const res = await apiClient.get('/price-ranking', { params })
    return res.data
  },

  // 地点相关
  async getLocations() {
    const res = await apiClient.get('/locations')
    return res.data
  },

  async getLocationHerbs(location: string) {
    const res = await apiClient.get('/location-herbs', {
      params: { location },
    })
    return res.data
  },

  async getLocationPrices(params: LocationPricesParams) {
    const res = await apiClient.get('/location-prices', { params })
    return res.data
  },

  // 价格预测相关
  async predictPrice(params: PricePredictionParams) {
    const res = await apiClient.post('/price-prediction', params)
    return res.data
  },

  async getPredictionHistory() {
    const res = await apiClient.get('/prediction-history')
    return res.data
  },

  async loadPredictionResult(filename: string) {
    const res = await apiClient.get(`/prediction-result/${encodeURIComponent(filename)}`)
    return res.data
  },

  async getPredictionModels() {
    const res = await apiClient.get('/prediction-models')
    return res.data
  },

  async getPredictionResults(herbName: string, specification?: string) {
    const res = await apiClient.get(`/prediction-results/${encodeURIComponent(herbName)}`, {
      params: specification ? { specification } : undefined,
    })
    return res.data
  },

  async getActualVsPredicted(params: ActualVsPredictedParams) {
    const res = await apiClient.get('/actual-vs-predicted', { params })
    return res.data
  },

  // 情绪分析相关
  async getHerbsList() {
    const res = await apiClient.get('/herbs/list')
    return res.data
  },

  async getSentimentAnalysis(params: SentimentAnalysisParams) {
    const res = await apiClient.get('/sentiment-analysis', { params })
    return res.data
  },

  // 价格趋势聚类相关
  async getPriceTrendClustering(params: PriceTrendClusteringParams) {
    const res = await apiClient.get('/price-trend-clustering', { params })
    return res.data
  },

  async saveClusteringResult(clusteringData: unknown) {
    const res = await apiClient.post('/save-clustering-result', clusteringData)
    return res.data
  },

  async getClusteringHistory() {
    const res = await apiClient.get('/price-trend-clustering/history')
    return res.data
  },
  async loadClusteringFile(filename: string) {
    const res = await apiClient.get(
      `/price-trend-clustering/load/${encodeURIComponent(filename)}`,
    )
    return res.data
  },
  // 用户登录
  async login(params: LoginParams) {
    const res = await apiClient.post('/user/login', params)
    return res.data
  },
  // 用户注册
  async register(params: RegisterParams) {
    const res = await apiClient.post('/user/register', params)
    return res.data
  },
}
export default api
