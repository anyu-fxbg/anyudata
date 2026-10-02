// 白标品牌（来自后端 /api/brand，兜底用构建期 runtimeConfig）
import { reactive } from 'vue'

const brand = reactive({
  name: '',
  logo: '',
  color: '#6C63FF',
  loaded: false,
})

export function useBrand() {
  const config = useRuntimeConfig()
  if (!brand.name) {
    brand.name = config.public.brandName || '数据查询服务'
    brand.logo = config.public.brandLogo || ''
    brand.color = config.public.brandColor || '#6C63FF'
  }

  async function load() {
    if (brand.loaded) return brand
    try {
      const res = await fetch(`${config.public.apiBase || '/api'}/brand/`)
      const j = await res.json()
      if (j.code === 0 && j.data) {
        brand.name = j.data.tenant_name || brand.name
        brand.logo = j.data.logo_url || brand.logo
        brand.color = j.data.primary_color || brand.color
        document.documentElement.style.setProperty('--accent', brand.color)
      }
    } catch (e) { /* 离线兜底 */ }
    brand.loaded = true
    return brand
  }

  return { brand, load }
}
