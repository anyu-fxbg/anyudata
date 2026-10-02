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
const filters = ref({ kw: '', blocked: '' })

const detail = ref<any>(null)
const note = ref('')
const acting = ref(false)

async function refresh() {
  loading.value = true
  err.value = ''
  const j: any = await admin.getUsers({ ...filters.value, page: page.value, page_size: 20 })
  loading.value = false
  if (j.code === 0 && j.data) {
    list.value = j.data.list || []
    total.value = j.data.total || 0
    pages.value = j.data.pages || 0
  } else err.value = j.message || '加载失败'
}
onMounted(refresh)

async function viewDetail(openid: string) {
  const j: any = await admin.getUser(openid)
  if (j.code === 0 && j.data) {
    detail.value = j.data
    note.value = j.data.note || ''
  }
}
async function act(action: string, extra?: any) {
  if (!detail.value) return
  acting.value = true
  const j: any = await admin.userAction(detail.value.openid, action, extra)
  acting.value = false
  if (j.code === 0) {
    detail.value = j.data
    refresh()
  } else err.value = j.message || '操作失败'
}
async function saveNote() { await act('set_note', { note: note.value }) }
function prev() { if (page.value > 1) { page.value--; refresh() } }
function next() { if (page.value < pages.value) { page.value++; refresh() } }
</script>

<template>
  <div class="admin-card">
    <h2>用户管理</h2>
    <p class="sub">C 端客户（按微信 openid 标识）；可拉黑禁止下单、记录备注。</p>

    <div class="filter-bar">
      <select class="neu-input" v-model="filters.blocked" @change="page = 1; refresh()">
        <option value="">全部</option>
        <option value="0">正常</option>
        <option value="1">已拉黑</option>
      </select>
      <input class="neu-input" v-model="filters.kw" placeholder="openid / 昵称 / 手机" @keyup.enter="page = 1; refresh()" />
      <button class="neu-btn-primary" @click="page = 1; refresh()">查询</button>
    </div>

    <p v-if="err" class="err">{{ err }}</p>
    <table class="tbl" v-if="list.length">
      <thead><tr><th>昵称</th><th>手机</th><th>订单数</th><th>累计(元)</th><th>状态</th><th></th></tr></thead>
      <tbody>
        <tr v-for="u in list" :key="u.openid" @click="viewDetail(u.openid)" style="cursor:pointer">
          <td>{{ u.nickname || '—' }}</td>
          <td>{{ u.phone || '—' }}</td>
          <td>{{ u.order_count }}</td>
          <td class="amount">¥{{ u.total_yuan }}</td>
          <td><span class="badge" :class="u.is_blocked ? 'danger' : 'ok'">{{ u.is_blocked ? '已拉黑' : '正常' }}</span></td>
          <td><button class="btn-mini" @click.stop="viewDetail(u.openid)">查看</button></td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!loading" class="sub">暂无用户。</p>

    <div class="pager" v-if="pages > 1">
      <button class="btn-mini" @click="prev" :disabled="page <= 1">上一页</button>
      <span>第 {{ page }} / {{ pages }} 页 · 共 {{ total }} 条</span>
      <button class="btn-mini" @click="next" :disabled="page >= pages">下一页</button>
    </div>
  </div>

  <div class="modal-mask" v-if="detail" @click.self="detail = null">
    <div class="modal">
      <h3>用户详情</h3>
      <div class="kv">
        <div class="k">昵称</div><div class="v">{{ detail.nickname || '—' }}</div>
        <div class="k">手机</div><div class="v">{{ detail.phone || '—' }}</div>
        <div class="k">openid</div><div class="v">{{ detail.openid }}</div>
        <div class="k">订单数</div><div class="v">{{ detail.order_count }}</div>
        <div class="k">累计消费</div><div class="v amount">¥{{ detail.total_yuan }}</div>
        <div class="k">最近下单</div><div class="v">{{ detail.last_order_at || '—' }}</div>
        <div class="k">状态</div><div class="v"><span class="badge" :class="detail.is_blocked ? 'danger' : 'ok'">{{ detail.is_blocked ? '已拉黑' : '正常' }}</span></div>
        <div class="k">备注</div><div class="v">{{ detail.note || '—' }}</div>
      </div>

      <div class="label">修改备注</div>
      <input class="neu-input" v-model="note" placeholder="备注" />

      <div class="label">近期订单</div>
      <table class="tbl" v-if="detail.recent_orders && detail.recent_orders.length">
        <thead><tr><th>订单号</th><th>套餐</th><th>金额</th><th>状态</th></tr></thead>
        <tbody>
          <tr v-for="o in detail.recent_orders" :key="o.order_no">
            <td>{{ o.order_no }}</td><td>{{ o.package_name }}</td><td>¥{{ o.amount_yuan }}</td>
            <td><span class="badge" :class="o.status">{{ o.status_label }}</span></td>
          </tr>
        </tbody>
      </table>
      <p v-else class="sub">无订单记录。</p>

      <div class="admin-actions">
        <button class="btn-mini" :disabled="acting" @click="saveNote">保存备注</button>
        <button class="btn-mini" v-if="!detail.is_blocked" :disabled="acting" @click="act('block')">拉黑</button>
        <button class="btn-mini ok" v-else :disabled="acting" @click="act('unblock')">解除拉黑</button>
        <button class="btn-mini" @click="detail = null">关闭</button>
      </div>
      <p v-if="err" class="err">{{ err }}</p>
    </div>
  </div>
</template>
