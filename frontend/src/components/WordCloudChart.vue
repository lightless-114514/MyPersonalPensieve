<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import type { ComputedRef } from 'vue'
import type { WordCloudItem } from '@/types'

const props = defineProps<{
  data: WordCloudItem[]
  modelValue?: 'month' | 'year'
}>()

const canvasRef = ref<HTMLCanvasElement>()
const period = computed({
  get: () => props.modelValue ?? 'month',
  set: (val) => emit('update:modelValue', val),
})
const hoveredWord = ref<string | null>(null)

const emit = defineEmits<{
  (e: 'click-word', word: string): void
  (e: 'update:modelValue', value: 'month' | 'year'): void
}>()

// Color palette for words
const PALETTE = [
  'hsl(var(--primary))',
  'hsl(142 71% 45%)',
  'hsl(200 80% 50%)',
  'hsl(280 60% 55%)',
  'hsl(35 90% 50%)',
  'hsl(170 60% 45%)',
  'hsl(340 70% 55%)',
  'hsl(60 70% 45%)',
]

interface PlacedWord {
  text: string
  x: number
  y: number
  fontSize: number
  color: string
  width: number
  height: number
  count: number
}

function renderCloud() {
  const canvas = canvasRef.value
  if (!canvas || !props.data?.length) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const dpr = window.devicePixelRatio || 1
  const rect = canvas.getBoundingClientRect()
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  ctx.scale(dpr, dpr)
  ctx.clearRect(0, 0, rect.width, rect.height)

  const centerX = rect.width / 2
  const centerY = rect.height / 2

  const maxCount = Math.max(...props.data.map((d) => d.count))
  const minCount = Math.min(...props.data.map((d) => d.count))
  const range = maxCount - minCount || 1

  // Font size scale: 12px ~ 36px
  const minFont = 12
  const maxFont = Math.min(36, rect.width / 12)

  // Sort by count descending (place big words first)
  const sorted = [...props.data].sort((a, b) => b.count - a.count)

  const placed: PlacedWord[] = []

  for (const item of sorted) {
    const fontSize = minFont + ((item.count - minCount) / range) * (maxFont - minFont)
    const color = PALETTE[placed.length % PALETTE.length]

    ctx.font = `${Math.round(fontSize)}px "Inter", "PingFang SC", "Microsoft YaHei", sans-serif`
    const metrics = ctx.measureText(item.word)
    const textWidth = metrics.width + 8
    const textHeight = fontSize * 1.2 + 4

    // Spiral placement
    let placedOk = false
    let angle = 0
    let radius = 0
    const step = 0.3
    const radiusStep = 1.5

    for (let i = 0; i < 500; i++) {
      const x = centerX + radius * Math.cos(angle) - textWidth / 2
      const y = centerY + radius * Math.sin(angle) - textHeight / 2

      // Check bounds
      if (x < 0 || y < 0 || x + textWidth > rect.width || y + textHeight > rect.height) {
        angle += step
        radius += radiusStep * step / (2 * Math.PI)
        continue
      }

      // Check overlap
      const overlap = placed.some((p) =>
        x < p.x + p.width &&
        x + textWidth > p.x &&
        y < p.y + p.height &&
        y + textHeight > p.y
      )

      if (!overlap) {
        placed.push({
          text: item.word,
          x, y,
          fontSize,
          color,
          width: textWidth,
          height: textHeight,
          count: item.count,
        })
        placedOk = true
        break
      }

      angle += step
      radius += radiusStep * step / (2 * Math.PI)
    }
  }

  // Draw all placed words
  for (const w of placed) {
    ctx.font = `${Math.round(w.fontSize)}px "Inter", "PingFang SC", "Microsoft YaHei", sans-serif`
    ctx.fillStyle = hoveredWord.value === w.text ? 'hsl(var(--primary))' : w.color
    ctx.textBaseline = 'top'
    ctx.globalAlpha = hoveredWord.value && hoveredWord.value !== w.text ? 0.3 : 1
    ctx.fillText(w.text, w.x + 4, w.y + 2)
  }
  ctx.globalAlpha = 1

  // Store placed words for hit testing (use dataset as typed storage)
  ;(canvas as any)._placedWords = placed
}

// Hit test on mouse move
function handleMouseMove(e: MouseEvent) {
  const canvas = canvasRef.value
  if (!canvas || !(canvas as any)._placedWords) return

  const rect = canvas.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top

  const hit = ((canvas as any)._placedWords as PlacedWord[]).find((w) =>
    x >= w.x && x <= w.x + w.width && y >= w.y && y <= w.y + w.height
  )

  const newHovered = hit?.text ?? null
  if (newHovered !== hoveredWord.value) {
    hoveredWord.value = newHovered
    canvas.style.cursor = newHovered ? 'pointer' : 'default'
    renderCloud()
  }
}

function handleClick(e: MouseEvent) {
  if (hoveredWord.value) {
    emit('click-word', hoveredWord.value)
  }
}

function handleMouseLeave() {
  if (hoveredWord.value) {
    hoveredWord.value = null
    renderCloud()
  }
}

let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  renderCloud()
  if (canvasRef.value) {
    resizeObserver = new ResizeObserver(() => renderCloud())
    resizeObserver.observe(canvasRef.value.parentElement!)
  }
})

onUnmounted(() => {
  resizeObserver?.disconnect()
})

watch(() => props.data, () => setTimeout(renderCloud, 50))
</script>

<template>
  <div class="w-full">
    <div class="flex items-center justify-between mb-2">
      <slot name="header" />
      <div class="flex gap-1">
        <button
          @click="period = 'month'"
          :class="[
            'px-2.5 py-0.5 rounded-md text-xs font-medium transition-all',
            period === 'month'
              ? 'bg-primary text-primary-foreground'
              : 'bg-secondary text-muted-foreground hover:bg-accent'
          ]"
        >
          本月
        </button>
        <button
          @click="period = 'year'"
          :class="[
            'px-2.5 py-0.5 rounded-md text-xs font-medium transition-all',
            period === 'year'
              ? 'bg-primary text-primary-foreground'
              : 'bg-secondary text-muted-foreground hover:bg-accent'
          ]"
        >
          本年
        </button>
      </div>
    </div>
    <div class="relative w-full h-[200px] rounded-lg bg-card/50">
      <canvas
        ref="canvasRef"
        class="w-full h-full"
        @mousemove="handleMouseMove"
        @click="handleClick"
        @mouseleave="handleMouseLeave"
      />
      <div
        v-if="!data?.length"
        class="absolute inset-0 flex items-center justify-center text-muted-foreground text-sm"
      >
        暂无词汇数据
      </div>
    </div>
  </div>
</template>