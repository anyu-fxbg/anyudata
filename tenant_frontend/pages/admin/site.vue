<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdmin } from '~/composables/useAdmin'

definePageMeta({ layout: 'admin', middleware: 'admin' })

const admin = useAdmin()
const form = ref({ tenant_name: '', logo_url: '', primary_color: '#6C63FF', public_base_url: '' })
const saved = ref(false)
const loading = ref(false)
const err = ref('')

onMounted(async () => {
  const j: any = await admin.getConfig()
  if (j.code === 0) {
    const d = j.data
    form.value = {
      tenant_name: d.tenant_name || '',
      logo_url: d.logo_url || '',
      primary_color: d.primary_color || '#6C63FF',
      public_base_url: d.public_base_url || '',
    }
  }
})

async function save() {
  err.value = ''
  saved.value = false
  loading.value = true
  const j: any = await admin.saveConfig({
    tenant_name: form.value.tenant_name,
    logo_url: form.value.logo_url,
    primary_color: form.value.primary_color,
    public_base_url: form.value.public_base_url,
  })
  loading.value = false
  if (j.code === 0) saved.value = true
  else err.value = j.message || '保存失败'
}
</script>

<template>
  <div class="admin-card">
    <h2>站点管理</h2>
    <p class="sub">白标信息，保存后立即在 C 端生效（无需重启）。</p>

    <div class="label">站点名称</div>
    <input class="neu-input" v-model="form.tenant_name" placeholder="例如：老王数据查询" />

    <div class="label">Logo 地址</div>
    <input class="neu-input" v-model="form.logo_url" placeholder="https://… 留空则只显示名称" />

    <div class="label">主色调</div>
    <div class="admin-row" style="align-items: center">
      <input type="color" v-model="form.primary_color" style="width: 56px; height: 44px; border: none; background: none" />
      <input class="neu-input" v-model="form.primary_color" style="flex: 1" />
    </div>

    <div class="label">对外域名（C 端访问地址）</div>
    <input class="neu-input" v-model="form.public_base_url" placeholder="https://your-domain.com" />

    <div v-if="err" class="err">{{ err }}</div>
    <div v-if="saved" class="err" style="color: #16a34a">已保存</div>
    <button class="neu-btn-primary" style="width: 100%; margin-top: 18px" :disabled="loading" @click="save">
      {{ loading ? '保存中…' : '保存' }}
    </button>
  </div>
</template>
