<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useRoute, useRouter } from 'vue-router'
import { getCapsuleDetail, openCapsule, forceOpenCapsule, deleteCapsule } from '@/api'
import type { CapsuleStatus } from '@/types'
import {
  Hourglass,
  ArrowLeft,
  Lock,
  LockOpen,
  Unlock,
  Calendar,
  Trash2,
  Loader2,
  AlertTriangle,
  Clock,
  Package,
  PackageOpen,
  Sparkles,
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const queryClient = useQueryClient()
const capsuleId = route.params.id as string

// ---- Capsule Data ----
const { data: capsule, isLoading, refetch } = useQuery({
  queryKey: ['capsule-detail', capsuleId],
  queryFn: () => getCapsuleDetail(capsuleId),
})

// ---- Open Capsule ----
const isOpening = ref(false)
const openMutation = useMutation({
  mutationFn: () => openCapsule(capsuleId),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['capsule-detail', capsuleId] })
    queryClient.invalidateQueries({ queryKey: ['capsules'] })
    queryClient.invalidateQueries({ queryKey: ['capsule-stats'] })
    refetch()
  },
  onSettled: () => { isOpening.value = false },
})

// ---- Force Open (with cooldown) ----
const showForceConfirm = ref(false)
const forceCooldown = ref(0) // 30s countdown
let cooldownTimer: ReturnType<typeof setInterval> | null = null
const isForceOpening = ref(false)

const forceOpenMutation = useMutation({
  mutationFn: () => forceOpenCapsule(capsuleId),
  onSuccess: () => {
    showForceConfirm.value = false
    queryClient.invalidateQueries({ queryKey: ['capsule-detail', capsuleId] })
    queryClient.invalidateQueries({ queryKey: ['capsules'] })
    queryClient.invalidateQueries({ queryKey: ['capsule-stats'] })
    refetch()
  },
  onSettled: () => { isForceOpening.value = false },
})

function startForceConfirm() {
  showForceConfirm.value = true
  forceCooldown.value = 30
  cooldownTimer = setInterval(() => {
    forceCooldown.value--
    if (forceCooldown.value <= 0) {
      if (cooldownTimer) clearInterval(cooldownTimer)
      cooldownTimer = null
    }
  }, 1000)
}

function cancelForce() {
  showForceConfirm.value = false
  forceCooldown.value = 0
  if (cooldownTimer) {
    clearInterval(cooldownTimer)
    cooldownTimer = null
  }
}

function executeForceOpen() {
  if (forceCooldown.value > 0) return
  isForceOpening.value = true
  forceOpenMutation.mutate()
}

onUnmounted(() => {
  if (cooldownTimer) clearInterval(cooldownTimer)
})

// ---- Delete ----
const isDeleting = ref(false)
const deleteMutation = useMutation({
  mutationFn: () => deleteCapsule(capsuleId),
  onSuccess: () => {
    router.push('/capsules')
  },
  onSettled: () => { isDeleting.value = false },
})

function handleDelete() {
  if (confirm('确定要删除这个时间胶囊吗？此操作不可撤销。')) {
    isDeleting.value = true
    deleteMutation.mutate()
  }
}

// ---- Helpers ----
function isReady(dateStr: string) {
  return new Date(dateStr) <= new Date()
}

function daysUntil(dateStr: string) {
  const diff = new Date(dateStr).getTime() - Date.now()
  return Math.ceil(diff / (1000 * 60 * 60 * 24))
}

function daysBetween(from: string, to: string) {
  const diff = new Date(to).getTime() - new Date(from).getTime()
  return Math.floor(diff / (1000 * 60 * 60 * 24))
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function formatDateTime(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function statusLabel(status: CapsuleStatus) {
  switch (status) {
    case 'SEALED': return '封存中'
    case 'OPENED': return '已开启'
    case 'FORCED_OPEN': return '破拆'
    default: return status
  }
}

function statusClass(status: CapsuleStatus) {
  switch (status) {
    case 'SEALED': return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
    case 'OPENED': return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
    case 'FORCED_OPEN': return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
  }
}
</script>

<template>
  <div class="max-w-3xl mx-auto space-y-6 p-1">
    <!-- Back -->
    <button
      @click="router.push('/capsules')"
      class="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
    >
      <ArrowLeft class="w-4 h-4" />
      返回时间胶囊
    </button>

    <!-- Loading -->
    <div v-if="isLoading" class="flex justify-center py-20">
      <Loader2 class="w-8 h-8 animate-spin text-muted-foreground" />
    </div>

    <template v-else-if="capsule">
      <!-- Header Card -->
      <div class="rounded-xl border border-border bg-card shadow-card overflow-hidden">
        <!-- Status banner -->
        <div
          class="px-6 py-3 text-sm font-medium flex items-center gap-2"
          :class="{
            'bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-400': capsule.status === 'SEALED',
            'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400': capsule.status === 'OPENED',
            'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400': capsule.status === 'FORCED_OPEN',
          }"
        >
          <component
            :is="capsule.status === 'SEALED' ? Lock : capsule.status === 'OPENED' ? LockOpen : Unlock"
            class="w-4 h-4"
          />
          {{ statusLabel(capsule.status as CapsuleStatus) }}
          <span
            v-if="capsule.status === 'SEALED' && isReady(capsule.openDate)"
            class="ml-2 text-primary font-bold animate-pulse"
          >
            ✨ 已到期可开封
          </span>
        </div>

        <div class="p-6 space-y-4">
          <!-- Title -->
          <h1 class="text-2xl font-bold tracking-tight">{{ capsule.title }}</h1>

          <!-- Date info grid -->
          <div class="grid grid-cols-2 gap-4">
            <div class="flex items-start gap-3">
              <Calendar class="w-5 h-5 text-muted-foreground mt-0.5 shrink-0" />
              <div>
                <p class="text-xs text-muted-foreground">埋藏日期</p>
                <p class="text-sm font-medium">{{ formatDate(capsule.buriedDate) }}</p>
              </div>
            </div>
            <div class="flex items-start gap-3">
              <Calendar class="w-5 h-5 text-muted-foreground mt-0.5 shrink-0" />
              <div>
                <p class="text-xs text-muted-foreground">预定开启日期</p>
                <p class="text-sm font-medium">{{ formatDate(capsule.openDate) }}</p>
              </div>
            </div>
          </div>

          <!-- Countdown / Duration -->
          <div v-if="capsule.status === 'SEALED'" class="rounded-lg bg-muted/50 p-4">
            <div class="flex items-center gap-2">
              <Clock class="w-4 h-4 text-muted-foreground" />
              <template v-if="isReady(capsule.openDate)">
                <span class="text-primary font-medium">已到期，可以开封！</span>
              </template>
              <template v-else>
                <span class="text-muted-foreground">
                  还有 <span class="font-bold text-foreground">{{ daysUntil(capsule.openDate) }}</span> 天开启
                  （共封存 {{ daysBetween(capsule.buriedDate, capsule.openDate) }} 天）
                </span>
              </template>
            </div>
          </div>

          <!-- Opened info -->
          <div v-if="capsule.status !== 'SEALED' && capsule.openedAt" class="rounded-lg bg-muted/50 p-4">
            <div class="flex items-center gap-2">
              <PackageOpen class="w-4 h-4 text-emerald-500" />
              <span class="text-sm">
                于 {{ formatDateTime(capsule.openedAt) }} {{ capsule.isForced ? '强行破拆' : '开启' }}
                <span v-if="capsule.isForced" class="text-red-500 ml-1">(提前 {{ daysUntil(capsule.openDate) > 0 ? daysUntil(capsule.openDate) : 0 }} 天)</span>
              </span>
            </div>
          </div>

          <!-- Message -->
          <div v-if="capsule.message" class="rounded-lg bg-primary/5 border border-primary/10 p-4">
            <p class="text-xs text-muted-foreground mb-1">给未来自己的一段话：</p>
            <p class="text-sm italic leading-relaxed">"{{ capsule.message }}"</p>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-3 pt-2">
            <!-- Open button (when ready) -->
            <button
              v-if="capsule.status === 'SEALED' && isReady(capsule.openDate)"
              @click="isOpening = true; openMutation.mutate()"
              :disabled="isOpening"
              class="flex items-center gap-2 px-5 py-2.5 bg-emerald-500 text-white rounded-lg text-sm font-medium hover:bg-emerald-600 disabled:opacity-50 transition-all shadow-sm"
            >
              <Loader2 v-if="isOpening" class="w-4 h-4 animate-spin" />
              <LockOpen v-else class="w-4 h-4" />
              开启胶囊
            </button>

            <!-- Force open button (when not ready) -->
            <button
              v-if="capsule.status === 'SEALED' && !isReady(capsule.openDate)"
              @click="startForceConfirm"
              class="flex items-center gap-2 px-4 py-2.5 border border-red-300 text-red-600 dark:border-red-800 dark:text-red-400 rounded-lg text-sm font-medium hover:bg-red-50 dark:hover:bg-red-900/20 transition-all"
            >
              <Unlock class="w-4 h-4" />
              强行破拆
            </button>

            <!-- Delete -->
            <button
              @click="handleDelete"
              :disabled="isDeleting"
              class="flex items-center gap-2 px-4 py-2.5 text-muted-foreground hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg text-sm transition-all"
            >
              <Trash2 class="w-4 h-4" />
              删除
            </button>
          </div>
        </div>
      </div>

      <!-- Content Card (only when opened) -->
      <div
        v-if="capsule.status !== 'SEALED' && capsule.memoryContent"
        class="rounded-xl border border-border bg-card shadow-card p-6 animate-fade-in"
      >
        <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
          <PackageOpen class="w-5 h-5 text-emerald-500" />
          胶囊内容
        </h2>
        <div class="prose prose-sm dark:prose-invert max-w-none whitespace-pre-wrap">
          {{ capsule.memoryContent }}
        </div>
      </div>

      <!-- Sealed content placeholder -->
      <div
        v-if="capsule.status === 'SEALED'"
        class="rounded-xl border-2 border-dashed border-border bg-muted/20 p-12 text-center"
      >
        <Lock class="w-16 h-16 mx-auto mb-4 text-muted-foreground/30" />
        <p class="text-lg font-medium text-muted-foreground mb-2">内容已封存</p>
        <p class="text-sm text-muted-foreground/60">胶囊开启前不可查看内容</p>
        <p class="text-xs text-muted-foreground/40 mt-1">
          {{ isReady(capsule.openDate) ? '已到期，可以开启查看' : `还有 ${daysUntil(capsule.openDate)} 天开启` }}
        </p>
      </div>
    </template>

    <!-- Force Open Confirmation Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showForceConfirm"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
          @click.self="cancelForce"
        >
          <div class="bg-card border border-border rounded-2xl shadow-xl w-full max-w-md mx-4 overflow-hidden">
            <!-- Warning header -->
            <div class="bg-red-50 dark:bg-red-900/20 p-5 flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/40 flex items-center justify-center shrink-0">
                <AlertTriangle class="w-5 h-5 text-red-500" />
              </div>
              <div>
                <h3 class="font-bold text-red-700 dark:text-red-400">确认破拆时间胶囊？</h3>
                <p class="text-xs text-red-600/70 dark:text-red-400/70">此操作不可撤销</p>
              </div>
            </div>

            <div class="p-5 space-y-4">
              <p class="text-sm leading-relaxed">
                你真的想要提前查看吗？这个胶囊原本要在
                <span class="font-medium">{{ formatDate(capsule?.openDate ?? '') }}</span>
                才开启，提前破拆会失去等待的意义。
              </p>

              <!-- Cooldown timer -->
              <div v-if="forceCooldown > 0" class="rounded-lg bg-muted p-4 text-center">
                <p class="text-sm text-muted-foreground mb-2">冷静期 — 请认真思考</p>
                <div class="text-4xl font-bold text-foreground tabular-nums">{{ forceCooldown }}s</div>
                <div class="mt-2 h-1.5 bg-muted-foreground/20 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-primary rounded-full transition-all duration-1000"
                    :style="{ width: ((30 - forceCooldown) / 30 * 100) + '%' }"
                  />
                </div>
              </div>

              <div v-else class="rounded-lg bg-red-50 dark:bg-red-900/20 p-3 text-center">
                <p class="text-sm text-red-600 dark:text-red-400 font-medium">冷静期已过，确认要破拆吗？</p>
              </div>

              <!-- Buttons -->
              <div class="flex items-center justify-end gap-3">
                <button
                  @click="cancelForce"
                  class="px-4 py-2 rounded-lg text-sm text-muted-foreground hover:bg-accent transition-all"
                >
                  再想想
                </button>
                <button
                  :disabled="forceCooldown > 0 || isForceOpening"
                  @click="executeForceOpen"
                  class="flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg text-sm font-medium hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  <Loader2 v-if="isForceOpening" class="w-4 h-4 animate-spin" />
                  <Unlock v-else class="w-4 h-4" />
                  {{ forceCooldown > 0 ? `等待 ${forceCooldown}s` : '确认破拆' }}
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