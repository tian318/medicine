<template>
  <div class="bg-white rounded-xl card-shadow p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="font-bold text-lg">热门药材</h3>
      <router-link to="/zhongyaoku" class="text-herbal-green text-sm hover:underline">
        查看全部
      </router-link>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div v-for="medicine in hotMedicines" :key="medicine.id" class="medicine-card">
        <div class="medicine-image">
          <img :src="medicine.image" :alt="medicine.name" />
        </div>
        <div class="medicine-info">
          <h4 class="font-medium text-gray-800">{{ medicine.name }}</h4>
          <p class="text-sm text-gray-600 mb-2">{{ medicine.description }}</p>
          <div class="flex justify-between items-center">
            <span class="text-herbal-green font-bold">{{ medicine.price }} 元/公斤</span>
            <span :class="['text-xs px-2 py-1 rounded-full', getTrendClass(medicine.trend)]">
              {{ medicine.trend > 0 ? '↑' : '↓' }} {{ Math.abs(medicine.trend) }}%
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const hotMedicines = ref([
  {
    id: 1,
    name: '人参',
    description: '补气养血，安神益智',
    price: 850,
    trend: 5.2,
    image: 'https://picsum.photos/id/1/300/200',
  },
  {
    id: 2,
    name: '鹿茸',
    description: '补肾壮阳，益精血',
    price: 1200,
    trend: 3.8,
    image: 'https://picsum.photos/id/2/300/200',
  },
  {
    id: 3,
    name: '灵芝',
    description: '增强免疫力，抗肿瘤',
    price: 680,
    trend: -2.1,
    image: 'https://picsum.photos/id/3/300/200',
  },
  {
    id: 4,
    name: '冬虫夏草',
    description: '补肾益肺，止血化痰',
    price: 1500,
    trend: 8.5,
    image: 'https://picsum.photos/id/4/300/200',
  },
])

const getTrendClass = (trend) => {
  return trend > 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
}
</script>

<style scoped>
.medicine-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.medicine-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.medicine-image {
  height: 150px;
  overflow: hidden;
}

.medicine-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.medicine-card:hover .medicine-image img {
  transform: scale(1.05);
}

.medicine-info {
  padding: 1rem;
}

.medicine-info h4 {
  margin: 0 0 0.5rem 0;
}

.medicine-info p {
  margin: 0 0 1rem 0;
  line-height: 1.4;
}
</style>
