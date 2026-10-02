// 管理后台路由守卫：除 /admin/login 外，所有 /admin/* 需已登录，否则跳登录页。
export default defineNuxtRouteMiddleware(async (to) => {
  if (to.path === '/admin/login') return
  if (!to.path.startsWith('/admin')) return
  const { useAdmin } = await import('~/composables/useAdmin')
  const admin = useAdmin()
  const j: any = await admin.load()
  if (!j || j.code !== 0) {
    return navigateTo('/admin/login')
  }
})
