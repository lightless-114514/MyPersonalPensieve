<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { getRecentMemories } from '@/api'
import { formatDate, typeIcon, sentimentColor } from '@/lib/utils'
import { Brain, ArrowRight } from 'lucide-vue-next'

const { data: memories, isLoading } = useQuery({
  queryKey: ['recent-memories'],
  queryFn: () => getRecentMemories(10),
})
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-8">
    <!-- Hero -->
    <div class="text-center py-12">
      <Brain class="w-16 h-16 text-primary mx-auto mb-4" />
      <h1 class="text-3xl font-bold mb-2">你的第二大脑</h1>
      <p class="text-muted-foreground max-w-md mx-auto">
        存储文字、截图、语音、链接。用自然语言查询你的过去。
      </p>
      <router-link
        to="/memories?new=true"
        class="inline-flex items-center gap-2 mt-6 px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors"
      >
        记录第一条记忆
        <ArrowRight class="w-4 h-4" />
      </router-link>
    </div>

    <!-- Recent memories -->
    <div v-if="memories?.length">
      <h2 class="text-lg font-semibold mb-4">最近的记忆</h2>
      <div class="grid gap-3">
        <router-link
          v-for="m in memories"
          :key="m.id"
          :to="`/memories/${m.id}`"
          class="block p-4 rounded-lg border border-border bg-card hover:bg-accent/50 transition-colors"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span>{{ typeIcon(m.type) }}</span>
                <h3 class="font-medium truncate">{{ m.title }}</h3>
              </div>
              <p class="text-sm text-muted-foreground line-clamp-2">{{ m.content }}</p>
            </div>
            <span class="text-xs text-muted-foreground shrink-0">{{ formatDate(m.createdAt) }}</span>
          </div>
          <div class="flex gap-2 mt-2" v-if="m.tags?.length">
            <span
              v-for="tag in m.tags"
              :key="tag"
              class="px-2 py-0.5 rounded-full bg-secondary text-xs text-muted-foreground"
            >
              {{ tag }}
            </span>
          </div>
        </router-link>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else-if="!isLoading" class="text-center py-16">
      <p class="text-muted-foreground">还没有记忆。开始记录你的第一条吧 ✨</p>
    </div>

    <div v-else class="text-center py-12 text-muted-foreground">加载中...</div>
  </div>
</template>