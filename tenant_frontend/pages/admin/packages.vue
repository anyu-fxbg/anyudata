<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdmin } from '~/composables/useAdmin'

definePageMeta({ layout: 'admin', middleware: 'admin' })

const admin = useAdmin()
const list = ref<any[]>([])
const loading = ref(false)
const err = ref('')
const editing = ref<any>(null)
const form = ref({ query_config_id: null, name: '', price_yuan: 0, desc: '', enabled: true, sort: 0 })

async function refresh() {
  const j: any = await admin.getPackages()
  if (j.code === 0) list.value = j.data
}
onMounted(refresh)

function newOne() {
  editing.value = 'new'
  form.value = { query_config_id: null, name: '', price_yuan: 0, desc: '', enabled: true, sort: list.value.length }
}
function editOne(p: any) {
  editing.value = p.id
  form.value = { query_config_id: p.query_config_id, name: p.name, price_yuan: p.price_yuan, desc: p.desc, enabled: p.enabled, sort: p.sort }
}
async function remove(p: any) {
  if (!confirm(`确认删除套餐「${p.name}」？`)) return
  const j: any = await admin.deletePackage(p.id)
  if (j.code === 0) refresh()
}
async function submit() {
  err.value = ''
  loading.value = true
  let j: any
  if (editing.value === 'new') j = await admin.createPackage({ ...form.value })
  else j = await admin.updatePackage(editing.value, { ...form.value })
  loading.value = false
  if (j.code === 0) { editing.value = null; refresh() }
  else err.value = j.message || '保存失败'
}
</script>

<template>
  <div class="admin-card">
    <h2>套餐管理</h2>
    <p class="sub">对客套餐：id 对应平台 QueryConfig.id，价格为你的定价（元）。</p>

    <table class="tbl" v-if="list.length">
      <thead><tr><th>ID</th><th>名称</th><th>定价(元)</th><th>启用</th><th></th></tr></thead>
      <tbody>
        <tr v-for="p in list" :key="p.id">
          <td>{{ p.query_config_id }}</td>
          <td>{{ p.name }}</td>
          <td>{{ p.price_yuan }}</td>
          <td>{{ p.enabled ? '是' : '否' }}</td>
          <td>
            <button class="btn-mini" @click="editOne(p)">编辑</button>
            <button class="btn-mini danger" style="margin-left: 6px" @click="remove(p)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else class="sub">暂无套餐，点击下方新增。</p>

    <button class="neu-btn-primary" style="margin-top: 16px" @click="newOne">新增套餐</button>

    <div v-if="editing" class="neu-inset" style="padding: 18px; margin-top: 16px">
      <div class="label">平台 QueryConfig ID</div>
      <input class="neu-input" type="number" v-model.number="form.query_config_id" placeholder="例如 1" />
      <div class="label">套餐名称</div>
      <input class="neu-input" v-model="form.name" placeholder="个人标准套餐" />
      <div class="label">定价（元）</div>
      <input class="neu-input" type="number" step="0.01" v-model.number="form.price_yuan" />
      <div class="label">描述</div>
      <input class="neu-input" v-model="form.desc" placeholder="5合1 综合报告" />
      <label class="toggle" style="margin-top: 12px">
        <input type="checkbox" v-model="form.enabled" /> 启用（C 端可见）
      </label>
      <div v-if="err" class="err">{{ err }}</div>
      <div class="admin-row" style="margin-top: 14px">
        <button class="neu-btn-primary" :disabled="loading" @click="submit">{{ loading ? '保存中…' : '保存' }}</button>
        <button class="btn-mini" style="margin-left: 8px" @click="editing = null">取消</button>
      </div>
    </div>
  </div>
</template>
