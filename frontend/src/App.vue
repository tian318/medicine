<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// App 组件作为根组件，只需显示路由视图
</script>

<style>
/* 全局样式 */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

body {
  font-family: 'Inter', system-ui, sans-serif;
  margin: 0;
  padding: 0;
}

:root {
  --herbal-dark: #5c4033;
  --herbal-medium: #8b6e4e;
  --herbal-light: #d9c5b4;
  --herbal-green: #2d5d2b;
  --herbal-lightGreen: #4a7a48;
  --primary: #4d7c0f;
  --secondary: #fef3c7;
  --neutral: #f9fafb;
}
</style>
