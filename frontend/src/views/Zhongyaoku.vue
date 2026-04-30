<template>
  <div class="page-container">
    <AppSidebar />

    <!-- 主内容区域：改为弹性盒，让页脚固定底部 -->
    <main class="main-content">
      <div class="content-wrapper">
        <!-- 页面头部 -->
        <header class="bg-primary text-white py-4 shadow-md mb-8 rounded-lg">
          <div class="container mx-auto px-4">
            <h1 class="text-[clamp(1.5rem,3vw,2.5rem)] font-bold">
              中药材资源库
            </h1>
          </div>
        </header>

        <!-- 筛选区域 -->
        <section class="filter-section">
          <div class="bg-gray-light p-6 rounded-lg border border-gray-100">
            <h2 class="text-base font-semibold mb-3 text-gray-800 filter-title">首字母筛选</h2>
            <div class="letter-buttons-container">
              <button
                @click="filterByLetter('')"
                :class="[
                  'letter-btn',
                  currentInitial === '' ? 'letter-active' : ''
                ]"
              >
                全部 <span class="text-xs bg-gray-200 rounded-full px-1.5 ml-1">{{ medicineData.length }}</span>
              </button>
              <button
                v-for="letter in letters"
                :key="letter"
                @click="filterByLetter(letter)"
                :class="[
                  'letter-btn',
                  currentInitial === letter ? 'letter-active' : ''
                ]"
              >
                {{ letter }} <span class="text-xs bg-gray-200 rounded-full px-1.5 ml-1">{{ getCountByLetter(letter) }}</span>
              </button>
            </div>

            <div class="text-gray-600 filter-stat">
              <span>共 <strong>{{ filteredData.length }}</strong> 种中药材</span>
              <span v-if="currentInitial" class="ml-4">当前筛选：<strong>{{ currentInitial }}</strong></span>
            </div>
          </div>
        </section>

        <!-- 药材列表 -->
        <section class="mb-8">
          <div id="medicine-list">
            <template v-if="filteredData.length">
              <div v-for="medicine in filteredData" :key="medicine.id" class="medicine-card" @click="handleHerbClick(medicine.name)">
                <div class="flex items-center justify-between mb-3">
                  <h3 class="text-lg font-bold text-primary">{{ medicine.name }}</h3>
                  <span class="text-sm bg-secondary text-primary w-6 h-6 rounded-full flex items-center justify-center">{{ medicine.initial }}</span>
                </div>
                <div class="pt-3 flex items-baseline">
                  <span class="text-sm font-medium text-gray-700">产地：</span>
                  <span class="text-sm text-gray-600 ml-1">{{ medicine.distribution || '未记录' }}</span>
                </div>
              </div>
            </template>
            <div v-else class="col-span-full text-center text-gray-500 py-12">
              <!-- <i class="fas fa-search fa-3x mb-4 text-gray-300"></i> -->
              <p>未找到符合条件的中药材</p>
            </div>
          </div>
        </section>
      </div>

      <footer class="footer">
        <p>© 2026 灵汐药策 版权所有</p>
      </footer>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppSidebar from '@/components/AppSidebar.vue'
import axios from 'axios'

defineOptions({ name: 'MedicineLibraryPage' })

// 定义中药材数据接口
interface HerbData {
  id: number
  name: string
  pinyin: string
  initial: string
  efficacy: string
  distribution?: string
}

const router = useRouter()
const currentInitial = ref('')
const medicineData = ref<HerbData[]>([])

const letters = [
  'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
  'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
]

const handleHerbClick = (herbName: string) => {
  router.push({
    path: '/herb-detail',
    query: { herb_name: herbName },
  })
}

const getCountByLetter = (letter: string) => {
  return medicineData.value.filter((item: HerbData) => item.initial === letter).length
}

const filterByLetter = (letter: string) => {
  currentInitial.value = letter
}

const filteredData = computed(() => {
  if (!currentInitial.value) return medicineData.value
  return medicineData.value.filter((item: HerbData) => item.initial === currentInitial.value)
})

const fetchMedicineData = async () => {
  try {
    console.log('开始获取药材数据')
    const response = await axios.get('/api/herbs-data')
    console.log('获取药材数据成功，数据长度:', response.data.length)
    medicineData.value = response.data.map((item: HerbData) => ({
      id: item.id,
      name: item.name,
      pinyin: item.pinyin || '',
      initial: item.initial,
      efficacy: item.efficacy || '',
      distribution: item.distribution
    }))
  } catch (error) {
    console.error('获取药材数据失败:', error)
    if (axios.isAxiosError(error)) {
      if (error.response) {
        console.error('响应错误:', error.response.data)
        console.error('响应状态:', error.response.status)
      } else if (error.request) {
        console.error('请求错误:', error.request)
      } else {
        console.error('其他错误:', error.message)
      }
    } else {
      console.error('未知错误:', error)
    }
    // 模拟数据
    medicineData.value = [
      { id: 1, name: '阿胶', pinyin: 'Ejiao', initial: 'E', efficacy: '补血滋阴，润燥，止血' },
      { id: 2, name: '艾叶', pinyin: 'Aiye', initial: 'A', efficacy: '温经止血，散寒止痛，祛湿止痒' },
      { id: 3, name: '八角茴香', pinyin: 'Bajiaohuixiang', initial: 'B', efficacy: '温阳散寒，理气止痛' },
      { id: 4, name: '巴戟天', pinyin: 'Bajitian', initial: 'B', efficacy: '补肾阳，强筋骨，祛风湿' },
      { id: 5, name: '白扁豆', pinyin: 'Baidou', initial: 'B', efficacy: '健脾化湿，和中消暑' },
      { id: 6, name: '白矾', pinyin: 'Baifan', initial: 'B', efficacy: '外用解毒杀虫，燥湿止痒；内服止血止泻，祛除风痰' },
      { id: 7, name: '白果', pinyin: 'Baiguo', initial: 'B', efficacy: '敛肺定喘，止带缩尿' },
      { id: 8, name: '白及', pinyin: 'Baiji', initial: 'B', efficacy: '收敛止血，消肿生肌' },
      { id: 9, name: '白术', pinyin: 'Baizhu', initial: 'B', efficacy: '健脾益气，燥湿利水，止汗，安胎' },
      { id: 10, name: '白芷', pinyin: 'Baizhi', initial: 'B', efficacy: '解表散寒，祛风止痛，宣通鼻窍，燥湿止带，消肿排脓' },
      { id: 11, name: '百部', pinyin: 'Baibu', initial: 'B', efficacy: '润肺下气止咳，杀虫灭虱' },
      { id: 12, name: '百合', pinyin: 'Baihe', initial: 'B', efficacy: '养阴润肺，清心安神' },
      { id: 13, name: '柏子仁', pinyin: 'Baiziren', initial: 'B', efficacy: '养心安神，润肠通便，止汗' },
      { id: 14, name: '板蓝根', pinyin: 'Banlangen', initial: 'B', efficacy: '清热解毒，凉血，利咽' },
      { id: 15, name: '半夏', pinyin: 'Banxia', initial: 'B', efficacy: '燥湿化痰，降逆止呕，消痞散结' },
      { id: 16, name: '薄荷', pinyin: 'Bohe', initial: 'B', efficacy: '疏散风热，清利头目，利咽，透疹，疏肝行气' },
      { id: 17, name: '苍术', pinyin: 'Cangzhu', initial: 'C', efficacy: '燥湿健脾，祛风散寒，明目' },
      { id: 18, name: '草果', pinyin: 'Caoguo', initial: 'C', efficacy: '燥湿温中，截疟除痰' }
    ]
  }
}

onMounted(() => {
  fetchMedicineData()
})
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* 核心修改1：主内容区域改为弹性盒，方向垂直，占满高度 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column; /* 垂直排列内容和页脚 */
  background-color: #f0f8f0;
  margin-top: 70px;
  padding: 0 0.5rem;
}

/* 核心修改2：内容容器占满剩余高度，推页脚到底部 */
.content-wrapper {
  max-width: 1500px;
  margin: 0 auto;
  width: 100%;
  flex: 1; /* 占满主内容区域剩余高度 */
  display: flex;
  flex-direction: column;
  margin-bottom: 40px; /* 为页脚添加间距 */
}

/* 筛选区域样式（不变） */
.filter-section {
  min-height: auto !important;
  width: 100%;
  margin-bottom: 48px !important;
}

.bg-gray-light {
  background-color: white;
  transition: background-color 0.2s ease;
  width: 100%;
  padding: 16px 24px !important;
  box-sizing: border-box;
}

.filter-title, .filter-stat {
  padding-left: 0;
  margin-left: 0;
  line-height: 1.2;
}

.filter-stat {
  margin-bottom: 0 !important;
  padding-bottom: 8px !important;
  font-size: 20px;
}

/* 自定义颜色变量 */
:root {
  --primary: #6A994E; /* 中药主题绿色 */
  --secondary: #FEF3C7;
  --neutral: #F9FAFB;
  --text-dark: #374151;
}

/* 按钮容器样式（不变） */
.letter-buttons-container {
  display: flex;
  flex-wrap: wrap;
  padding: 6px 0 !important;
  margin: 0 0 6px 0 !important;
  gap: 12px;
  width: 100%;
  box-sizing: border-box;
}

/* 按钮样式（不变） */
.letter-btn {
  padding: 8px 20px;
  min-width: 80px;
  height: 42px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border-radius: 9999px;
  border: 1px solid #e5e7eb;
  background-color: white;
  color: #374151;
  font-weight: 400;
  font-size: 1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.letter-btn:hover {
  border-color: var(--primary);
  background-color: #f9fafb;
}

.letter-active {
  background-color: var(--primary);
  color: white;
  border-color: var(--primary);
}

.letter-btn span {
  background-color: #f3f4f6 !important;
  color: #6b7280 !important;
  font-weight: 500;
  border-radius: 9999px;
  padding: 2px 8px;
  margin-left: 4px;
  font-size: 0.75rem;
  min-width: 24px;
  text-align: center;
  box-sizing: border-box;
}

.letter-active span {
  background-color: rgba(255, 255, 255, 0.25) !important;
  color: white !important;
}

/* 药材列表网格样式（不变） */
#medicine-list {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
  width: 100%;
}

/* 药材卡片样式（不变） */
.medicine-card {
  background-color: white;
  border: 1px solid var(--primary);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  cursor: pointer;
}

.medicine-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
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

/* 响应式设计（不变） */
@media (max-width: 640px) {
  .main-content {
    padding: 0 0.5rem;
  }

  #medicine-list {
    grid-template-columns: 1fr !important;
  }

  .letter-btn {
    padding: 6px 16px;
    min-width: 70px;
  }

  .bg-gray-light {
    padding: 12px 16px !important;
  }

  .filter-section {
    margin-bottom: 32px !important;
  }
  .filter-stat {
    padding-bottom: 6px !important;
  }
  .letter-buttons-container {
    padding: 4px 0 !important;
    margin: 0 0 4px 0 !important;
  }
}

@media (min-width: 641px) and (max-width: 1023px) {
  #medicine-list {
    grid-template-columns: repeat(2, 1fr) !important;
  }
}

@media (min-width: 1024px) {
  #medicine-list {
    grid-template-columns: repeat(4, 1fr) !important;
  }
}

/* 优化header圆角（不变） */
header.bg-primary {
  border-radius: 8px;
  overflow: hidden;
  padding:25px;
}

/* 文本溢出省略（不变） */
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
