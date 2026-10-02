<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useApi } from '~/composables/useApi'
import { useRoute } from 'vue-router'
import ReportView from '~/components/ReportView.vue'

const { get } = useApi()
const route = useRoute()
const orderNo = (route.params.orderNo as string) || ''
const status = ref('')
const report = ref<any>(null)
const subject = ref<any>({})

function poll() {
  get('/order/' + orderNo + '/report/').then((r: any) => {
    if (r.code === 0) {
      status.value = r.data.status
      if (r.data.report) {
        report.value = r.data.report
        subject.value = r.data
      }
    }
    if (status.value !== 'done') setTimeout(poll, 1500)
  })
}
onMounted(poll)
</script>

<template>
  <div class="page">
    <div class="neu" style="padding: 18px">
      <div v-if="status !== 'done'" class="status-pill">查询中（{{ status || '…' }}），请稍候…</div>
      <template v-else>
        <h2 style="margin: 0 0 4px">查询报告</h2>
        <p class="muted" style="font-size: 13px">被查询人：{{ subject.subject_name }} / {{ subject.subject_id_card }}</p>
        <ReportView :report="report" />
      </template>
    </div>
  </div>
</template>

<style scoped>
.muted { color: #6b7280; }
</style>
