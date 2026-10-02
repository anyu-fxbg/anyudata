// 租户前端调用本租户后端 /api 的封装（同源，nginx 已代理 /api -> backend）
export function useApi() {
  const config = useRuntimeConfig()
  const base = config.public.apiBase || '/api'

  async function req(path: string, opts: any = {}) {
    const res = await fetch(`${base}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...opts,
    })
    return res.json()
  }

  return {
    get: (p: string) => req(p),
    post: (p: string, body: any) =>
      req(p, { method: 'POST', body: JSON.stringify(body) }),
  }
}
