<script setup lang="ts">
import { ref, computed } from 'vue'
import { useBirthdayStore } from '@/stores/birthday'
import { Star, X, Send, Trash2 } from 'lucide-vue-next'

const birthdayStore = useBirthdayStore()

const showInput = ref(false)
const wishContent = ref('')
const showWishList = ref(false)

/** 今年愿望 */
const thisYearWishes = computed(() => {
  const today = new Date()
  return birthdayStore.wishes.filter(w => {
    const d = new Date(w.date)
    return d.getFullYear() === today.getFullYear()
  })
})

/** 去年及更早的愿望 */
const pastWishes = computed(() => {
  const today = new Date()
  return birthdayStore.wishes.filter(w => {
    const d = new Date(w.date)
    return d.getFullYear() < today.getFullYear()
  })
})

function toggleInput() {
  showInput.value = !showInput.value
  if (showInput.value) {
    wishContent.value = ''
  }
}

function submitWish() {
  const content = wishContent.value.trim()
  if (!content) return
  birthdayStore.addWish(content)
  wishContent.value = ''
  showInput.value = false
}

function removeWish(id: string) {
  birthdayStore.removeWish(id)
}

function toggleWishList() {
  showWishList.value = !showWishList.value
}
</script>

<template>
  <div
    v-if="birthdayStore.isBirthdayToday"
    class="rounded-xl border border-border bg-card p-4 shadow-card"
  >
    <!-- 许愿按钮 -->
    <div class="flex items-center justify-between">
      <button
        @click="toggleInput"
        class="inline-flex items-center gap-2 px-3 py-2 bg-primary/10 text-primary rounded-lg text-sm font-medium hover:bg-primary/20 transition-colors"
      >
        <Star class="w-4 h-4" />
        许个愿吧 🌟
      </button>
      <button
        v-if="birthdayStore.wishes.length > 0"
        @click="toggleWishList"
        class="text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        {{ showWishList ? '收起' : `查看愿望 (${birthdayStore.wishes.length})` }}
      </button>
    </div>

    <!-- 许愿输入框 -->
    <Transition name="wish-input">
      <div v-if="showInput" class="mt-3">
        <div class="flex gap-2">
          <input
            v-model="wishContent"
            type="text"
            placeholder="写下你的生日愿望..."
            maxlength="200"
            class="flex-1 px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            @keydown.enter="submitWish"
          />
          <button
            @click="submitWish"
            :disabled="!wishContent.trim()"
            class="inline-flex items-center gap-1 px-3 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send class="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </Transition>

    <!-- 愿望列表 -->
    <Transition name="wish-list">
      <div v-if="showWishList && birthdayStore.wishes.length > 0" class="mt-3 space-y-2">
        <!-- 今年愿望 -->
        <div v-if="thisYearWishes.length > 0">
          <p class="text-xs text-muted-foreground mb-1.5">今年的愿望</p>
          <div
            v-for="wish in thisYearWishes"
            :key="wish.id"
            class="flex items-start gap-2 p-2.5 rounded-lg bg-accent/30 border border-border/50 group"
          >
            <span class="text-sm mt-0.5">🎂</span>
            <div class="flex-1 min-w-0">
              <p class="text-sm leading-relaxed">{{ wish.content }}</p>
              <p class="text-xs text-muted-foreground/50 mt-1">{{ wish.date }}</p>
            </div>
            <button
              @click="removeWish(wish.id)"
              class="p-1 rounded text-muted-foreground/30 hover:text-destructive opacity-0 group-hover:opacity-100 transition-all"
            >
              <Trash2 class="w-3 h-3" />
            </button>
          </div>
        </div>

        <!-- 往年愿望回顾 -->
        <div v-if="pastWishes.length > 0">
          <p class="text-xs text-muted-foreground mb-1.5">往年的愿望</p>
          <div
            v-for="wish in pastWishes.slice(0, 5)"
            :key="wish.id"
            class="flex items-start gap-2 p-2.5 rounded-lg bg-accent/20 border border-border/30 group"
          >
            <span class="text-sm mt-0.5">✨</span>
            <div class="flex-1 min-w-0">
              <p class="text-sm leading-relaxed text-muted-foreground">{{ wish.content }}</p>
              <p class="text-xs text-muted-foreground/40 mt-1">
                {{ wish.date }}
                <span v-if="wish.age"> · {{ wish.age }}岁时</span>
              </p>
            </div>
            <button
              @click="removeWish(wish.id)"
              class="p-1 rounded text-muted-foreground/30 hover:text-destructive opacity-0 group-hover:opacity-100 transition-all"
            >
              <Trash2 class="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.wish-input-enter-active {
  animation: slideDown 0.2s ease-out;
}
.wish-input-leave-active {
  animation: slideUp 0.15s ease-in;
}

.wish-list-enter-active {
  animation: slideDown 0.2s ease-out;
}
.wish-list-leave-active {
  animation: slideUp 0.15s ease-in;
}

@keyframes slideDown {
  from { opacity: 0; max-height: 0; }
  to { opacity: 1; max-height: 300px; }
}

@keyframes slideUp {
  from { opacity: 1; max-height: 300px; }
  to { opacity: 0; max-height: 0; }
}
</style>