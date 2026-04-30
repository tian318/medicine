import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// 引入Font Awesome (通过CDN方式，在index.html中引入)
// 如果需要本地使用，可以安装依赖：npm install @fortawesome/fontawesome-free
import '@fortawesome/fontawesome-free/css/all.css'
const app = createApp(App)
app.use(router)
app.mount('#app')
