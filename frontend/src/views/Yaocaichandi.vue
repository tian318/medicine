<template>
  <div class="page-container">
    <AppSidebar />
    <main class="main-content">
      <div class="mb-6">
        <h2 class="text-2xl font-bold text-gray-800">数据概览</h2>
      </div>
      <div class="flex gap-6">
        <!-- 左侧地图 -->
        <div class="map-container">
          <h3 class="font-bold text-lg mb-4">中国中药材产地分布</h3>
          <div ref="mapRef" class="map-echarts">
            <div v-if="!mapLoaded" style="display: flex; align-items: center; justify-content: center; height: 100%; color: #666;">加载中...</div>
          </div>
        </div>

        <!-- 右侧信息 -->
        <div class="info-container">
          <div class="unified-box">
            <div class="search-section">
              <div class="flex items-center gap-2">
                <div class="flex-1">
                  <span class="text-sm font-medium text-gray-700 mb-1 block">产地/市场</span>
                  <select v-model="filterForm.location" class="form-select w-full">
                    <option value="">请选择</option>
                    <option v-for="loc in locationGroups.majorMarkets" :key="loc.location_name" :value="loc.location_name">{{ loc.location_name }}</option>
                    <option v-for="loc in locationGroups.markets" :key="loc.location_name" :value="loc.location_name">{{ loc.location_name }}</option>
                    <option v-for="loc in locationGroups.origins" :key="loc.location_name" :value="loc.location_name">{{ loc.location_name }}</option>
                  </select>
                </div>
                <div class="flex-1">
                  <span class="text-sm font-medium text-gray-700 mb-1 block">药材名称</span>
                  <select v-model="filterForm.herbName" @change="handleHerbChange" class="form-select w-full">
                    <option value="">请选择</option>
                    <option v-for="herb in herbs" :key="herb" :value="herb">{{ herb }}</option>
                  </select>
                </div>
                <div>
                  <span class="text-sm font-medium text-gray-700 mb-1 block">&nbsp;</span>
                  <button @click="fetchLocationHerbPrices(filterForm.location, filterForm.herbName)" class="btn-primary">
                    <img src="../img/sousuo.png" alt="">
                  </button>
                </div>
              </div>
            </div>

            <div class="price-section">
              <h4 class="font-medium text-gray-700 mb-3">
                {{ selectedLocation ? selectedLocation.name + ' 药材价格信息' : filterForm.herbName ? filterForm.herbName + ' 在各地的价格信息' : '药材价格信息' }}
              </h4>
              <div class="price-list-scroll">
                <table class="price-table">
                  <thead>
                    <tr><th>药材名称</th><th>规格</th><th>价格</th><th>走势</th><th>周涨跌</th><th>月涨跌</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, index) in displayPriceData" :key="index">
                      <td class="herb-name">{{ item.herb_name }}</td>
                      <td class="spec">{{ item.specification }}</td>
                      <td class="price">{{ parseFloat(item.price).toFixed(2) }}</td>
                      <td :class="['trend', item.trend.includes('涨') ? 'trend-up' : item.trend.includes('跌') ? 'trend-down' : 'trend-steady']">{{ item.trend }}</td>
                      <td :class="item.week_change.startsWith('-') ? 'text-red-600' : 'text-green-600'">{{ item.week_change }}</td>
                      <td :class="item.month_change.startsWith('-') ? 'text-red-600' : 'text-green-600'">{{ item.month_change }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
declare global { interface Window { T: any } }
declare const T: any

import { ref, onMounted, onUnmounted, onActivated, nextTick, computed, watch } from 'vue'
import AppSidebar from '@/components/AppSidebar.vue'
import axios from 'axios'
// import { API_BASE_URL } from '@/services/apiConfig'
defineOptions({ name: 'HomePage' })

// ==================== 1. 静态默认数据（图片中显示的数据） ====================
const DEFAULT_PRICE_DATA: HerbPrice[] = [
  { herb_name: '丁香', specification: '统进口', price: '55.00', trend: '稳', week_change: '0.00%', month_change: '0.00%', location: '荷花池', recorded_at: new Date().toISOString() },
  { herb_name: '三七', specification: '120头春七云南', price: '100.00', trend: '稳', week_change: '0.00%', month_change: '0.00%', location: '荷花池', recorded_at: new Date().toISOString() },
  { herb_name: '三七', specification: '20头春七云南', price: '145.00', trend: '稳', week_change: '0.00%', month_change: '0.00%', location: '荷花池', recorded_at: new Date().toISOString() },
  { herb_name: '三七', specification: '40头春七云南', price: '135.00', trend: '稳', week_change: '0.00%', month_change: '0.00%', location: '荷花池', recorded_at: new Date().toISOString() },
  { herb_name: '三七', specification: '60头春七云南', price: '128.00', trend: '平', week_change: '0.00%', month_change: '0.00%', location: '荷花池', recorded_at: new Date().toISOString() },
  { herb_name: '三七', specification: '80头春七云南', price: '120.00', trend: '平', week_change: '0.00%', month_change: '0.00%', location: '荷花池', recorded_at: new Date().toISOString() },
  { herb_name: '三七花', specification: '两年花云南', price: '210.00', trend: '稳', week_change: '0.00%', month_change: '0.00%', location: '荷花池', recorded_at: new Date().toISOString() },
  { herb_name: '三棱', specification: '统片浙江', price: '16.00', trend: '稳', week_change: '0.00%', month_change: '0.00%', location: '荷花池', recorded_at: new Date().toISOString() },
  { herb_name: '丝棉木', specification: '统片湖北', price: '42.00', trend: '稳', week_change: '0.00%', month_change: '0.00%', location: '荷花池', recorded_at: new Date().toISOString() },
  { herb_name: '两头尖', specification: '统东北', price: '70.00', trend: '稳', week_change: '0.00%', month_change: '0.00%', location: '荷花池', recorded_at: new Date().toISOString() },
  { herb_name: '丹参', specification: '统个山东', price: '14.00', trend: '稳', week_change: '0.00%', month_change: '7.69%', location: '荷花池', recorded_at: new Date().toISOString() },
  { herb_name: '乌梅', specification: '烟熏统个广东', price: '15.00', trend: '稳', week_change: '0.00%', month_change: '0.00%', location: '荷花池', recorded_at: new Date().toISOString() },
  {herb_name: '乌梢蛇', specification: '全开货 四川', price: '550.00', trend: '慢', week_change: '0.00%', month_change: '0.00', location: '荷花池', recorded_at: new Date().toISOString()},
  {herb_name: '乌药', specification: '统片 较广', price: '18.00', trend: '慢', week_change: '0.00%', month_change: '0.00', location: '荷花池', recorded_at: new Date().toISOString()},
  {herb_name: '九节菖蒲', specification: '统 陕西', price: '260.00', trend: '慢', week_change: '0.00%', month_change: '0.00', location: '荷花池', recorded_at: new Date().toISOString()},
  {herb_name: '乳香', specification: '统货 进口', price: '38.00', trend: '平', week_change: '0.00%', month_change: '0.00', location: '荷花池', recorded_at: new Date().toISOString()},  
  {herb_name: '五倍子', specification: '花倍 较广', price: '55.00', trend: '慢', week_change: '0.00%', month_change: '0.00', location: '荷花池', recorded_at: new Date().toISOString()},
  {herb_name: '五味子', specification: '统 辽宁', price: '33.00', trend: '慢', week_change: '0.00%', month_change: '0.00', location: '荷花池', recorded_at: new Date().toISOString()},
  {herb_name: '人参', specification: '生晒25支 东北', price: '370.00', trend: '平', week_change: '0.00%', month_change: '0.00', location: '荷花池', recorded_at: new Date().toISOString()},
  {herb_name: '仙茅', specification: '统个 四川', price: '118.00', trend: '慢', week_change: '0.00%', month_change: '0.00', location: '荷花池', recorded_at: new Date().toISOString()},
  {herb_name: '仙鹤草', specification: '统 较广', price: '6.00', trend: '慢', week_change: '0.00%', month_change: '0.00', location: '荷花池', recorded_at: new Date().toISOString()},
  {herb_name: '何首乌', specification: '家统片 较广', price: '24.00', trend: '慢', week_change: '0.00%', month_change: '0.00', location: '荷花池', recorded_at: new Date().toISOString()},
  {herb_name: '佛手', specification: '统个 四川', price: '118.00', trend: '慢', week_change: '0.00%', month_change: '0.00', location: '荷花池', recorded_at: new Date().toISOString()},
];

// ==================== 2. 缓存对象 ====================
const cache = {
  herbs: null as string[] | null,
  locations: null as LocationItem[] | null,
  locationHerbs: {} as Record<string, string[]>,
  locationPrices: {} as Record<string, HerbPrice[]>,
  isFirstLoad: true, // 是否是第一次加载页面
  currentPriceData: null as HerbPrice[] | null, // 缓存当前显示的价格数据
  selectedLocation: null as { name: string; isMarket: boolean; isMajorMarket: boolean; province: string; city: string } | null, // 缓存选中的地点
  filterForm: null as { location: string; herbName: string } | null // 缓存筛选条件
}

// ==================== 2. 类型定义 ====================
interface LocationItem {
  location_name: string
  longitude: number
  latitude: number
  is_market: boolean
  is_major_market: boolean
  province: string
  city: string
}
interface HerbPrice {
  location: string
  herb_name: string
  specification: string
  price: string
  trend: string
  week_change: string
  month_change: string
  recorded_at: string
}

// ==================== 3. 响应式数据 ====================
const mapLoaded = ref(false)
const mapRef = ref<HTMLElement | null>(null)
let tianDiTuMap: any = null

// 从缓存中恢复数据
const herbs = ref<string[]>(cache.herbs || [])
const locations = ref<LocationItem[]>(cache.locations || [])
const locationHerbPrices = ref<HerbPrice[]>(cache.currentPriceData || [])
const selectedLocation = ref<{ name: string; isMarket: boolean; isMajorMarket: boolean; province: string; city: string } | null>(cache.selectedLocation || null)

// 从缓存中恢复筛选条件
const filterForm = ref(cache.filterForm || { location: '荷花池', herbName: '' })
const displayPriceData = computed(() => locationHerbPrices.value)

const locationGroups = computed(() => {
  const groups = { majorMarkets: [] as LocationItem[], markets: [] as LocationItem[], origins: [] as LocationItem[] }
  locations.value.forEach(loc => {
    if (loc.is_major_market) groups.majorMarkets.push(loc)
    else if (loc.is_market) groups.markets.push(loc)
    else groups.origins.push(loc)
  })
  return groups
})


// ==================== 5. API 请求函数 ====================
const fetchHerbs = async () => {
  try {
    if (cache.herbs) { herbs.value = cache.herbs; return }
    const response = await axios.get(`/api/herbs`)
    herbs.value = response.data
    cache.herbs = response.data
  } catch (error) { console.error('获取药材列表失败:', error) }
}

const fetchLocations = async () => {
  try {
    if (cache.locations) { locations.value = cache.locations; return cache.locations }
    const response = await axios.get(`/api/locations`)
    locations.value = response.data
    cache.locations = response.data
    return response.data
  } catch (error) { console.error('获取地点列表失败:', error); return [] }
}

const fetchLocationHerbs = async (location: string, updateHerbs: boolean = true) => {
  try {
    if (cache.locationHerbs[location]) {
      if (updateHerbs) herbs.value = cache.locationHerbs[location]
      return
    }
    const response = await axios.get(`/api/location-herbs`, { params: { location } })
    if (updateHerbs) herbs.value = response.data
    cache.locationHerbs[location] = response.data
    if (updateHerbs && filterForm.value.herbName && !response.data.includes(filterForm.value.herbName)) {
      filterForm.value.herbName = ''
    }
  } catch (error) { console.error(`获取${location}药材列表失败:`, error) }
}

const fetchLocationHerbPrices = async (location: string | null, herbName: string | null): Promise<HerbPrice[]> => {
  try {
    const params: Record<string, string> = {}
    if (location) params.location = location
    if (herbName) params.herb_name = herbName
    if (!location && !herbName) { 
      locationHerbPrices.value = []
      cache.currentPriceData = []
      return [] 
    }
    const response = await axios.get(`/api/location-prices`, { params })
    locationHerbPrices.value = response.data
    cache.currentPriceData = response.data // 缓存当前显示的价格数据
    // 同时保存筛选条件到缓存
    cache.filterForm = { ...filterForm.value }
    return response.data
  } catch (error) { console.error('获取药材价格失败:', error); return [] }
}

// ==================== 6. 地图标记添加（使用圆形图标） ====================
// 生成圆形图标的 dataURL
const getCircleIconUrl = (color: string, size: number = 24) => {
  try {
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');
    if (!ctx) return '';
    ctx.clearRect(0, 0, size, size);
    ctx.beginPath();
    ctx.arc(size/2, size/2, size/2 - 2, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();
    return canvas.toDataURL();
  } catch (e) {
    console.error('生成圆形图标失败', e);
    return '';
  }
};

// ==================== 新增：带脉冲动画的红色标记（兼容 DomOverlay 与 Canvas 定时器） ====================
let pulseIntervals: any[] = []; // 存储所有定时器，用于清理

const addRedMarkerWithPulse = (location: LocationItem) => {
  if (!tianDiTuMap || !window.T) return;

  // ---------- 方案1：使用 DomOverlay（CSS 动画，性能最优） ----------
  if (typeof window.T.DomOverlay === 'function') {
    const container = document.createElement('div');
    container.style.position = 'relative';
    container.style.width = '40px';
    container.style.height = '40px';
    container.style.cursor = 'pointer';
    container.style.zIndex = '1000';

    // 中心红色圆形（放大到 32px）
    const centerCircle = document.createElement('div');
    centerCircle.style.position = 'absolute';
    centerCircle.style.top = '50%';
    centerCircle.style.left = '50%';
    centerCircle.style.transform = 'translate(-50%, -50%)';
    centerCircle.style.width = '32px';
    centerCircle.style.height = '32px';
    centerCircle.style.borderRadius = '50%';
    centerCircle.style.backgroundColor = '#e53e3e';
    centerCircle.style.border = '2px solid white';
    centerCircle.style.boxShadow = '0 0 6px rgba(0,0,0,0.3)';
    centerCircle.style.zIndex = '2';
    container.appendChild(centerCircle);

    // 添加三个脉冲线圈（延迟依次为 0s, 0.5s, 1s）
    const delays = [0, 0.5, 1];
    delays.forEach(delay => {
      const ring = document.createElement('div');
      ring.style.position = 'absolute';
      ring.style.top = '50%';
      ring.style.left = '50%';
      ring.style.transform = 'translate(-50%, -50%)';
      ring.style.width = '32px';
      ring.style.height = '32px';
      ring.style.borderRadius = '50%';
      ring.style.border = '2px solid #e53e3e';
      ring.style.opacity = '0';
      ring.style.animation = `pulse 1.5s ${delay}s infinite`;
      ring.style.zIndex = '1';
      ring.style.pointerEvents = 'none';
      container.appendChild(ring);
    });

    // 点击联动
    container.onclick = () => {
      filterForm.value.location = location.location_name;
      tianDiTuMap.panTo(new window.T.LngLat(location.longitude, location.latitude));
    };
    
    // 鼠标悬停显示信息
    container.onmouseover = () => {
      const tooltip = document.createElement('div');
      tooltip.className = 'map-tooltip';
      tooltip.innerHTML = `
        <div class="tooltip-content">
          <div class="tooltip-title">${location.location_name}</div>
          <div class="tooltip-info">省份: ${location.province}</div>
          <div class="tooltip-info">城市: ${location.city}</div>
          <div class="tooltip-info">类型: ${location.is_major_market ? '主要市场' : location.is_market ? '市场' : '产地'}</div>
        </div>
      `;
      tooltip.style.position = 'absolute';
      tooltip.style.zIndex = '99999';
      tooltip.style.pointerEvents = 'none';
      container.appendChild(tooltip);
    };
    
    container.onmouseout = () => {
      const tooltip = container.querySelector('.map-tooltip');
      if (tooltip) {
        tooltip.remove();
      }
    };

    const overlay = new window.T.DomOverlay({
      position: new window.T.LngLat(location.longitude, location.latitude),
      content: container,
      offset: new window.T.Point(0, -20) // 使标记中心对准坐标点
    });
    
    // 确保容器的z-index设置为更高的值
    container.style.zIndex = '9999';
    
    tianDiTuMap.addOverLay(overlay);
    setTimeout(() => {
  try {
    // 获取 DomOverlay 对应的 DOM 元素
    const overlayElement = overlay.getElement ? overlay.getElement() : null;
    if (overlayElement) {
      overlayElement.style.zIndex = '9999';
      // 向上遍历父级，确保整个容器层级足够高
      let parent = overlayElement.parentElement;
      while (parent && parent !== mapRef.value) {
        parent.style.zIndex = '9999';
        parent = parent.parentElement;
      }
    }
    // 如果存在 setTop 方法则调用
    if (overlay.setTop) overlay.setTop();
  } catch(e) {
    console.warn('提升红色标记层级失败', e);
  }
}, 10);
    // 尝试将标记置于顶层
    if (overlay.setTop) {
      overlay.setTop();
    }
    
    // 尝试使用setZIndex方法设置更高的层级
    if (overlay.setZIndex) {
      overlay.setZIndex(9999);
    }

    // 添加地名标签（使用 T.Label）
    if (typeof window.T.Label === 'function') {
      const label = new window.T.Label({
        content: location.location_name,
        position: new window.T.LngLat(location.longitude, location.latitude),
        offset: new window.T.Point(0, -35),
        className: 'custom-marker-label'
      });
      tianDiTuMap.addOverLay(label);
    } else {
      // 降级：使用 Popup 保持打开
      const dummyMarker = new window.T.Marker(new window.T.LngLat(location.longitude, location.latitude));
      dummyMarker.bindPopup(`<div class="custom-marker-label">${location.location_name}</div>`);
      dummyMarker.openPopup();
      tianDiTuMap.addOverLay(dummyMarker);
    }
    return;
  }

  // ---------- 方案2：降级 - 使用 Canvas 动态图标 + 定时器模拟脉冲 ----------
  console.warn('DomOverlay 不可用，使用 Canvas 动画方案（红色标记）');

  const size = 32;          // 图标总大小
  const centerSize = 28;    // 中心圆大小
  let marker: any = null;
  let startTime = Date.now();

  // 生成带脉冲环的 Canvas 图标（根据周期进度绘制）
  const generatePulseIcon = (progress: number) => {
    // progress: 0~1 一个脉冲周期内的进度
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');
    if (!ctx) return '';

    ctx.clearRect(0, 0, size, size);

    // 绘制中心红色圆点
    ctx.beginPath();
    ctx.arc(size/2, size/2, centerSize/2, 0, 2 * Math.PI);
    ctx.fillStyle = '#e53e3e';
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();

    // 绘制两个脉冲环（模拟线圈扩散）
    const ringCount = 2;
    for (let i = 0; i < ringCount; i++) {
      let ringProgress = progress - i * 0.5;
      if (ringProgress < 0 || ringProgress > 1) continue;
      const radius = 14 + ringProgress * 16; // 半径从 14px 扩大到 30px
      const opacity = 0.8 * (1 - ringProgress);
      ctx.beginPath();
      ctx.arc(size/2, size/2, radius, 0, 2 * Math.PI);
      ctx.strokeStyle = `rgba(229, 62, 62, ${opacity})`;
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    return canvas.toDataURL();
  };

  // 创建初始标记（使用第一帧图标）
  const initialIconUrl = generatePulseIcon(0);
  if (initialIconUrl) {
    const icon = new window.T.Icon({
      iconUrl: initialIconUrl,
      iconSize: [size, size],
      iconAnchor: [size/2, size/2],
      popupAnchor: [0, -size/2]
    });
    marker = new window.T.Marker(
      new window.T.LngLat(location.longitude, location.latitude),
      { icon: icon }
    );
  } else {
    marker = new window.T.Marker(new window.T.LngLat(location.longitude, location.latitude));
  }

  // 点击联动
  marker.on('click', () => {
    filterForm.value.location = location.location_name;
    tianDiTuMap.panTo(new window.T.LngLat(location.longitude, location.latitude));
  });
  tianDiTuMap.addOverLay(marker);

  // 添加地名标签
  if (typeof window.T.Label === 'function') {
    const label = new window.T.Label({
      content: location.location_name,
      position: new window.T.LngLat(location.longitude, location.latitude),
      offset: new window.T.Point(0, -28),
      className: 'custom-marker-label'
    });
    tianDiTuMap.addOverLay(label);
  } else {
    marker.bindPopup(`<div class="custom-marker-label">${location.location_name}</div>`);
    marker.openPopup();
    marker.on('click', () => marker.openPopup());
  }

  // 启动定时器，每 150ms 更新图标（模拟脉冲）
  const intervalId = setInterval(() => {
    if (!marker || !tianDiTuMap) return;
    const elapsed = (Date.now() - startTime) % 1200; // 周期 1.2 秒
    const progress = elapsed / 1200;
    const iconUrl = generatePulseIcon(progress);
    if (iconUrl) {
      const newIcon = new window.T.Icon({
        iconUrl: iconUrl,
        iconSize: [size, size],
        iconAnchor: [size/2, size/2],
        popupAnchor: [0, -size/2]
      });
      marker.setIcon(newIcon);
    }
  }, 150);

  pulseIntervals.push(intervalId); // 记录以便后续清理
};


const addLocationMarkers = () => {
  if (!tianDiTuMap || !window.T) {
    setTimeout(addLocationMarkers, 500);
    return;
  }
  if (locations.value.length === 0) {
    setTimeout(addLocationMarkers, 500);
    return;
  }

  const hasLabel = typeof window.T.Label === 'function';
  const redLocations = ['荷花池', '亳州', '玉林', '安国'];

  // ----- 辅助函数：添加蓝色标记（保持原逻辑）-----
  const addBlueMarker = (location: LocationItem) => {
    if (!location.longitude || !location.latitude) return;
    const size = 24;
    const color = '#409DFF';
    const iconUrl = getCircleIconUrl(color, size);
    let marker = null;
    if (iconUrl) {
      const icon = new window.T.Icon({
        iconUrl: iconUrl,
        iconSize: [size, size],
        iconAnchor: [size/2, size/2],
        popupAnchor: [0, -size/2]
      });
      marker = new window.T.Marker(
        new window.T.LngLat(location.longitude, location.latitude),
        { icon: icon }
      );
    } else {
      marker = new window.T.Marker(
        new window.T.LngLat(location.longitude, location.latitude)
      );
    }

    // 添加地名标签
    if (hasLabel) {
      const label = new window.T.Label({
        content: location.location_name,
        position: new window.T.LngLat(location.longitude, location.latitude),
        offset: new window.T.Point(0, -(size/2 + 8)),
        className: 'custom-marker-label'
      });
      tianDiTuMap.addOverLay(label);
    } else {
      marker.bindPopup(`<div class="custom-marker-label">${location.location_name}</div>`);
      marker.openPopup();
      marker.on('click', () => marker.openPopup());
    }

    marker.on('click', () => {
      filterForm.value.location = location.location_name;
      tianDiTuMap.panTo(new window.T.LngLat(location.longitude, location.latitude));
    });
    
    // 鼠标悬停显示信息
    marker.on('mouseover', () => {
      const popupContent = `
        <div class="tooltip-content">
          <div class="tooltip-title">${location.location_name}</div>
          <div class="tooltip-info">省份: ${location.province}</div>
          <div class="tooltip-info">城市: ${location.city}</div>
          <div class="tooltip-info">类型: ${location.is_major_market ? '主要市场' : location.is_market ? '市场' : '产地'}</div>
        </div>
      `;
      marker.bindPopup(popupContent);
      marker.openPopup();
    });
    
    marker.on('mouseout', () => {
      marker.closePopup();
    });
    tianDiTuMap.addOverLay(marker);
  };

  // 1. 添加所有蓝色标记
  locations.value.forEach(location => {
    if (!redLocations.includes(location.location_name)) {
      addBlueMarker(location);
    }
  });

  // 2. 添加红色标记（带脉冲效果）
  locations.value.forEach(location => {
    if (redLocations.includes(location.location_name)) {
      addRedMarkerWithPulse(location);
    }
  });
};

// ==================== 7. 地图初始化（修复语法错误） ====================
const initMap = async () => {
  if (!mapRef.value) return
  try {
    await nextTick()
    if (mapRef.value.clientHeight === 0) mapRef.value.style.height = '400px'
    const tdtKey = '464ff1f181dea1b5abda0f0e02f6469f'

    const initTianDiTu = () => {
      const script = document.createElement('script')
      script.src = `https://api.tianditu.gov.cn/api?v=4.0&tk=${tdtKey}`
      script.type = 'text/javascript'
      script.async = false
      script.onload = () => {
        setTimeout(() => {
          if (window.T) createTianDiTuMap()
          else console.error('天地图API加载后未定义')
        }, 2000)
      }
      script.onerror = () => console.error('天地图API加载失败')
      const existingScript = document.querySelector('script[src*="tianditu.gov.cn/api"]')
      if (existingScript) existingScript.remove()
      document.head.appendChild(script)
    }

    const createTianDiTuMap = () => {
      if (!mapRef.value || !window.T) return
      try {
        tianDiTuMap = new window.T.Map(mapRef.value, {
          projection: 'EPSG:4326',
          zoom: 4,
          center: new window.T.LngLat(105, 35),
          minZoom: 3,
          maxZoom: 18,
          scrollWheelZoom: true
        })
        setTimeout(() => { if (tianDiTuMap) tianDiTuMap.centerAndZoom(new window.T.LngLat(105, 35), 4) }, 100)
        const layer = new window.T.TileLayer(`https://t0.tianditu.gov.cn/DataServer?T=vec_c&x={x}&y={y}&l={z}&tk=${tdtKey}`, {})
        tianDiTuMap.addLayer(layer)
        const labelLayer = new window.T.TileLayer(`https://t0.tianditu.gov.cn/DataServer?T=cva_c&x={x}&y={y}&l={z}&tk=${tdtKey}`, {})
        tianDiTuMap.addLayer(labelLayer)
        const zoomCtrl = new window.T.Control.Zoom()
        tianDiTuMap.addControl(zoomCtrl)
        window.addEventListener('resize', () => { if (tianDiTuMap) tianDiTuMap.checkResize() })

        // 等待 locations 数据后添加标记（递归等待）
        const tryAddMarkers = () => {
          if (locations.value.length > 0) addLocationMarkers()
          else setTimeout(tryAddMarkers, 500)
        }
        setTimeout(tryAddMarkers, 500)
      } catch (error) { console.error('创建天地图实例失败:', error) }
    }

    initTianDiTu()
    mapLoaded.value = true
  } catch (error) {
    console.error('加载中国地图失败:', error)
    if (mapRef.value) mapRef.value.innerHTML = `<div style="...">地图加载失败</div>`
    mapLoaded.value = true
  }
}

// ==================== 8. 事件处理 ====================
const handleHerbChange = async () => {
  const herbName = filterForm.value.herbName
  if (herbName) {
    if (filterForm.value.location) await fetchLocationHerbPrices(filterForm.value.location, herbName)
    else await fetchLocationHerbPrices(null, herbName)
  } else {
    if (filterForm.value.location) await fetchLocationHerbPrices(filterForm.value.location, null)
    else locationHerbPrices.value = []
  }
}

const preloadData = async () => {
  const hotLocations = ['荷花池', '安国', '亳州', '樟树']
  for (const loc of hotLocations) await fetchLocationHerbs(loc, false)
  // 预加载默认地点（荷花池）的价格数据，确保页面加载时右侧有数据显示
  if (filterForm.value.location) {
    await fetchLocationHerbPrices(filterForm.value.location, filterForm.value.herbName)
  }
}

// 确保默认数据加载的函数
const ensureDefaultData = async () => {
  // 确保默认筛选条件是荷花池
  if (!filterForm.value.location) {
    filterForm.value.location = '荷花池'
  }
  
  // 如果是默认地点（荷花池）且没有选择药材名称，使用静态默认数据
  if (filterForm.value.location === '荷花池' && !filterForm.value.herbName) {
    locationHerbPrices.value = DEFAULT_PRICE_DATA
    cache.currentPriceData = DEFAULT_PRICE_DATA
    cache.filterForm = { ...filterForm.value }
  } else {
    // 其他情况从API获取数据
    await fetchLocationHerbPrices(filterForm.value.location, filterForm.value.herbName)
  }
}

// ==================== 9. 监听器 ====================
watch(
  () => filterForm.value.location,
  async (newLocation) => {
    if (newLocation) {
      const locationObj = locations.value.find(loc => loc.location_name === newLocation)
      if (locationObj) {
        selectedLocation.value = { name: locationObj.location_name, isMarket: locationObj.is_market, isMajorMarket: locationObj.is_major_market, province: locationObj.province, city: locationObj.city }
        cache.selectedLocation = selectedLocation.value // 缓存选中的地点
      }
      await fetchLocationHerbs(newLocation)
      
      // 如果是默认地点（荷花池）且没有选择药材名称，使用静态默认数据
      if (newLocation === '荷花池' && !filterForm.value.herbName) {
        locationHerbPrices.value = DEFAULT_PRICE_DATA
        cache.currentPriceData = DEFAULT_PRICE_DATA
      } else {
        // 其他情况从API获取数据
        await fetchLocationHerbPrices(newLocation, filterForm.value.herbName)
      }
      
      // 保存筛选条件到缓存
      cache.filterForm = { ...filterForm.value }
    } else {
      selectedLocation.value = null
      cache.selectedLocation = null
      await fetchHerbs()
      locationHerbPrices.value = []
      cache.currentPriceData = []
      // 保存筛选条件到缓存
      cache.filterForm = { ...filterForm.value }
    }
  }
)

watch(
  () => filterForm.value.herbName,
  async (newHerbName) => {
    if (newHerbName) {
      // 选择了药材名称，从API获取数据
      if (filterForm.value.location) await fetchLocationHerbPrices(filterForm.value.location, newHerbName)
      else await fetchLocationHerbPrices(null, newHerbName)
    } else {
      // 没有选择药材名称
      if (filterForm.value.location) {
        // 从API获取数据
        await fetchLocationHerbPrices(filterForm.value.location, null)
      } else {
        locationHerbPrices.value = []
        cache.currentPriceData = []
      }
    }
    // 保存筛选条件到缓存
    cache.filterForm = { ...filterForm.value }
  }
)

// ==================== 10. 生命周期 ====================
onMounted(async () => {
  // 初始化地图
  await initMap()
  
  // 只有在第一次加载时才加载默认数据
  if (cache.isFirstLoad) {
    await Promise.all([fetchHerbs(), fetchLocations()])
    preloadData()
    // 确保加载默认数据（荷花池的价格信息）
    await ensureDefaultData()
    cache.isFirstLoad = false
  } else {
    // 非第一次加载，检查缓存是否有数据
    if (cache.currentPriceData && cache.currentPriceData.length > 0) {
      // 使用缓存的数据
      locationHerbPrices.value = cache.currentPriceData
    } else {
      // 如果缓存没有数据，确保加载默认数据
      await ensureDefaultData()
    }
  }
})

onUnmounted(() => {
  // 清理所有脉冲动画定时器
  if (pulseIntervals && pulseIntervals.length) {
    pulseIntervals.forEach(clearInterval);
    pulseIntervals = [];
  }
  // 天地图实例无需特殊清理
});

// 当组件被激活时（从其他页面切换回来时）
onActivated(async () => {
  // 确保地图初始化
  if (!tianDiTuMap) {
    await initMap();
  }
  
  // 确保有数据显示
  if (cache.currentPriceData && cache.currentPriceData.length > 0) {
    // 使用缓存的数据
    locationHerbPrices.value = cache.currentPriceData;
  } else {
    // 如果缓存没有数据，确保加载默认数据
    await ensureDefaultData();
  }
});
</script>
<style scoped>
/* 悬浮智能体样式 */
.floating-agent {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9999;
}

/* 折叠按钮 */
.agent-toggle {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #2A5F48;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: transform 0.2s;
}

.agent-toggle:hover {
  transform: scale(1.05);
}

.agent-toggle i {
  font-size: 20px;
}

/* 聊天窗口 */
.agent-chat {
  width: 320px;
  height: 480px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  display: none;
  flex-direction: column;
  overflow: hidden;
}

.agent-chat.active {
  display: flex;
}

/* 头部 */
.agent-header {
  background: #2A5F48;
  color: white;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.agent-close {
  background: none;
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
}

/* 消息区 */
.agent-messages {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
  background: #F9F6F0;
  display: flex;
  flex-direction: column;
  color: black !important;
  * {
    color: black !important;
  }
}

.agent-msg {
  margin-bottom: 10px;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.5;
  max-width: 85%;
  color: black !important;
}

.agent-msg.ai {
  background: white;
  border: 1px solid #D1C7B8;
  align-self: flex-start;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  color: black !important;
}

.agent-msg.user {
  background: #E1F0EC;
  align-self: flex-end;
  margin-left: auto;
  color: black !important;
}

/* 输入框 */
.agent-input {
  display: flex;
  padding: 10px;
  border-top: 1px solid #D1C7B8;
}

#agentInput {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #D1C7B8;
  border-radius: 20px;
  outline: none;
  font-size: 13px;
}

#agentSend {
  margin-left: 8px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #2A5F48;
  color: white;
  border: none;
  cursor: pointer;
}

.page-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 70px); /* 减去顶部导航栏高度 */
  overflow: auto;
  background-color: #f6f8f6;
  padding: 20px 20px 0 0;
  box-sizing: border-box;
}

/* 左右布局 */
.flex {
  display: flex;
  gap: 20px;
  flex: 1;
  min-height: 0;
}

/* 左侧地图区域 */
.map-container {
  flex: 0 0 60%;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: #f0f8f0;
  border-radius: 0.75rem 0.75rem 0 0;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(92, 64, 51, 0.1);
  box-sizing: border-box;
  height: 100%;
}

/* 右侧信息区域 */
.info-container {
  flex: 0 0 40%;
  min-width: 0;
  height: 100%;
  box-sizing: border-box;
}

/* 统一盒子 */
.unified-box {
  background: #f0f8f0;
  border-radius: 1rem 1rem 0 0;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
  border: 1px solid #edf2f7;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 搜索条件区域 */
.search-section {
  flex: 0 0 auto;
}

/* 价格信息区域 */
.price-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.map-echarts {
  width: 100%;
  flex: 1;
  min-height: 0;
  border-radius: 0.5rem;
  position: relative;
  overflow: hidden;
}

/* 确保天地图容器正常显示 */
#tianditu-map {
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 100% !important;
  z-index: 0 !important;
  overflow: hidden !important;
}

/* 隐藏天地图瓦片加载失败的占位图标 */
#tianditu-map img {
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
  width: 0 !important;
  height: 0 !important;
  position: absolute !important;
  left: -9999px !important;
  top: -9999px !important;
  z-index: -1 !important;
  pointer-events: none !important;
}

/* 隐藏任何data:image形式的背景图片（通常是错误图标） */
#tianditu-map [style*="data:image"] {
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
  width: 0 !important;
  height: 0 !important;
  overflow: hidden !important;
  position: absolute !important;
  left: -9999px !important;
  top: -9999px !important;
  z-index: -1 !important;
  pointer-events: none !important;
}

/* 隐藏错误提示元素 */
#tianditu-map .tdt-tile-error,
#tianditu-map .tdt-tile-fail,
#tianditu-map .tdt-tile-loading,
#tianditu-map .tdt-error,
#tianditu-map .tdt-fail,
#tianditu-map .tdt-loading,
#tianditu-map .tdt-tile-err,
#tianditu-map .tdt-tile-broken,
#tianditu-map .tdt-tile-missing,
#tianditu-map .tdt-tile-error-icon,
#tianditu-map .tdt-tile-fail-icon,
#tianditu-map .tdt-tile-loading-icon,
#tianditu-map .tdt-icon,
#tianditu-map .tdt-error-icon,
#tianditu-map .tdt-fail-icon,
#tianditu-map .tdt-loading-icon {
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
  width: 0 !important;
  height: 0 !important;
  overflow: hidden !important;
  position: absolute !important;
  left: -9999px !important;
  top: -9999px !important;
  z-index: -1 !important;
  pointer-events: none !important;
}

/* 确保地图瓦片和控件正常显示 */
#tianditu-map canvas,
#tianditu-map .tdt-control,
#tianditu-map .tdt-control *,
#tianditu-map .tdt-copyright,
#tianditu-map .tdt-copyright * {
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  width: auto !important;
  height: auto !important;
  overflow: visible !important;
  position: relative !important;
  left: auto !important;
  top: auto !important;
  z-index: 1 !important;
  pointer-events: auto !important;
}

.price-list-scroll {
  flex: 1;
  overflow-y: auto;
  padding-right: 0.5rem;
  min-height: 0;
  margin-top: 1rem;
}

/* 隐藏滚动条（可选） */
.price-list-scroll::-webkit-scrollbar {
  width: 4px;
}
.price-list-scroll::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 4px;
}

.card-shadow {
  box-shadow: 0 4px 12px rgba(92, 64, 51, 0.1);
}

/* 其余原有样式保持不变 */
/* 价格标签样式 */

.footer {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
  text-align: center;
  font-size: 14px;
  color: #6b7280;
}
/* 统一下拉框样式 */
.form-select {
  padding: 0.5rem 0.75rem;        /* 左右内边距由原来的2rem/1rem减小 */
  border: 1px solid #e2e8f0;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: #1a202c;
  background-color: white;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  cursor: pointer;
  width: 100%;                    /* 确保宽度填满父容器 */
}
.form-select:focus {
  outline: none;
  border-color: #2D5D2B;      /* 主题绿色 */
  box-shadow: 0 0 0 3px rgba(45, 93, 43, 0.1);
}
/* 统一按钮样式 */
.btn-primary {
  padding: 0.5rem 1rem;
  background-color: #2D5D2B;   /* 深绿色主题 */
  color: white;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 250;
  border: none;
  transition: background-color 0.2s, transform 0.1s;
  cursor: pointer;
  white-space: nowrap;
  height: 38px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}
.btn-primary:hover {
  background-color: #1e3f1c;   /* 更深的绿色 */
}
.btn-primary:active {
  transform: scale(0.98);
}

.btn-secondary {
  padding: 0.5rem 1.5rem;
  background-color: #f1f5f9;
  color: #334155;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  border: 1px solid #e2e8f0;
  transition: background-color 0.2s;
  cursor: pointer;
}
.btn-secondary:hover {
  background-color: #e2e8f0;
}

/* 价格表格 */
.price-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.75rem;
  line-height: 1.5;
  table-layout: fixed; /* 固定布局，配合列宽比例 */
}

.price-table th {
  text-align: left;
  padding: 0.5rem 0.25rem;
  background-color: #f9fafb;
  font-weight: 600;
  color: #1e293b;
  border-bottom: 1px solid #e2e8f0;
  white-space: nowrap;
}

.price-table td {
  padding: 0.5rem 0.25rem;
  border-bottom: 1px solid #edf2f7;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.price-table tbody tr:hover {
  background-color: #f8fafc;
}

/* 列宽分配（根据内容调整） */
.price-table th:nth-child(1) { width: 18%; } /* 药材名称 */
.price-table th:nth-child(2) { width: 12%; } /* 规格 */
.price-table th:nth-child(3) { width: 10%; } /* 价格 */
.price-table th:nth-child(4) { width: 8%; }  /* 走势 */
.price-table th:nth-child(5) { width: 10%; } /* 周涨跌 */
.price-table th:nth-child(6) { width: 10%; } /* 月涨跌 */
.price-table th:nth-child(7) { width: 22%; } /* 记录时间 */

/* 特定列样式 */
.price-table .herb-name {
  font-weight: 500;
  color: #2D5D2B; /* 主题绿色 */
}

.price-table .price {
  font-weight: 500;
  color: #1a202c;
}

/* 地图悬停提示框样式 */
.map-tooltip {
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  font-size: 14px;
  line-height: 1.4;
  min-width: 180px;
}

.tooltip-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tooltip-title {
  font-weight: 600;
  color: #2D5D2B;
  margin-bottom: 4px;
}

.tooltip-info {
  color: #4a5568;
  font-size: 13px;
}

/* 天地图Popup样式 */
.tdt-popup-content {
  background: rgba(255, 255, 255, 0.95) !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 8px !important;
  padding: 12px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
  font-size: 14px !important;
  line-height: 1.4 !important;
  min-width: 180px !important;
}

.price-table .trend-up { color: #dc2626; }   /* 涨 - 红色 */
.price-table .trend-down { color: #16a34a; } /* 跌 - 绿色 */
.price-table .trend-steady { color: #4b5563; } /* 平/稳 - 灰色 */

.price-table .record-date {
  color: #6b7280;
  font-size: 0.7rem;
}

/* 确保滚动容器支持水平和垂直滚动 */
.price-list-scroll {
  overflow: auto; /* 同时允许水平和垂直滚动 */
  padding-right: 0.25rem;
}

/* 美化滚动条（可选） */
.price-list-scroll::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}
.price-list-scroll::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}
.price-list-scroll::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 4px;
}
.price-list-scroll::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

/* “显示更多”按钮样式 */
.show-more-btn {
  color: #2D5D2B;
  font-size: 0.875rem;
  font-weight: 500;
  padding: 0.5rem 1rem;
  background: #f0f7ee;
  border-radius: 999px;
  transition: background 0.2s;
  display: inline-block;
  border: 1px solid #d9e6d6;
  cursor: pointer;
}
/* .show-more-btn:hover {
  background: #e2efe0;
  text-decoration: none;
} */

.price-table th:nth-child(1) { width: 15%; }
.price-table th:nth-child(2) { width: 22%; }
.price-table th:nth-child(3) { width: 13%; }
.price-table th:nth-child(4) { width: 8%; }
.price-table th:nth-child(5) { width: 13%; }
.price-table th:nth-child(6) { width: 13%; } /* 总和 84%，剩余 16% 作为留白或自动分配 */

/* 自定义标记标签样式（黑底白字，带小三角） */
/* 自定义标记文字标签样式（黑底白字） */
.custom-marker-label {
  background: rgba(0, 0, 0, 0.7) !important;
  color: white !important;
  font-size: 12px !important;
  padding: 4px 8px !important;
  border-radius: 4px !important;
  border: none !important;
  box-shadow: 0 2px 6px rgba(0,0,0,0.2) !important;
  white-space: nowrap;
  font-weight: 500;
  pointer-events: none; /* 让标签不干扰点击 */
  font-family: sans-serif;
}

/* 调整小三角箭头颜色 */
.custom-marker-tooltip::before {
  border-top-color: rgba(0, 0, 0, 0.7) !important;
}

/* 脉冲动画 */
@keyframes pulse {
  0% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 0.8;
    border-width: 2px;
  }
  70% {
    transform: translate(-50%, -50%) scale(2);
    opacity: 0;
    border-width: 1px;
  }
  100% {
    transform: translate(-50%, -50%) scale(2.5);
    opacity: 0;
    border-width: 0px;
  }
}
</style>
