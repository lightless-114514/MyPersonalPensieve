<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useBirthdayStore } from '@/stores/birthday'
import { useQuery } from '@tanstack/vue-query'
import { getMemories } from '@/api'
import type { Memory } from '@/types'
import { Calendar, X, BookOpen } from 'lucide-vue-next'

const birthdayStore = useBirthdayStore()
const dismissed = ref(false)

/** 计算去年今日的日期范围 */
const lastYearRange = computed(() => {
  const today = new Date()
  const lastYear = today.getFullYear() - 1
  const month = String(today.getMonth() + 1).padStart(2, '0')
  const day = String(today.getDate()).padStart(2, '0')
  const dateStr = `${lastYear}-${month}-${day}`
  return dateStr
})

/** 获取日记列表，筛选去年今日的日记 */
const { data: memoriesData, isLoading } = useQuery({
  queryKey: ['birthday-memories-review'],
  queryFn: () => getMemories({ page: 0, size: 50 }),
  enabled: computed(() => birthdayStore.isBirthdayToday && birthdayStore.showMemoryReview && !dismissed.value),
})

/** 去年今日的日记 */
const lastYearMemories = computed(() => {
  if (!memoriesData.value?.content) return []
  const targetDate = lastYearRange.value
  return (memoriesData.value.content as Memory[]).filter((m: Memory) => {
    const createdDate = (m.createdAt || m.created_at || '').slice(0, 10)
    return createdDate === targetDate
  })
})

/** 最早年份的今日日记（如果去年没有的话） */
const earliestYearMemories = computed(() => {
  if (lastYearMemories.value.length > 0) return []
  if (!memoriesData.value?.content) return []
  const today = new Date()
  const month = today.getMonth() + 1
  const day = today.getDate()
  const allMemories = memoriesData.value.content as Memory[]
  // 找所有月日匹配的日记
  const matched = allMemories.filter((m: Memory) => {
    const d = new Date(m.createdAt || m.created_at || '')
    return d.getMonth() + 1 === month && d.getDate() === day && d.getFullYear() < today.getFullYear()
  })
  // 按年份分组，取最早的
  if (matched.length === 0) return []
  matched.sort((a: Memory, b: Memory) => {
    const da = new Date(a.createdAt || a.created_at || '')
    const db = new Date(b.createdAt || b.created_at || '')
    return da.getTime() - db.getTime()
  })
  // 返回最早年份的日记
  const earliestYear = new Date(matched[0].createdAt || matched[0].created_at || '').getFullYear()
  return matched.filter((m: Memory) => {
    return new Date(m.createdAt || m.created_at || '').getFullYear() === earliestYear
  })
})

const hasMemories = computed(() => lastYearMemories.value.length > 0 || earliestYearMemories.value.length > 0)
const displayMemories = computed(() => lastYearMemories.value.length > 0 ? lastYearMemories.value : earliestYearMemories.value)
const displayYear = computed(() => {
  if (displayMemories.value.length === 0) return ''
  const d = new Date(displayMemories.value[0].createdAt || displayMemories.value[0].created_at || '')
  return d.getFullYear().toString()
})

function dismiss() {
  dismissed.value = true
}
</script>

<template>
  <Transition name="memory-review">
    <div
      v-if="birthdayStore.isBirthdayToday && birthdayStore.showMemoryReview && !dismissed"
      class="rounded-xl border border-border bg-card p-5 shadow-card"
    >
      <!-- 标题栏 -->
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          <Calendar class="w-4 h-4 text-primary" />
          <h3 class="text-sm font-semibold font-display">去年的今天</h3>
        </div>
        <button
          @click="dismiss"
          class="p-1 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- 加载中 -->
      <div v-if="isLoading" class="text-sm text-muted-foreground py-4 text-center">
        回忆加载中...
      </div>

      <!-- 有日记 -->
      <div v-else-if="hasMemories" class="space-y-3">
        <p class="text-xs text-muted-foreground mb-2">
          {{ displayYear }}年的今天，你在记录这些 📖
        </p>
        <div
          v-for="m in displayMemories.slice(0, 3)"
          :key="m.id"
          class="p-3 rounded-lg bg-accent/30 border border-border/50"
        >
          <router-link :to="`/memories/${m.id}`" class="block group">
            <h4 class="text-sm font-medium group-hover:text-primary transition-colors truncate">
              {{ m.title }}
            </h4>
            <p class="text-xs text-muted-foreground line-clamp-2 mt-1">
              {{ m.content?.slice(0, 100) }}
            </p>
          </router-link>
        </div>
        <p v-if="displayMemories.length > 3" class="text-xs text-muted-foreground text-center">
          还有 {{ displayMemories.length - 3 }} 条记忆...
        </p>
      </div>

      <!-- 无日记 -->
      <div v-else class="text-center py-4">
        <BookOpen class="w-8 h-8 text-muted-foreground/30 mx-auto mb-2" />
        <p class="text-sm text-muted-foreground">
          去年的今天，你在做什么呢？📖
        </p>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.memory-review-enter-active {
  animation: reviewIn 0.5s ease-out;
}
.memory-review-leave-active {
  animation: reviewOut 0.3s ease-in;
}

@keyframes reviewIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes reviewOut {
  from { opacity: 1; transform: translateY(0); }
  to { opacity: 0; transform: translateY(10px); }
}
</style>