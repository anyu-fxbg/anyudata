// 租户管理后台：鉴权 + 配置/套餐/平台连通性 调用封装（同源 /api/admin，session Cookie）
export function useAdmin() {
  const config = useRuntimeConfig()
  const base = (config.public.apiBase || '/api').replace(/\/$/, '')
  const authed = useState('admin_authed', () => false)
  const user = useState<any>('admin_user', () => null)

  async function call(path: string, method = 'GET', body?: any) {
    const opts: any = {
      method,
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
    }
    if (body !== undefined) opts.body = JSON.stringify(body)
    const res = await fetch(`${base}${path}`, opts)
    try {
      return await res.json()
    } catch {
      return { code: res.status, message: res.statusText, data: null }
    }
  }

  function qs(params?: any) {
    if (!params) return ''
    const sp = new URLSearchParams()
    for (const k in params) {
      const v = params[k]
      if (v !== undefined && v !== null && v !== '') sp.set(k, String(v))
    }
    const s = sp.toString()
    return s ? '?' + s : ''
  }

  async function load() {
    const j: any = await call('/admin/me/')
    if (j && j.code === 0) {
      authed.value = true
      user.value = j.data
    } else {
      authed.value = false
      user.value = null
    }
    return j
  }

  async function login(username: string, password: string) {
    const j: any = await call('/admin/login/', 'POST', { username, password })
    if (j && j.code === 0) {
      authed.value = true
      await load()
    }
    return j
  }

  async function logout() {
    await call('/admin/logout/', 'POST')
    authed.value = false
    user.value = null
  }

  const getConfig = () => call('/admin/config/')
  const saveConfig = (d: any) => call('/admin/config/', 'PUT', d)
  const getPackages = () => call('/admin/packages/')
  const createPackage = (d: any) => call('/admin/packages/', 'POST', d)
  const updatePackage = (id: number, d: any) => call(`/admin/packages/${id}/`, 'PUT', d)
  const deletePackage = (id: number) => call(`/admin/packages/${id}/`, 'DELETE')
  const testPlatform = () => call('/admin/test-platform/', 'POST')

  // 订单管理
  const getOrders = (params?: any) => call('/admin/orders/' + qs(params))
  const getOrder = (orderNo: string) => call(`/admin/orders/${orderNo}/`)
  const orderAction = (orderNo: string, action: string, extra?: any) =>
    call(`/admin/orders/${orderNo}/action/`, 'POST', { action, ...(extra || {}) })

  // 分销管理
  const getDistributors = (params?: any) => call('/admin/distributors/' + qs(params))
  const createDistributor = (d: any) => call('/admin/distributors/', 'POST', d)
  const updateDistributor = (id: number, d: any) => call(`/admin/distributors/${id}/`, 'PUT', d)
  const deleteDistributor = (id: number) => call(`/admin/distributors/${id}/`, 'DELETE')
  const settleDistributor = (id: number, d?: any) => call(`/admin/distributors/${id}/settle/`, 'POST', d || {})

  // 用户管理
  const getUsers = (params?: any) => call('/admin/users/' + qs(params))
  const getUser = (openid: string) => call(`/admin/users/${encodeURIComponent(openid)}/`)
  const userAction = (openid: string, action: string, extra?: any) =>
    call(`/admin/users/${encodeURIComponent(openid)}/action/`, 'POST', { action, ...(extra || {}) })

  return {
    authed, user, load, login, logout,
    getConfig, saveConfig, getPackages, createPackage, updatePackage, deletePackage, testPlatform,
    getOrders, getOrder, orderAction,
    getDistributors, createDistributor, updateDistributor, deleteDistributor, settleDistributor,
    getUsers, getUser, userAction,
  }
}
