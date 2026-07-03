<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { BookOpen, FileText, Flame, Calendar } from 'lucide-vue-next'
import type { StatsSummary } from '@/types'

const props = defineProps<{
  stats: StatsSummary | null
}>()

// Animated number display
function useAnimatedNumber(target: () => number) {
  const current = ref(0)
  let rafId: number | null = null

  function animate() {
    const targetVal = target()
    if (current.value === targetVal) return

    const diff = targetVal - current.value
    const step = Math.max(1, Math.abs(Math.floor(diff / 20)))

    function tick() {
      if (Math.abs(current.value - targetVal) <= step) {
        current.value = targetVal
        return
      }
      current.value += current.value < targetVal ? step : -step
      rafId = requestAnimationFrame(tick)
    }
    tick()
  }

  watch(target, () => animate())
  onMounted(() => animate())

  return current
}

const totalMemories = useAnimatedNumber(() => props.stats?.total_memories ?? 0)
const totalWords = useAnimatedNumber(() => props.stats?.total_words ?? 0)
const streakDays = useAnimatedNumber(() => props.stats?.streak_days ?? 0)
const thisMonth = useAnimatedNumber(() => props.stats?.this_month ?? 0)

// Format large numbers
function formatNum(n: number): string {
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return n.toString()
}

const cards = [
  { icon: FileText, label: '总记忆', value: totalMemories, format: formatNum, color: 'text-blue-500', bg: 'bg-blue-500/10' },
  { icon: BookOpen, label: '总字数', value: totalWords, format: formatNum, color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
  { icon: Flame, label: '连续天数', value: streakDays, format: (n: number) => n + ' 天', color: 'text-orange-500', bg: 'bg-orange-500/10' },
  { icon: Calendar, label: '本月新增', value: thisMonth, format: formatNum, color: 'text-purple-500', bg: 'bg-purple-500/10' },
]
</script>

<template>
  <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
    <div
      v-for="card in cards"
      :key="card.label"
      class="flex items-center gap-3 p-3.5 rounded-xl border border-border bg-card shadow-card hover:shadow-card-hover transition-all duration-200"
    >
      <div :class="['w-9 h-9 rounded-lg flex items-center justify-center shrink-0', card.bg]">
        <component :is="card.icon" :class="['w-4.5 h-4.5', card.color]" />
      </div>
      <div class="min-w-0">
        <div class="text-lg font-bold tracking-tight leading-tight">
          {{ card.format(card.value.value) }}
        </div>
        <div class="text-[11px] text-muted-foreground leading-tight">{{ card.label }}</div>
      </div>
    </div>
  </div>
</template>