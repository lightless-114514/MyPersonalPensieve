<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { getMemory, deleteMemory } from '@/api'
import { formatDate, typeIcon, sentimentColor, sentimentBg, bigTagClass, bigTagLabel } from '@/lib/utils'
import { ArrowLeft, Trash2, ExternalLink } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const queryClient = useQueryClient()

const { data: memory, isLoading } = useQuery({
  queryKey: ['memory', route.params.id],
  queryFn: () => getMemory(route.params.id as string),
})

const deleteMutation = useMutation({
  mutationFn: () => deleteMemory(route.params.id as string),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['memories'] })
    router.push('/memories')
  },
})
</script>

<template>
  <div class="max-w-3xl mx-auto space-y-6">
    <!-- Back -->
    <button
      @click="router.back()"
      class="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
    >
      <ArrowLeft class="w-4 h-4" />
      返回
    </button>

    <div v-if="isLoading" class="text-center py-12 text-muted-foreground">加载中...</div>

    <div v-else-if="memory" class="space-y-6">
      <!-- Header -->
      <div class="space-y-3">
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-center gap-2">
            <span class="text-2xl">{{ typeIcon(memory.type) }}</span>
            <h1 class="text-2xl font-bold">{{ memory.title }}</h1>
          </div>
          <button
            @click="deleteMutation.mutate()"
            class="p-2 rounded-lg text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-colors"
          >
            <Trash2 class="w-4 h-4" />
          </button>
        </div>

        <div class="flex items-center gap-3 text-sm text-muted-foreground">
          <span>{{ formatDate(memory.createdAt) }}</span>

          <!-- Big tag badge -->
          <span
            v-if="memory.bigTag"
            :class="[
              'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border',
              bigTagClass(memory.bigTag)
            ]"
          >
            {{ bigTagLabel(memory.bigTag) }}
          </span>

          <span v-if="memory.sentiment" :class="['px-2 py-0.5 rounded-full text-xs font-medium', sentimentColor(memory.sentiment), sentimentBg(memory.sentiment)]">
            {{ memory.sentiment === 'POSITIVE' ? '😊 积极' : memory.sentiment === 'NEGATIVE' ? '😔 消极' : '😐 中性' }}
          </span>
        </div>
      </div>

      <!-- Source link -->
      <div v-if="memory.sourceUrl" class="p-3 rounded-lg bg-accent/50">
        <a
          :href="memory.sourceUrl"
          target="_blank"
          class="inline-flex items-center gap-1 text-sm text-primary hover:underline"
        >
          <ExternalLink class="w-3 h-3" />
          {{ memory.sourceUrl }}
        </a>
      </div>

      <!-- Content -->
      <div class="p-6 rounded-lg border border-border bg-card">
        <p class="whitespace-pre-wrap leading-relaxed">{{ memory.content }}</p>
      </div>

      <!-- Tags -->
      <div v-if="memory.tags?.length" class="flex flex-wrap gap-2">
        <span
          v-for="tag in memory.tags"
          :key="tag"
          class="px-3 py-1 rounded-full bg-secondary text-sm"
        >
          #{{ tag }}
        </span>
      </div>

      <!-- File -->
      <div v-if="memory.filePath" class="p-3 rounded-lg bg-accent/50 text-sm text-muted-foreground">
        📎 附件：{{ memory.filePath }}
      </div>
    </div>
  </div>
</template>
