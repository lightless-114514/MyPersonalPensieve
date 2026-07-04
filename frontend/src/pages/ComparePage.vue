<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { getMemories, compareMemories } from '@/api'
import { formatDate, typeIcon, sentimentColor, bigTagClass, bigTagLabel } from '@/lib/utils'
import type { CompareResult, BigTagCategory } from '@/types'
import {
  GitCompare, ArrowRight, Loader2, Check, X, Search,
  Calendar, Tag, TrendingUp, Lightbulb, ChevronDown, ChevronUp,
  Sparkles, ArrowLeftRight, Users, User, Copy, CheckCircle2,
} from 'lucide-vue-next'

// ---- 对比模式 ----
type CompareMode = '1v1' | '1vN' | 'Nv1' | 'NvN'
const mode = ref<CompareMode>('1v1')

const modeConfig: Record<CompareMode, { label: string; icon: typeof User; sourceMax: number; targetMax: number; desc: string }> = {
  '1v1': { label: '一对一', icon: User, sourceMax: 1, targetMax: 1, desc: '对比两条记忆' },
  '1vN': { label: '一对多', icon: ArrowRight, sourceMax: 1, targetMax: 99, desc: '一条与多条对比' },
  'Nv1': { label: '多对一', icon: ArrowLeftRight, sourceMax: 99, targetMax: 1, desc: '多条与一条对比' },
  'NvN': { label: '多对多', icon: Users, sourceMax: 99, targetMax: 99, desc: '两组记忆对比' },
}

// ---- 记忆选择 ----
const sourceIds = ref<string[]>([])
const targetIds = ref<string[]>([])
const searchQuery = ref('')
const sourceSearch = ref('')
const targetSearch = ref('')
const showSourcePicker = ref(false)
const showTargetPicker = ref(false)

// ---- 对比结果 ----
const compareResult = ref<CompareResult | null>(null)
const isComparing = ref(false)
const errorMsg = ref('')

// ---- 分页 ----
const page = ref(0)
const { data, isLoading } = useQuery({
  queryKey: ['memories', page, false],
  queryFn: () => getMemories({ page: page.value, size: 50 }),
})

const allMemories = computed(() => data.value?.content ?? [])

const filteredSourceMemories = computed(() => {
  const q = sourceSearch.value.toLowerCase()
  return allMemories.value.filter((m: any) => {
    if (sourceIds.value.includes(m.id)) return false
    if (!q) return true
    return m.title.toLowerCase().includes(q) || m.content?.toLowerCase().includes(q)
  })
})

const filteredTargetMemories = computed(() => {
  const q = targetSearch.value.toLowerCase()
  return allMemories.value.filter((m: any) => {
    if (targetIds.value.includes(m.id)) return false
    if (sourceIds.value.includes(m.id)) return false
    if (!q) return true
    return m.title.toLowerCase().includes(q) || m.content?.toLowerCase().includes(q)
  })
})

const selectedSourceMemories = computed(() =>
  allMemories.value.filter((m: any) => sourceIds.value.includes(m.id))
)

const selectedTargetMemories = computed(() =>
  allMemories.value.filter((m: any) => targetIds.value.includes(m.id))
)

function addSource(id: string) {
  const cfg = modeConfig[mode.value]
  if (sourceIds.value.length >= cfg.sourceMax && cfg.sourceMax < 99) return
  if (!sourceIds.value.includes(id) && !targetIds.value.includes(id)) {
    sourceIds.value.push(id)
  }
  if (cfg.sourceMax === 1) showSourcePicker.value = false
}

function addTarget(id: string) {
  const cfg = modeConfig[mode.value]
  if (targetIds.value.length >= cfg.targetMax && cfg.targetMax < 99) return
  if (!targetIds.value.includes(id) && !sourceIds.value.includes(id)) {
    targetIds.value.push(id)
  }
  if (cfg.targetMax === 1) showTargetPicker.value = false
}

function removeSource(id: string) {
  sourceIds.value = sourceIds.value.filter(i => i !== id)
}

function removeTarget(id: string) {
  targetIds.value = targetIds.value.filter(i => i !== id)
}

// 切换模式时清空选择
watch(mode, () => {
  sourceIds.value = []
  targetIds.value = []
  compareResult.value = null
  errorMsg.value = ''
})

const canCompare = computed(() => sourceIds.value.length > 0 && targetIds.value.length > 0)

// ---- 执行对比 ----
async function doCompare() {
  if (!canCompare.value) return
  isComparing.value = true
  errorMsg.value = ''
  compareResult.value = null
  try {
    const result = await compareMemories(sourceIds.value, targetIds.value)
    compareResult.value = result
  } catch (e: any) {
    errorMsg.value = e?.response?.data?.detail || e?.message || '对比失败，请重试'
  } finally {
    isComparing.value = false
  }
}

// ---- 展开/收起 ----
const showSimilarities = ref(true)
const showDifferences = ref(true)
const showInsight = ref(true)

// ---- 复制结果 ----
const copied = ref(false)
function copyResult() {
  if (!compareResult.value) return
  const r = compareResult.value
  let text = `📊 记忆对比分析\n`
  text += `时间跨度：${r.earliestDate || '?'} → ${r.latestDate || '?'}（${r.timeSpanDays ?? '?'}天）\n`
  text += `源记忆：${r.sourceCount}条 | 目标记忆：${r.targetCount}条\n\n`
  text += `✅ 相同点：\n`
  r.similarities.forEach((s, i) => { text += `  ${i + 1}. ${s.content}\n` })
  text += `\n🔄 变化点：\n`
  r.differences.forEach((d, i) => { text += `  ${i + 1}. ${d.content}\n` })
  if (r.growthInsight) text += `\n💡 成长洞察：${r.growthInsight}\n`
  navigator.clipboard.writeText(text)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}

function resetCompare() {
  sourceIds.value = []
  targetIds.value = []
  compareResult.value = null
  errorMsg.value = ''
}
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
          <GitCompare class="w-5 h-5 text-primary" />
        </div>
        <div>
          <h1 class="text-2xl font-bold tracking-tight font-display">记忆对比</h1>
          <p class="text-xs text-muted-foreground">选取记忆，AI 分析相同点与变化点，洞察成长轨迹</p>
        </div>
      </div>
      <button
        v-if="compareResult"
        @click="resetCompare"
        class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm border border-border bg-card text-muted-foreground hover:bg-accent hover:text-foreground transition-all duration-200"
      >
        <X class="w-4 h-4" />
        重新选择
      </button>
    </div>

    <!-- 对比模式选择 -->
    <div v-if="!compareResult" class="p-5 rounded-xl border border-border bg-card shadow-card space-y-4">
      <h2 class="text-sm font-semibold text-muted-foreground uppercase tracking-wider">选择对比模式</h2>
      <div class="grid grid-cols-4 gap-3">
        <button
          v-for="(cfg, key) in modeConfig"
          :key="key"
          @click="mode = key as CompareMode"
          :class="[
            'flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all duration-200',
            mode === key
              ? 'border-primary bg-primary/5 shadow-sm scale-[1.02]'
              : 'border-border bg-background hover:border-primary/30 hover:bg-accent/50'
          ]"
        >
          <component :is="cfg.icon" class="w-5 h-5" :class="mode === key ? 'text-primary' : 'text-muted-foreground'" />
          <span class="text-sm font-medium" :class="mode === key ? 'text-primary' : 'text-foreground'">{{ cfg.label }}</span>
          <span class="text-[10px] text-muted-foreground">{{ cfg.desc }}</span>
        </button>
      </div>
    </div>

    <!-- 记忆选择区域 -->
    <div v-if="!compareResult" class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- 源记忆（左侧） -->
      <div class="p-5 rounded-xl border border-border bg-card shadow-card space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-semibold flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-blue-500"></span>
            源记忆 <span class="text-xs text-muted-foreground font-normal">({{ sourceIds.length }}条)</span>
          </h3>
          <button
            @click="showSourcePicker = !showSourcePicker"
            class="text-xs px-2 py-1 rounded-md border border-border hover:bg-accent transition-colors"
          >
            {{ showSourcePicker ? '收起' : '添加' }}
          </button>
        </div>

        <!-- 已选源记忆 -->
        <div v-if="selectedSourceMemories.length" class="space-y-2">
          <div
            v-for="m in selectedSourceMemories"
            :key="m.id"
            class="flex items-start gap-2 p-2.5 rounded-lg bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800"
          >
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium truncate">{{ m.title }}</p>
              <p class="text-xs text-muted-foreground truncate">{{ m.content?.slice(0, 60) }}</p>
            </div>
            <button @click="removeSource(m.id)" class="shrink-0 p-1 rounded-md hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors">
              <X class="w-3.5 h-3.5 text-muted-foreground" />
            </button>
          </div>
        </div>
        <div v-else class="py-6 text-center text-sm text-muted-foreground">
          点击"添加"选择源记忆
        </div>

        <!-- 源记忆选择器 -->
        <Transition name="slide">
          <div v-if="showSourcePicker" class="space-y-2 border-t border-border pt-3">
            <div class="relative">
              <Search class="absolute left-2.5 top-2.5 w-4 h-4 text-muted-foreground" />
              <input
                v-model="sourceSearch"
                placeholder="搜索记忆..."
                class="w-full pl-8 pr-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring/50"
              />
            </div>
            <div class="max-h-48 overflow-y-auto space-y-1">
              <button
                v-for="m in filteredSourceMemories.slice(0, 20)"
                :key="m.id"
                @click="addSource(m.id)"
                class="w-full text-left p-2.5 rounded-lg hover:bg-accent transition-colors group"
              >
                <div class="flex items-start gap-2">
                  <component :is="typeIcon(m.type)" class="w-4 h-4 text-muted-foreground shrink-0 mt-0.5" />
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium truncate group-hover:text-primary transition-colors">{{ m.title }}</p>
                    <p class="text-xs text-muted-foreground truncate">{{ m.content?.slice(0, 50) }}</p>
                  </div>
                  <span class="text-[10px] text-muted-foreground shrink-0">{{ formatDate(m.createdAt || '') }}</span>
                </div>
              </button>
              <div v-if="!filteredSourceMemories.length" class="py-4 text-center text-sm text-muted-foreground">
                暂无可选记忆
              </div>
            </div>
          </div>
        </Transition>
      </div>

      <!-- 目标记忆（右侧） -->
      <div class="p-5 rounded-xl border border-border bg-card shadow-card space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-semibold flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
            目标记忆 <span class="text-xs text-muted-foreground font-normal">({{ targetIds.length }}条)</span>
          </h3>
          <button
            @click="showTargetPicker = !showTargetPicker"
            class="text-xs px-2 py-1 rounded-md border border-border hover:bg-accent transition-colors"
          >
            {{ showTargetPicker ? '收起' : '添加' }}
          </button>
        </div>

        <!-- 已选目标记忆 -->
        <div v-if="selectedTargetMemories.length" class="space-y-2">
          <div
            v-for="m in selectedTargetMemories"
            :key="m.id"
            class="flex items-start gap-2 p-2.5 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800"
          >
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium truncate">{{ m.title }}</p>
              <p class="text-xs text-muted-foreground truncate">{{ m.content?.slice(0, 60) }}</p>
            </div>
            <button @click="removeTarget(m.id)" class="shrink-0 p-1 rounded-md hover:bg-emerald-100 dark:hover:bg-emerald-900/50 transition-colors">
              <X class="w-3.5 h-3.5 text-muted-foreground" />
            </button>
          </div>
        </div>
        <div v-else class="py-6 text-center text-sm text-muted-foreground">
          点击"添加"选择目标记忆
        </div>

        <!-- 目标记忆选择器 -->
        <Transition name="slide">
          <div v-if="showTargetPicker" class="space-y-2 border-t border-border pt-3">
            <div class="relative">
              <Search class="absolute left-2.5 top-2.5 w-4 h-4 text-muted-foreground" />
              <input
                v-model="targetSearch"
                placeholder="搜索记忆..."
                class="w-full pl-8 pr-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring/50"
              />
            </div>
            <div class="max-h-48 overflow-y-auto space-y-1">
              <button
                v-for="m in filteredTargetMemories.slice(0, 20)"
                :key="m.id"
                @click="addTarget(m.id)"
                class="w-full text-left p-2.5 rounded-lg hover:bg-accent transition-colors group"
              >
                <div class="flex items-start gap-2">
                  <component :is="typeIcon(m.type)" class="w-4 h-4 text-muted-foreground shrink-0 mt-0.5" />
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium truncate group-hover:text-primary transition-colors">{{ m.title }}</p>
                    <p class="text-xs text-muted-foreground truncate">{{ m.content?.slice(0, 50) }}</p>
                  </div>
                  <span class="text-[10px] text-muted-foreground shrink-0">{{ formatDate(m.createdAt || '') }}</span>
                </div>
              </button>
              <div v-if="!filteredTargetMemories.length" class="py-4 text-center text-sm text-muted-foreground">
                暂无可选记忆
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <!-- 开始对比按钮 -->
    <div v-if="!compareResult" class="flex justify-center">
      <button
        @click="doCompare"
        :disabled="!canCompare || isComparing"
        class="inline-flex items-center gap-2 px-8 py-3 bg-primary text-primary-foreground rounded-xl text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-all duration-200 shadow-sm hover:shadow-md active:scale-[0.98]"
      >
        <Loader2 v-if="isComparing" class="w-4 h-4 animate-spin" />
        <Sparkles v-else class="w-4 h-4" />
        {{ isComparing ? 'AI 分析中...' : '开始对比分析' }}
      </button>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMsg" class="p-4 rounded-xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-950/30 text-sm text-red-700 dark:text-red-300">
      {{ errorMsg }}
    </div>

    <!-- 加载中 -->
    <div v-if="isComparing" class="text-center py-16 space-y-4">
      <div class="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto animate-pulse">
        <Sparkles class="w-8 h-8 text-primary" />
      </div>
      <p class="text-muted-foreground">AI 正在深度分析记忆对比...</p>
      <p class="text-xs text-muted-foreground/60">这可能需要几秒钟</p>
    </div>

    <!-- 对比结果 -->
    <div v-if="compareResult && !isComparing" class="space-y-5 animate-fade-in">
      <!-- 结果头部 - 时间跨度与统计 -->
      <div class="p-5 rounded-xl border border-border bg-card shadow-card">
        <div class="flex items-start justify-between gap-4">
          <div class="space-y-3 flex-1">
            <div class="flex items-center gap-2">
              <GitCompare class="w-5 h-5 text-primary" />
              <h2 class="text-lg font-bold font-display">对比分析结果</h2>
            </div>
            <div class="flex flex-wrap gap-4 text-sm">
              <div class="flex items-center gap-1.5 text-muted-foreground">
                <Calendar class="w-4 h-4" />
                <span v-if="compareResult.timeSpanDays !== null" class="font-medium text-foreground">{{ compareResult.timeSpanDays }}</span>
                <span>天跨度</span>
              </div>
              <div class="flex items-center gap-1.5 text-muted-foreground">
                <span class="text-xs">{{ compareResult.earliestDate || '?' }}</span>
                <ArrowRight class="w-3 h-3" />
                <span class="text-xs">{{ compareResult.latestDate || '?' }}</span>
              </div>
              <div class="flex items-center gap-1.5 text-muted-foreground">
                <span class="w-2 h-2 rounded-full bg-blue-500"></span>
                源 {{ compareResult.sourceCount }}条
              </div>
              <div class="flex items-center gap-1.5 text-muted-foreground">
                <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                目标 {{ compareResult.targetCount }}条
              </div>
            </div>
            <!-- 标签对比 -->
            <div v-if="compareResult.sourceTags.length || compareResult.targetTags.length" class="flex flex-wrap gap-3">
              <div v-if="compareResult.sourceTags.length" class="flex items-center gap-1.5 flex-wrap">
                <Tag class="w-3.5 h-3.5 text-blue-500" />
                <span
                  v-for="tag in compareResult.sourceTags.slice(0, 5)"
                  :key="tag"
                  class="px-1.5 py-0.5 rounded-md bg-blue-100 dark:bg-blue-900/40 text-xs text-blue-700 dark:text-blue-300"
                >{{ tag }}</span>
              </div>
              <div v-if="compareResult.targetTags.length" class="flex items-center gap-1.5 flex-wrap">
                <Tag class="w-3.5 h-3.5 text-emerald-500" />
                <span
                  v-for="tag in compareResult.targetTags.slice(0, 5)"
                  :key="tag"
                  class="px-1.5 py-0.5 rounded-md bg-emerald-100 dark:bg-emerald-900/40 text-xs text-emerald-700 dark:text-emerald-300"
                >{{ tag }}</span>
              </div>
            </div>
          </div>
          <!-- 复制按钮 -->
          <button
            @click="copyResult"
            class="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs border border-border hover:bg-accent transition-colors"
          >
            <CheckCircle2 v-if="copied" class="w-3.5 h-3.5 text-emerald-500" />
            <Copy v-else class="w-3.5 h-3.5" />
            {{ copied ? '已复制' : '复制结果' }}
          </button>
        </div>
        <!-- 概要 -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
          <div class="p-3 rounded-lg bg-blue-50/50 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900/50">
            <p class="text-[10px] font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wider mb-1">源概要</p>
            <p class="text-sm text-foreground">{{ compareResult.sourceSummary || '—' }}</p>
          </div>
          <div class="p-3 rounded-lg bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/50">
            <p class="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider mb-1">目标概要</p>
            <p class="text-sm text-foreground">{{ compareResult.targetSummary || '—' }}</p>
          </div>
        </div>
      </div>

      <!-- 相同点 -->
      <div class="rounded-xl border border-border bg-card shadow-card overflow-hidden">
        <button
          @click="showSimilarities = !showSimilarities"
          class="w-full flex items-center justify-between p-5 hover:bg-accent/30 transition-colors"
        >
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center">
              <Check class="w-4 h-4 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 class="font-semibold font-display">相同点</h3>
            <span class="px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/40 text-xs text-blue-700 dark:text-blue-300 font-medium">
              {{ compareResult.similarities.length }}
            </span>
          </div>
          <ChevronDown v-if="!showSimilarities" class="w-5 h-5 text-muted-foreground" />
          <ChevronUp v-else class="w-5 h-5 text-muted-foreground" />
        </button>
        <Transition name="slide">
          <div v-if="showSimilarities" class="px-5 pb-5 space-y-3">
            <div
              v-for="(item, idx) in compareResult.similarities"
              :key="idx"
              class="p-4 rounded-lg bg-blue-50/30 dark:bg-blue-950/10 border border-blue-100/50 dark:border-blue-900/30"
            >
              <div class="flex gap-3">
                <span class="shrink-0 w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/50 flex items-center justify-center text-xs font-bold text-blue-600 dark:text-blue-400">
                  {{ idx + 1 }}
                </span>
                <div class="flex-1 min-w-0">
                  <p class="text-sm leading-relaxed">{{ item.content }}</p>
                  <div v-if="item.sourceRefs?.length || item.targetRefs?.length" class="mt-2 flex flex-wrap gap-1.5">
                    <span
                      v-for="ref in (item.sourceRefs || [])"
                      :key="'s-' + ref"
                      class="px-1.5 py-0.5 rounded bg-blue-100/50 dark:bg-blue-900/30 text-[10px] text-blue-600 dark:text-blue-400"
                    >{{ ref }}</span>
                    <span
                      v-for="ref in (item.targetRefs || [])"
                      :key="'t-' + ref"
                      class="px-1.5 py-0.5 rounded bg-emerald-100/50 dark:bg-emerald-900/30 text-[10px] text-emerald-600 dark:text-emerald-400"
                    >{{ ref }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="!compareResult.similarities.length" class="py-4 text-center text-sm text-muted-foreground">
              未发现明显相同点
            </div>
          </div>
        </Transition>
      </div>

      <!-- 变化点 -->
      <div class="rounded-xl border border-border bg-card shadow-card overflow-hidden">
        <button
          @click="showDifferences = !showDifferences"
          class="w-full flex items-center justify-between p-5 hover:bg-accent/30 transition-colors"
        >
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center">
              <TrendingUp class="w-4 h-4 text-amber-600 dark:text-amber-400" />
            </div>
            <h3 class="font-semibold font-display">变化点</h3>
            <span class="px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/40 text-xs text-amber-700 dark:text-amber-300 font-medium">
              {{ compareResult.differences.length }}
            </span>
          </div>
          <ChevronDown v-if="!showDifferences" class="w-5 h-5 text-muted-foreground" />
          <ChevronUp v-else class="w-5 h-5 text-muted-foreground" />
        </button>
        <Transition name="slide">
          <div v-if="showDifferences" class="px-5 pb-5 space-y-3">
            <div
              v-for="(item, idx) in compareResult.differences"
              :key="idx"
              class="p-4 rounded-lg bg-amber-50/30 dark:bg-amber-950/10 border border-amber-100/50 dark:border-amber-900/30"
            >
              <div class="flex gap-3">
                <span class="shrink-0 w-6 h-6 rounded-full bg-amber-100 dark:bg-amber-900/50 flex items-center justify-center text-xs font-bold text-amber-600 dark:text-amber-400">
                  {{ idx + 1 }}
                </span>
                <div class="flex-1 min-w-0">
                  <p class="text-sm leading-relaxed">{{ item.content }}</p>
                  <div v-if="item.sourceRefs?.length || item.targetRefs?.length" class="mt-2 flex flex-wrap gap-1.5">
                    <span
                      v-for="ref in (item.sourceRefs || [])"
                      :key="'s-' + ref"
                      class="px-1.5 py-0.5 rounded bg-blue-100/50 dark:bg-blue-900/30 text-[10px] text-blue-600 dark:text-blue-400"
                    >{{ ref }}</span>
                    <span
                      v-for="ref in (item.targetRefs || [])"
                      :key="'t-' + ref"
                      class="px-1.5 py-0.5 rounded bg-emerald-100/50 dark:bg-emerald-900/30 text-[10px] text-emerald-600 dark:text-emerald-400"
                    >{{ ref }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="!compareResult.differences.length" class="py-4 text-center text-sm text-muted-foreground">
              未发现明显变化点
            </div>
          </div>
        </Transition>
      </div>

      <!-- 成长洞察 -->
      <div v-if="compareResult.growthInsight" class="rounded-xl border border-primary/20 bg-primary/5 shadow-card overflow-hidden">
        <button
          @click="showInsight = !showInsight"
          class="w-full flex items-center justify-between p-5 hover:bg-primary/10 transition-colors"
        >
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <Lightbulb class="w-4 h-4 text-primary" />
            </div>
            <h3 class="font-semibold font-display">成长洞察</h3>
          </div>
          <ChevronDown v-if="!showInsight" class="w-5 h-5 text-muted-foreground" />
          <ChevronUp v-else class="w-5 h-5 text-muted-foreground" />
        </button>
        <Transition name="slide">
          <div v-if="showInsight" class="px-5 pb-5">
            <div class="p-4 rounded-lg bg-primary/5 border border-primary/10">
              <p class="text-sm leading-relaxed">{{ compareResult.growthInsight }}</p>
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!compareResult && !isComparing && !errorMsg && allMemories.length === 0 && !isLoading" class="text-center py-16 text-muted-foreground">
      <p>暂无记忆可供对比，请先记录一些记忆</p>
    </div>
  </div>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease;
  overflow: hidden;
}
.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
}
.slide-enter-to,
.slide-leave-from {
  opacity: 1;
  max-height: 600px;
}

.animate-fade-in {
  animation: fadeIn 0.4s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>