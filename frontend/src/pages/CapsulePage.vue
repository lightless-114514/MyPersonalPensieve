<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useRouter } from 'vue-router'
import {
  getCapsules,
  getCapsuleStats,
  createCapsule,
  deleteCapsule,
  getRecentMemories,
} from '@/api'
import { formatDate } from '@/lib/utils'
import type { CapsuleStatus } from '@/types'
import {
  Hourglass,
  Plus,
  Search,
  Lock,
  LockOpen,
  Unlock,
  Trash2,
  Calendar,
  ChevronLeft,
  ChevronRight,
  X,
  Loader2,
  Package,
  PackageOpen,
  PackageCheck,
  Sparkles,
  BookOpen,
  PenLine,
  ImageIcon,
  FileImage,
} from 'lucide-vue-next'
import { BIG_TAG_OPTIONS, bigTagClass, bigTagLabel } from '@/lib/utils'
import type { BigTagCategory } from '@/types'

const router = useRouter()
const queryClient = useQueryClient()

// ---- Stats ----
const { data: stats } = useQuery({
  queryKey: ['capsule-stats'],
  queryFn: getCapsuleStats,
  refetchInterval: 30_000,
})

// ---- List ----
const page = ref(0)
const search = ref('')
const statusFilter = ref<CapsuleStatus | ''>('')
const bigTagFilter = ref<BigTagCategory | ''>('')
const pageSize = 5

const { data: capsuleData, isLoading } = useQuery({
  queryKey: computed(() => ['capsules', page, search, statusFilter, bigTagFilter]),
  queryFn: () =>
    getCapsules({
      page: page.value,
      size: pageSize,
      status: statusFilter.value || undefined,
      search: search.value.trim() || undefined,
      bigTag: bigTagFilter.value || undefined,
    }),
})

const capsules = computed(() => capsuleData.value?.content ?? [])
const totalPages = computed(() => capsuleData.value?.totalPages ?? 0)
const totalElements = computed(() => capsuleData.value?.totalElements ?? 0)

function prevPage() {
  if (page.value > 0) page.value--
}
function nextPage() {
  if (page.value < totalPages.value - 1) page.value++
}

// Reset page when filter/search changes
watch([search, statusFilter, bigTagFilter], () => {
  page.value = 0
})

// ---- Create Dialog ----
const showCreate = ref(false)
const createSource = ref<'memory' | 'custom' | ''>('') // 选择来源
const createContentType = ref<'TEXT' | 'IMAGE'>('TEXT') // 自定义内容类型
const imageFile = ref<File | null>(null) // 选中的图片文件
const imagePreviewUrl = ref<string | null>(null) // 图片预览 URL
const createForm = ref({
  memoryId: '',
  title: '',
  content: '',
  openDate: '',
  message: '',
})
const createStep = ref(1) // 1=选择来源, 2=选择日记(记忆库模式)或填写内容(新建模式), 3=填写信息

const { data: recentMemories } = useQuery({
  queryKey: ['recent-memories-for-capsule'],
  queryFn: () => getRecentMemories(50),
  enabled: computed(() => showCreate.value && createSource.value === 'memory'),
})

const filteredMemories = computed(() => {
  const list = recentMemories.value ?? []
  const q = createForm.value.title.trim().toLowerCase()
  if (!q) return list
  return list.filter(
    (m) => m.title.toLowerCase().includes(q) || m.content.toLowerCase().includes(q)
  )
})

function selectSource(source: 'memory' | 'custom') {
  createSource.value = source
  createStep.value = 2
}

function selectMemory(memoryId: string, memoryTitle: string) {
  createForm.value.memoryId = memoryId
  createForm.value.title = memoryTitle
  createStep.value = 3
}

function handleImageSelect(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    const file = input.files[0]
    if (!file.type.startsWith('image/')) {
      createError.value = '请选择图片文件'
      return
    }
    imageFile.value = file
    // 生成预览 URL
    if (imagePreviewUrl.value) URL.revokeObjectURL(imagePreviewUrl.value)
    imagePreviewUrl.value = URL.createObjectURL(file)
    createError.value = ''
  }
}

function clearImage() {
  imageFile.value = null
  if (imagePreviewUrl.value) {
    URL.revokeObjectURL(imagePreviewUrl.value)
    imagePreviewUrl.value = null
  }
}

function goBackStep() {
  if (createStep.value === 3) {
    if (createSource.value === 'memory') {
      createForm.value.memoryId = ''
      createForm.value.title = ''
      createStep.value = 2
    } else {
      createStep.value = 2
    }
  } else if (createStep.value === 2) {
    createSource.value = ''
    createContentType.value = 'TEXT'
    clearImage()
    createStep.value = 1
  }
}

const createError = ref('')
const isCreating = ref(false)

const createMutation = useMutation({
  mutationFn: async () => {
    if (!createForm.value.openDate) throw new Error('请选择开启日期')
    if (createSource.value === 'custom') {
      if (createContentType.value === 'TEXT' && !createForm.value.content.trim()) throw new Error('请输入胶囊内容')
      if (createContentType.value === 'IMAGE' && !imageFile.value) throw new Error('请选择一张图片')
    }
    createError.value = ''
    isCreating.value = true
    return createCapsule({
      memoryId: createSource.value === 'memory' ? createForm.value.memoryId : undefined,
      content: createSource.value === 'custom' && createContentType.value === 'TEXT' ? createForm.value.content.trim() : undefined,
      title: createForm.value.title,
      openDate: createForm.value.openDate + 'T00:00:00',
      message: createForm.value.message.trim() || undefined,
      file: createSource.value === 'custom' && createContentType.value === 'IMAGE' ? imageFile.value! : undefined,
    })
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['capsules'] })
    queryClient.invalidateQueries({ queryKey: ['capsule-stats'] })
    showCreate.value = false
    resetCreateForm()
  },
  onError: (err: any) => {
    console.error('创建胶囊失败:', err)
    const detail = err?.response?.data?.detail
    const msg = detail || (err?.message === 'Network Error' ? '网络错误，请检查后端服务是否启动' : err?.message) || '创建失败，请重试'
    createError.value = msg
  },
  onSettled: () => {
    isCreating.value = false
  },
})

function resetCreateForm() {
  createForm.value = { memoryId: '', title: '', content: '', openDate: '', message: '' }
  createSource.value = ''
  createContentType.value = 'TEXT'
  clearImage()
  createStep.value = 1
  createError.value = ''
}

function closeCreateDialog() {
  showCreate.value = false
  resetCreateForm()
}

// ---- Delete ----
const deleteMutation = useMutation({
  mutationFn: async (id: string) => {
    await deleteCapsule(id)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['capsules'] })
    queryClient.invalidateQueries({ queryKey: ['capsule-stats'] })
  },
})

function handleDelete(e: MouseEvent, id: string) {
  e.stopPropagation()
  if (confirm('确定要删除这个时间胶囊吗？')) {
    deleteMutation.mutate(id)
  }
}

// ---- Helpers ----
function statusLabel(status: CapsuleStatus) {
  switch (status) {
    case 'SEALED': return '封存中'
    case 'OPENED': return '已开启'
    case 'FORCED_OPEN': return '破拆'
    default: return status
  }
}

function statusIcon(status: CapsuleStatus) {
  switch (status) {
    case 'SEALED': return Lock
    case 'OPENED': return LockOpen
    case 'FORCED_OPEN': return Unlock
  }
}

function statusClass(status: CapsuleStatus) {
  switch (status) {
    case 'SEALED': return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
    case 'OPENED': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
    case 'FORCED_OPEN': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
  }
}

function daysUntil(dateStr: string) {
  const now = new Date()
  const target = new Date(dateStr)
  const diff = target.getTime() - now.getTime()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

function daysSince(dateStr: string) {
  const now = new Date()
  const target = new Date(dateStr)
  const diff = now.getTime() - target.getTime()
  return Math.floor(diff / (1000 * 60 * 60 * 24))
}

function formatRelative(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

// Min date for date picker (tomorrow in local timezone)
const minDate = computed(() => {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
})
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6 p-1">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-2">
      <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
        <Hourglass class="w-5 h-5 text-primary" />
      </div>
      <div>
        <h1 class="text-2xl font-bold tracking-tight">时间胶囊</h1>
        <p class="text-sm text-muted-foreground">把今天的记忆封存，留给未来的自己</p>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <div class="rounded-xl border border-border bg-card p-4 shadow-card">
        <div class="flex items-center gap-2 mb-1">
          <Package class="w-4 h-4 text-amber-500" />
          <span class="text-xs text-muted-foreground">等待开封</span>
        </div>
        <p class="text-2xl font-bold">{{ stats?.waitingCount ?? 0 }}</p>
      </div>
      <div class="rounded-xl border border-border bg-card p-4 shadow-card">
        <div class="flex items-center gap-2 mb-1">
          <PackageCheck class="w-4 h-4 text-emerald-500" />
          <span class="text-xs text-muted-foreground">已成功开封</span>
        </div>
        <p class="text-2xl font-bold">{{ stats?.openedCount ?? 0 }}</p>
      </div>
      <div class="rounded-xl border border-border bg-card p-4 shadow-card">
        <div class="flex items-center gap-2 mb-1">
          <Unlock class="w-4 h-4 text-red-500" />
          <span class="text-xs text-muted-foreground">强行破拆</span>
        </div>
        <p class="text-2xl font-bold">{{ stats?.forcedCount ?? 0 }}</p>
      </div>
      <div class="rounded-xl border border-border bg-card p-4 shadow-card">
        <div class="flex items-center gap-2 mb-1">
          <Sparkles class="w-4 h-4 text-blue-500" />
          <span class="text-xs text-muted-foreground">已到期可开封</span>
        </div>
        <p class="text-2xl font-bold">{{ stats?.readyCount ?? 0 }}</p>
      </div>
    </div>

    <!-- Ready notification -->
    <div
      v-if="stats?.readyCount && stats.readyCount > 0"
      class="rounded-xl border-2 border-primary/30 bg-primary/5 p-4 flex items-center gap-3 animate-fade-in"
    >
      <Sparkles class="w-6 h-6 text-primary animate-pulse shrink-0" />
      <div class="flex-1">
        <p class="font-medium text-primary">你有 {{ stats.readyCount }} 个胶囊已到期，可以开封了！</p>
        <p class="text-xs text-muted-foreground mt-0.5">点击下方封存中的胶囊查看详情并开封</p>
      </div>
    </div>

    <!-- Toolbar -->
    <div class="flex items-center gap-3 flex-wrap">
      <!-- Search -->
      <div class="relative flex-1 min-w-[200px]">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <input
          v-model="search"
          type="text"
          placeholder="搜索胶囊标题或留言..."
          class="w-full pl-9 pr-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
        />
      </div>

      <!-- Status filter -->
      <select
        v-model="statusFilter"
        class="px-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
      >
        <option value="">全部状态</option>
        <option value="SEALED">封存中</option>
        <option value="OPENED">已开启</option>
        <option value="FORCED_OPEN">破拆</option>
      </select>

      <!-- Create button -->
      <button
        @click="showCreate = true"
        class="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-all shadow-sm hover:shadow-md active:scale-[0.98]"
      >
        <Plus class="w-4 h-4" />
        新增胶囊
      </button>
    </div>

    <!-- Big Tag filter -->
    <div class="flex flex-wrap gap-2">
      <button
        @click="bigTagFilter = ''"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border-2 transition-all duration-200"
        :class="!bigTagFilter ? 'bg-primary/10 text-primary border-primary/30 shadow-sm' : 'border-muted bg-background text-muted-foreground hover:border-border'"
      >
        全部
      </button>
      <button
        v-for="opt in BIG_TAG_OPTIONS"
        :key="opt.value"
        @click="bigTagFilter = bigTagFilter === opt.value ? '' : opt.value"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border-2 transition-all duration-200"
        :class="bigTagFilter === opt.value ? bigTagClass(opt.value) + ' shadow-sm' : 'border-muted bg-background text-muted-foreground hover:border-border'"
      >
        <component :is="opt.icon" class="w-3.5 h-3.5" />
        <span>{{ opt.label }}</span>
      </button>
    </div>

    <!-- Capsule List -->
    <div v-if="isLoading" class="flex justify-center py-12">
      <Loader2 class="w-6 h-6 animate-spin text-muted-foreground" />
    </div>

    <div v-else-if="capsules.length === 0" class="text-center py-16 text-muted-foreground">
      <Hourglass class="w-12 h-12 mx-auto mb-3 opacity-30" />
      <p class="text-lg font-medium mb-1">还没有时间胶囊</p>
      <p class="text-sm">点击「新增胶囊」封存一段记忆给未来的自己</p>
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="capsule in capsules"
        :key="capsule.id"
        class="rounded-xl border border-border bg-card p-4 shadow-card hover:shadow-md transition-all cursor-pointer group"
        @click="router.push(`/capsules/${capsule.id}`)"
      >
        <div class="flex items-start gap-3">
          <!-- Status icon -->
          <div
            class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
            :class="capsule.status === 'SEALED' ? 'bg-amber-100 dark:bg-amber-900/30' : capsule.status === 'OPENED' ? 'bg-emerald-100 dark:bg-emerald-900/30' : 'bg-red-100 dark:bg-red-900/30'"
          >
            <component
              :is="statusIcon(capsule.status)"
              class="w-5 h-5"
              :class="capsule.status === 'SEALED' ? 'text-amber-600 dark:text-amber-400' : capsule.status === 'OPENED' ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'"
            />
          </div>

          <div class="flex-1 min-w-0">
            <!-- Title row -->
            <div class="flex items-center gap-2 mb-1 flex-wrap">
              <h3 class="font-semibold text-sm truncate">{{ capsule.title }}</h3>
              <span
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium shrink-0"
                :class="statusClass(capsule.status)"
              >
                {{ statusLabel(capsule.status) }}
              </span>
              <span
                v-if="capsule.bigTag"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium shrink-0"
                :class="bigTagClass(capsule.bigTag)"
              >
                {{ bigTagLabel(capsule.bigTag) }}
              </span>
            </div>

            <!-- Date info -->
            <div class="flex items-center gap-4 text-xs text-muted-foreground">
              <span class="flex items-center gap-1">
                <Calendar class="w-3 h-3" />
                埋藏: {{ formatRelative(capsule.buriedDate) }}
              </span>
              <span class="flex items-center gap-1">
                <Calendar class="w-3 h-3" />
                开启: {{ formatRelative(capsule.openDate) }}
              </span>
            </div>

            <!-- Countdown or opened info -->
            <div class="mt-1.5">
              <span
                v-if="capsule.status === 'SEALED'"
                class="text-xs"
                :class="daysUntil(capsule.openDate) <= 0 ? 'text-primary font-medium' : 'text-muted-foreground'"
              >
                <template v-if="daysUntil(capsule.openDate) <= 0">
                  ✨ 已到期，可以开封！
                </template>
                <template v-else>
                  还有 {{ daysUntil(capsule.openDate) }} 天开启
                </template>
              </span>
              <span v-else-if="capsule.openedAt" class="text-xs text-muted-foreground">
                于 {{ formatRelative(capsule.openedAt) }} {{ capsule.isForced ? '破拆' : '开启' }}
              </span>
            </div>

            <!-- Message preview -->
            <p v-if="capsule.message" class="mt-1.5 text-xs text-muted-foreground/70 truncate italic">
              "{{ capsule.message }}"
            </p>
          </div>

          <!-- Delete button -->
          <button
            @click="handleDelete($event, capsule.id)"
            class="opacity-0 group-hover:opacity-100 p-1.5 rounded-md text-muted-foreground hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all"
            title="删除胶囊"
          >
            <Trash2 class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="flex items-center justify-between pt-2">
        <span class="text-xs text-muted-foreground">
          共 {{ totalElements }} 个胶囊，第 {{ page + 1 }}/{{ totalPages }} 页
        </span>
        <div class="flex items-center gap-2">
          <button
            :disabled="page === 0"
            @click="prevPage"
            class="p-1.5 rounded-md border border-border hover:bg-accent disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            <ChevronLeft class="w-4 h-4" />
          </button>
          <button
            :disabled="page >= totalPages - 1"
            @click="nextPage"
            class="p-1.5 rounded-md border border-border hover:bg-accent disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- ===== Create Dialog ===== -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showCreate"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          @click.self="closeCreateDialog"
        >
          <div class="bg-card border border-border rounded-2xl shadow-xl w-full max-w-lg mx-4 max-h-[85vh] overflow-hidden flex flex-col">
            <!-- Header -->
            <div class="flex items-center justify-between p-5 border-b border-border">
              <h2 class="text-lg font-bold">{{ createStep === 1 ? '新增时间胶囊' : createStep === 2 ? (createSource === 'memory' ? '选择记忆' : '填写内容') : '封存胶囊' }}</h2>
              <button @click="closeCreateDialog" class="p-1 rounded-md hover:bg-accent transition-colors">
                <X class="w-5 h-5" />
              </button>
            </div>

            <!-- Step 1: Choose Source -->
            <div v-if="createStep === 1" class="flex-1 overflow-y-auto p-5 space-y-3">
              <p class="text-sm text-muted-foreground mb-3">选择胶囊内容来源：</p>
              <div
                @click="selectSource('memory')"
                class="p-4 rounded-lg border border-border hover:border-primary/50 hover:bg-primary/5 cursor-pointer transition-all group"
              >
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                    <BookOpen class="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <h4 class="text-sm font-medium">从记忆库选取</h4>
                    <p class="text-xs text-muted-foreground mt-0.5">选择已有的一篇记忆封存到胶囊</p>
                  </div>
                </div>
              </div>
              <div
                @click="selectSource('custom')"
                class="p-4 rounded-lg border border-border hover:border-primary/50 hover:bg-primary/5 cursor-pointer transition-all group"
              >
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                    <PenLine class="w-5 h-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <h4 class="text-sm font-medium">新建胶囊内容</h4>
                    <p class="text-xs text-muted-foreground mt-0.5">直接撰写内容，不存入记忆库</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Step 2: Select Memory (memory mode) or Write Content (custom mode) -->
            <div v-if="createStep === 2 && createSource === 'memory'" class="flex-1 overflow-y-auto p-5 space-y-3">
              <p class="text-sm text-muted-foreground mb-3">选择一篇记忆作为胶囊内容：</p>
              <div
                v-for="m in filteredMemories"
                :key="m.id"
                @click="selectMemory(m.id, m.title)"
                class="p-3 rounded-lg border border-border hover:border-primary/50 hover:bg-primary/5 cursor-pointer transition-all"
              >
                <h4 class="text-sm font-medium truncate">{{ m.title }}</h4>
                <p class="text-xs text-muted-foreground mt-1 line-clamp-2">{{ m.content }}</p>
                <p class="text-[10px] text-muted-foreground/50 mt-1">{{ formatDate(m.createdAt || m.created_at) }}</p>
              </div>
              <div v-if="filteredMemories.length === 0" class="text-center py-8 text-muted-foreground text-sm">
                暂无记忆可选，请先创建一篇记忆
              </div>
            </div>

            <div v-if="createStep === 2 && createSource === 'custom'" class="flex-1 overflow-y-auto p-5 space-y-4">
              <!-- Title -->
              <div>
                <label class="block text-sm font-medium mb-1.5">胶囊标题</label>
                <input
                  v-model="createForm.title"
                  type="text"
                  placeholder="给这个胶囊起个名字..."
                  class="w-full px-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>

              <!-- Content type toggle -->
              <div>
                <label class="block text-sm font-medium mb-1.5">内容类型</label>
                <div class="flex gap-2">
                  <button
                    @click="createContentType = 'TEXT'; clearImage()"
                    class="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium transition-all"
                    :class="createContentType === 'TEXT' ? 'border-primary bg-primary/10 text-primary' : 'border-border hover:border-primary/30'"
                  >
                    <PenLine class="w-4 h-4" />
                    文字
                  </button>
                  <button
                    @click="createContentType = 'IMAGE'; createForm.content = ''"
                    class="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium transition-all"
                    :class="createContentType === 'IMAGE' ? 'border-primary bg-primary/10 text-primary' : 'border-border hover:border-primary/30'"
                  >
                    <ImageIcon class="w-4 h-4" />
                    图片
                  </button>
                </div>
              </div>

              <!-- Text content -->
              <div v-if="createContentType === 'TEXT'">
                <label class="block text-sm font-medium mb-1.5">胶囊内容</label>
                <textarea
                  v-model="createForm.content"
                  rows="6"
                  placeholder="写下你想给未来自己的话..."
                  class="w-full px-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
                />
              </div>

              <!-- Image upload -->
              <div v-if="createContentType === 'IMAGE'">
                <label class="block text-sm font-medium mb-1.5">选择图片</label>
                <div v-if="!imagePreviewUrl" class="relative">
                  <input
                    type="file"
                    accept="image/*"
                    @change="handleImageSelect"
                    class="hidden"
                    id="capsule-image-input"
                  />
                  <label
                    for="capsule-image-input"
                    class="flex flex-col items-center justify-center w-full h-48 rounded-lg border-2 border-dashed border-border hover:border-primary/50 hover:bg-primary/5 cursor-pointer transition-all"
                  >
                    <FileImage class="w-10 h-10 text-muted-foreground/40 mb-2" />
                    <p class="text-sm text-muted-foreground">点击选择图片</p>
                    <p class="text-xs text-muted-foreground/60 mt-1">支持 JPEG/PNG/GIF/WebP，最大 10MB</p>
                  </label>
                </div>
                <div v-else class="relative rounded-lg overflow-hidden border border-border">
                  <img :src="imagePreviewUrl" alt="预览" class="w-full max-h-64 object-contain bg-muted/20" />
                  <button
                    @click="clearImage"
                    class="absolute top-2 right-2 p-1.5 rounded-full bg-black/50 text-white hover:bg-black/70 transition-colors"
                  >
                    <X class="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            <!-- Step 3: Fill Details -->
            <div v-if="createStep === 3" class="flex-1 overflow-y-auto p-5 space-y-4">
              <!-- Selected memory (memory mode) -->
              <div v-if="createSource === 'memory'" class="p-3 rounded-lg bg-primary/5 border border-primary/20">
                <p class="text-xs text-muted-foreground mb-1">已选择记忆：</p>
                <p class="text-sm font-medium">{{ createForm.title }}</p>
              </div>
              <!-- Custom content summary -->
              <div v-if="createSource === 'custom'" class="p-3 rounded-lg bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800/30">
                <p class="text-xs text-muted-foreground mb-1">{{ createContentType === 'IMAGE' ? '图片已选择' : '胶囊内容已填写' }}</p>
                <p v-if="createContentType === 'TEXT'" class="text-sm font-medium truncate">{{ createForm.content.slice(0, 50) }}{{ createForm.content.length > 50 ? '...' : '' }}</p>
                <img v-else-if="imagePreviewUrl" :src="imagePreviewUrl" alt="预览" class="max-h-32 rounded object-contain" />
              </div>

              <!-- Title -->
              <div>
                <label class="block text-sm font-medium mb-1.5">胶囊标题</label>
                <input
                  v-model="createForm.title"
                  type="text"
                  placeholder="给这个胶囊起个名字..."
                  class="w-full px-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>

              <!-- Open Date -->
              <div>
                <label class="block text-sm font-medium mb-1.5">开启日期</label>
                <input
                  v-model="createForm.openDate"
                  type="date"
                  :min="minDate"
                  class="w-full px-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
                <p class="text-xs text-muted-foreground mt-1">到达此日期后，胶囊将可以开启</p>
              </div>

              <!-- Message -->
              <div>
                <label class="block text-sm font-medium mb-1.5">给未来自己的一段话 <span class="text-muted-foreground font-normal">(可选)</span></label>
                <textarea
                  v-model="createForm.message"
                  rows="3"
                  placeholder="写几句话给未来的自己..."
                  class="w-full px-3 py-2 rounded-lg border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
                />
              </div>

              <!-- Back button -->
              <button
                @click="goBackStep"
                class="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                ← {{ createSource === 'memory' ? '重新选择记忆' : '修改内容' }}
              </button>
            </div>

            <!-- Footer -->
            <div class="p-5 border-t border-border">
              <!-- Error message -->
              <p v-if="createError" class="text-sm text-red-500 dark:text-red-400 mb-3 text-center">{{ createError }}</p>
              <div class="flex items-center justify-end gap-3">
                <button
                  @click="closeCreateDialog"
                  class="px-4 py-2 rounded-lg text-sm text-muted-foreground hover:bg-accent transition-all"
                >
                  取消
                </button>
                <button
                  v-if="createStep === 2 && createSource === 'custom'"
                  :disabled="!createForm.title.trim() || (createContentType === 'TEXT' && !createForm.content.trim()) || (createContentType === 'IMAGE' && !imageFile) || isCreating"
                  @click="createStep = 3"
                  class="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  下一步
                </button>
                <button
                  v-if="createStep === 3"
                  :disabled="!createForm.title.trim() || !createForm.openDate || isCreating || (createSource === 'custom' && createContentType === 'TEXT' && !createForm.content.trim()) || (createSource === 'custom' && createContentType === 'IMAGE' && !imageFile)"
                  @click="createMutation.mutate()"
                  class="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  <Loader2 v-if="isCreating" class="w-4 h-4 animate-spin" />
                  <Hourglass v-else class="w-4 h-4" />
                  封存胶囊
                </button>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.fade-enter-active { animation: fadeIn 0.2s ease-out; }
.fade-leave-active { animation: fadeIn 0.15s ease-in reverse; }
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>