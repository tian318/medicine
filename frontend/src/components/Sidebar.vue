<template>
  <aside class="w-64 bg-white border-r border-gray-200 overflow-y-auto">
    <!-- 系统Logo -->
    <div class="p-4 bg-herbal-green text-white">
      <div class="flex items-center">
        <i class="fa-solid fa-leaf text-2xl mr-3"></i>
        <h1 class="text-lg font-bold">中药材价格系统</h1>
      </div>
    </div>

    <!-- 导航菜单 -->
    <nav class="p-4">
      <div class="space-y-1">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center px-4 py-2 rounded-lg transition"
          :class="[
            $route.path === item.path ? 'sidebar-item-active' : 'text-gray-700 hover:bg-gray-100',
          ]"
        >
          <i :class="[item.icon, 'w-5 text-center mr-3']"></i>
          <span>{{ item.name }}</span>
        </router-link>
      </div>

      <!-- 分隔线 -->
      <div class="my-4 border-t border-gray-200"></div>

      <!-- 用户信息 -->
      <div class="flex items-center p-4 bg-gray-50 rounded-lg">
        <img
          src="https://picsum.photos/id/64/100/100"
          alt="用户头像"
          class="w-8 h-8 rounded-full mr-3"
        />
        <div>
          <p class="text-sm font-medium">系统管理员</p>
          <p class="text-xs text-gray-500">admin@herbal.com</p>
        </div>
        <router-link to="/login" class="ml-auto text-gray-400 hover:text-herbal-green">
          <i class="fa-solid fa-right-from-bracket"></i>
        </router-link>
      </div>
    </nav>
  </aside>
</template>

<script setup lang="ts">
defineOptions({
  name: 'AppSidebar',
})

const menuItems = [
  { path: '/index', name: '数据首页', icon: 'fa-solid fa-home' },
  { path: '/jiageyulan', name: '价格预览', icon: 'fa-solid fa-magnifying-glass' },
  { path: '/', name: '价格走势', icon: 'fa-solid fa-chart-line' },
  { path: '/zhongyaoku', name: '药材库', icon: 'fa-solid fa-database' },
  { path: '/', name: '市场分析', icon: 'fa-solid fa-chart-pie' },
  { path: '/', name: '资讯动态', icon: 'fa-solid fa-newspaper' },
  { path: '/gerenzhongxin', name: '个人中心', icon: 'fa-solid fa-user' },
]
</script>

<style scoped>
.sidebar-item-active {
  background: linear-gradient(90deg, #e8f5e9 0%, #c8e6c9 100%);
  color: #1b5e20;
  border-left: 3px solid #2e7d32;
  box-shadow: 0 2px 4px rgba(46, 125, 50, 0.15);
}
</style>
