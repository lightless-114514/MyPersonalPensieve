<script setup lang="ts">
import { computed } from 'vue'
import { useBirthdayStore } from '@/stores/birthday'
import { X, PartyPopper } from 'lucide-vue-next'

const birthdayStore = useBirthdayStore()

const message = computed(() => {
  if (!birthdayStore.data?.birthday) return ''
  const days = birthdayStore.daysUntilBirthday
  if (days === 0) return '今天是你的生日！🎂 生日快乐！'
  if (days === 1) return '明天就是你的生日啦！🎉 准备好了吗？'
  if (days <= 3) return `还有 ${days} 天就是你的生日了！🎁`
  return ''
})

function dismiss() {
  birthdayStore.markReminderShown()
}
</script>

<template>
  <Transition name="reminder">
    <div
      v-if="birthdayStore.shouldShowReminder && message"
      class="relative flex items-center gap-3 px-4 py-3 rounded-xl bg-gradient-to-r from-pink-500/10 via-purple-500/10 to-orange-500/10 border border-pink-500/20 shadow-card"
    >
      <PartyPopper class="w-5 h-5 text-pink-500 shrink-0" />
      <p class="flex-1 text-sm font-medium text-foreground">
        {{ message }}
      </p>
      <button
        @click="dismiss"
        class="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
      >
        <X class="w-4 h-4" />
      </button>
    </div>
  </Transition>
</template>

<style scoped>
.reminder-enter-active {
  animation: slideDown 0.3s ease-out;
}
.reminder-leave-active {
  animation: slideUp 0.2s ease-in;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideUp {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-8px);
  }
}
</style>