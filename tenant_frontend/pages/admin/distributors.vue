<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAdmin } from '~/composables/useAdmin'

definePageMeta({ layout: 'admin', middleware: 'admin' })

const admin = useAdmin()
const list = ref<any[]>([])
const loading = ref(false)
const err = ref('')
const editing = ref<any>(null)
const form = ref({ code: '', name: '', contact: '', rate: 0.1, enabled: true, note: '' })
const settling = ref<number | null>(null)

// 分成比例以「百分数」展示，提交时转成 0~1 的小数
const ratePct = computed({
  get: () => Math.round((form.value.rate || 0) * 100),
  set: (v: number) => { form.value.rate = Number(v) / 100 },
})

async function refresh() {
  loading.value = true
  const j: any = await admin.getDistributors()
  loading.value = false
  if (j.code === 0) list.value = j.data
  else err.value = j.message || '加载失败'
}
onMounted(refresh)

function newOne() {
  editing.value = 'new'
  form.value = { code: '', name: '', contact: '', rate: 0.1, enabled: true, note: '' }
}
function editOne(d: any) {
  editing.value = d.id
  form.value = { code: d.code, name: d.name, contact: d.contact, rate: d.rate, enabled: d.enabled, note: d.note }
}
async function remove(d: any) {
  if (!confirm(`确认删除分销商「${d.name}」？已产生的订单记录会保留分销码但不计未结。`)) return
  const j: any = await admin.deleteDistributor(d.id)
  if (j.code === 0) refresh()
}
async function submit() {
  err.value = ''
  loading.value = true
  let j: any
  if (editing.value === 'new') j = await admin.createDistributor({ ...form.value })
  else j = await admin.updateDistributor(editing.value, { ...form.value })
  loading.value = false
  if (j.code === 0) { editing.value = null; refresh() }
  else err.value = j.message || '保存失败'
}
async function settle(d: any) {
  if (!confirm(`结算「${d.name}」的全部未结佣金 ¥${d.unsettled_yuan}？`)) return
  settling.value = d.id
  const j: any = await admin.settleDistributor(d.id, {})
  settling.value = null
  if (j.code === 0) refresh()
  else err.value = j.message || '结算失败'
}
</script>

<template>
  <div class="admin-card">
    <h2>分销管理</h2>
    <p class="sub">分销商持邀请码；C 端下单携带该码即按分成比例计佣金（未结 → 结算）。</p>

    <p v-if="err" class="err">{{ err }}</p>
    <table class="tbl" v-if="list.length">
      <thead><tr><th>名称</th><th>邀请码</th><th>分成</th><th>未结(元)</th><th>已结(元)</th><th>启用</th><th></th></tr></thead>
      <tbody>
        <tr v-for="d in list" :key="d.id">
          <td>{{ d.name }}</td>
          <td>{{ d.code }}</td>
          <td>{{ (d.rate * 100).toFixed(0) }}%</td>
          <td class="amount">¥{{ d.unsettled_yuan }}</td>
          <td>¥{{ d.settled_yuan }}</td>
          <td><span class="badge" :class="d.enabled ? 'ok' : 'muted'">{{ d.enabled ? '是' : '否' }}</span></td>
          <td>
            <button class="btn-mini" @click="editOne(d)">编辑</button>
            <button class="btn-mini" style="margin-left:6px" :disabled="!d.unsettled_fen || settling === d.id" @click="settle(d)">
              {{ settling === d.id ? '结算中' : '结算' }}
            </button>
            <button class="btn-mini danger" style="margin-left:6px" @click="remove(d)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else-if="!loading" class="sub">暂无分销商。</p>

    <button class="neu-btn-primary" style="margin-top:16px" @click="newOne">新增分销商</button>

    <div v-if="editing" class="neu-inset" style="padding:18px; margin-top:16px">
      <div class="label">邀请码</div>
      <input class="neu-input" v-model="form.code" placeholder="如 CHANNEL01（唯一）" />
      <div class="label">名称</div>
      <input class="neu-input" v-model="form.name" placeholder="分销商/渠道名" />
      <div class="label">联系方式</div>
      <input class="neu-input" v-model="form.contact" placeholder="微信 / 手机" />
      <div class="label">分成比例（%）</div>
      <input class="neu-input" type="number" step="1" min="0" max="100" v-model.number="ratePct" />
      <div class="label" style="color:#9aa5b1; margin-top:-6px">提示：直接填百分数，如 10 表示 10%</div>
      <div class="label">备注</div>
      <input class="neu-input" v-model="form.note" placeholder="可选" />
      <label class="toggle" style="margin-top:12px"><input type="checkbox" v-model="form.enabled" /> 启用</label>
      <div v-if="err" class="err">{{ err }}</div>
      <div class="admin-row" style="margin-top:14px">
        <button class="neu-btn-primary" :disabled="loading" @click="submit">{{ loading ? '保存中…' : '保存' }}</button>
        <button class="btn-mini" style="margin-left:8px" @click="editing = null">取消</button>
      </div>
    </div>
  </div>
</template>
