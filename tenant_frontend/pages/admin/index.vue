<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdmin } from '~/composables/useAdmin'

definePageMeta({ layout: 'admin', middleware: 'admin' })

const admin = useAdmin()
const cfg = ref<any>({})
const balance = ref<any>(null)
const testMsg = ref('')
const testing = ref(false)

onMounted(async () => {
  const j: any = await admin.getConfig()
  if (j.code === 0) cfg.value = j.data
})

async function testConn() {
  testing.value = true
  testMsg.value = '测试中…'
  const j: any = await admin.testPlatform()
  testing.value = false
  if (j.code === 0 && j.data) {
    const d = j.data
    if (d.code === 0) balance.value = d.data
    testMsg.value = d.message || '连接成功'
  } else {
    testMsg.value = j.message || '调用失败'
  }
}
</script>

<template>
  <div>
    <div class="admin-card">
      <h2>概览</h2>
      <p class="sub">站点「{{ cfg.tenant_name || '—' }}」· 平台地址 {{ cfg.platform_api_base || '—' }}</p>
      <div class="admin-link-grid">
        <NuxtLink to="/admin/site" class="admin-link">站点管理</NuxtLink>
        <NuxtLink to="/admin/packages" class="admin-link">套餐管理</NuxtLink>
        <NuxtLink to="/admin/orders" class="admin-link">订单管理</NuxtLink>
        <NuxtLink to="/admin/distributors" class="admin-link">分销管理</NuxtLink>
        <NuxtLink to="/admin/users" class="admin-link">用户管理</NuxtLink>
        <NuxtLink to="/admin/payment" class="admin-link">支付设置</NuxtLink>
        <NuxtLink to="/admin/wechat" class="admin-link">公众号设置</NuxtLink>
        <NuxtLink to="/admin/apikey" class="admin-link">API &amp; Key</NuxtLink>
      </div>
    </div>

    <div class="admin-card">
      <h2>平台连接</h2>
      <p class="sub">用后台保存的 API Key 调平台余额接口，验证连通性与 Key 有效性。</p>
      <button class="neu-btn-primary" :disabled="testing" @click="testConn">
        {{ testing ? '测试中…' : '测试平台连接' }}
      </button>
      <div v-if="testMsg" class="err" style="color: #2563eb">{{ testMsg }}</div>
      <div v-if="balance" class="admin-row" style="margin-top: 14px">
        <div class="neu-sm admin-stat" style="padding: 14px">
          <div class="label" style="margin: 0">平台余额（分）</div>
          <div class="price">{{ balance.balance }}</div>
        </div>
        <div class="neu-sm admin-stat" style="padding: 14px">
          <div class="label" style="margin: 0">今日配额剩余</div>
          <div class="price">{{ balance.quota_remain }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
