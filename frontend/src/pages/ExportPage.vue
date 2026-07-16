<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { getAllMemoriesForExport, getMemories } from '@/api'
import { formatDate, typeIcon, sentimentColor, bigTagClass, bigTagLabel } from '@/lib/utils'
import type { Memory } from '@/types'
import {
  Download,
  FileText,
  FileDown,
  Search,
  CheckSquare,
  Square,
  Loader2,
  Eye,
  X,
  Filter,
  Star,
  Calendar,
  Tag,
} from 'lucide-vue-next'

// ---- State ----
const searchQuery = ref('')
const selectedIds = ref<Set<string>>(new Set())
const exportFormat = ref<'pdf' | 'markdown'>('pdf')
const isExporting = ref(false)
const showPreview = ref(false)
const dateFrom = ref('')
const dateTo = ref('')
const tagFilter = ref('')
const favoriteOnly = ref(false)

// ---- Load memories ----
const { data: memories, isLoading } = useQuery({
  queryKey: ['export-memories'],
  queryFn: () => getAllMemoriesForExport(),
  staleTime: 60_000,
})

// ---- Computed ----
const filteredMemories = computed(() => {
  let list = memories.value || []
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(
      (m) =>
        m.title.toLowerCase().includes(q) ||
        m.content.toLowerCase().includes(q) ||
        m.tags.some((t) => t.toLowerCase().includes(q))
    )
  }
  if (dateFrom.value) {
    list = list.filter((m) => (m.createdAt || m.created_at) >= dateFrom.value)
  }
  if (dateTo.value) {
    list = list.filter((m) => (m.createdAt || m.created_at) <= dateTo.value + 'T23:59:59')
  }
  if (tagFilter.value) {
    const t = tagFilter.value.toLowerCase()
    list = list.filter((m) => m.tags.some((tag) => tag.toLowerCase().includes(t)))
  }
  if (favoriteOnly.value) {
    list = list.filter((m) => m.favorite)
  }
  return list
})

const selectedMemories = computed(() =>
  (memories.value || []).filter((m) => selectedIds.value.has(m.id))
)

const allSelected = computed(() => {
  const fl = filteredMemories.value
  return fl.length > 0 && fl.every((m) => selectedIds.value.has(m.id))
})

const allTags = computed(() => {
  const tagMap = new Map<string, number>()
  for (const m of memories.value || []) {
    for (const t of m.tags) {
      tagMap.set(t, (tagMap.get(t) || 0) + 1)
    }
  }
  return Array.from(tagMap.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 30)
})

// ---- Selection ----
function toggleSelect(id: string) {
  const s = new Set(selectedIds.value)
  s.has(id) ? s.delete(id) : s.add(id)
  selectedIds.value = s
}

function toggleSelectAll() {
  if (allSelected.value) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(filteredMemories.value.map((m) => m.id))
  }
}

function clearSelection() {
  selectedIds.value = new Set()
}

function clearFilters() {
  searchQuery.value = ''
  dateFrom.value = ''
  dateTo.value = ''
  tagFilter.value = ''
  favoriteOnly.value = false
}

// ---- Export Markdown ----
function generateMarkdown(items: Memory[]): string {
  const lines: string[] = []
  lines.push('# Pensieve 记忆导出')
  lines.push('')
  lines.push(`> 导出时间：${new Date().toLocaleString('zh-CN')}`)
  lines.push(`> 共 ${items.length} 篇记忆`)
  lines.push('')
  lines.push('---')
  lines.push('')

  for (const m of items) {
    const date = formatDate(m.createdAt || m.created_at)
    lines.push(`## ${m.title}`)
    lines.push('')
    lines.push(`📅 ${date}`)
    if (m.tags?.length) {
      lines.push(`🏷️ ${m.tags.map((t) => '`' + t + '`').join(' ')}`)
    }
    if (m.bigTag) {
      lines.push(`📂 ${bigTagLabel(m.bigTag)}`)
    }
    if (m.sentiment) {
      const sentimentLabel = m.sentiment === 'POSITIVE' ? '😊 积极' : m.sentiment === 'NEGATIVE' ? '😔 消极' : '😐 中性'
      lines.push(`💭 ${sentimentLabel}`)
    }
    lines.push('')
    lines.push(m.content)
    lines.push('')
    if (m.sourceUrl || m.source_url) {
      lines.push(`🔗 [来源链接](${m.sourceUrl || m.source_url})`)
      lines.push('')
    }
    lines.push('---')
    lines.push('')
  }
  return lines.join('\n')
}

// ---- Export PDF ----
async function generatePDF(items: Memory[]) {
  const html2pdf = (await import('html2pdf.js')).default

  const container = document.createElement('div')
  container.innerHTML = buildPDFHtml(items)

  const opt = {
    margin: [10, 12, 10, 12],
    filename: `Pensieve记忆导出_${new Date().toLocaleDateString('zh-CN').replace(/\//g, '-')}.pdf`,
    image: { type: 'jpeg', quality: 0.95 },
    html2canvas: { scale: 2, useCORS: true, letterRendering: true },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' as const },
    pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  await html2pdf().set(opt as any).from(container).save()
}

function buildPDFHtml(items: Memory[]): string {
  const memoriesHtml = items
    .map((m) => {
      const date = formatDate(m.createdAt || m.created_at)
      const tags = m.tags?.length
        ? m.tags.map((t) => `<span style="display:inline-block;padding:1px 8px;margin:2px 4px 2px 0;border-radius:12px;background:#f0f0f0;font-size:11px;color:#555;">${t}</span>`).join('')
        : ''
      const bigTag = m.bigTag ? `<span style="display:inline-block;padding:1px 8px;margin:2px 4px 2px 0;border-radius:12px;background:#e8f5e9;font-size:11px;color:#2e7d32;">${bigTagLabel(m.bigTag)}</span>` : ''
      const sentiment = m.sentiment
        ? `<span style="font-size:12px;color:${m.sentiment === 'POSITIVE' ? '#2e7d32' : m.sentiment === 'NEGATIVE' ? '#c62828' : '#666'};">${m.sentiment === 'POSITIVE' ? '😊 积极' : m.sentiment === 'NEGATIVE' ? '😔 消极' : '😐 中性'}</span>`
        : ''

      return `
        <div style="margin-bottom:24px;padding:20px;border:1px solid #e8e8e8;border-radius:10px;background:#fafafa;page-break-inside:avoid;">
          <h3 style="margin:0 0 8px 0;font-size:16px;color:#1a1a1a;">${escapeHtml(m.title)}</h3>
          <div style="margin-bottom:8px;font-size:12px;color:#888;">
            📅 ${date}
            ${sentiment ? ' · ' + sentiment : ''}
          </div>
          <div style="margin-bottom:8px;">
            ${bigTag}${tags}
          </div>
          <div style="font-size:13px;line-height:1.8;color:#333;white-space:pre-wrap;">${escapeHtml(m.content)}</div>
          ${m.sourceUrl || m.source_url ? `<div style="margin-top:8px;font-size:11px;"><a href="${escapeHtml(m.sourceUrl || m.source_url || '')}" style="color:#1976d2;text-decoration:none;">🔗 来源链接</a></div>` : ''}
        </div>
      `
    })
    .join('')

  return `
    <div style="font-family:'PingFang SC','Microsoft YaHei','Helvetica Neue',Arial,sans-serif;padding:20px;color:#1a1a1a;">
      <div style="text-align:center;margin-bottom:30px;padding-bottom:20px;border-bottom:2px solid #e8e8e8;">
        <h1 style="margin:0;font-size:24px;color:#1a1a1a;">🧠 Pensieve 记忆导出</h1>
        <p style="margin:8px 0 0;font-size:12px;color:#888;">导出时间：${new Date().toLocaleString('zh-CN')} · 共 ${items.length} 篇记忆</p>
      </div>
      ${memoriesHtml}
    </div>
  `
}

function escapeHtml(text: string): string {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

// ---- Download ----
async function handleExport() {
  const items = selectedMemories.value
  if (!items.length) return
  isExporting.value = true

  try {
    if (exportFormat.value === 'markdown') {
      const md = generateMarkdown(items)
      const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `Pensieve记忆导出_${new Date().toLocaleDateString('zh-CN').replace(/\//g, '-')}.md`
      a.click()
      URL.revokeObjectURL(url)
    } else {
      await generatePDF(items)
    }
  } finally {
    isExporting.value = false
  }
}

// ---- Preview ----
const previewContent = computed(() => {
  const items = selectedMemories.value
  if (!items.length) return ''
  if (exportFormat.value === 'markdown') {
    return generateMarkdown(items)
  }
  return buildPDFHtml(items)
})
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold tracking-tight font-display">记忆导出</h1>
        <p class="text-sm text-muted-foreground mt-1">选择记忆，导出为排版精美的 PDF 或 Markdown 文件</p>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="showPreview = true"
          :disabled="selectedMemories.length === 0"
          class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium border border-border bg-card hover:bg-accent disabled:opacity-40 transition-all duration-200"
        >
          <Eye class="w-4 h-4" />
          预览 ({{ selectedMemories.length }})
        </button>
        <button
          @click="handleExport"
          :disabled="selectedMemories.length === 0 || isExporting"
          class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-all duration-200 shadow-sm hover:shadow-md active:scale-[0.98]"
        >
          <Loader2 v-if="isExporting" class="w-4 h-4 animate-spin" />
          <Download v-else class="w-4 h-4" />
          {{ isExporting ? '导出中...' : '导出' }}
        </button>
      </div>
    </div>

    <!-- Format selector -->
    <div class="flex items-center gap-3 p-4 rounded-xl border border-border bg-card">
      <span class="text-sm font-medium text-muted-foreground">导出格式：</span>
      <button
        @click="exportFormat = 'pdf'"
        :class="[
          'inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium border-2 transition-all duration-200',
          exportFormat === 'pdf'
            ? 'border-primary bg-primary/10 text-primary shadow-sm'
            : 'border-muted bg-background text-muted-foreground hover:border-border',
        ]"
      >
        <FileDown class="w-4 h-4" />
        PDF 文档
      </button>
      <button
        @click="exportFormat = 'markdown'"
        :class="[
          'inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium border-2 transition-all duration-200',
          exportFormat === 'markdown'
            ? 'border-primary bg-primary/10 text-primary shadow-sm'
            : 'border-muted bg-background text-muted-foreground hover:border-border',
        ]"
      >
        <FileText class="w-4 h-4" />
        Markdown
      </button>
    </div>

    <!-- Filters -->
    <div class="p-4 rounded-xl border border-border bg-card space-y-3">
      <div class="flex items-center gap-2 mb-2">
        <Filter class="w-4 h-4 text-muted-foreground" />
        <span class="text-sm font-medium">筛选记忆</span>
        <button @click="clearFilters" class="ml-auto text-xs text-muted-foreground hover:text-foreground transition-colors">清除筛选</button>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div class="relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            v-model="searchQuery"
            placeholder="搜索标题、内容、标签…"
            class="w-full pl-9 pr-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring/50 focus:border-ring transition-all duration-200"
          />
        </div>
        <div class="flex items-center gap-2">
          <Calendar class="w-4 h-4 text-muted-foreground shrink-0" />
          <input
            v-model="dateFrom"
            type="date"
            class="flex-1 px-2 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring/50 transition-all duration-200"
          />
          <span class="text-muted-foreground text-xs">至</span>
          <input
            v-model="dateTo"
            type="date"
            class="flex-1 px-2 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring/50 transition-all duration-200"
          />
        </div>
        <div class="relative">
          <Tag class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            v-model="tagFilter"
            placeholder="按标签筛选"
            class="w-full pl-9 pr-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring/50 focus:border-ring transition-all duration-200"
          />
        </div>
        <button
          @click="favoriteOnly = !favoriteOnly"
          :class="[
            'inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium border transition-all duration-200',
            favoriteOnly
              ? 'bg-yellow-100 text-yellow-700 border-yellow-300 shadow-sm'
              : 'border-border bg-background text-muted-foreground hover:bg-accent',
          ]"
        >
          <Star class="w-4 h-4" :class="favoriteOnly ? 'fill-yellow-500 text-yellow-500' : ''" />
          仅收藏
        </button>
      </div>
      <!-- Quick tag pills -->
      <div v-if="allTags.length" class="flex flex-wrap gap-1.5 pt-1">
        <button
          v-for="[tag, count] in allTags"
          :key="tag"
          @click="tagFilter = tagFilter === tag ? '' : tag"
          :class="[
            'px-2.5 py-1 rounded-full text-xs font-medium transition-all duration-200',
            tagFilter === tag
              ? 'bg-primary/15 text-primary shadow-sm'
              : 'bg-secondary text-muted-foreground hover:bg-accent',
          ]"
        >
          {{ tag }} <span class="opacity-60">{{ count }}</span>
        </button>
      </div>
    </div>

    <!-- Selection bar -->
    <div class="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
      <button @click="toggleSelectAll" class="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
        <component :is="allSelected ? CheckSquare : Square" class="w-4 h-4" :class="allSelected ? 'text-primary' : ''" />
        {{ allSelected ? '取消全选' : '全选当前' }}
      </button>
      <span class="text-sm text-muted-foreground">
        已选 <span class="font-semibold text-foreground">{{ selectedMemories.length }}</span> 篇
        / 共 {{ filteredMemories.length }} 篇
      </span>
      <button v-if="selectedMemories.length > 0" @click="clearSelection" class="ml-auto text-xs text-muted-foreground hover:text-foreground transition-colors">
        清除选择
      </button>
    </div>

    <!-- Memory list -->
    <div v-if="isLoading" class="text-center py-12 text-muted-foreground">
      <Loader2 class="w-6 h-6 animate-spin inline-block mb-2" />
      <p>加载记忆中…</p>
    </div>
    <div v-else-if="filteredMemories.length === 0" class="text-center py-16 text-muted-foreground">
      没有匹配的记忆
    </div>
    <div v-else class="space-y-2">
      <div
        v-for="m in filteredMemories"
        :key="m.id"
        @click="toggleSelect(m.id)"
        :class="[
          'flex items-start gap-3 p-4 rounded-xl border cursor-pointer transition-all duration-200',
          selectedIds.has(m.id)
            ? 'border-primary bg-primary/5 shadow-sm'
            : 'border-border bg-card hover:bg-accent/50',
        ]"
      >
        <component
          :is="selectedIds.has(m.id) ? CheckSquare : Square"
          class="w-5 h-5 mt-0.5 shrink-0 transition-colors"
          :class="selectedIds.has(m.id) ? 'text-primary' : 'text-muted-foreground'"
        />
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <h3 class="font-medium text-sm truncate">{{ m.title }}</h3>
            <span v-if="m.sentiment" :class="['text-xs', sentimentColor(m.sentiment)]">
              {{ m.sentiment === 'POSITIVE' ? '积极' : m.sentiment === 'NEGATIVE' ? '消极' : '中性' }}
            </span>
            <Star v-if="m.favorite" class="w-3.5 h-3.5 fill-yellow-400 text-yellow-400 shrink-0" />
          </div>
          <p class="text-xs text-muted-foreground line-clamp-2 mb-1">{{ m.content }}</p>
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-[11px] text-muted-foreground/60">{{ formatDate(m.createdAt || m.created_at) }}</span>
            <span
              v-for="tag in m.tags.slice(0, 3)"
              :key="tag"
              class="px-1.5 py-0.5 rounded-full bg-secondary text-[10px] text-muted-foreground"
            >
              {{ tag }}
            </span>
            <span v-if="m.tags.length > 3" class="text-[10px] text-muted-foreground/50">+{{ m.tags.length - 3 }}</span>
            <span v-if="m.bigTag" :class="['px-1.5 py-0.5 rounded-full text-[10px] font-medium', bigTagClass(m.bigTag)]">
              {{ bigTagLabel(m.bigTag) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Preview modal -->
    <Teleport to="body">
      <Transition name="fade">
        <div v-if="showPreview" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="showPreview = false">
          <div class="bg-card rounded-2xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col overflow-hidden border border-border">
            <div class="flex items-center justify-between px-6 py-4 border-b border-border">
              <h2 class="font-semibold text-lg">
                导出预览
                <span class="text-sm font-normal text-muted-foreground ml-2">{{ selectedMemories.length }} 篇记忆 · {{ exportFormat === 'pdf' ? 'PDF' : 'Markdown' }}</span>
              </h2>
              <button @click="showPreview = false" class="p-1.5 rounded-lg hover:bg-accent transition-colors">
                <X class="w-5 h-5" />
              </button>
            </div>
            <div class="flex-1 overflow-y-auto p-6">
              <div v-if="exportFormat === 'markdown'" class="bg-muted rounded-lg p-4 font-mono text-xs whitespace-pre-wrap break-words leading-relaxed">{{ previewContent }}</div>
              <div v-else v-html="previewContent" class="prose prose-sm max-w-none" />
            </div>
            <div class="px-6 py-4 border-t border-border flex justify-end gap-3">
              <button @click="showPreview = false" class="px-4 py-2 rounded-lg text-sm border border-border hover:bg-accent transition-colors">关闭</button>
              <button
                @click="showPreview = false; handleExport()"
                :disabled="isExporting"
                class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-all duration-200"
              >
                <Loader2 v-if="isExporting" class="w-4 h-4 animate-spin" />
                <Download v-else class="w-4 h-4" />
                确认导出
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.fade-enter-active {
  animation: fadeIn 0.2s ease-out;
}
.fade-leave-active {
  animation: fadeOut 0.15s ease-in;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes fadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}
</style>