<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdmin } from '~/composables/useAdmin'

definePageMeta({ layout: 'admin', middleware: 'admin' })

const admin = useAdmin()
const form = ref({ platform_api_base: '', platform_api_key: '', platform_mock: true })
const saved = ref(false)
const loading = ref(false)
const err = ref('')
const testMsg = ref('')
const testing = ref(false)

onMounted(async () => {
  const j: any = await admin.getConfig()
  if (j.code === 0) {
    const d = j.data
    form.value = {
      platform_api_base: d.platform_api_base || 'https://www.gemidaojia.com/saas/api',
      platform_api_key: d.platform_api_key || '',
      platform_mock: !!d.platform_mock,
    }
  }
})

async function save() {
  err.value = ''
  saved.value = false
  loading.value = true
  const j: any = await admin.saveConfig({ ...form.value })
  loading.value = false
  if (j.code === 0) saved.value = true
  else err.value = j.message || '保存失败'
}

async function testConn() {
  testing.value = true
  testMsg.value = '测试中…'
  const j: any = await admin.testPlatform()
  testing.value = false
  if (j.code === 0 && j.data) {
    testMsg.value = j.data.code === 0 ? `连接成功，平台余额 ${j.data.data?.balance} 分` : (j.data.message || '连接异常')
  } else {
    testMsg.value = j.message || '调用失败'
  }
}
</script>

<template>
  <div class="admin-card">
    <h2>API &amp; Key 设置</h2>
    <p class="sub">填写平台下发的 OpenAPI 地址与 API Key（在平台侧「开发者中心」获取）。</p>

    <div class="label">平台 API 地址</div>
    <input class="neu-input" v-model="form.platform_api_base" placeholder="https://www.gemidaojia.com/saas/api" />
    <div class="label">API Key</div>
    <input class="neu-input" v-model="form.platform_api_key" placeholder="平台下发的 X-Api-Key" />
    <label class="toggle" style="margin-top: 12px">
      <input type="checkbox" v-model="form.platform_mock" /> 模拟平台模式（联调用，不真正打平台/不扣费）
    </label>

    <div v-if="err" class="err">{{ err }}</div>
    <div v-if="saved" class="err" style="color: #16a34a">已保存</div>

    <div class="admin-row" style="margin-top: 18px">
      <button class="neu-btn-primary" :disabled="loading" @click="save">{{ loading ? '保存中…' : '保存' }}</button>
      <button class="btn-mini" style="margin-left: 10px; padding: 14px 18px" :disabled="testing" @click="testConn">
        {{ testing ? '测试中…' : '测试连接' }}
      </button>
    </div>
    <div v-if="testMsg" class="err" style="color: #2563eb">{{ testMsg }}</div>
  </div>
</template>
