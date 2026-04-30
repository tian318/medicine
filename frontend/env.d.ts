/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module '@/data/medicineData' {
  interface Medicine {
    id: number
    name: string
    pinyin: string
    initial: string
    efficacy: string
  }

  const medicineData: Medicine[]
  export default medicineData
}
