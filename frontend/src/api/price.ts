import axios from 'axios'
// import { API_BASE_URL } from '@/services/apiConfig'

// 价格相关API
export async function getHerbs(): Promise<string[]> {
  const response = await axios.get(`/api/herbs`)
  return response.data
}

export async function getSpecifications(herbName: string): Promise<string[]> {
  const response = await axios.get(`/api/specifications`, { 
    params: { herb_name: herbName }
  })
  return response.data
}

export async function getPriceTrend(params: {
  herbName: string
  specification: string
  startDate: string
  endDate: string
}): Promise<{
  dates: string[]
  avg_prices: number[]
  min_prices: number[]
  max_prices: number[]
}> {
  const response = await axios.get(`/api/price-trend`, {
    params: {
      herb_name: params.herbName,
      specification: params.specification,
      start_date: params.startDate,
      end_date: params.endDate
    }
  })
  return response.data
}

export async function getMarketComparison(params: {
  herbName: string
  specification: string
}): Promise<{
  locations: string[]
  prices: number[]
}> {
  const response = await axios.get(`/api/market-comparison`, {
    params: {
      herb_name: params.herbName,
      specification: params.specification
    }
  })
  return response.data
}

export async function getWeatherPriceCorrelation(params: {
  herbName: string
  specification: string
  startDate: string
  endDate: string
}): Promise<{
  dates: string[]
  prices: number[]
  temperatures: number[]
  precipitations: number[]
}> {
  const response = await axios.get(`/api/weather-price-correlation`, {
    params: {
      herb_name: params.herbName,
      specification: params.specification,
      start_date: params.startDate,
      end_date: params.endDate
    }
  })
  return response.data
}

export async function getPriceTrendClustering(params: {
  startDate: string
  endDate: string
  saveResult?: boolean
}): Promise<{
  analysis_time?: string
  date_range?: {
    start_date: string
    end_date: string
  }
  trend_types: Record<number, string>
  clusters: Record<number, {
    total_herbs: number
    all_herb_names: string[]
    herbs: Array<{
      herb_name: string
      specification: string
      location: string
      prices: number[]
      dates: string[]
    }>
  }>
}> {
  const response = await axios.get(`/api/price-trend-clustering`, {
    params: {
      start_date: params.startDate,
      end_date: params.endDate,
      save_result: params.saveResult
    }
  })
  return response.data
}

export async function saveClusteringResult(data: {
  analysis_time?: string
  date_range?: {
    start_date: string
    end_date: string
  }
  trend_types: Record<number, string>
  clusters: Record<number, {
    total_herbs: number
    all_herb_names: string[]
    herbs: Array<{
      herb_name: string
      specification: string
      location: string
      prices: number[]
      dates: string[]
    }>
  }>
}): Promise<{
  success: boolean
  file_path?: string
  error?: string
}> {
  const response = await axios.post(`/api/save-clustering-result`, data)
  return response.data
}

export async function getClusteringHistory(): Promise<{
  filename: string
  date: string
  size: string
}[]> {
  const response = await axios.get(`/api/price-trend-clustering/history`)   
  return response.data
}

export async function loadClusteringHistory(filename: string): Promise<{
  analysis_time?: string
  date_range?: {
    start_date: string
    end_date: string
  }
  trend_types: Record<number, string>
  clusters: Record<number, {
    total_herbs: number
    all_herb_names: string[]
    herbs: Array<{
      herb_name: string
      specification: string
      location: string
      prices: number[]
      dates: string[]
    }>
  }>
}> {
  const response = await axios.get(`/api/price-trend-clustering/load/${encodeURIComponent(filename)}`)
  return response.data
}