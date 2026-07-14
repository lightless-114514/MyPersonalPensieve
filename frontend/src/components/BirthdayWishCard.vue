<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useBirthdayStore } from '@/stores/birthday'
import { generateBirthdayWish } from '@/api'
import { X, Sparkles, Loader2 } from 'lucide-vue-next'

const birthdayStore = useBirthdayStore()

const wishText = ref('')
const isLoading = ref(false)
const isFallback = ref(false)
const visible = ref(false)
const dismissed = ref(false)

onMounted(async () => {
  if (birthdayStore.shouldShowAiWishCard && !dismissed.value) {
    visible.value = true
    isLoading.value = true
    try {
      const result = await generateBirthdayWish()
      wishText.value = result.wish
      isFallback.value = result.fallback
    } catch {
      wishText.value = birthdayStore.randomGreeting
      isFallback.value = true
    } finally {
      isLoading.value = false
    }
    birthdayStore.markAiWishShown()
  }
})

function dismiss() {
  dismissed.value = true
  visible.value = false
}
</script>

<template>
  <Transition name="wish-card">
    <div
      v-if="visible && !dismissed"
      class="relative rounded-xl border border-border bg-card p-5 shadow-card overflow-hidden"
    >
      <!-- 装饰背景 -->
      <div class="absolute top-0 right-0 w-24 h-24 opacity-10 pointer-events-none">
        <span class="text-6xl">🎂</span>
      </div>

      <!-- 关闭按钮 -->
      <button
        @click="dismiss"
        class="absolute top-3 right-3 p-1 rounded-full text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
      >
        <X class="w-4 h-4" />
      </button>

      <!-- 标题 -->
      <div class="flex items-center gap-2 mb-3">
        <Sparkles class="w-5 h-5 text-primary" />
        <h3 class="text-sm font-semibold font-display">AI 专属生日祝福</h3>
      </div>

      <!-- 加载状态 -->
      <div v-if="isLoading" class="flex items-center gap-2 py-4">
        <Loader2 class="w-4 h-4 animate-spin text-primary" />
        <span class="text-sm text-muted-foreground">正在为你生成专属祝福...</span>
      </div>

      <!-- 祝福内容 -->
      <div v-else>
        <p class="text-sm leading-relaxed text-foreground/90 mb-3">
          {{ wishText }}
        </p>
        <p v-if="birthdayStore.age" class="text-xs text-muted-foreground">
          🎂 记录于你第 {{ birthdayStore.age + 1 }} 岁的第一天
        </p>
        <p v-if="isFallback" class="text-xs text-muted-foreground/50 mt-1">
          （过去一年暂无足够日记数据，使用预设祝福）
        </p>
      </div>

      <!-- 底部装饰线 -->
      <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-pink-400 via-yellow-400 to-blue-400 opacity-60"></div>
    </div>
  </Transition>
</template>

<style scoped>
.wish-card-enter-active {
  animation: wishCardIn 0.5s ease-out;
}
.wish-card-leave-active {
  animation: wishCardOut 0.3s ease-in;
}

@keyframes wishCardIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes wishCardOut {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-10px);
  }
}
</style>