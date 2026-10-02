<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAdmin } from '~/composables/useAdmin'

definePageMeta({ layout: 'admin', middleware: 'admin' })

const admin = useAdmin()
const cfg = ref<any>({})
const form = ref({ wechat_appsecret: '', oa_scope: 'snsapi_base' })
const saved = ref(false)
const loading = ref(false)
const err = ref('')

const callbackUrl = computed(() => {
  const base = (cfg.value.public_base_url || '').replace(/\/$/, '')
  return base ? `${base}/api/wechat/oauth/callback/` : ''
})

onMounted(async () => {
  const j: any = await admin.getConfig()
  if (j.code === 0) {
    const d = j.data
    cfg.value = d
    form.value = {
      wechat_appsecret: d.wechat_appsecret || '',
      oa_scope: d.oa_scope || 'snsapi_base',
    }
  }
})

async function save() {
  err.value = ''
  saved.value = false
  loading.value = true
  const j: any = await admin.saveConfig({
    wechat_appsecret: form.value.wechat_appsecret,
    oa_scope: form.value.oa_scope,
  })
  loading.value = false
  if (j.code === 0) saved.value = true
  else err.value = j.message || '保存失败'
}
</script>

<template>
  <div class="admin-card">
    <h2>公众号设置（网页授权 OAuth）</h2>
    <p class="sub">用于获取 C 端客户微信 openid（JSAPI 支付必需）。保存后立即生效，无需重启。</p>

    <div class="label">公众号 AppID</div>
    <input class="neu-input" :value="cfg.wechat_appid || '（未填写，请在「支付设置」填写）'" disabled />

    <div class="label">AppSecret（网页授权用）</div>
    <input class="neu-input" v-model="form.wechat_appsecret" type="password" placeholder="公众号后台「开发 → 基本配置」的 AppSecret" />
    <p class="hint">仅用于 code 换 openid，不会下发到客户端。</p>

    <div class="label">授权作用域</div>
    <select class="neu-input" v-model="form.oa_scope">
      <option value="snsapi_base">snsapi_base（静默授权，仅拿 openid，推荐）</option>
      <option value="snsapi_userinfo">snsapi_userinfo（弹窗授权，可拿昵称头像）</option>
    </select>

    <div class="label">网页授权回调地址</div>
    <input class="neu-input" :value="callbackUrl || '（请先在「站点管理」填写对外域名）'" disabled />
    <p class="hint">
      在公众号后台「设置与开发 → 公众号设置 → 功能设置 → 网页授权域名」中，
      填入上述回调地址的<strong>域名</strong>（不含 https:// 与路径），并将校验文件按要求放到根目录。
    </p>

    <div v-if="err" class="err">{{ err }}</div>
    <div v-if="saved" class="err" style="color: #16a34a">已保存</div>
    <button class="neu-btn-primary" style="width: 100%; margin-top: 18px" :disabled="loading" @click="save">
      {{ loading ? '保存中…' : '保存' }}
    </button>
  </div>
</template>

<style scoped>
.hint { color: var(--muted); font-size: 12px; margin: 8px 0 0; line-height: 1.6; }
.hint strong { color: var(--text); }
</style>
