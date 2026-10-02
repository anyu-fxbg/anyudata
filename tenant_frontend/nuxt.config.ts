export default defineNuxtConfig({
  ssr: false,
  devtools: { enabled: false },
  css: ['~/assets/css/main.css'],
  app: {
    head: {
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no' },
        { name: 'theme-color', content: '#E0E5EC' },
      ],
      title: '数据查询',
    },
  },
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_API_BASE || '/api',
      brandName: process.env.NUXT_BRAND_NAME || '',
      brandColor: process.env.NUXT_BRAND_COLOR || '#6C63FF',
      brandLogo: process.env.NUXT_BRAND_LOGO || '',
    },
  },
})
