<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { getKnowledgeGraph } from '@/api'
import * as d3 from 'd3'

const container = ref<HTMLDivElement>()

const { data: graph } = useQuery({
  queryKey: ['knowledge-graph'],
  queryFn: getKnowledgeGraph,
})

let simulation: d3.Simulation<any, any> | null = null

function renderGraph() {
  if (!container.value || !graph.value) return

  const width = container.value.clientWidth
  const height = container.value.clientHeight

  d3.select(container.value).selectAll('svg').remove()

  const svg = d3.select(container.value)
    .append('svg')
    .attr('width', width)
    .attr('height', height)

  const g = svg.append('g')

  const zoom = d3.zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.3, 3])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    })
  svg.call(zoom)

  const nodes = graph.value.nodes.map((n) => ({ ...n }))
  const links = graph.value.links.map((l) => ({ ...l }))

  if (nodes.length === 0) return

  const color = d3.scaleOrdinal(d3.schemeCategory10)

  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id((d: any) => d.id).distance(100))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide(30))

  const link = g.append('g')
    .selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke', 'hsl(var(--border))')
    .attr('stroke-width', (d) => Math.max(1, d.strength * 3))

  const node = g.append('g')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .call(
      d3.drag<SVGGElement, any>()
        .on('start', (event, d) => {
          if (!event.active) simulation?.alphaTarget(0.3).restart()
          d.fx = d.x
          d.fy = d.y
        })
        .on('drag', (event, d) => {
          d.fx = event.x
          d.fy = event.y
        })
        .on('end', (event, d) => {
          if (!event.active) simulation?.alphaTarget(0)
          d.fx = null
          d.fy = null
        })
    )

  node.append('circle')
    .attr('r', 8)
    .attr('fill', (d) => color(d.group))

  node.append('text')
    .text((d) => d.name)
    .attr('x', 12)
    .attr('y', 4)
    .attr('font-size', '11px')
    .attr('fill', 'hsl(var(--foreground))')

  simulation.on('tick', () => {
    link
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y)

    node.attr('transform', (d) => `translate(${d.x},${d.y})`)
  })
}

onMounted(() => {
  renderGraph()
  window.addEventListener('resize', renderGraph)
})

onUnmounted(() => {
  simulation?.stop()
  window.removeEventListener('resize', renderGraph)
})

// Re-render when data changes
import { watch } from 'vue'
watch(graph, () => {
  setTimeout(renderGraph, 100)
})
</script>

<template>
  <div class="space-y-4">
    <h1 class="text-2xl font-bold">知识图谱</h1>
    <div
      ref="container"
      class="w-full h-[calc(100vh-10rem)] rounded-lg border border-border bg-card"
    >
      <div
        v-if="!graph?.nodes?.length"
        class="flex items-center justify-center h-full text-muted-foreground"
      >
        暂无图谱数据。添加更多记忆后，AI 会自动提取实体和关系。
      </div>
    </div>
  </div>
</template>
