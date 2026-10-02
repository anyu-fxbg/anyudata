<script setup lang="ts">
import { ref } from 'vue'
import { useAdmin } from '~/composables/useAdmin'
import { useRouter } from 'vue-router'

const { login } = useAdmin()
const router = useRouter()
const username = ref('')
const password = ref('')
const err = ref('')
const loading = ref(false)

async function submit() {
  err.value = ''
  loading.value = true
  const j: any = await login(username.value, password.value)
  loading.value = false
  if (j.code === 0) router.push('/admin')
  else err.value = j.message || '登录失败'
}
</script>

<template>
  <div class="page" style="min-height: 100vh; display: flex; align-items: center">
    <div class="neu" style="padding: 28px; width: 100%">
      <h2 style="margin: 0 0 4px">租户管理后台</h2>
      <p class="label" style="margin-top: 0">请登录以管理站点、套餐与支付</p>
      <input class="neu-input" v-model="username" placeholder="用户名" style="margin-top: 12px" />
      <input class="neu-input" type="password" v-model="password" placeholder="密码" style="margin-top: 12px" />
      <div v-if="err" class="err">{{ err }}</div>
      <button class="neu-btn-primary" style="width: 100%; margin-top: 18px" :disabled="loading" @click="submit">
        {{ loading ? '登录中…' : '登录' }}
      </button>
    </div>
  </div>
</template>
