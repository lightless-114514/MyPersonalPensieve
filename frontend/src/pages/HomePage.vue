<script setup lang="ts">
import { computed, ref } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { getRecentMemories, getHeatmap, getWordCloud, getStats } from '@/api'
import { formatDate, typeIcon, bigTagClass, bigTagLabel } from '@/lib/utils'
import { Brain, ArrowRight, Activity, Tag } from 'lucide-vue-next'
import { useGreeting } from '@/composables/useGreeting'
import { useBirthdayStore } from '@/stores/birthday'
import HeatmapChart from '@/components/HeatmapChart.vue'
import WordCloudChart from '@/components/WordCloudChart.vue'
import StatsCards from '@/components/StatsCards.vue'
import BirthdayWishCard from '@/components/BirthdayWishCard.vue'
import BirthdayMemoryReview from '@/components/BirthdayMemoryReview.vue'
import BirthdayWish from '@/components/BirthdayWish.vue'
import BirthdayReminder from '@/components/BirthdayReminder.vue'
import CapsuleNotification from '@/components/CapsuleNotification.vue'
import { useRouter } from 'vue-router'
import { getFilePreviewUrl } from '@/api'

const router = useRouter()
const birthdayStore = useBirthdayStore()

const { data: memories, isLoading } = useQuery({
  queryKey: ['recent-memories'],
  queryFn: () => getRecentMemories(10),
})

const { data: heatmapData } = useQuery({
  queryKey: ['heatmap'],
  queryFn: () => getHeatmap(),
})

const wordCloudPeriod = ref<'month' | 'year'>('month')
const { data: wordCloudData } = useQuery({
  queryKey: computed(() => ['wordcloud', wordCloudPeriod.value]),
  queryFn: () => getWordCloud(wordCloudPeriod.value),
})

const { data: stats } = useQuery({
  queryKey: ['stats'],
  queryFn: () => getStats(),
})

const hasMemories = computed(() => (memories.value?.length ?? 0) > 0)
const { greeting } = useGreeting()

function handleWordClick(word: string) {
  router.push(`/memories?q=${encodeURIComponent(word)}`)
}
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-8">
    <!-- Hero -->
    <div class="text-center py-10 animate-fade-in">
      <div class="w-20 h-20 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-5 animate-breathe">
        <Brain class="w-10 h-10 text-primary" />
      </div>
      <h1 class="text-3xl font-bold mb-2 tracking-tight font-display">{{ greeting }}</h1>
      <div class="w-12 h-0.5 bg-primary/40 rounded-full mx-auto mb-4"></div>
      <p class="text-muted-foreground max-w-md mx-auto leading-relaxed">
        存储文字、截图、语音、链接。用自然语言查询你的过去。
      </p>
      <router-link
        to="/memories?new=true"
        class="inline-flex items-center gap-2 mt-6 px-6 py-3 bg-primary text-primary-foreground rounded-xl font-medium hover:bg-primary/90 transition-all duration-200 shadow-sm hover:shadow-md active:scale-[0.98]"
      >
        {{ hasMemories ? '记录新的记忆' : '记录第一条记忆' }}
        <ArrowRight class="w-4 h-4" />
      </router-link>
    </div>

    <!-- 生日提醒条 -->
    <BirthdayReminder />

    <!-- 时间胶囊到期通知 -->
    <CapsuleNotification />

    <!-- 生日专属区域 -->
    <div v-if="birthdayStore.isBirthdayToday" class="space-y-4 animate-fade-in">
      <!-- AI祝福卡 -->
      <BirthdayWishCard v-if="birthdayStore.showAiWish" />
      <!-- 记忆回顾 -->
      <BirthdayMemoryReview v-if="birthdayStore.showMemoryReview" />
      <!-- 愿望清单 -->
      <BirthdayWish />
    </div>

    <!-- Stats Cards -->
    <div class="animate-fade-in">
      <StatsCards :stats="stats ?? null" />
    </div>

    <!-- Heatmap -->
    <div class="rounded-xl border border-border bg-card p-4 shadow-card animate-fade-in">
      <div class="flex items-center gap-2 mb-2">
        <Activity class="w-4 h-4 text-primary" />
        <h2 class="text-sm font-semibold">写作热力图</h2>
      </div>
      <HeatmapChart :data="heatmapData ?? []" />
      <div v-if="!heatmapData?.length" class="flex items-center justify-center h-24 text-muted-foreground text-sm">
        暂无写作数据
      </div>
    </div>

    <!-- Word Cloud -->
    <div class="rounded-xl border border-border bg-card p-4 shadow-card animate-fade-in">
      <WordCloudChart :data="wordCloudData ?? []" v-model="wordCloudPeriod" @click-word="handleWordClick">
        <template #header>
          <div class="flex items-center gap-2">
            <Tag class="w-4 h-4 text-primary" />
            <h2 class="text-sm font-semibold">词汇云图</h2>
          </div>
        </template>
      </WordCloudChart>
    </div>

    <!-- Recent memories -->
    <div v-if="memories?.length">
      <h2 class="text-lg font-semibold mb-4">最近的记忆</h2>
      <div class="grid gap-3">
        <router-link
          v-for="(m, index) in memories"
          :key="m.id"
          :to="`/memories/${m.id}`"
          class="block p-4 rounded-xl border border-border bg-card hover:bg-accent/50 transition-all duration-200 relative group shadow-card hover:shadow-card-hover animate-slide-up"
          :style="{ animationDelay: `${index * 50}ms` }"
        >
          <!-- Big tag badge -->
          <div
            v-if="m.bigTag"
            :class="[
              'absolute -top-0.5 -left-0.5 inline-flex items-center gap-1 px-2 py-0.5 rounded-br-lg rounded-tl-lg text-xs font-semibold border',
              bigTagClass(m.bigTag)
            ]"
          >
            {{ bigTagLabel(m.bigTag) }}
          </div>

          <div class="flex items-start justify-between gap-3">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <component :is="typeIcon(m.type)" class="w-4 h-4 text-muted-foreground shrink-0" />
                <h3 class="font-medium truncate group-hover:text-primary transition-colors duration-200">{{ m.title }}</h3>
              </div>
              <p class="text-sm text-muted-foreground line-clamp-2">{{ m.content }}</p>
            </div>
            <!-- 图片缩略图 -->
            <div v-if="m.type === 'IMAGE' && m.filePath" class="shrink-0">
              <img :src="getFilePreviewUrl(m.id)" :alt="m.title" class="w-12 h-12 object-cover rounded-lg border border-border" />
            </div>
            <!-- 文件类型图标 -->
            <div v-else-if="m.type === 'FILE'" class="shrink-0 w-10 h-10 flex items-center justify-center rounded-lg bg-accent/50 border border-border">
              <component :is="typeIcon(m.type)" class="w-5 h-5 text-muted-foreground" />
            </div>
            <span class="text-xs text-muted-foreground shrink-0">{{ formatDate(m.createdAt || '') }}</span>
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
    <div v-else-if="!isLoading" class="text-center py-16 animate-fade-in">
      <p class="text-muted-foreground">还没有记忆。开始记录你的第一条吧</p>
    </div>

    <div v-else class="text-center py-12 text-muted-foreground animate-fade-in">加载中...</div>
  </div>
</template>