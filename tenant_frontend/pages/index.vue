<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApi } from '~/composables/useApi'
import { useBrand } from '~/composables/useBrand'
import { useRoute, useRouter } from 'vue-router'

const { get, post } = useApi()
const { brand, load } = useBrand()
const route = useRoute()
const router = useRouter()

const packages = ref<any[]>([])
const sel = ref<number | null>(null)
const name = ref('')
const idCard = ref('')
const phone = ref('')
const purpose = ref('')
const agree = ref(false)
const loading = ref(false)
const err = ref('')
const distCode = ref('')
const openid = ref('')

onMounted(async () => {
  await load()
  const r = await get('/packages/')
  if (r.code === 0) {
    packages.value = r.data
    if (packages.value.length) sel.value = packages.value[0].id
  }
  // 分销归因：优先取推广链接 ?dist=，否则读本地持久化（同一浏览器后续下单续带）
  const q = (route.query.dist as string) || ''
  if (q) {
    distCode.value = q
    localStorage.setItem('dist_code', q)
  } else {
    distCode.value = localStorage.getItem('dist_code') || ''
  }
  // openid 解析（授权回跳 → 本地持久 → 微信内触发授权）
  await ensureOpenid()
})

async function ensureOpenid() {
  // 1) 授权回跳带 openid（优先级最高）
  const qOpenid = (route.query.openid as string) || ''
  if (qOpenid) {
    openid.value = qOpenid
    localStorage.setItem('wx_openid', qOpenid)
    // 清掉 URL 中的 openid / oauth_error，避免重复触发
    const url = new URL(window.location.href)
    url.searchParams.delete('openid')
    url.searchParams.delete('oauth_error')
    window.history.replaceState({}, '', url.pathname + url.search)
    return
  }
  // 2) 本地持久
  const local = localStorage.getItem('wx_openid') || ''
  if (local) {
    openid.value = local
    return
  }
  // 3) 微信内浏览器且无 openid → 发起网页授权
  const isWechat = /micromessenger/i.test(navigator.userAgent)
  if (isWechat) {
    try {
      const r: any = await get('/wechat/oauth/start/?redirect=' + encodeURIComponent(window.location.href))
      if (r && r.code === 0 && r.data && r.data.url) {
        window.location.href = r.data.url
        return
      }
    } catch (e) { /* 授权不可用则降级为无 openid 继续 */ }
  }
  openid.value = ''
}

async function submit() {
  err.value = ''
  const pkg = packages.value.find((p) => p.id === sel.value)
  if (!pkg) { err.value = '请选择套餐'; return }
  if (!name.value || !idCard.value) { err.value = '请填写姓名和身份证'; return }
  if (!agree.value) { err.value = '请先阅读并同意《数据查询授权书》'; return }
  loading.value = true
  const r = await post('/order/create/', {
    package_id: sel.value, name: name.value, id_card: idCard.value,
    phone: phone.value, purpose: purpose.value, openid: openid.value,
    dist_code: distCode.value.trim(),
  })
  loading.value = false
  if (r.code === 0) {
    sessionStorage.setItem('pay_' + r.data.order_no, JSON.stringify(r.data.pay))
    router.push('/pay?order=' + r.data.order_no)
  } else {
    err.value = r.message || '下单失败'
  }
}
</script>

<template>
  <div class="page">
    <header class="brand">
      <img v-if="brand.logo" :src="brand.logo" class="logo" />
      <h1>{{ brand.name }}</h1>
      <p class="slogan">授权查询 · 数据清晰 · 安全合规</p>
    </header>

    <section class="neu" style="padding: 18px">
      <div class="label">选择套餐</div>
      <div v-for="p in packages" :key="p.id" class="pkg" :class="{ on: sel === p.id }" @click="sel = p.id">
        <div>
          <div class="pkg-name">{{ p.name }}</div>
          <div class="pkg-desc">{{ p.desc }}</div>
        </div>
        <div class="price">¥{{ p.price_yuan }}<small> /次</small></div>
      </div>
    </section>

    <section class="neu" style="padding: 18px; margin-top: 16px">
      <div class="label">被查询人信息</div>
      <input class="neu-input" v-model="name" placeholder="姓名" />
      <input class="neu-input" v-model="idCard" placeholder="身份证号" style="margin-top: 12px" />
      <input class="neu-input" v-model="phone" placeholder="手机号（选填）" style="margin-top: 12px" />
      <div class="label" style="margin-top: 14px">分销码（选填）</div>
      <input class="neu-input" v-model="distCode" placeholder="推广链接自带的邀请码，留空不计分销" />
      <div class="label">查询用途（用于授权书）</div>
      <textarea class="neu-area" v-model="purpose" placeholder="例如：本人了解个人信用与涉诉情况"></textarea>
      <label class="agree">
        <input type="checkbox" v-model="agree" />
        我已阅读并同意《数据查询授权书》，授权依法查询上述个人信息。
      </label>
      <div v-if="err" class="err">{{ err }}</div>
      <button class="neu-btn-primary" style="width: 100%; margin-top: 18px" :disabled="loading" @click="submit">
        {{ loading ? '提交中…' : '提交并支付 ¥' + (sel ? (packages.find(p => p.id === sel)?.price_yuan) : '') }}
      </button>
    </section>
  </div>
</template>

<style scoped>
.brand { text-align: center; padding: 8px 0 18px; }
.logo { width: 56px; height: 56px; border-radius: 14px; object-fit: contain; }
.brand h1 { margin: 8px 0 2px; font-size: 22px; color: var(--accent-deep); }
.slogan { margin: 0; color: var(--muted); font-size: 13px; }
.pkg { display: flex; align-items: center; justify-content: space-between; padding: 14px; border-radius: 16px;
  background: var(--bg); box-shadow: var(--out-sm); margin-top: 12px; cursor: pointer; border: 2px solid transparent; }
.pkg.on { border-color: var(--accent); }
.pkg-name { font-weight: 600; font-size: 15px; }
.pkg-desc { color: var(--muted); font-size: 12px; margin-top: 2px; }
.err { color: #dc2626; font-size: 13px; margin-top: 12px; }
</style>
