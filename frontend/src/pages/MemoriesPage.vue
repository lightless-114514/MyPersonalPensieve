<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { getMemories, createMemory, getTags } from '@/api'
import { formatDate, typeIcon, sentimentColor, BIG_TAG_OPTIONS, bigTagClass, bigTagLabel } from '@/lib/utils'
import type { BigTagCategory } from '@/types'
import { Search, Plus, X, Loader2, Tag } from 'lucide-vue-next'

const route = useRoute()
const queryClient = useQueryClient()

const page = ref(0)
const showCreate = ref(route.query.new === 'true')
const isUploading = ref(false)

const createForm = ref({ title: '', content: '', type: 'TEXT', sourceUrl: '' })
const selectedTags = ref<string[]>([])
const selectedBigTag = ref<BigTagCategory | ''>('')

// ---- Tag selector ----
const tagText = ref('')
const tagOpen = ref(false)
const tagInputRef = ref<HTMLInputElement | null>(null)

const { data: allTags } = useQuery({
  queryKey: ['tags'],
  queryFn: () => getTags(void 0, 100),
  placeholderData: (prev: any) => prev,
  staleTime: 30_000,
})

const suggestions = computed(() => {
  const tags = allTags.value
  if (!tags || tags.length === 0) return []
  const q = tagText.value.trim().toLowerCase()
  let filtered = tags.filter((t: any) => !selectedTags.value.includes(t.tag))
  if (q) {
    filtered = filtered.filter((t: any) => t.tag.toLowerCase().includes(q))
  }
  return filtered
})

function addTag(tag: string) {
  const t = tag.trim()
  if (!t) return
  if (!selectedTags.value.includes(t)) selectedTags.value.push(t)
  tagText.value = ''
  tagOpen.value = true
  nextTick(() => tagInputRef.value?.focus())
}

function removeTag(tag: string) {
  selectedTags.value = selectedTags.value.filter((t: string) => t !== tag)
}

function onTagKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault()
    const parts = tagText.value.split(',').map(s => s.trim()).filter(Boolean)
    if (parts.length) {
      const merged = [...selectedTags.value]
      parts.forEach(p => {
        if (!merged.includes(p)) merged.push(p)
      })
      selectedTags.value = merged
    }
    tagText.value = ''
    tagOpen.value = true
    return
  }
  if (e.key === 'Escape') {
    tagOpen.value = false
    return
  }
  if (e.key === 'Backspace' && !tagText.value && selectedTags.value.length) {
    const removed = [...selectedTags.value]
    removed.pop()
    selectedTags.value = removed
  }
}

function onTagInput() {
  tagOpen.value = true
}

function openTagDropdownAndFocus() {
  tagOpen.value = true
  nextTick(() => tagInputRef.value?.focus())
}
// ---- End tag selector ----

const maxTags = 5
const expanded = ref<Set<string>>(new Set())
function toggleExpand(id: string) {
  const s = new Set(expanded.value)
  s.has(id) ? s.delete(id) : s.add(id)
  expanded.value = s
}

const { data, isLoading } = useQuery({
  queryKey: ['memories', page.value],
  queryFn: () => getMemories({ page: page.value, size: 20 }),
})

const createMutation = useMutation({
  mutationFn: async () => {
    isUploading.value = true
    const payload: any = {
      title: createForm.value.title.trim(),
      content: createForm.value.content.trim(),
      type: createForm.value.type,
      tags: [...selectedTags.value],
    }
    if (createForm.value.sourceUrl) payload.source_url = createForm.value.sourceUrl.trim()
    if (selectedBigTag.value) payload.big_tag = selectedBigTag.value
    return createMemory(payload)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['memories'] })
    queryClient.invalidateQueries({ queryKey: ['recent-memories'] })
    queryClient.invalidateQueries({ queryKey: ['tags'] })
    showCreate.value = false
    isUploading.value = false
    resetForm()
  },
  onError: () => { isUploading.value = false },
})

function resetForm() {
  createForm.value = { title: '', content: '', type: 'TEXT', sourceUrl: '' }
  selectedTags.value = []
  selectedBigTag.value = ''
  tagText.value = ''
}

const totalPages = computed(() => data.value?.total_pages ?? 1)
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6">
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

    <div v-if="showCreate" class="p-6 rounded-lg border border-border bg-card space-y-4">
      <h2 class="font-semibold">新建记忆</h2>
      <div class="grid gap-3">
        <input v-model="createForm.title" placeholder="标题" class="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
        <select v-model="createForm.type" class="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring">
          <option value="TEXT">📝 文本</option>
          <option value="IMAGE">🖼️ 图片</option>
        </select>

        <!-- Big tag selector -->
        <div class="space-y-1.5">
          <label class="text-xs text-muted-foreground font-medium">🏷️ 大标签（可选）</label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="opt in BIG_TAG_OPTIONS"
              :key="opt.value"
              type="button"
              @click="selectedBigTag = selectedBigTag === opt.value ? '' : opt.value"
              :class="[
                'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border-2 transition-all',
                selectedBigTag === opt.value
                  ? bigTagClass(opt.value) + ' shadow-sm scale-105'
                  : 'border-muted bg-background text-muted-foreground hover:border-border'
              ]"
            >
              <span>{{ opt.icon }}</span>
              <span>{{ opt.label }}</span>
            </button>
          </div>
        </div>

        <input v-model="createForm.sourceUrl" placeholder="来源 URL（可选）" class="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring" />

        <textarea
          v-model="createForm.content"
          placeholder="写下你的记忆…"
          rows="6"
          class="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-y"
        ></textarea>

        <!-- Tag selector -->
        <div class="space-y-1.5">
          <label class="text-xs text-muted-foreground font-medium">🏷️ 标签</label>
          <div class="relative" @click="openTagDropdownAndFocus">
            <div class="flex flex-wrap items-center gap-1.5 px-3 py-2 rounded-md border border-input bg-background cursor-text min-h-[38px]">
              <span
                v-for="tag in selectedTags"
                :key="tag"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-secondary text-xs"
              >
                {{ tag }}
                <button @click.stop="removeTag(tag)" class="hover:text-foreground">&times;</button>
              </span>
              <input
                ref="tagInputRef"
                v-model="tagText"
                @keydown="onTagKeydown"
                @input="onTagInput"
                @focus="tagOpen = true"
                placeholder="输入标签，用逗号分隔多个"
                class="flex-1 min-w-[80px] bg-transparent text-sm outline-none border-none p-0"
              />
            </div>
            <div
              v-if="tagOpen"
              class="absolute z-50 mt-1 w-full rounded-md border border-border bg-card shadow-lg max-h-48 overflow-y-auto"
            >
              <div
                v-for="t in suggestions.slice(0, 20)"
                :key="t.tag"
                @mousedown.prevent="addTag(t.tag)"
                class="flex items-center justify-between px-3 py-2 text-sm hover:bg-accent cursor-pointer transition-colors"
              >
                <span>{{ t.tag }}</span>
                <span class="text-xs text-muted-foreground">{{ t.count }}</span>
              </div>
              <div v-if="suggestions.length === 0" class="px-3 py-4 text-sm text-center text-muted-foreground">
                <template v-if="tagText">
                  按 <kbd class="px-1.5 py-0.5 rounded bg-muted text-xs font-mono">Enter</kbd> 创建 &ldquo;{{ tagText }}&rdquo;
                </template>
                <template v-else>
                  输入标签名，用逗号分隔多个，按 <kbd class="px-1.5 py-0.5 rounded bg-muted text-xs font-mono">Enter</kbd> 添加
                </template>
              </div>
            </div>
          </div>
        </div>
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

    <div v-if="isLoading" class="text-center py-12 text-muted-foreground">加载中...</div>
    <div v-else class="space-y-3">
      <router-link
        v-for="m in data?.content"
        :key="m.id"
        :to="`/memories/${m.id}`"
        class="block p-4 rounded-lg border border-border bg-card hover:bg-accent/50 transition-colors relative"
      >
        <!-- Big tag badge (top-right corner) -->
        <div
          v-if="m.bigTag"
          :class="[
            'absolute -top-0.5 -left-0.5 inline-flex items-center gap-1 px-2.5 py-1 rounded-br-lg rounded-tl-lg text-xs font-semibold border',
            bigTagClass(m.bigTag)
          ]"
        >
          {{ bigTagLabel(m.bigTag) }}
        </div>

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
        <div class="flex gap-2 mt-2 flex-wrap" v-if="m.tags?.length">
          <template v-for="(tag, i) in m.tags" :key="tag">
            <span v-if="expanded.has(m.id) || i < maxTags" class="px-2 py-0.5 rounded-full bg-secondary text-xs text-muted-foreground">{{ tag }}</span>
          </template>
          <button v-if="m.tags.length > maxTags && !expanded.has(m.id)" @click.prevent="toggleExpand(m.id)" class="px-2 py-0.5 rounded-full bg-secondary/50 text-xs text-muted-foreground hover:bg-secondary transition-colors">
            +{{ m.tags.length - maxTags }} more
          </button>
          <button v-if="expanded.has(m.id)" @click.prevent="toggleExpand(m.id)" class="px-2 py-0.5 text-xs text-muted-foreground hover:text-foreground transition-colors">
            收起
          </button>
        </div>
      </router-link>
      <div v-if="!data?.content?.length" class="text-center py-16 text-muted-foreground">暂无记忆</div>
    </div>

    <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 pt-4">
      <button :disabled="page === 0" @click="page--; queryClient.invalidateQueries({ queryKey: ['memories'] })" class="px-3 py-1.5 rounded-md text-sm border border-border hover:bg-accent disabled:opacity-50 transition-colors">上一页</button>
      <span class="text-sm text-muted-foreground">{{ page + 1 }} / {{ totalPages }}</span>
      <button :disabled="page >= totalPages - 1" @click="page++; queryClient.invalidateQueries({ queryKey: ['memories'] })" class="px-3 py-1.5 rounded-md text-sm border border-border hover:bg-accent disabled:opacity-50 transition-colors">下一页</button>
    </div>
  </div>
</template>
