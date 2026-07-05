﻿﻿﻿﻿﻿﻿<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { getMemory, deleteMemory, updateMemory, toggleFavoriteMemory } from '@/api'
import { formatDate, typeIcon, sentimentColor, sentimentBg, bigTagClass, bigTagLabel, BIG_TAG_OPTIONS } from '@/lib/utils'
import type { BigTagCategory } from '@/types'
import { useExperienceStore } from '@/stores/experience'
import { ArrowLeft, Trash2, ExternalLink, Edit3, Save, X, Star } from 'lucide-vue-next'
import FilePreview from '@/components/FilePreview.vue'

const route = useRoute()
const router = useRouter()
const queryClient = useQueryClient()
const exp = useExperienceStore()

const isEditing = ref(false)
const editForm = ref({ title: '', content: '', sourceUrl: '', bigTag: '' as BigTagCategory | '', tags: [] as string[] })

// Tag editor state
const editTagText = ref('')
const editTagOpen = ref(false)

const { data: memory, isLoading } = useQuery({
  queryKey: ['memory', route.params.id],
  queryFn: () => getMemory(route.params.id as string),
})

function startEdit() {
  if (!memory.value) return
  editForm.value = {
    title: memory.value.title,
    content: memory.value.content,
    sourceUrl: memory.value.sourceUrl || '',
    bigTag: memory.value.bigTag || '',
    tags: [...(memory.value.tags || [])],
  }
  isEditing.value = true
}

function cancelEdit() {
  isEditing.value = false
}

function addEditTag(tag: string) {
  const t = tag.trim()
  if (!t || editForm.value.tags.includes(t)) return
  editForm.value.tags.push(t)
  editTagText.value = ''
}

function removeEditTag(tag: string) {
  editForm.value.tags = editForm.value.tags.filter(t => t !== tag)
}

function onEditTagKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault()
    const parts = editTagText.value.split(',').map(s => s.trim()).filter(Boolean)
    parts.forEach(p => addEditTag(p))
    editTagOpen.value = true
  }
  if (e.key === 'Escape') editTagOpen.value = false
  if (e.key === 'Backspace' && !editTagText.value && editForm.value.tags.length) {
    editForm.value.tags.pop()
  }
}

const updateMutation = useMutation({
  mutationFn: async () => {
    const payload: any = {}
    if (editForm.value.title !== memory.value?.title) payload.title = editForm.value.title
    if (editForm.value.content !== memory.value?.content) payload.content = editForm.value.content
    if (editForm.value.sourceUrl !== (memory.value?.sourceUrl || '')) payload.source_url = editForm.value.sourceUrl || ''
    if (editForm.value.bigTag !== (memory.value?.bigTag || '')) payload.big_tag = editForm.value.bigTag || ''
    const oldTags = [...(memory.value?.tags || [])].sort().join(',')
    const newTags = [...editForm.value.tags].sort().join(',')
    if (oldTags !== newTags) payload.tags = editForm.value.tags
    return updateMemory(route.params.id as string, payload)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['memory', route.params.id] })
    queryClient.invalidateQueries({ queryKey: ['memories'] })
    queryClient.invalidateQueries({ queryKey: ['recent-memories'] })
    queryClient.invalidateQueries({ queryKey: ['tags'] })
    exp.claimSubmitReward()
    isEditing.value = false
  },
})

const deleteMutation = useMutation({
  mutationFn: () => deleteMemory(route.params.id as string),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['memories'] })
    router.push('/memories')
  },
})

const favoriteMutation = useMutation({
  mutationFn: async ({ id, favorite }: { id: string; favorite: boolean }) => {
    return toggleFavoriteMemory(id, favorite)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['memory', route.params.id] })
    queryClient.invalidateQueries({ queryKey: ['memories'] })
    queryClient.invalidateQueries({ queryKey: ['recent-memories'] })
  },
})

function toggleFavorite() {
  if (!memory.value) return
  favoriteMutation.mutate({ id: memory.value.id, favorite: !memory.value.favorite })
}
</script>

<template>
  <div class="max-w-3xl mx-auto space-y-6 animate-fade-in">
    <button
      @click="router.back()"
      class="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-all duration-200 group"
    >
      <ArrowLeft class="w-4 h-4 group-hover:-translate-x-0.5 transition-transform duration-200" />
      返回
    </button>

    <div v-if="isLoading" class="text-center py-12 text-muted-foreground">加载中...</div>

    <div v-else-if="memory" class="space-y-6">
      <!-- Header -->
      <div class="space-y-3">
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-center gap-2.5">
            <component :is="typeIcon(memory.type)" class="w-6 h-6 text-muted-foreground shrink-0" />
            <h1 class="text-2xl font-bold tracking-tight font-display">{{ memory.title }}</h1>
          </div>
          <div class="flex items-center gap-1">
            <button
              v-if="!isEditing"
              @click="toggleFavorite()"
              class="p-2 rounded-lg transition-all duration-200"
              :class="memory?.favorite ? 'text-yellow-500 hover:text-yellow-600 hover:bg-yellow-500/10' : 'text-muted-foreground hover:text-yellow-500 hover:bg-yellow-500/10'"
              :title="memory?.favorite ? '取消收藏' : '收藏'"
            >
              <Star class="w-4 h-4" :class="memory?.favorite ? 'fill-yellow-400' : ''" />
            </button>
            <button
              v-if="!isEditing"
              @click="startEdit()"
              class="p-2 rounded-lg text-muted-foreground hover:text-primary hover:bg-primary/10 transition-all duration-200"
              title="编辑"
            >
              <Edit3 class="w-4 h-4" />
            </button>
            <button
              @click="deleteMutation.mutate()"
              class="p-2 rounded-lg text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-all duration-200"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>

        <div class="flex items-center gap-3 text-sm text-muted-foreground">
          <span>{{ formatDate(memory.createdAt || '') }}</span>
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
            {{ memory.sentiment === 'POSITIVE' ? '积极' : memory.sentiment === 'NEGATIVE' ? '消极' : '中性' }}
          </span>
        </div>
      </div>

      <!-- Edit form -->
      <div v-if="isEditing" class="p-6 rounded-xl border-2 border-primary/30 bg-card space-y-4 shadow-card animate-scale-in">
        <h2 class="font-semibold flex items-center gap-2">
          <Edit3 class="w-4 h-4" />
          编辑记忆
        </h2>

        <div class="grid gap-3">
          <div>
            <label class="text-xs text-muted-foreground font-medium mb-1 block">标题</label>
            <input v-model="editForm.title" class="w-full px-3 py-2.5 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring/50 focus:border-ring transition-all duration-200" />
          </div>

          <!-- Big tag selector -->
          <div>
            <label class="text-xs text-muted-foreground font-medium mb-1.5 block">大标签</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="opt in BIG_TAG_OPTIONS"
                :key="opt.value"
                type="button"
                @click="editForm.bigTag = editForm.bigTag === opt.value ? '' : opt.value"
                :class="[
                  'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border-2 transition-all duration-200',
                  editForm.bigTag === opt.value
                    ? bigTagClass(opt.value) + ' shadow-sm scale-105'
                    : 'border-muted bg-background text-muted-foreground hover:border-border'
                ]"
              >
                <component :is="opt.icon" class="w-4 h-4" />
                <span>{{ opt.label }}</span>
              </button>
            </div>
          </div>

          <div>
            <label class="text-xs text-muted-foreground font-medium mb-1 block">来源 URL</label>
            <input v-model="editForm.sourceUrl" placeholder="https://..." class="w-full px-3 py-2.5 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring/50 focus:border-ring transition-all duration-200" />
          </div>

          <div>
            <label class="text-xs text-muted-foreground font-medium mb-1 block">内容</label>
            <textarea
              v-model="editForm.content"
              rows="10"
              class="w-full px-3 py-2.5 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring/50 focus:border-ring resize-y transition-all duration-200"
              @input="exp.onInput()"
            ></textarea>
          </div>

          <!-- Tags editor -->
          <div>
            <label class="text-xs text-muted-foreground font-medium mb-1.5 block">标签</label>
            <div class="relative">
              <div class="flex flex-wrap items-center gap-1.5 px-3 py-2.5 rounded-lg border border-input bg-background cursor-text min-h-[42px] focus-within:ring-2 focus-within:ring-ring/50 focus-within:border-ring transition-all duration-200">
                <span
                  v-for="tag in editForm.tags"
                  :key="tag"
                  class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-primary/10 text-primary text-xs font-medium"
                >
                  {{ tag }}
                  <button @click="removeEditTag(tag)" class="hover:text-primary/70 transition-colors">&times;</button>
                </span>
                <input
                  v-model="editTagText"
                  @keydown="onEditTagKeydown"
                  @focus="editTagOpen = true"
                  placeholder="添加标签..."
                  class="flex-1 min-w-[80px] bg-transparent text-sm outline-none border-none p-0"
                />
              </div>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-3 pt-2">
          <button
            @click="updateMutation.mutate()"
            :disabled="!editForm.title || !editForm.content"
            class="inline-flex items-center gap-2 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-all duration-200 shadow-sm hover:shadow-md active:scale-[0.98]"
          >
            <Save class="w-4 h-4" />
            保存
          </button>
          <button
            @click="cancelEdit()"
            class="inline-flex items-center gap-2 px-4 py-2.5 border border-border rounded-lg text-sm font-medium hover:bg-accent transition-all duration-200"
          >
            <X class="w-4 h-4" />
            取消
          </button>
        </div>
      </div>

      <!-- Source link -->
      <div v-if="memory.sourceUrl" class="p-3 rounded-lg bg-accent/50 border border-border/50">
        <a
          :href="memory.sourceUrl"
          target="_blank"
          class="inline-flex items-center gap-1.5 text-sm text-primary hover:underline transition-colors duration-200"
        >
          <ExternalLink class="w-3.5 h-3.5" />
          {{ memory.sourceUrl }}
        </a>
      </div>

      <!-- Content -->
      <div class="p-6 rounded-xl border border-border bg-card shadow-card">
        <p class="whitespace-pre-wrap leading-relaxed">{{ memory.content }}</p>
      </div>

      <!-- Tags -->
      <div v-if="memory.tags?.length" class="flex flex-wrap gap-2">
        <span
          v-for="tag in memory.tags"
          :key="tag"
          class="px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium"
        >
          #{{ tag }}
        </span>
      </div>

      <!-- File preview -->
      <FilePreview
        v-if="memory.filePath"
        :memory-id="memory.id"
        :file-path="memory.filePath"
        :mime-type="memory.mimeType"
        :file-size="memory.fileSize"
        :title="memory.title"
      />
    </div>
  </div>
</template>