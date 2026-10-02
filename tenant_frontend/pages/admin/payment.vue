<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdmin } from '~/composables/useAdmin'

definePageMeta({ layout: 'admin', middleware: 'admin' })

const admin = useAdmin()
const form = ref<any>({
  wechat_mock: true, wechat_appid: '', wechat_mchid: '', wechat_apiv3_key: '',
  wechat_serial_no: '', wechat_cert_dir: '/certs', wechat_notify_url: '', wechat_private_key: '',
})
const saved = ref(false)
const loading = ref(false)
const err = ref('')

onMounted(async () => {
  const j: any = await admin.getConfig()
  if (j.code === 0) {
    const d = j.data
    form.value = {
      wechat_mock: !!d.wechat_mock,
      wechat_appid: d.wechat_appid || '',
      wechat_mchid: d.wechat_mchid || '',
      wechat_apiv3_key: d.wechat_apiv3_key || '',
      wechat_serial_no: d.wechat_serial_no || '',
      wechat_cert_dir: d.wechat_cert_dir || '/certs',
      wechat_notify_url: d.wechat_notify_url || '',
      wechat_private_key: '',
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
</script>

<template>
  <div class="admin-card">
    <h2>支付设置（微信支付 APIv3）</h2>
    <p class="sub">填写你自己的商户号。保存后立即生效，无需重启。</p>

    <label class="toggle">
      <input type="checkbox" v-model="form.wechat_mock" /> 模拟支付模式（联调用，不接真实微信）
    </label>

    <div class="label">AppID</div>
    <input class="neu-input" v-model="form.wechat_appid" placeholder="wx…" />
    <div class="label">商户号 MCHID</div>
    <input class="neu-input" v-model="form.wechat_mchid" placeholder="1234567890" />
    <div class="label">APIv3 密钥</div>
    <input class="neu-input" v-model="form.wechat_apiv3_key" placeholder="32 位密钥" />
    <div class="label">证书序列号 Serial No</div>
    <input class="neu-input" v-model="form.wechat_serial_no" placeholder="微信商户平台证书序列号" />
    <div class="label">私钥证书目录（PEM 落盘路径）</div>
    <input class="neu-input" v-model="form.wechat_cert_dir" placeholder="/certs" />
    <div class="label">支付回调地址</div>
    <input class="neu-input" v-model="form.wechat_notify_url" placeholder="https://your-domain.com/api/wechat/notify" />

    <div class="label">商户私钥（apiclient_key.pem 内容，粘贴即保存）</div>
    <textarea class="neu-area" v-model="form.wechat_private_key" placeholder="-----BEGIN PRIVATE KEY----- …（留空则不修改）" style="min-height: 120px"></textarea>

    <div v-if="err" class="err">{{ err }}</div>
    <div v-if="saved" class="err" style="color: #16a34a">已保存</div>
    <button class="neu-btn-primary" style="width: 100%; margin-top: 18px" :disabled="loading" @click="save">
      {{ loading ? '保存中…' : '保存' }}
    </button>
  </div>
</template>
