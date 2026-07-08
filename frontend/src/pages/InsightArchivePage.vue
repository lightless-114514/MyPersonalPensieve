<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useInsightStore } from '@/stores/insight'
import { formatDate } from '@/lib/utils'
import type { InsightReportListItem } from '@/types'
import { Archive, CalendarDays, CalendarRange, Trash2, ChevronRight, Loader2, Eye } from 'lucide-vue-next'

const router = useRouter()
const insight = useInsightStore()

const page = ref(0)
const pageSize = 20

onMounted(() => {
  insight.fetchArchive(page.value, pageSize)
})

const totalPages = computed(() => Math.ceil(insight.archiveTotal / pageSize))

function reportTypeLabel(type: string): string {
  return type === 'WEEKLY' ? '周报' : '月报'
}

function reportTypeIcon(type: string) {
  return type === 'WEEKLY' ? CalendarDays : CalendarRange
}

function reportTypeClass(type: string): string {
  return type === 'WEEKLY'
    ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20'
    : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
}

function formatDateRange(item: InsightReportListItem): string {
  const start = item.dateStart.slice(5)
  const end = item.dateEnd.slice(5)
  return `${start} ~ ${end}`
}

function goToDetail(id: string) {
  router.push(`/insight/archive/${id}`)
}

async function handleDelete(e: Event, id: string) {
  e.stopPropagation()
  if (!confirm('确定要删除此洞察报告吗？')) return
  await insight.doDeleteReport(id)
}

function prevPage() {
  if (page.value > 0) {
    page.value--
    insight.fetchArchive(page.value, pageSize)
  }
}

function nextPage() {
  if (page.value < totalPages.value - 1) {
    page.value++
    insight.fetchArchive(page.value, pageSize)
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <!-- 标题栏 -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center">
          <Archive class="w-5 h-5 text-red-500" />
        </div>
        <h1 class="text-2xl font-bold tracking-tight font-display">洞察档案</h1>
      </div>
      <span class="text-sm text-muted-foreground">共 {{ insight.archiveTotal }} 份报告</span>
    </div>

    <!-- 加载状态 -->
    <div v-if="insight.isLoading && !insight.archiveItems.length" class="flex items-center justify-center py-16">
      <Loader2 class="w-8 h-8 animate-spin text-primary" />
    </div>

    <!-- 空状态 -->
    <div v-else-if="!insight.archiveItems.length" class="text-center py-16 space-y-3">
      <Archive class="w-12 h-12 text-muted-foreground/30 mx-auto" />
      <p class="text-muted-foreground">暂无洞察报告</p>
      <p class="text-sm text-muted-foreground/70">生成周报或月报后，报告将自动归档在此</p>
    </div>

    <!-- 档案列表 -->
    <div v-else class="space-y-3">
      <div
        v-for="item in insight.archiveItems"
        :key="item.id"
        @click="goToDetail(item.id)"
        class="group block p-4 rounded-xl border border-border bg-card hover:bg-accent/50 transition-all duration-200 cursor-pointer shadow-card hover:shadow-card-hover relative"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1.5">
              <!-- 类型标签 -->
              <span :class="['inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium border', reportTypeClass(item.reportType)]">
                <component :is="reportTypeIcon(item.reportType)" class="w-3 h-3" />
                {{ reportTypeLabel(item.reportType) }}
              </span>
              <!-- 未读标记 -->
              <span v-if="!item.isRead" class="w-2 h-2 rounded-full bg-red-500 shrink-0" title="未读" />
              <!-- 日期范围 -->
              <span class="text-xs text-muted-foreground">{{ formatDateRange(item) }}</span>
            </div>
            <p class="text-sm text-muted-foreground line-clamp-2">{{ item.summary }}</p>
            <div class="flex items-center gap-3 mt-2 text-xs text-muted-foreground/60">
              <span>{{ item.memoryCount }} 条记忆</span>
              <span>{{ formatDate(item.createdAt) }}</span>
            </div>
          </div>
          <div class="flex items-center gap-1 shrink-0">
            <button
              @click="handleDelete($event, item.id)"
              class="p-2 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-100 dark:hover:bg-red-950/30 text-muted-foreground hover:text-red-500 transition-all"
              title="删除"
            >
              <Trash2 class="w-4 h-4" />
            </button>
            <ChevronRight class="w-4 h-4 text-muted-foreground/40 group-hover:text-muted-foreground transition-colors" />
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 pt-4">
      <button :disabled="page === 0" @click="prevPage" class="px-3 py-1.5 rounded-lg text-sm border border-border hover:bg-accent disabled:opacity-50 transition-all duration-200">上一页</button>
      <span class="text-sm text-muted-foreground tabular-nums">{{ page + 1 }} / {{ totalPages }}</span>
      <button :disabled="page >= totalPages - 1" @click="nextPage" class="px-3 py-1.5 rounded-lg text-sm border border-border hover:bg-accent disabled:opacity-50 transition-all duration-200">下一页</button>
    </div>
  </div>
</template>