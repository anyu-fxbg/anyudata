<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdmin } from '~/composables/useAdmin'

definePageMeta({ layout: 'admin', middleware: 'admin' })

const admin = useAdmin()
const list = ref<any[]>([])
const loading = ref(false)
const err = ref('')
const total = ref(0)
const pages = ref(0)
const page = ref(1)
const filters = ref({ status: '', kw: '' })

const detail = ref<any>(null)
const remark = ref('')
const acting = ref(false)

async function refresh() {
  loading.value = true
  err.value = ''
  const j: any = await admin.getOrders({ ...filters.value, page: page.value, page_size: 20 })
  loading.value = false
  if (j.code === 0 && j.data) {
    list.value = j.data.list || []
    total.value = j.data.total || 0
    pages.value = j.data.pages || 0
  } else {
    err.value = j.message || '加载失败'
  }
}
onMounted(refresh)

function openDetail(o: any) {
  detail.value = o
  remark.value = o.admin_remark || ''
}
async function viewDetail(orderNo: string) {
  const j: any = await admin.getOrder(orderNo)
  if (j.code === 0 && j.data) {
    detail.value = j.data
    remark.value = j.data.admin_remark || ''
  }
}
async function act(action: string, extra?: any) {
  if (!detail.value) return
  acting.value = true
  const j: any = await admin.orderAction(detail.value.order_no, action, extra)
  acting.value = false
  if (j.code === 0) {
    detail.value = j.data
    refresh()
  } else {
    err.value = j.message || '操作失败'
  }
}
async function saveRemark() {
  await act('set_remark', { remark: remark.value })
}
function prev() { if (page.value > 1) { page.value--; refresh() } }
function next() { if (page.value < pages.value) { page.value++; refresh() } }
</script>

<template>
  <div class="admin-card">
    <h2>订单管理</h2>
    <p class="sub">查看与处理 C 端客户订单（支付 / 查询 / 退款）。</p>

    <div class="filter-bar">
      <select class="neu-input" v-model="filters.status" @change="page = 1; refresh()">
        <option value="">全部状态</option>
        <option value="unpaid">待支付</option>
        <option value="paid">已支付</option>
        <option value="querying">查询中</option>
        <option value="done">已完成</option>
        <option value="failed">失败</option>
      </select>
      <input class="neu-input" v-model="filters.kw" placeholder="订单号 / 姓名 / openid / 身份证" @keyup.enter="page = 1; refresh()" />
      <button class="neu-btn-primary" @click="page = 1; refresh()">查询</button>
    </div>

    <p v-if="err" class="err">{{ err }}</p>
    <table class="tbl" v-if="list.length">
      <thead><tr><th>订单号</th><th>客户</th><th>套餐</th><th>金额</th><th>状态</th><th>分销</th><th></th></tr></thead>
      <tbody>
        <tr v-for="o in list" :key="o.order_no" @click="viewDetail(o.order_no)" style="cursor:pointer">
          <td>{{ o.order_no }}</td>
          <td>{{ o.subject_name || '—' }}</td>
          <td>{{ o.package_name || '—' }}</td>
          <td class="amount">¥{{ o.amount_yuan }}</td>
          <td><span class="badge" :class="o.status">{{ o.status_label }}</span></td>
          <td>{{ o.dist_code || '—' }}</td>
          <td><button class="btn-mini" @click.stop="viewDetail(o.order_no)">查看</button></td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!loading" class="sub">暂无订单。</p>

    <div class="pager" v-if="pages > 1">
      <button class="btn-mini" @click="prev" :disabled="page <= 1">上一页</button>
      <span>第 {{ page }} / {{ pages }} 页 · 共 {{ total }} 条</span>
      <button class="btn-mini" @click="next" :disabled="page >= pages">下一页</button>
    </div>
  </div>

  <div class="modal-mask" v-if="detail" @click.self="detail = null">
    <div class="modal">
      <h3>订单详情 · {{ detail.order_no }}</h3>
      <div class="kv">
        <div class="k">状态</div><div class="v"><span class="badge" :class="detail.status">{{ detail.status_label }}</span></div>
        <div class="k">客户</div><div class="v">{{ detail.subject_name }}（{{ detail.subject_id_card }}）</div>
        <div class="k">手机</div><div class="v">{{ detail.subject_phone || '—' }}</div>
        <div class="k">套餐</div><div class="v">{{ detail.package_name }}</div>
        <div class="k">金额</div><div class="v amount">¥{{ detail.amount_yuan }}</div>
        <div class="k">openid</div><div class="v">{{ detail.openid || '—' }}</div>
        <div class="k">分销码</div><div class="v">{{ detail.dist_code || '—' }}（佣金 ¥{{ (detail.commission_fen / 100).toFixed(2) }}）</div>
        <div class="k">平台单号</div><div class="v">{{ detail.platform_query_id || '—' }}</div>
        <div class="k">创建</div><div class="v">{{ detail.created_at || '—' }}</div>
        <div class="k">支付</div><div class="v">{{ detail.paid_at || '—' }}</div>
        <div class="k">退款</div><div class="v">{{ detail.refunded_at || '—' }}</div>
        <div class="k">报告</div><div class="v">{{ detail.has_report ? '已生成' : '无' }}</div>
        <div class="k">备注</div><div class="v">{{ detail.admin_remark || '—' }}</div>
      </div>

      <div class="label">修改备注</div>
      <input class="neu-input" v-model="remark" placeholder="后台备注" />

      <div class="admin-actions">
        <button class="btn-mini" :disabled="acting" @click="saveRemark">保存备注</button>
        <button class="btn-mini" :disabled="acting" @click="act('mark_paid')">标记已付</button>
        <button class="btn-mini" :disabled="acting" @click="act('mark_failed')">标记失败</button>
        <button class="btn-mini" :disabled="acting" @click="act('resync')">重新查询</button>
        <button class="btn-mini danger" :disabled="acting || detail.refunded_at" @click="act('refund')">退款</button>
        <button class="btn-mini" @click="detail = null">关闭</button>
      </div>
      <p v-if="err" class="err">{{ err }}</p>
    </div>
  </div>
</template>
