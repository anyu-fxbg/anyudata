<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApi } from '~/composables/useApi'
import { useRoute, useRouter } from 'vue-router'

const { post } = useApi()
const route = useRoute()
const router = useRouter()
const orderNo = (route.query.order as string) || ''
const pay = ref<any>(null)
const msg = ref('正在准备支付…')

onMounted(() => {
  const raw = sessionStorage.getItem('pay_' + orderNo)
  pay.value = raw ? JSON.parse(raw) : null
  if (!pay.value) msg.value = '未找到支付信息，请重新下单'
})

function mockPay() {
  post('/order/' + orderNo + '/mock-pay/', {}).then(() => router.push('/report/' + orderNo))
}

function wxPay() {
  const pp = pay.value?.pay_params || pay.value
  if (typeof (window as any).WeixinJSBridge !== 'undefined') {
    invoke(pp)
  } else {
    document.addEventListener('WeixinJSBridgeReady', () => invoke(pp), false)
  }
}

function invoke(pp: any) {
  ;(window as any).WeixinJSBridge.invoke('getBrandWCPayRequest', pp, (res: any) => {
    if (res.err_msg === 'get_brand_wcpay_request:ok') {
      router.push('/report/' + orderNo)
    } else {
      msg.value = '支付未完成，请重试'
    }
  })
}
</script>

<template>
  <div class="page">
    <div class="neu" style="padding: 24px; text-align: center">
      <div class="label" style="margin-top: 0">订单 {{ orderNo }}</div>
      <p style="color: var(--muted)">{{ msg }}</p>
      <button v-if="pay && pay.mock" class="neu-btn-primary" style="width: 100%; margin-top: 16px" @click="mockPay">
        模拟支付成功
      </button>
      <button v-else-if="pay && !pay.mock" class="neu-btn-primary" style="width: 100%; margin-top: 16px" @click="wxPay">
        调起微信支付
      </button>
    </div>
  </div>
</template>
