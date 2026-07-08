<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useInsightStore } from '@/stores/insight'
import { formatDate } from '@/lib/utils'
import type { EmotionCurvePoint, KeywordPoint } from '@/types'
import { CalendarRange, Loader2, TrendingUp, TrendingDown, Hash, FileText, Layers, Target } from 'lucide-vue-next'

const insight = useInsightStore()

// ---- 月选择器 ----
function getMonthStart(date: Date): string {
  return date.toISOString().slice(0, 7) + '-01'
}

function getMonthLabel(monthStart: string): string {
  const d = new Date(monthStart)
  return `${d.getFullYear()}年${d.getMonth() + 1}月`
}

function getMonthEnd(monthStart: string): string {
  const d = new Date(monthStart)
  const lastDay = new Date(d.getFullYear(), d.getMonth() + 1, 0)
  return lastDay.toISOString().slice(0, 10)
}

const currentMonthStart = ref(getMonthStart(new Date()))

function prevMonth() {
  const d = new Date(currentMonthStart.value)
  d.setMonth(d.getMonth() - 1)
  currentMonthStart.value = getMonthStart(d)
}

function nextMonth() {
  const d = new Date(currentMonthStart.value)
  d.setMonth(d.getMonth() + 1)
  const next = getMonthStart(d)
  if (next <= getMonthStart(new Date())) {
    currentMonthStart.value = next
  }
}

const isCurrentMonth = computed(() => currentMonthStart.value === getMonthStart(new Date()))

// ---- 数据加载 ----
async function loadMonthData() {
  await insight.fetchMonthlyReport(currentMonthStart.value)
}

onMounted(() => {
  loadMonthData()
})

watch(currentMonthStart, () => {
  loadMonthData()
})

// ---- 生成月报 ----
async function handleGenerate() {
  const ok = await insight.doGenerateMonthly(currentMonthStart.value)
  if (ok) {
    await loadMonthData()
  }
}

// ---- 解析 JSON 字段 ----
function parseJSON<T>(str: string | null | undefined, fallback: T): T {
  if (!str) return fallback
  try {
    return JSON.parse(str)
  } catch {
    return fallback
  }
}

const report = computed(() => insight.currentReport)
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

function weekLabels(): { x: number; label: string }[] {
  if (!emotionCurve.value.length) return []
  const xStep = (chartWidth - chartPadding.left - chartPadding.right) / Math.max(emotionCurve.value.length - 1, 1)
  return emotionCurve.value.map((p, i) => ({
    x: chartPadding.left + i * xStep,
    label: (p.weekStart || p.date || '').slice(5),
  }))
}
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <!-- 标题栏 -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
          <CalendarRange class="w-5 h-5 text-emerald-500" />
        </div>
        <h1 class="text-2xl font-bold tracking-tight font-display">月报</h1>
      </div>
    </div>

    <!-- 月选择器 -->
    <div class="flex items-center justify-center gap-4 p-4 rounded-xl border border-border bg-card">
      <button @click="prevMonth" class="p-2 rounded-lg hover:bg-accent transition-colors text-muted-foreground hover:text-foreground">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
      </button>
      <span class="text-sm font-medium min-w-[120px] text-center">{{ getMonthLabel(currentMonthStart) }}</span>
      <button @click="nextMonth" :disabled="isCurrentMonth" class="p-2 rounded-lg hover:bg-accent transition-colors text-muted-foreground hover:text-foreground disabled:opacity-30">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
      </button>
    </div>

    <!-- 操作 -->
    <div class="flex items-center gap-3">
      <div v-if="report" class="flex items-center gap-2 text-sm text-muted-foreground">
        <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
        已生成 · {{ report.memoryCount }} 条记忆
      </div>
      <div class="flex-1"></div>
      <button
        @click="handleGenerate"
        :disabled="insight.isGenerating"
        class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-all shadow-sm hover:shadow-md active:scale-[0.98]"
      >
        <Loader2 v-if="insight.isGenerating" class="w-4 h-4 animate-spin" />
        <CalendarRange v-else class="w-4 h-4" />
        {{ insight.isGenerating ? '生成中...' : (report ? '重新生成' : '生成月报') }}
      </button>
    </div>

    <!-- 错误提示 -->
    <div v-if="insight.error" class="p-4 rounded-xl border border-red-200 bg-red-50 dark:bg-red-950/20 dark:border-red-900 text-red-700 dark:text-red-400 text-sm">
      {{ insight.error }}
    </div>

    <!-- 加载状态 -->
    <div v-if="insight.isLoading" class="flex items-center justify-center py-16">
      <Loader2 class="w-8 h-8 animate-spin text-primary" />
    </div>

    <!-- 无报告 -->
    <div v-else-if="!report && !insight.isGenerating" class="text-center py-16 space-y-3">
      <CalendarRange class="w-12 h-12 text-muted-foreground/30 mx-auto" />
      <p class="text-muted-foreground">本月暂无月报</p>
      <p class="text-sm text-muted-foreground/70">点击「生成月报」按钮，基于本月日记生成深度洞察分析</p>
    </div>

    <!-- 报告内容 -->
    <div v-else-if="report" class="space-y-6 animate-fade-in">
      <!-- 摘要 -->
      <div class="p-5 rounded-xl border border-border bg-card shadow-card">
        <div class="flex items-center gap-2 mb-3">
          <FileText class="w-4 h-4 text-primary" />
          <h2 class="font-semibold text-sm text-muted-foreground">月度摘要</h2>
        </div>
        <p class="text-sm leading-relaxed">{{ report.summary }}</p>
      </div>

      <!-- 核心主题 -->
      <div v-if="coreTheme" class="p-5 rounded-xl border border-primary/20 bg-primary/5 shadow-card">
        <div class="flex items-center gap-2 mb-3">
          <Target class="w-4 h-4 text-primary" />
          <h2 class="font-semibold text-sm text-primary/80">核心主题</h2>
        </div>
        <p class="text-sm leading-relaxed font-medium">{{ coreTheme }}</p>
      </div>

      <!-- 情绪趋势 -->
      <div v-if="emotionCurve.length" class="p-5 rounded-xl border border-border bg-card shadow-card">
        <div class="flex items-center gap-2 mb-4">
          <TrendingUp class="w-4 h-4 text-primary" />
          <h2 class="font-semibold text-sm text-muted-foreground">月度情绪趋势</h2>
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
          <template v-for="label in weekLabels()" :key="label.x">
            <text :x="label.x" :y="chartHeight - 5" text-anchor="middle" class="text-[10px] fill-muted-foreground">{{ label.label }}</text>
          </template>
        </svg>
        <div class="flex justify-between text-xs text-muted-foreground mt-1 px-10">
          <span>消极</span>
          <span>中性</span>
          <span>积极</span>
        </div>
      </div>

      <!-- 关键词 TOP10 -->
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

      <!-- 模式识别 -->
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
            <h2 class="font-semibold text-sm text-emerald-600 dark:text-emerald-400">月度高点</h2>
          </div>
          <p class="text-sm leading-relaxed">{{ typeof highPoint === 'object' ? (highPoint as any).description || JSON.stringify(highPoint) : highPoint }}</p>
        </div>
        <div v-if="lowPoint" class="p-5 rounded-xl border border-orange-200 dark:border-orange-900 bg-orange-50/50 dark:bg-orange-950/20 shadow-card">
          <div class="flex items-center gap-2 mb-3">
            <TrendingDown class="w-4 h-4 text-orange-500" />
            <h2 class="font-semibold text-sm text-orange-600 dark:text-orange-400">月度低点</h2>
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