<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { getKnowledgeGraph } from '@/api'
import * as d3 from 'd3'

const container = ref<HTMLDivElement>()
const layoutMode = ref<'force' | 'tree'>('force')

const { data: graph } = useQuery({
  queryKey: ['knowledge-graph'],
  queryFn: getKnowledgeGraph,
})

let simulation: d3.Simulation<any, any> | null = null

function buildHierarchy(nodes: any[], links: any[]) {
  // Build adjacency map
  const nodeMap = new Map<string, any>()
  nodes.forEach(n => nodeMap.set(n.id, { ...n, children: [], _depth: -1 }))

  const adj = new Map<string, string[]>()
  links.forEach(l => {
    const s = typeof l.source === 'object' ? l.source.id : l.source
    const t = typeof l.target === 'object' ? l.target.id : l.target
    if (!adj.has(s)) adj.set(s, [])
    if (!adj.has(t)) adj.set(t, [])
    adj.get(s)!.push(t)
    adj.get(t)!.push(s)
  })

  // Separate connected nodes from isolated ones
  const connectedNodes = nodes.filter(n => adj.has(n.id) && adj.get(n.id)!.length > 0)
  const isolatedNodes = nodes.filter(n => !adj.has(n.id) || adj.get(n.id)!.length === 0)

  if (connectedNodes.length === 0) return null

  // Find root: connected node with most connections
  let rootId = connectedNodes[0].id
  let maxDeg = -1
  connectedNodes.forEach(n => {
    const deg = (adj.get(n.id) || []).length
    if (deg > maxDeg) { maxDeg = deg; rootId = n.id }
  })

  const root = nodeMap.get(rootId)!
  root._depth = 0

  // BFS to build tree from connected nodes only
  const visited = new Set<string>([rootId])
  const queue = [root]
  while (queue.length) {
    const cur = queue.shift()!
    const neighbors = adj.get(cur.id) || []
    for (const nid of neighbors) {
      if (visited.has(nid)) continue
      visited.add(nid)
      const child = nodeMap.get(nid)!
      child._depth = cur._depth + 1
      cur.children.push(child)
      queue.push(child)
    }
  }

  // Find any connected nodes not visited by BFS — these belong to
  // separate connected components and need their own independent trees.
  const remaining = connectedNodes.filter(n => !visited.has(n.id))
  const extraRoots: any[] = []
  while (remaining.length > 0) {
    const compRootId = remaining[0].id
    const compRoot = nodeMap.get(compRootId)!
    compRoot._depth = 0
    visited.add(compRootId)
    const compQueue = [compRoot]
    remaining.splice(0, 1)
    while (compQueue.length) {
      const cur = compQueue.shift()!
      const neighbors = adj.get(cur.id) || []
      for (const nid of neighbors) {
        if (visited.has(nid)) continue
        visited.add(nid)
        const child = nodeMap.get(nid)!
        child._depth = cur._depth + 1
        cur.children.push(child)
        compQueue.push(child)
        const idx = remaining.findIndex((r: any) => r.id === nid)
        if (idx !== -1) remaining.splice(idx, 1)
      }
    }
    extraRoots.push(compRoot)
  }

  // Wrap in a virtual root: children = [main tree root, ...extra component roots, ...isolated nodes]
  const virtualRoot = {
    id: '__virtual__',
    name: '',
    type: 'VIRTUAL',
    group: -1,
    children: [root, ...extraRoots] as any[],
    _depth: -1,
  }
  root._depth = 0
  extraRoots.forEach((r: any) => { r._depth = 0 })

  // Isolated nodes become direct children of the virtual root (independent roots)
  if (isolatedNodes.length > 0) {
    isolatedNodes.forEach(n => {
      const node = nodeMap.get(n.id)!
      node._depth = 1
      node.children = [] // ensure no stray children
      virtualRoot.children.push(node)
    })
  }

  return virtualRoot
}

function renderGraph() {
  if (!container.value || !graph.value) return
  if (layoutMode.value === 'tree') {
    renderTree()
  } else {
    renderForce()
  }
}

function renderForce() {
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
          d.fx = event.x
          d.fy = event.y
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

function renderTree() {
  if (!container.value || !graph.value) return
  simulation?.stop()
  simulation = null

  const width = container.value.clientWidth
  const height = container.value.clientHeight

  const rootData = buildHierarchy(graph.value.nodes, graph.value.links)
  if (!rootData) return

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

  // Use horizontal tree layout (left to right, mind-map style)
  const root = d3.hierarchy<any>(rootData)
  const treeLayout = d3.tree<any>()
    .size([height - 80, width - 200])
    .separation((a, b) => (a.parent?.data.id === b.parent?.data.id ? 1.2 : 1.8))
  treeLayout(root)

  const color = d3.scaleOrdinal(d3.schemeCategory10)

  // Links as curved paths — hide links coming from the virtual root
  g.append('g')
    .selectAll('path')
    .data(root.links().filter((l: any) => l.source.data.id !== '__virtual__'))
    .join('path')
    .attr('fill', 'none')
    .attr('stroke', 'hsl(var(--border))')
    .attr('stroke-width', 1.5)
    .attr('d', d3.linkHorizontal<any, any>()
      .x((d) => d.y)
      .y((d) => d.x))

  // Nodes
  const node = g.append('g')
    .selectAll('g')
    .data(root.descendants())
    .join('g')
    .attr('transform', (d) => `translate(${d.y},${d.x})`)

  node.append('circle')
    .attr('r', (d) => d.data.id === '__virtual__' ? 0 : (d.depth === 1 ? 10 : 6))
    .attr('fill', (d) => color(d.data.group ?? 0))
    .attr('stroke', 'hsl(var(--background))')
    .attr('stroke-width', 2)

  node.append('text')
    .text((d) => { const n = d.data.name; return n.length > 14 ? n.slice(0, 13) + '…' : n })
    .attr('x', (d) => d.children ? -12 : 12)
    .attr('y', 4)
    .attr('text-anchor', (d) => d.children ? 'end' : 'start')
    .attr('font-size', '11px')
    .attr('fill', 'hsl(var(--foreground))')
    .attr('opacity', (d) => d.data.id === '__virtual__' ? 0 : 1)

  node.append('title')
    .text((d) => d.data.name)

  // Auto-fit: center the tree (exclude the invisible virtual root from bounds)
  const visible = root.descendants().filter((d) => d.data.id !== '__virtual__')
  const x0 = visible.reduce((min, d) => Math.min(min, d.x), Infinity)
  const x1 = visible.reduce((max, d) => Math.max(max, d.x), -Infinity)
  const y0 = visible.reduce((min, d) => Math.min(min, d.y), Infinity)
  const y1 = visible.reduce((max, d) => Math.max(max, d.y), -Infinity)
  const treeW = y1 - y0
  const treeH = x1 - x0
  if (treeW > 0 && treeH > 0) {
    const scale = Math.min(0.9, (width - 40) / treeW, (height - 40) / treeH)
    const tx = (width - treeW * scale) / 2 - y0 * scale
    const ty = (height - treeH * scale) / 2 - x0 * scale
    g.attr('transform', `translate(${tx},${ty}) scale(${scale})`)
  }
}

function toggleLayout() {
  layoutMode.value = layoutMode.value === 'force' ? 'tree' : 'force'
  setTimeout(renderGraph, 50)
}

onMounted(() => {
  renderGraph()
  window.addEventListener('resize', renderGraph)
})

onUnmounted(() => {
  simulation?.stop()
  window.removeEventListener('resize', renderGraph)
})

watch(graph, () => {
  setTimeout(renderGraph, 100)
})

watch(layoutMode, () => {
  setTimeout(renderGraph, 50)
})
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">知识图谱</h1>
      <button
        @click="toggleLayout"
        class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
      >
        {{ layoutMode === 'force' ? '🔀 切换思维导图' : '🌀 切换力导向图' }}
      </button>
    </div>
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
