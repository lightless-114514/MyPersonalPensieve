<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { checkReadyCapsules } from '@/api'
import { useRouter } from 'vue-router'
import { Hourglass, X, Sparkles } from 'lucide-vue-next'

const router = useRouter()
const dismissed = ref(false)

const { data: readyCapsules } = useQuery({
  queryKey: ['capsule-ready-check'],
  queryFn: checkReadyCapsules,
  refetchInterval: 60_000, // 每分钟检查一次
  staleTime: 30_000,
})

const showNotification = ref(false)

// 只在首次加载时显示通知
onMounted(() => {
  // 延迟显示，避免页面加载时立即弹出
  const timer = setTimeout(() => {
    if (readyCapsules.value && readyCapsules.value.length > 0 && !dismissed.value) {
      showNotification.value = true
    }
  }, 1500)
  onUnmounted(() => clearTimeout(timer))
})

function dismiss() {
  dismissed.value = true
  showNotification.value = false
}

function goToCapsules() {
  router.push('/capsules')
  dismiss()
}
</script>

<template>
  <Transition name="slide-down">
    <div
      v-if="showNotification && readyCapsules && readyCapsules.length > 0"
      class="rounded-xl border-2 border-primary/30 bg-gradient-to-r from-primary/5 via-primary/10 to-primary/5 p-4 shadow-lg animate-fade-in"
    >
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center shrink-0 animate-pulse">
          <Sparkles class="w-5 h-5 text-primary" />
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="font-semibold text-sm">你的时间胶囊已开启！</h3>
          <p class="text-xs text-muted-foreground mt-0.5">
            你有 {{ readyCapsules.length }} 个胶囊已到期，点击查看当年写下的内容
          </p>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <button
            @click="goToCapsules"
            class="px-4 py-1.5 bg-primary text-primary-foreground rounded-lg text-xs font-medium hover:bg-primary/90 transition-all"
          >
            去开封
          </button>
          <button
            @click="dismiss"
            class="p-1 rounded-md text-muted-foreground hover:bg-accent transition-colors"
          >
            <X class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.slide-down-enter-active {
  animation: slideDown 0.4s ease-out;
}
.slide-down-leave-active {
  animation: slideDown 0.2s ease-in reverse;
}
@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>