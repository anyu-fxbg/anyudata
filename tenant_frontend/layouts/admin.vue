<script setup lang="ts">
import { useAdmin } from '~/composables/useAdmin'
import { useRouter } from 'vue-router'
const { user, logout } = useAdmin()
const router = useRouter()

async function doLogout() {
  await logout()
  router.push('/admin/login')
}
</script>

<template>
  <div class="admin-shell">
    <header class="admin-top neu">
      <div class="brand">
        <span class="dot"></span>
        <div>
          <div class="t">租户管理后台</div>
          <div class="s">{{ user?.username || 'admin' }}</div>
        </div>
      </div>
      <nav class="admin-nav">
        <NuxtLink to="/admin" class="nav">概览</NuxtLink>
        <NuxtLink to="/admin/site" class="nav">站点管理</NuxtLink>
        <NuxtLink to="/admin/packages" class="nav">套餐管理</NuxtLink>
        <NuxtLink to="/admin/orders" class="nav">订单管理</NuxtLink>
        <NuxtLink to="/admin/distributors" class="nav">分销管理</NuxtLink>
        <NuxtLink to="/admin/users" class="nav">用户管理</NuxtLink>
        <NuxtLink to="/admin/payment" class="nav">支付设置</NuxtLink>
        <NuxtLink to="/admin/wechat" class="nav">公众号设置</NuxtLink>
        <NuxtLink to="/admin/apikey" class="nav">API &amp; Key</NuxtLink>
        <a class="nav" @click="doLogout">退出登录</a>
      </nav>
    </header>
    <main class="admin-main">
      <slot />
    </main>
  </div>
</template>
