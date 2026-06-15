<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { searchMemories, createMemory } from '@/api'
import { useMemoryStore } from '@/stores/memory'
import { formatDate, typeIcon, sentimentColor } from '@/lib/utils'
import { Search, Plus, X, Loader2 } from 'lucide-vue-next'
import type { Memory, ProcessingProgress } from '@/types'

const route = useRoute()
const queryClient = useQueryClient()

const searchText = ref('')
const page = ref(0)
const showCreate = ref(route.query.new === 'true')
const isUploading = ref(false)
const uploadProgress = ref<ProcessingProgress | null>(null)

// Create form
const createForm = ref({
  title: '',
  content: '',
  type: 'TEXT',
  sourceUrl: '',
  tags: '',
})

const { data, isLoading } = useQuery({
  queryKey: ['memories', { query: searchText.value, page: page.value }],
  queryFn: () => searchMemories({ query: searchText.value, page: page.value, size: 20 }),
})

const createMutation = useMutation({
  mutationFn: async () => {
    isUploading.value = true
    const formData = new FormData()
    formData.append('title', createForm.value.title)
    formData.append('content', createForm.value.content)
    formData.append('type', createForm.value.type)
    if (createForm.value.sourceUrl) formData.append('sourceUrl', createForm.value.sourceUrl)
    if (createForm.value.tags) {
      createForm.value.tags.split(',').forEach((t) => formData.append('tags', t.trim()))
    }
    return createMemory(formData)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['memories'] })
    showCreate.value = false
    isUploading.value = false
    resetForm()
  },
  onError: () => {
    isUploading.value = false
  },
})

function resetForm() {
  createForm.value = { title: '', content: '', type: 'TEXT', sourceUrl: '', tags: '' }
}

function onSearch() {
  page.value = 0
  queryClient.invalidateQueries({ queryKey: ['memories'] })
}

const totalPages = computed(() => data.value?.totalPages ?? 1)
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">记忆</h1>
      <button
        @click="showCreate = !showCreate"
        class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
      >
        <Plus v-if="!showCreate" class="w-4 h-4" />
        <X v-else class="w-4 h-4" />
        {{ showCreate ? '取消' : '新建' }}
      </button>
    </div>

    <!-- Create form -->
    <div v-if="showCreate" class="p-6 rounded-lg border border-border bg-card space-y-4">
      <h2 class="font-semibold">新建记忆</h2>

      <div class="grid gap-3">
        <input
          v-model="createForm.title"
          placeholder="标题"
          class="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />

        <select
          v-model="createForm.type"
          class="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="TEXT">📝 文字</option>
          <option value="LINK">🔗 链接</option>
          <option value="IMAGE">🖼️ 图片</option>
          <option value="AUDIO">🎙️ 语音</option>
        </select>

        <textarea
          v-model="createForm.content"
          placeholder="记忆内容..."
          rows="4"
          class="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-none"
        ></textarea>

        <input
          v-if="createForm.type === 'LINK'"
          v-model="createForm.sourceUrl"
          placeholder="https://..."
          class="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />

        <input
          v-model="createForm.tags"
          placeholder="标签（逗号分隔）"
          class="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>

      <div class="flex items-center gap-3">
        <button
          @click="createMutation.mutate()"
          :disabled="!createForm.title || !createForm.content || isUploading"
          class="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          <Loader2 v-if="isUploading" class="w-4 h-4 animate-spin inline mr-1" />
          保存记忆
        </button>
      </div>
    </div>

    <!-- Search -->
    <div class="relative">
      <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
      <input
        v-model="searchText"
        @keyup.enter="onSearch"
        placeholder="搜索记忆..."
        class="w-full pl-10 pr-4 py-2.5 rounded-lg border border-border bg-card text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      />
    </div>

    <!-- List -->
    <div v-if="isLoading" class="text-center py-12 text-muted-foreground">加载中...</div>

    <div v-else class="space-y-3">
      <router-link
        v-for="m in data?.content"
        :key="m.id"
        :to="`/memories/${m.id}`"
        class="block p-4 rounded-lg border border-border bg-card hover:bg-accent/50 transition-colors"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span>{{ typeIcon(m.type) }}</span>
              <h3 class="font-medium truncate">{{ m.title }}</h3>
              <span v-if="m.sentiment" :class="['text-xs', sentimentColor(m.sentiment)]">
                {{ m.sentiment === 'POSITIVE' ? '😊' : m.sentiment === 'NEGATIVE' ? '😔' : '😐' }}
              </span>
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

      <div v-if="!data?.content?.length" class="text-center py-16 text-muted-foreground">
        暂无记忆
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 pt-4">
      <button
        :disabled="page === 0"
        @click="page--; queryClient.invalidateQueries({ queryKey: ['memories'] })"
        class="px-3 py-1.5 rounded-md text-sm border border-border hover:bg-accent disabled:opacity-50 transition-colors"
      >
        上一页
      </button>
      <span class="text-sm text-muted-foreground">{{ page + 1 }} / {{ totalPages }}</span>
      <button
        :disabled="page >= totalPages - 1"
        @click="page++; queryClient.invalidateQueries({ queryKey: ['memories'] })"
        class="px-3 py-1.5 rounded-md text-sm border border-border hover:bg-accent disabled:opacity-50 transition-colors"
      >
        下一页
      </button>
    </div>
  </div>
</template>
