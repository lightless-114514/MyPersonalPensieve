<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import * as d3 from 'd3'
import type { HeatmapDay } from '@/types'

const props = defineProps<{
  data: HeatmapDay[]
  modelValue?: 'year' | 'quarter' | 'month'
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: 'year' | 'quarter' | 'month'): void
}>()

const internalPeriod = ref<'year' | 'quarter' | 'month'>('year')

const period = computed({
  get: () => props.modelValue ?? internalPeriod.value,
  set: (val) => {
    internalPeriod.value = val
    emit('update:modelValue', val)
  },
})

const container = ref<HTMLDivElement>()
const tooltip = ref<{ x: number; y: number; text: string; visible: boolean }>({
  x: 0, y: 0, text: '', visible: false,
})

// Month labels in Chinese
const MONTH_LABELS = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
const DAY_LABELS = ['日', '一', '二', '三', '四', '五', '六']

// Filter data by period
const filteredData = computed(() => {
  if (!props.data?.length) return []
  if (period.value === 'year') return props.data

  const now = new Date()
  let startDate: Date

  if (period.value === 'quarter') {
    const quarterStart = Math.floor(now.getMonth() / 3) * 3
    startDate = new Date(now.getFullYear(), quarterStart, 1)
  } else {
    startDate = new Date(now.getFullYear(), now.getMonth(), 1)
  }

  const startStr = startDate.toISOString().slice(0, 10)
  return props.data.filter((d) => d.date >= startStr)
})

// Get current year
const currentYear = computed(() => {
  if (props.data?.length > 0) {
    return new Date(props.data[0].date).getFullYear()
  }
  return new Date().getFullYear()
})

function renderChart() {
  if (!container.value || !filteredData.value?.length) return

  const el = container.value
  d3.select(el).selectAll('svg').remove()

  const data = filteredData.value
  const cellSize = 13
  const cellPadding = 2
  const cellStep = cellSize + cellPadding
  const marginLeft = 32
  const marginBottom = 8
  const marginTop = 22  // enough space for month labels
  const marginRight = 8

  // Calculate date range from filtered data
  const dates = data.map((d) => new Date(d.date))
  const minDate = new Date(Math.min(...dates.map((d) => d.getTime())))
  const maxDate = new Date(Math.max(...dates.map((d) => d.getTime())))

  // Calculate weeks to display
  const startSunday = new Date(minDate)
  startSunday.setDate(startSunday.getDate() - startSunday.getDay())
  const endSaturday = new Date(maxDate)
  endSaturday.setDate(endSaturday.getDate() + (6 - endSaturday.getDay()))

  const totalDays = Math.ceil((endSaturday.getTime() - startSunday.getTime()) / 86400000) + 1
  const totalWeeks = Math.ceil(totalDays / 7)

  const width = marginLeft + totalWeeks * cellStep + marginRight
  const height = marginTop + 7 * cellStep + marginBottom

  const svg = d3.select(el)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)
    .style('max-width', '100%')
    .style('height', 'auto')

  const g = svg.append('g')
    .attr('transform', `translate(${marginLeft}, ${marginTop})`)

  // Build data map
  const dataMap = new Map<string, HeatmapDay>()
  for (const d of data) {
    dataMap.set(d.date, d)
  }

  // Find max word count for color scale
  const maxWords = d3.max(data, (d) => d.word_count) || 1

  // Color scale: 5 levels like GitHub
  const colorScale = d3.scaleQuantize<string>()
    .domain([0, maxWords])
    .range([
      'var(--heatmap-0, rgba(110,118,129,0.15))',
      'var(--heatmap-1, rgba(56,166,79,0.3))',
      'var(--heatmap-2, rgba(56,166,79,0.5))',
      'var(--heatmap-3, rgba(56,166,79,0.75))',
      'var(--heatmap-4, rgba(56,166,79,1))',
    ])

  // Draw day labels
  const dayLabelIndices = [1, 3, 5] // Mon, Wed, Fri
  dayLabelIndices.forEach((day) => {
    g.append('text')
      .attr('x', -4)
      .attr('y', day * cellStep + cellSize / 2)
      .attr('text-anchor', 'end')
      .attr('dominant-baseline', 'middle')
      .attr('font-size', '10px')
      .attr('fill', 'hsl(var(--muted-foreground))')
      .text(DAY_LABELS[day])
  })

  // Draw month labels
  let prevMonth = -1
  for (let week = 0; week < totalWeeks; week++) {
    const weekStart = new Date(startSunday)
    weekStart.setDate(weekStart.getDate() + week * 7)
    const month = weekStart.getMonth()
    if (month !== prevMonth) {
      g.append('text')
        .attr('x', week * cellStep)
        .attr('y', -6)
        .attr('font-size', '10px')
        .attr('fill', 'hsl(var(--muted-foreground))')
        .text(MONTH_LABELS[month])
      prevMonth = month
    }
  }

  // Draw cells
  for (let week = 0; week < totalWeeks; week++) {
    for (let day = 0; day < 7; day++) {
      const cellDate = new Date(startSunday)
      cellDate.setDate(cellDate.getDate() + week * 7 + day)

      // Skip cells outside the data range
      if (cellDate < minDate || cellDate > maxDate) continue

      const dateStr = cellDate.toISOString().slice(0, 10)
      const dayData = dataMap.get(dateStr)
      const wordCount = dayData?.word_count ?? 0
      const memCount = dayData?.memory_count ?? 0

      const rect = g.append('rect')
        .attr('x', week * cellStep)
        .attr('y', day * cellStep)
        .attr('width', cellSize)
        .attr('height', cellSize)
        .attr('rx', 2)
        .attr('fill', colorScale(wordCount))

      // Hover interaction
      rect.on('mouseenter', (event) => {
        const text = wordCount > 0
          ? `${dateStr}：${wordCount} 字 / ${memCount} 条`
          : `${dateStr}：无记录`
        tooltip.value = { x: event.offsetX, y: event.offsetY - 10, text, visible: true }
      })
      rect.on('mouseleave', () => {
        tooltip.value.visible = false
      })
    }
  }
}

let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  renderChart()
  if (container.value) {
    resizeObserver = new ResizeObserver(() => renderChart())
    resizeObserver.observe(container.value)
  }
})

onUnmounted(() => {
  resizeObserver?.disconnect()
})

watch(filteredData, () => setTimeout(renderChart, 50))
</script>

<template>
  <div>
    <!-- Period toggle buttons -->
    <div class="flex items-center gap-1.5 mb-3">
      <div class="flex bg-secondary/60 rounded-lg p-0.5 gap-0.5">
        <button
          v-for="opt in ([
            { value: 'year', label: '全年' },
            { value: 'quarter', label: '本季度' },
            { value: 'month', label: '本月' },
          ] as const)"
          :key="opt.value"
          @click="period = opt.value"
          :class="[
            'px-3 py-1 rounded-md text-xs font-medium transition-all duration-200',
            period === opt.value
              ? 'bg-primary text-primary-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
          ]"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>

    <div class="relative">
      <div ref="container" class="w-full overflow-x-auto" />
      <!-- Tooltip -->
      <div
        v-if="tooltip.visible"
        class="absolute pointer-events-none z-50 px-2.5 py-1.5 rounded-md bg-popover text-popover-foreground text-xs shadow-md border border-border whitespace-nowrap transition-opacity"
        :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px', transform: 'translate(-50%, -100%)' }"
      >
        {{ tooltip.text }}
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Dark mode heatmap colors override */
:root {
  --heatmap-0: rgba(110, 118, 129, 0.15);
  --heatmap-1: rgba(56, 166, 79, 0.3);
  --heatmap-2: rgba(56, 166, 79, 0.5);
  --heatmap-3: rgba(56, 166, 79, 0.75);
  --heatmap-4: rgba(56, 166, 79, 1);
}

.dark {
  --heatmap-0: rgba(110, 118, 129, 0.15);
  --heatmap-1: rgba(56, 166, 79, 0.25);
  --heatmap-2: rgba(56, 166, 79, 0.45);
  --heatmap-3: rgba(56, 166, 79, 0.7);
  --heatmap-4: rgba(56, 166, 79, 1);
}
</style>