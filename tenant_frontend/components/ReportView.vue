<template>
  <div>
    <div v-for="s in sections" :key="s.code" class="card">
      <!-- 风险报告 DWBG8B4D -->
      <template v-if="s.code === 'DWBG8B4D' && s.item.success">
        <h3>风险报告</h3>
        <p class="muted">被查询人：{{ s.item.data.baseInfo?.name }} / {{ s.item.data.baseInfo?.idCard }}</p>
        <div v-if="s.item.data.baseInfo?.phone">手机号：{{ s.item.data.baseInfo.phone }}</div>

        <template v-if="s.item.data.riskPoint">
          <h4>风险标注</h4>
          <ul>
            <li v-for="(v, k) in s.item.data.riskPoint" :key="k" v-show="v">
              {{ riskLabel(k) }}：<b :class="v ? 'hit' : ''">{{ v ? '命中' : '正常' }}</b>
            </li>
          </ul>
        </template>

        <template v-if="s.item.data.rentalBehavior">
          <h4>租赁行为分析</h4>
          <ul>
            <li v-for="(v, k) in s.item.data.rentalBehavior" :key="k">
              {{ rentalLabel(k) }}：{{ v }}
            </li>
          </ul>
        </template>

        <template v-if="s.item.data.overdueRecord">
          <h4>逾期记录</h4>
          <div>当前逾期机构：{{ s.item.data.overdueRecord.currentOverdueInstitution }}</div>
          <div>当前逾期次数：{{ s.item.data.overdueRecord.currentOverdueCount }}</div>
        </template>
      </template>

      <!-- 个人司法涉诉 FLXG7E8F -->
      <template v-else-if="s.code === 'FLXG7E8F' && s.item.success">
        <h3>个人司法涉诉</h3>
        <div v-for="(p, i) in (s.item.data.lawsuit_company_info?.data || [])" :key="i">
          <p class="muted">被查询主体：{{ p.id }}</p>
          <h4>失信被执行人（{{ (p.sx?.sxbzxr_current || []).length }}）</h4>
          <div v-for="(c, j) in (p.sx?.sxbzxr_current || [])" :key="j" class="case">
            <div>案号：{{ c.ah }}　法院：{{ c.zxfy }}</div>
            <div>立案：{{ c.larq }}　履行情况：{{ c.lxqk }}</div>
            <div v-if="c.yw" class="doc">生效文书确定义务：{{ c.yw }}</div>
          </div>
          <h4>限制高消费（{{ (p.lh?.lhbzxr_current || []).length }}）</h4>
          <div v-for="(c, j) in (p.lh?.lhbzxr_current || [])" :key="j" class="case">
            <div>案号：{{ c.ah }}　法院：{{ c.zxfy }}</div>
          </div>
          <h4>案件分类统计</h4>
          <div v-for="(v, k) in (p.detail || {})" :key="k">
            {{ caseTypeLabel(k) }}：{{ v.count ?? (v.cases ? v.cases.length : 0) }} 起
          </div>
        </div>
      </template>

      <!-- 婚姻状况 IVYZ81NC -->
      <template v-else-if="s.code === 'IVYZ81NC' && s.item.success">
        <h3>婚姻状况</h3>
        <div class="badge" :style="{ background: s.marriage.badgeBg, color: s.marriage.badgeColor, borderColor: s.marriage.badgeColor }">
          <span class="badge-code">{{ s.marriage.code }}</span>
          <span class="badge-text">{{ s.marriage.subtitle }}</span>
        </div>
        <div v-if="s.marriage.opDate" class="kv">登记日期：<b>{{ s.marriage.opDate }}</b></div>
        <div v-if="s.item.data.op_type_desc" class="kv muted">状态说明：{{ s.item.data.op_type_desc }}</div>
        <p class="m-desc">{{ s.marriage.desc }}</p>
      </template>

      <!-- 名下车辆 QCXG9P1C -->
      <template v-else-if="s.code === 'QCXG9P1C' && s.item.success">
        <h3>车辆信息</h3>
        <div class="kv">名下车辆：<b>{{ s.vehicle.count }}</b> 辆</div>
        <div v-for="(veh, i) in s.vehicle.list" :key="i" class="veh" :style="{ borderColor: veh.bd }">
          <div class="veh-plate" :style="{ background: veh.bg, color: veh.c, borderColor: veh.bd }">{{ veh.plateNum }}</div>
          <div class="veh-meta">
            <span>车牌颜色：{{ veh.plateColorText }}</span>
            <span>车辆类型：{{ veh.vehicleTypeText }}</span>
          </div>
        </div>
        <p v-if="!s.vehicle.count" class="m-desc">未查询到名下登记车辆。</p>
        <p class="m-desc note">本信息基于交管部门权威数据，包含车牌号、车牌颜色、车辆类型等核心信息，仅供参考。</p>
      </template>

      <!-- 个人信用分 IVYZRAX1 -->
      <template v-else-if="s.code === 'IVYZRAX1' && s.item.success">
        <h3>信用分</h3>
        <div class="credit">
          <div class="credit-top">
            <div class="credit-score" :style="{ color: s.credit.scoreColor }">{{ s.credit.score }}</div>
            <div class="credit-badge" :style="{ background: s.credit.badgeBg, color: s.credit.badgeColor }">{{ s.credit.level }}</div>
          </div>
          <div class="credit-bar"><div class="credit-fill" :style="{ width: s.credit.pct + '%', background: s.credit.bar }"></div></div>
          <p class="m-desc">{{ s.credit.desc }}</p>
          <div class="credit-dims">
            <div v-for="(d, i) in s.credit.dims" :key="i" class="credit-dim">
              <div class="dim-t">{{ d.title }}</div>
              <div class="dim-d">{{ d.desc }}</div>
            </div>
          </div>
        </div>
      </template>

      <!-- 兜底：未知接口原始 JSON -->
      <template v-else>
        <h3>{{ s.code }}</h3>
        <pre class="raw">{{ JSON.stringify(s.item, null, 2) }}</pre>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ report: Record<string, any> }>()

const riskLabel = (k: string) => ({
  multiQuery: '多头申请', riskList: '风险名单', judicialRisk: '司法风险',
  securityRisk: '安全风险', legalCasesFlag: '司法涉案', executionCasesFlag: '执行案件',
  disinCasesFlag: '失信被执行', limitCasesFlag: '限制高消费',
}[k] || k)

const rentalLabel = (k: string) =>
  k.replace('rentalApplicationInstitutions', '申请机构数(近')
   .replace('rentalApplicationCount', '申请次数(近')
   .replace('Last3Days', '3天)').replace('Last7Days', '7天)')
   .replace('Last14Days', '14天)').replace('Last1Month', '1月)')
   .replace('Last3Months', '3月)').replace('Last6Months', '6月)')
   .replace('Night', '-夜间').replace('Weekend', '-周末') || k

const caseTypeLabel = (k: string) => ({
  preservation: '财产保全', civil: '民事', administrative: '行政',
  criminal: '刑事', implement: '执行', bankrupt: '破产',
}[k] || k)

const MARRIAGE_IA = {
  code: 'IA', subtitle: '查询到婚姻登记记录', color: '#C0392B',
  badgeBg: '#F7D5D8', badgeColor: '#C0392B',
  desc: 'IA 状态表示查询到婚姻登记记录（结婚），但婚姻状况可能已发生变化，数据存在延迟，请以民政部门最新记录为准。',
}
const MARRIAGE_IB = {
  code: 'IB', subtitle: '查询到离婚记录', color: '#1E7A4A',
  badgeBg: '#DCEBDD', badgeColor: '#1E7A4A',
  desc: 'IB 状态表示查询到离婚记录，但婚姻状况可能已发生变化，数据存在延迟，请以民政部门最新记录为准。',
}
const MARRIAGE_INR = {
  code: 'INR', subtitle: '未查询到婚姻登记记录', color: '#3B5BDB',
  badgeBg: '#D6DFF8', badgeColor: '#3B5BDB',
  desc: 'INR 状态表示未查询到婚姻登记记录，但可能已结婚但数据未更新，建议过段时间重试或以民政部门最新记录为准。',
}
function marriageInfo(opType: string) {
  const t = (opType || '').toUpperCase()
  if (t === 'IA' || t === 'ICA') return MARRIAGE_IA
  if (t === 'IB') return MARRIAGE_IB
  return MARRIAGE_INR
}

const PLATE_COLOR: Record<number, any> = {
  0: { t: '蓝底白字', bg: '#D6DFF8', bd: '#8FA3E8', c: '#3B5BDB' },
  1: { t: '黄底黑字', bg: '#F3E5C8', bd: '#E0C882', c: '#A97400' },
  2: { t: '黑底白字', bg: '#E5EAEF', bd: '#8A94A6', c: '#333333' },
  3: { t: '白底黑字', bg: '#FFFFFF', bd: '#B8C2D0', c: '#333333' },
  4: { t: '渐变绿', bg: '#DCEBDD', bd: '#9CCBA4', c: '#1E7A4A' },
  5: { t: '黄绿双拼', bg: '#F3E5C8', bd: '#9CCBA4', c: '#1E7A4A' },
  6: { t: '蓝白渐变', bg: '#D6DFF8', bd: '#8FA3E8', c: '#3B5BDB' },
  7: { t: '临时牌照', bg: '#F3E5C8', bd: '#E0C882', c: '#A97400' },
  11: { t: '绿色', bg: '#DCEBDD', bd: '#7FB98A', c: '#1E7A4A' },
  12: { t: '红色', bg: '#F7D5D8', bd: '#E3A8AC', c: '#C0392B' },
}
const VEHICLE_TYPE: Record<number, string> = {
  1: '一型客车', 2: '二型客车', 3: '三型客车', 4: '四型客车',
  11: '一型货车', 12: '二型货车', 13: '三型货车', 14: '四型货车', 15: '五型货车', 16: '六型货车',
  21: '一型专项作业车', 22: '二型专项作业车', 23: '三型专项作业车', 24: '四型专项作业车', 25: '五型专项作业车', 26: '六型专项作业车',
}
function extractVehicle(data: any) {
  const count = (data && data.vehicleCount) || 0
  const list = ((data && data.list) || []).map((v: any) => {
    const pc = PLATE_COLOR[v.plateColor] || { t: '未知', bg: '#E5EAEF', bd: '#B8C2D0', c: '#5D6673' }
    return {
      plateNum: v.plateNum || '—',
      bg: pc.bg, bd: pc.bd, c: pc.c, plateColorText: pc.t,
      vehicleTypeText: VEHICLE_TYPE[v.vehicleType] || '未知类型',
    }
  })
  return { count, list }
}

function extractCredit(data: any) {
  const raw = data && data.scoreywbase
  const score = raw != null ? parseInt(raw, 10) : null
  const pct = score != null ? Math.max(0, Math.min(100, ((score - 300) / 700) * 100)) : 0
  let info: any
  if (score == null) {
    info = { level: '无评分', scoreColor: '#5D6673', bar: '#9AA5B1', badgeBg: '#E5EAEF', badgeColor: '#5D6673', desc: '当前客户未匹配上该模型依赖的数据产品，无法生成有效评分。' }
  } else if (score >= 800) {
    info = { level: '信用优秀', scoreColor: '#1E7A4A', bar: '#1E7A4A', badgeBg: '#DCEBDD', badgeColor: '#1E7A4A', desc: '该用户信用评分较高，违约概率极低。信用历史良好，履约能力强，属于优质客户群体。' }
  } else if (score >= 650) {
    info = { level: '信用良好', scoreColor: '#3B5BDB', bar: '#3B5BDB', badgeBg: '#D6DFF8', badgeColor: '#3B5BDB', desc: '该用户信用评分处于良好水平，违约概率较低。信用记录基本良好，具备较好的还款能力和意愿。' }
  } else if (score >= 500) {
    info = { level: '信用一般', scoreColor: '#A97400', bar: '#A97400', badgeBg: '#F3E5C8', badgeColor: '#A97400', desc: '该用户信用评分处于中等水平，存在一定违约风险。建议结合其他风控手段综合评估，审慎授信。' }
  } else {
    info = { level: '信用较差', scoreColor: '#C0392B', bar: '#C0392B', badgeBg: '#F7D5D8', badgeColor: '#C0392B', desc: '该用户信用评分较低，违约概率较高。建议谨慎处理信贷申请，必要时要求增加担保或共同借款人。' }
  }
  const dims = [
    { title: '基础身份信息', desc: '年龄、职业、收入稳定性等' },
    { title: '信用历史', desc: '信贷记录、逾期次数、负债等' },
    { title: '行为数据', desc: '消费习惯、社交关系等' },
    { title: '外部数据验证', desc: '运营商、电商、公共记录等' },
  ]
  return {
    score: score != null ? score : '--', pct: pct.toFixed(0), level: info.level,
    scoreColor: info.scoreColor, bar: info.bar, badgeBg: info.badgeBg,
    badgeColor: info.badgeColor, desc: info.desc, dims,
  }
}

// 报告卡片展示顺序：婚姻状况 → 信用分 → 车辆信息 → 风险报告 → 个人司法涉诉
const SECTION_ORDER: Record<string, number> = {
  IVYZ81NC: 1, // 婚姻状况
  IVYZRAX1: 2, // 信用分
  QCXG9P1C: 3, // 车辆信息
  DWBG8B4D: 4, // 风险报告
  FLXG7E8F: 5, // 个人司法涉诉
}

const sections = computed(() => Object.entries(props.report || {}).map(([code, item]) => {
  const data = (item && item.data) || {}
  return {
    code,
    item,
    marriage: code === 'IVYZ81NC' ? { ...marriageInfo(data.op_type), opDate: data.op_date || '' } : null,
    vehicle: code === 'QCXG9P1C' ? extractVehicle(data) : null,
    credit: code === 'IVYZRAX1' ? extractCredit(data) : null,
  }
}).sort((a, b) => {
  const oa = SECTION_ORDER[a.code] ?? 99
  const ob = SECTION_ORDER[b.code] ?? 99
  return oa - ob
}))
</script>

<style scoped>
.card { border: 1px solid #eef0f3; border-radius: 12px; padding: 16px; margin-bottom: 14px; background: #fff; }
.case { border-left: 3px solid #f59e0b; padding: 6px 10px; margin: 6px 0; background: #fffbeb; }
.doc { color: #92400e; font-size: 12px; margin-top: 4px; }
.hit { color: #dc2626; }
.raw { font-size: 11px; max-height: 200px; overflow: auto; }
h4 { margin: 12px 0 4px; color: #374151; }
.muted { color: #6b7280; font-size: 13px; }
.kv { font-size: 14px; margin: 6px 0; }
.m-desc { color: #4b5563; font-size: 13px; line-height: 1.7; margin: 10px 0 0; }
.note { color: #6b7280; font-size: 12px; }
.badge { display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 999px; border: 1px solid; font-weight: 600; margin: 4px 0 8px; }
.badge-code { font-weight: 800; letter-spacing: 1px; }
.badge-text { font-size: 14px; }
.veh { display: flex; align-items: center; gap: 12px; padding: 10px; border: 1px solid; border-radius: 10px; margin: 8px 0; background: #fafbfc; }
.veh-plate { font-weight: 800; font-size: 16px; letter-spacing: 1px; padding: 6px 12px; border: 2px solid; border-radius: 6px; min-width: 92px; text-align: center; }
.veh-meta { display: flex; flex-direction: column; gap: 2px; font-size: 13px; color: #374151; }
.credit { background: #fafbfc; border: 1px solid #eef0f3; border-radius: 12px; padding: 16px; }
.credit-top { display: flex; align-items: baseline; gap: 14px; }
.credit-score { font-size: 44px; font-weight: 800; line-height: 1; }
.credit-badge { padding: 4px 12px; border-radius: 999px; font-weight: 600; font-size: 13px; }
.credit-bar { height: 10px; border-radius: 999px; background: #eef0f3; margin: 12px 0; overflow: hidden; }
.credit-fill { height: 100%; border-radius: 999px; transition: width .3s; }
.credit-dims { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-top: 10px; }
.credit-dim { background: #fff; border: 1px solid #eef0f3; border-radius: 8px; padding: 8px 10px; }
.dim-t { font-weight: 600; font-size: 13px; color: #374151; }
.dim-d { font-size: 12px; color: #6b7280; margin-top: 2px; }
</style>
