<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useInsightStore } from '@/stores/insight'
import { formatDate } from '@/lib/utils'
import type { EmotionCurvePoint } from '@/types'
import { ArrowLeft, CalendarDays, CalendarRange, TrendingUp, TrendingDown, Hash, FileText, Layers, Target, Loader2, Trash2 } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const insight = useInsightStore()

const reportId = computed(() => route.params.id as string)

onMounted(() => {
  if (reportId.value) {
    insight.fetchReportDetail(reportId.value)
  }
})

const report = computed(() => insight.currentReport)

// ---- 解析 JSON 字段 ----
function parseJSON<T>(str: string | null | undefined, fallback: T): T {
  if (!str) return fallback
  try {
    return JSON.parse(str)
  } catch {
    return fallback
  }
}

const emotionCurve = computed<EmotionCurvePoint[]>(() =>
  parseJSON(report.value?.emotionCurve || null, [])
)
const keywords = computed<string[]>(() =>
  parseJSON(report.value?.keywords || null, [])
)
const lowPoint = computed(() => parseJSON(report.value?.lowPoint || null, null))
const highPoint = computed(() => parseJSON(report.value?.highPoint || null, null))
const pattern = computed(() => report.value?.pattern || null)
const coreTheme = computed(() => report.value?.coreTheme || null)

const isWeekly = computed(() => report.value?.reportType === 'WEEKLY')

// ---- 情绪曲线 SVG ----
const chartWidth = 600
const chartHeight = 160
const chartPadding = { top: 20, right: 20, bottom: 30, left: 40 }

function curvePoints(): string {
  if (!emotionCurve.value.length) return ''
  const points = emotionCurve.value
  const xStep = (chartWidth - chartPadding.left - chartPadding.right) / Math.max(points.length - 1, 1)
  const yRange = chartHeight - chartPadding.top - chartPadding.bottom
  return points.map((p, i) => {
    const x = chartPadding.left + i * xStep
    const score = p.score ?? p.avgScore ?? 0
    const y = chartPadding.top + yRange - ((score + 1) / 2) * yRange
    return `${x},${y}`
  }).join(' ')
}

function curveAreaPath(): string {
  if (!emotionCurve.value.length) return ''
  const points = emotionCurve.value
  const xStep = (chartWidth - chartPadding.left - chartPadding.right) / Math.max(points.length - 1, 1)
  const yRange = chartHeight - chartPadding.top - chartPadding.bottom
  const baseline = chartPadding.top + yRange / 2
  let path = `M ${chartPadding.left},${baseline}`
  points.forEach((p, i) => {
    const x = chartPadding.left + i * xStep
    const score = p.score ?? p.avgScore ?? 0
    const y = chartPadding.top + yRange - ((score + 1) / 2) * yRange
    path += ` L ${x},${y}`
  })
  path += ` L ${chartPadding.left + (points.length - 1) * xStep},${baseline} Z`
  return path
}

function curveLabels(): { x: number; label: string }[] {
  if (!emotionCurve.value.length) return []
  const xStep = (chartWidth - chartPadding.left - chartPadding.right) / Math.max(emotionCurve.value.length - 1, 1)
  return emotionCurve.value.map((p, i) => ({
    x: chartPadding.left + i * xStep,
    label: (p.date || p.weekStart || '').slice(5),
  }))
}

// ---- 删除 ----
async function handleDelete() {
  if (!confirm('确定要删除此洞察报告吗？')) return
  const ok = await insight.doDeleteReport(reportId.value)
  if (ok) {
    router.push('/insight/archive')
  }
}

// ---- 导出 Markdown ----
function exportMarkdown() {
  if (!report.value) return
  const r = report.value
  const typeLabel = r.reportType === 'WEEKLY' ? '周报' : '月报'
  let md = `# ${typeLabel} ${r.dateStart} ~ ${r.dateEnd}\n\n`
  md += `## 摘要\n\n${r.summary}\n\n`
  if (coreTheme.value) md += `## 核心主题\n\n${coreTheme.value}\n\n`
  if (keywords.value.length) md += `## 关键词\n\n${keywords.value.map((k, i) => `${i + 1}. ${k}`).join('\n')}\n\n`
  if (highPoint.value) md += `## 高点\n\n${typeof highPoint.value === 'object' ? JSON.stringify(highPoint.value) : highPoint.value}\n\n`
  if (lowPoint.value) md += `## 低点\n\n${typeof lowPoint.value === 'object' ? JSON.stringify(lowPoint.value) : lowPoint.value}\n\n`
  if (pattern.value) md += `## 模式识别\n\n${pattern.value}\n\n`
  md += `---\n\n基于 ${r.memoryCount} 条记忆生成 · ${formatDate(r.createdAt)}\n`

  const blob = new Blob([md], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${typeLabel}_${r.dateStart}_${r.dateEnd}.md`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <!-- 顶部导航 -->
    <div class="flex items-center justify-between">
      <button @click="router.push('/insight/archive')" class="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft class="w-4 h-4" />
        返回档案
      </button>
      <div class="flex items-center gap-2">
        <button @click="exportMarkdown" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm border border-border hover:bg-accent transition-colors">
          <FileText class="w-3.5 h-3.5" />
          导出
        </button>
        <button @click="handleDelete" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm border border-red-200 dark:border-red-900 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors">
          <Trash2 class="w-3.5 h-3.5" />
          删除
        </button>
      </div>
    </div>

    <!-- 加载 -->
    <div v-if="insight.isLoading" class="flex items-center justify-center py-16">
      <Loader2 class="w-8 h-8 animate-spin text-primary" />
    </div>

    <!-- 未找到 -->
    <div v-else-if="!report" class="text-center py-16 space-y-3">
      <p class="text-muted-foreground">未找到该报告</p>
    </div>

    <!-- 报告详情 -->
    <div v-else class="space-y-6 animate-fade-in">
      <!-- 标题 -->
      <div class="flex items-center gap-3">
        <div :class="['w-10 h-10 rounded-xl flex items-center justify-center', isWeekly ? 'bg-blue-500/10' : 'bg-emerald-500/10']">
          <component :is="isWeekly ? CalendarDays : CalendarRange" :class="['w-5 h-5', isWeekly ? 'text-blue-500' : 'text-emerald-500']" />
        </div>
        <div>
          <h1 class="text-2xl font-bold tracking-tight font-display">{{ isWeekly ? '周报' : '月报' }}</h1>
          <p class="text-sm text-muted-foreground">{{ report.dateStart }} ~ {{ report.dateEnd }}</p>
        </div>
      </div>

      <!-- 摘要 -->
      <div class="p-5 rounded-xl border border-border bg-card shadow-card">
        <div class="flex items-center gap-2 mb-3">
          <FileText class="w-4 h-4 text-primary" />
          <h2 class="font-semibold text-sm text-muted-foreground">摘要</h2>
        </div>
        <p class="text-sm leading-relaxed">{{ report.summary }}</p>
      </div>

      <!-- 核心主题 (月报) -->
      <div v-if="coreTheme" class="p-5 rounded-xl border border-primary/20 bg-primary/5 shadow-card">
        <div class="flex items-center gap-2 mb-3">
          <Target class="w-4 h-4 text-primary" />
          <h2 class="font-semibold text-sm text-primary/80">核心主题</h2>
        </div>
        <p class="text-sm leading-relaxed font-medium">{{ coreTheme }}</p>
      </div>

      <!-- 情绪曲线 -->
      <div v-if="emotionCurve.length" class="p-5 rounded-xl border border-border bg-card shadow-card">
        <div class="flex items-center gap-2 mb-4">
          <TrendingUp class="w-4 h-4 text-primary" />
          <h2 class="font-semibold text-sm text-muted-foreground">情绪曲线</h2>
        </div>
        <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" class="w-full" preserveAspectRatio="xMidYMid meet">
          <line :x1="chartPadding.left" :x2="chartWidth - chartPadding.right" :y1="chartPadding.top + (chartHeight - chartPadding.top - chartPadding.bottom) / 2" :y2="chartPadding.top + (chartHeight - chartPadding.top - chartPadding.bottom) / 2" stroke="hsl(var(--border))" stroke-dasharray="4 4" />
          <path :d="curveAreaPath()" fill="hsl(var(--primary) / 0.08)" />
          <polyline :points="curvePoints()" fill="none" stroke="hsl(var(--primary))" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
          <template v-for="(p, i) in emotionCurve" :key="i">
            <circle
              :cx="chartPadding.left + i * ((chartWidth - chartPadding.left - chartPadding.right) / Math.max(emotionCurve.length - 1, 1))"
              :cy="chartPadding.top + (chartHeight - chartPadding.top - chartPadding.bottom) - (((p.score ?? p.avgScore ?? 0) + 1) / 2) * (chartHeight - chartPadding.top - chartPadding.bottom)"
              r="4" fill="hsl(var(--primary))" stroke="hsl(var(--card))" stroke-width="2"
            />
          </template>
          <template v-for="label in curveLabels()" :key="label.x">
            <text :x="label.x" :y="chartHeight - 5" text-anchor="middle" class="text-[10px] fill-muted-foreground">{{ label.label }}</text>
          </template>
        </svg>
        <div class="flex justify-between text-xs text-muted-foreground mt-1 px-10">
          <span>消极</span>
          <span>中性</span>
          <span>积极</span>
        </div>
      </div>

      <!-- 关键词 -->
      <div v-if="keywords.length" class="p-5 rounded-xl border border-border bg-card shadow-card">
        <div class="flex items-center gap-2 mb-3">
          <Hash class="w-4 h-4 text-primary" />
          <h2 class="font-semibold text-sm text-muted-foreground">TOP 关键词</h2>
        </div>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="(kw, i) in keywords"
            :key="kw"
            :class="[
              'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border transition-all',
              i < 3 ? 'bg-primary/15 text-primary border-primary/30' :
              i < 5 ? 'bg-primary/10 text-primary/80 border-primary/20' :
              'bg-secondary text-muted-foreground border-border'
            ]"
          >
            <span class="text-xs opacity-50">{{ i + 1 }}</span>
            {{ kw }}
          </span>
        </div>
      </div>

      <!-- 模式识别 (月报) -->
      <div v-if="pattern" class="p-5 rounded-xl border border-border bg-card shadow-card">
        <div class="flex items-center gap-2 mb-3">
          <Layers class="w-4 h-4 text-primary" />
          <h2 class="font-semibold text-sm text-muted-foreground">模式识别</h2>
        </div>
        <p class="text-sm leading-relaxed">{{ pattern }}</p>
      </div>

      <!-- 高低点 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-if="highPoint" class="p-5 rounded-xl border border-emerald-200 dark:border-emerald-900 bg-emerald-50/50 dark:bg-emerald-950/20 shadow-card">
          <div class="flex items-center gap-2 mb-3">
            <TrendingUp class="w-4 h-4 text-emerald-500" />
            <h2 class="font-semibold text-sm text-emerald-600 dark:text-emerald-400">{{ isWeekly ? '本周' : '月度' }}高点</h2>
          </div>
          <p class="text-sm leading-relaxed">{{ typeof highPoint === 'object' ? (highPoint as any).description || JSON.stringify(highPoint) : highPoint }}</p>
        </div>
        <div v-if="lowPoint" class="p-5 rounded-xl border border-orange-200 dark:border-orange-900 bg-orange-50/50 dark:bg-orange-950/20 shadow-card">
          <div class="flex items-center gap-2 mb-3">
            <TrendingDown class="w-4 h-4 text-orange-500" />
            <h2 class="font-semibold text-sm text-orange-600 dark:text-orange-400">{{ isWeekly ? '本周' : '月度' }}低点</h2>
          </div>
          <p class="text-sm leading-relaxed">{{ typeof lowPoint === 'object' ? (lowPoint as any).description || JSON.stringify(lowPoint) : lowPoint }}</p>
        </div>
      </div>

      <!-- 底部信息 -->
      <div class="flex items-center justify-between text-xs text-muted-foreground/60 pt-2">
        <span>基于 {{ report.memoryCount }} 条记忆生成</span>
        <span>{{ formatDate(report.createdAt) }}</span>
      </div>
    </div>
  </div>
</template>