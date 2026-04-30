import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
  },
  {
    path: '/index',
    name: 'Index',
    component: () => import('@/views/Index.vue'),
  },
  {
    path: '/yaocaichandi',
    name: 'Yaocaichandi',
    component: () => import('@/views/Yaocaichandi.vue'),
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
  },
  {
    path: '/zhongyaoku',
    name: 'Zhongyaoku',
    component: () => import('@/views/Zhongyaoku.vue'),
  },
  {
    path: '/jiageyulan',
    name: 'Jiageyulan',
    component: () => import('@/views/Jiageyulan.vue'),
  },
  {
    path: '/jiagezoushi',
    name: 'Jiagezoushi',
    component: () => import('@/views/Jiagezoushi.vue'),
  },
  {
    path: '/shichangfenxi',
    name: 'Shichangfenxi',
    component: () => import('@/views/Shichangfenxi.vue'),
  },
  {
    path: '/zixundongtai',
    name: 'Zixundongtai',
    component: () => import('@/views/Zixundongtai.vue'),
  },
  {
    path: '/gerenzhongxin',
    name: 'Gerenzhongxin',
    component: () => import('@/views/Gerenzhongxin.vue'),
  },
  {
    path: '/herb-detail',
    name: 'HerbDetail',
    component: () => import('@/views/HerbDetail.vue'),
  },
  {
    path: '/herb-intro',
    name: 'HerbIntro',
    component: () => import('@/views/HerbIntro.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
