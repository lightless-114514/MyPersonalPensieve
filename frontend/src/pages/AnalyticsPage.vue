<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { getSentimentTrend } from '@/api'
import { BIG_TAG_OPTIONS, bigTagClass, bigTagLabel } from '@/lib/utils'
import type { BigTagCategory } from '@/types'
import * as d3 from 'd3'

const container = ref<HTMLDivElement>()
const days = ref(30)
const filterBigTag = ref<BigTagCategory | ''>('')

const { data: trends } = useQuery({
  queryKey: computed(() => ['sentiment-trend', days.value, filterBigTag.value]),
  queryFn: () => getSentimentTrend(days.value, filterBigTag.value || undefined),
})

let rendered = false

function renderChart() {
  if (!container.value || !trends.value?.length) return

  const el = container.value
  const margin = { top: 20, right: 30, bottom: 40, left: 40 }
  const width = el.clientWidth - margin.left - margin.right
  const height = 400 - margin.top - margin.bottom

  d3.select(el).selectAll('svg').remove()

  const svg = d3.select(el)
    .append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  const data = trends.value

  const x = d3.scalePoint()
    .domain(data.map((d) => d.date))
    .range([0, width])
    .padding(0.5)

  const y = d3.scaleLinear()
    .domain([-1, 1])
    .range([height, 0])

  svg.append('g')
    .attr('transform', `translate(0,${height / 2})`)
    .call(d3.axisBottom(x).tickValues(x.domain().filter((_, i) => i % Math.ceil(data.length / 10) === 0)))
    .selectAll('text')
    .attr('transform', 'rotate(-30)')
    .style('text-anchor', 'end')
    .attr('font-size', '10px')

  svg.append('g')
    .call(d3.axisLeft(y).ticks(5))

  svg.append('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', height / 2)
    .attr('y2', height / 2)
    .attr('stroke', 'hsl(var(--border))')
    .attr('stroke-dasharray', '4 4')

  const areaPositive = d3.area<typeof data[0]>()
    .x((d) => x(d.date)!)
    .y0(height / 2)
    .y1((d) => y(Math.max(0, d.average)))
  svg.append('path')
    .datum(data)
    .attr('fill', 'hsl(142 71% 45% / 0.15)')
    .attr('d', areaPositive)

  const areaNegative = d3.area<typeof data[0]>()
    .x((d) => x(d.date)!)
    .y0(height / 2)
    .y1((d) => y(Math.min(0, d.average)))
  svg.append('path')
    .datum(data)
    .attr('fill', 'hsl(0 84% 60% / 0.15)')
    .attr('d', areaNegative)

  const line = d3.line<typeof data[0]>()
    .x((d) => x(d.date)!)
    .y((d) => y(d.average))
    .curve(d3.curveMonotoneX)
  svg.append('path')
    .datum(data)
    .attr('fill', 'none')
    .attr('stroke', 'hsl(var(--primary))')
    .attr('stroke-width', 2)
    .attr('d', line)

  svg.selectAll('circle')
    .data(data)
    .join('circle')
    .attr('cx', (d) => x(d.date)!)
    .attr('cy', (d) => y(d.average))
    .attr('r', 3)
    .attr('fill', 'hsl(var(--primary))')

  rendered = true
}

function setFilter(bigTag: BigTagCategory | '') {
  filterBigTag.value = filterBigTag.value === bigTag ? '' : bigTag
}

onMounted(() => renderChart())
onUnmounted(() => rendered = false)
watch(trends, () => setTimeout(renderChart, 100))
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">情感趋势</h1>
      <select
        v-model="days"
        class="px-3 py-1.5 rounded-md border border-border bg-card text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      >
        <option :value="7">最近 7 天</option>
        <option :value="30">最近 30 天</option>
        <option :value="90">最近 90 天</option>
      </select>
    </div>

    <!-- Big tag filter buttons -->
    <div class="flex flex-wrap items-center gap-2">
      <span class="text-sm text-muted-foreground mr-1">筛选大标签：</span>
      <button
        @click="setFilter('')"
        :class="[
          'px-3 py-1 rounded-full text-xs font-medium border transition-all',
          !filterBigTag
            ? 'bg-primary text-primary-foreground border-primary'
            : 'bg-background text-muted-foreground border-border hover:border-muted-foreground'
        ]"
      >
        全部
      </button>
      <button
        v-for="opt in BIG_TAG_OPTIONS"
        :key="opt.value"
        @click="setFilter(opt.value)"
        :class="[
          'inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold border transition-all',
          filterBigTag === opt.value
            ? bigTagClass(opt.value) + ' shadow-sm'
            : 'bg-background text-muted-foreground border-border hover:border-muted-foreground'
        ]"
      >
        <span>{{ opt.icon }}</span>
        <span>{{ opt.label }}</span>
      </button>
    </div>

    <div ref="container" class="w-full rounded-lg border border-border bg-card p-4">
      <div
        v-if="!trends?.length"
        class="flex items-center justify-center h-[400px] text-muted-foreground"
      >
        暂无情感数据
      </div>
    </div>
  </div>
</template>
