<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { getKnowledgeGraph, getMemory } from '@/api'
import { BIG_TAG_OPTIONS, bigTagClass, bigTagLabel } from '@/lib/utils'
import type { BigTagCategory, GraphNode, GraphLink } from '@/types'
import * as d3 from 'd3'
import { GitBranch, Network, Maximize2, Eye, EyeOff, X, ChevronRight } from 'lucide-vue-next'

// ─── Refs & State ───────────────────────────────────────────────
const container = ref<HTMLDivElement>()
const layoutMode = ref<'force' | 'tree'>('force')
const filterBigTag = ref<BigTagCategory | ''>('')
const showArrows = ref(true)
const showLegend = ref(true)

// Detail panel
const detailPanel = ref<{ visible: boolean; node: any }>({ visible: false, node: null })
const detailLoading = ref(false)
const detailMemory = ref<any>(null)

// ─── Node type color mapping ────────────────────────────────────
const NODE_COLORS: Record<string, string> = {
  summary: '#3b82f6',  // blue
  entity: '#22c55e',   // green
  concept: '#eab308',  // yellow
  other: '#9ca3af',    // gray
}

const NODE_LABELS: Record<string, string> = {
  summary: '摘要',
  entity: '实体',
  concept: '概念',
  other: '其他',
}

function getNodeColor(d: any): string {
  const nt = d.nodeType || d.data?.nodeType || 'other'
  return NODE_COLORS[nt] || NODE_COLORS.other
}

// ─── Tooltip ────────────────────────────────────────────────────
const tooltip = ref({ visible: false, x: 0, y: 0, text: '', nodeId: '', nodeX: 0, nodeY: 0, nodeType: '' })

function showTooltip(event: MouseEvent, text: string, nodeId?: string, nodeType?: string) {
  if (!container.value) return
  tooltip.value = {
    visible: true,
    x: 0,
    y: 0,
    text,
    nodeId: nodeId || '',
    nodeX: 0,
    nodeY: 0,
    nodeType: nodeType || '',
  }
  _positionTooltip(event)
}

function moveTooltip(event: MouseEvent) {
  if (!tooltip.value.visible || !container.value) return
  _positionTooltip(event)
}

function _positionTooltip(event: MouseEvent) {
  if (!container.value) return
  const rect = container.value.getBoundingClientRect()
  const tipW = 200
  const tipH = 28
  let x = event.clientX - rect.left + 12
  let y = event.clientY - rect.top - tipH - 8
  x = Math.min(x, rect.width - tipW - 8)
  x = Math.max(x, 8)
  y = Math.min(y, rect.height - tipH - 8)
  y = Math.max(y, 8)
  tooltip.value.x = x
  tooltip.value.y = y
}

function hideTooltip() {
  tooltip.value.visible = false
}

// ─── Data query ─────────────────────────────────────────────────
const { data: graph } = useQuery({
  queryKey: computed(() => ['knowledge-graph', filterBigTag.value]),
  queryFn: () => getKnowledgeGraph(filterBigTag.value || undefined),
})

let simulation: d3.Simulation<any, any> | null = null
let isUnmounted = false
let pendingTimers: number[] = []
let currentZoom: d3.ZoomBehavior<SVGSVGElement, unknown> | null = null
let currentG: d3.Selection<SVGGElement, unknown, null, undefined> | null = null
let currentSvg: d3.Selection<SVGSVGElement, unknown, null, undefined> | null = null

// Track all nodes/links currently on canvas for incremental additions
let canvasNodes: any[] = []
let canvasLinks: any[] = []
let nodeById: Map<string, any> = new Map()

function safeTimeout(fn: () => void, delay: number) {
  const id = window.setTimeout(() => {
    pendingTimers = pendingTimers.filter(t => t !== id)
    if (!isUnmounted) fn()
  }, delay)
  pendingTimers.push(id)
  return id
}

// ─── Build hierarchy for tree layout ────────────────────────────
function buildHierarchy(nodes: any[], links: any[]) {
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

  const connectedNodes = nodes.filter(n => adj.has(n.id) && adj.get(n.id)!.length > 0)
  const isolatedNodes = nodes.filter(n => !adj.has(n.id) || adj.get(n.id)!.length === 0)

  if (connectedNodes.length === 0) return null

  let rootId = connectedNodes[0].id
  let maxDeg = -1
  connectedNodes.forEach(n => {
    const deg = (adj.get(n.id) || []).length
    if (deg > maxDeg) { maxDeg = deg; rootId = n.id }
  })

  const root = nodeMap.get(rootId)!
  root._depth = 0

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

  const virtualRoot = {
    id: '__virtual__',
    name: '',
    type: 'VIRTUAL',
    nodeType: 'other',
    group: -1,
    children: [root, ...extraRoots] as any[],
    _depth: -1,
  }
  root._depth = 0
  extraRoots.forEach((r: any) => { r._depth = 0 })

  if (isolatedNodes.length > 0) {
    isolatedNodes.forEach(n => {
      const node = nodeMap.get(n.id)!
      node._depth = 1
      node.children = []
      virtualRoot.children.push(node)
    })
  }

  return virtualRoot
}

// ─── Neighbor helper ────────────────────────────────────────────
function getNeighborIds(nodeId: string, links: any[]): string[] {
  const neighbors = new Set<string>()
  links.forEach(l => {
    const s = typeof l.source === 'object' ? l.source.id : l.source
    const t = typeof l.target === 'object' ? l.target.id : l.target
    if (s === nodeId) neighbors.add(t)
    if (t === nodeId) neighbors.add(s)
  })
  return [...neighbors]
}

// ─── Add neighbors to canvas (Shift+Click / ⊕) ────────────────
function addNeighborsToCanvas(d: any) {
  if (!graph.value) return
  const allLinks = graph.value.links
  const allNodes = graph.value.nodes
  const neighborIds = getNeighborIds(d.id, allLinks)
  let added = false

  neighborIds.forEach(nid => {
    if (!nodeById.has(nid)) {
      const nodeData = allNodes.find(n => n.id === nid)
      if (nodeData) {
        const baseX = (d as any).x ?? 0
        const baseY = (d as any).y ?? 0
        const newNode = { ...nodeData, x: baseX + (Math.random() - 0.5) * 80, y: baseY + (Math.random() - 0.5) * 80 }
        canvasNodes.push(newNode)
        nodeById.set(nid, newNode)
        added = true
      }
    }
  })

  // Add links for newly added nodes
  if (added) {
    allLinks.forEach(l => {
      const s: string = typeof (l as any).source === 'object' ? ((l as any).source as any).id : (l as any).source as string
      const t: string = typeof (l as any).target === 'object' ? ((l as any).target as any).id : (l as any).target as string
      if (nodeById.has(s) && nodeById.has(t)) {
        const exists = canvasLinks.some(cl => {
          const cs: string = typeof (cl as any).source === 'object' ? ((cl as any).source as any).id : (cl as any).source as string
          const ct: string = typeof (cl as any).target === 'object' ? ((cl as any).target as any).id : (cl as any).target as string
          return (cs === s && ct === t) || (cs === t && ct === s)
        })
        if (!exists) {
          canvasLinks.push({ source: s, target: t, type: (l as any).type, strength: (l as any).strength })
        }
      }
    })
    renderGraph()
  }
}

// ─── Focus on node (Double-click) ──────────────────────────────
function focusOnNode(d: any) {
  if (!currentSvg || !currentG || !currentZoom) return
  const width = container.value!.clientWidth
  const height = container.value!.clientHeight
  const scale = 1.5
  const transform = d3.zoomIdentity
    .translate(width / 2 - d.x * scale, height / 2 - d.y * scale)
    .scale(scale)
  currentSvg.transition().duration(750).call(currentZoom.transform, transform)
}

// ─── Open detail panel (Single-click) ──────────────────────────
async function openDetail(d: any) {
  detailPanel.value = { visible: true, node: d }
  // If it's a summary (memory) node, load memory details
  if (d.nodeType === 'summary' && d.id.startsWith('memory_')) {
    const memId = d.id.replace('memory_', '')
    detailLoading.value = true
    try {
      detailMemory.value = await getMemory(memId)
    } catch {
      detailMemory.value = null
    } finally {
      detailLoading.value = false
    }
  } else {
    detailMemory.value = null
  }
}

function closeDetail() {
  detailPanel.value = { visible: false, node: null }
  detailMemory.value = null
}

// ─── Fit to screen ─────────────────────────────────────────────
function fitToScreen() {
  if (!currentSvg || !currentG || !currentZoom || !container.value) return
  const width = container.value.clientWidth
  const height = container.value.clientHeight
  const bbox = (currentG.node() as SVGGElement).getBBox()
  if (bbox.width === 0 || bbox.height === 0) return
  const scale = Math.min(
    0.9,
    width / (bbox.width + 60),
    height / (bbox.height + 60)
  )
  const tx = width / 2 - (bbox.x + bbox.width / 2) * scale
  const ty = height / 2 - (bbox.y + bbox.height / 2) * scale
  currentSvg.transition().duration(750).call(
    currentZoom.transform,
    d3.zoomIdentity.translate(tx, ty).scale(scale)
  )
}

// ─── Render graph ──────────────────────────────────────────────
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

  currentSvg = svg

  // Arrow marker definition
  svg.append('defs').append('marker')
    .attr('id', 'arrowhead')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 20)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', 'hsl(var(--muted-foreground))')

  const g = svg.append('g')
  currentG = g

  const zoom = d3.zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.1, 5])
    .on('zoom', (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
      g.attr('transform', event.transform as any)
    })
  svg.call(zoom)
  currentZoom = zoom

  // Initialize canvas nodes and links
  canvasNodes = graph.value.nodes.map((n) => ({ ...n }))
  canvasLinks = graph.value.links.map((l) => ({ ...l }))
  nodeById = new Map(canvasNodes.map(n => [n.id, n]))

  if (canvasNodes.length === 0) return

  simulation = d3.forceSimulation(canvasNodes as any)
    .force('link', d3.forceLink(canvasLinks).id((d: any) => d.id).distance(100))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide(30))

  // Links
  const link = g.append('g')
    .selectAll('line')
    .data(canvasLinks)
    .join('line')
    .attr('stroke', 'hsl(var(--border))')
    .attr('stroke-width', 1.5)
    .attr('marker-end', showArrows.value ? 'url(#arrowhead)' : null)

  // Node groups
  const node = g.append('g')
    .selectAll('g')
    .data(canvasNodes)
    .join('g')
    .style('cursor', 'pointer')

  // Circles with color by nodeType
  node.append('circle')
    .attr('r', (d: any) => d.nodeType === 'summary' ? 12 : 8)
    .attr('fill', (d: any) => getNodeColor(d))
    .attr('stroke', 'hsl(var(--background))')
    .attr('stroke-width', 2)

  // Labels
  node.append('text')
    .text((d: any) => { const n = d.name; return n.length > 12 ? n.slice(0, 11) + '…' : n })
    .attr('x', (d: any) => d.nodeType === 'summary' ? 16 : 12)
    .attr('y', 4)
    .attr('font-size', '11px')
    .attr('fill', 'hsl(var(--foreground))')
    .style('pointer-events', 'none')

  // ─── ⊕ expand button on node top-right ────────────────────
  const nodeRadius = (d: any) => d.nodeType === 'summary' ? 12 : 8
  node.append('circle')
    .attr('class', 'expand-btn')
    .attr('cx', (d: any) => nodeRadius(d) * 0.7)
    .attr('cy', (d: any) => -nodeRadius(d) * 0.7)
    .attr('r', 7)
    .attr('fill', 'hsl(var(--primary))')
    .attr('stroke', 'hsl(var(--background))')
    .attr('stroke-width', 1.5)
    .attr('opacity', 0)
    .style('cursor', 'pointer')
    .style('pointer-events', 'all')

  node.append('text')
    .attr('class', 'expand-btn-text')
    .attr('x', (d: any) => nodeRadius(d) * 0.7)
    .attr('y', (d: any) => -nodeRadius(d) * 0.7 + 4)
    .attr('text-anchor', 'middle')
    .attr('font-size', '10px')
    .attr('font-weight', 'bold')
    .attr('fill', 'hsl(var(--primary-foreground))')
    .attr('opacity', 0)
    .style('pointer-events', 'none')
    .text('+')

  // ─── Drag behavior ─────────────────────────────────────────
  const drag = d3.drag<any, any>()
    .on('start', (event: any, d: any) => {
      if (!event.active) simulation?.alphaTarget(0.3).restart()
      d.fx = d.x
      d.fy = d.y
    })
    .on('drag', (event: any, d: any) => {
      d.fx = event.x
      d.fy = event.y
    })
    .on('end', (event: any, d: any) => {
      if (!event.active) simulation?.alphaTarget(0)
      d.fx = null
      d.fy = null
    })
  node.call(drag as any)

  // ─── Click: open detail ────────────────────────────────────
  let clickTimer: number | null = null
  node.on('click', (event: MouseEvent, d: any) => {
    if (event.shiftKey) {
      // Shift + Click: add neighbors
      event.preventDefault()
      addNeighborsToCanvas(d)
      return
    }
    // Distinguish single/double click
    if (clickTimer !== null) {
      clearTimeout(clickTimer)
      clickTimer = null
      return // double click will handle
    }
    clickTimer = window.setTimeout(() => {
      clickTimer = null
      openDetail(d)
    }, 250)
  })

  // ─── Double-click: focus on node ───────────────────────────
  node.on('dblclick', (event: MouseEvent, d: any) => {
    event.preventDefault()
    if (clickTimer !== null) {
      clearTimeout(clickTimer)
      clickTimer = null
    }
    focusOnNode(d)
  })

  // ─── Hover: show tooltip + ⊕ button ──────────────────────
  node.on('mouseenter', function(event: MouseEvent, d: any) {
    showTooltip(event, d.name, d.id, d.nodeType)
    d3.select(this).selectAll('.expand-btn').attr('opacity', 1)
    d3.select(this).selectAll('.expand-btn-text').attr('opacity', 1)
  })
  node.on('mousemove', function(event: MouseEvent) { moveTooltip(event) })
  node.on('mouseleave', function() {
    hideTooltip()
    d3.select(this).selectAll('.expand-btn').attr('opacity', 0)
    d3.select(this).selectAll('.expand-btn-text').attr('opacity', 0)
  })

  // ─── ⊕ button click: add neighbors ────────────────────────
  node.selectAll('.expand-btn')
    .on('click', (event: MouseEvent, d: any) => {
      event.stopPropagation()
      addNeighborsToCanvas(d)
    })

  // Tick
  simulation.on('tick', () => {
    link
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y)

    node.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
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

  currentSvg = svg

  // Arrow marker
  svg.append('defs').append('marker')
    .attr('id', 'arrowhead-tree')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 20)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', 'hsl(var(--muted-foreground))')

  const g = svg.append('g')
  currentG = g

  const zoom = d3.zoom<SVGSVGElement, unknown>()
    .scaleExtent([0.1, 5])
    .on('zoom', (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
      g.attr('transform', event.transform as any)
    })
  svg.call(zoom)
  currentZoom = zoom

  const root = d3.hierarchy<any>(rootData)
  const treeLayout = d3.tree<any>()
    .size([height - 80, width - 200])
    .separation((a: any, b: any) => (a.parent?.data.id === b.parent?.data.id ? 1.2 : 1.8))
  treeLayout(root)

  // Links
  g.append('g')
    .selectAll('path')
    .data(root.links().filter((l: any) => l.source.data.id !== '__virtual__'))
    .join('path')
    .attr('fill', 'none')
    .attr('stroke', 'hsl(var(--border))')
    .attr('stroke-width', 1.5)
    .attr('marker-end', showArrows.value ? 'url(#arrowhead-tree)' : null)
    .attr('d', d3.linkHorizontal<any, any>()
      .x((d: any) => d.y)
      .y((d: any) => d.x))

  // Nodes
  const node = g.append('g')
    .selectAll('g')
    .data(root.descendants())
    .join('g')
    .attr('transform', (d: any) => `translate(${d.y},${d.x})`)

  node.append('circle')
    .attr('r', (d: any) => d.data.id === '__virtual__' ? 0 : (d.depth === 1 ? 10 : 6))
    .attr('fill', (d: any) => getNodeColor(d.data))
    .attr('stroke', 'hsl(var(--background))')
    .attr('stroke-width', 2)

  node.append('text')
    .text((d: any) => { const n = d.data.name; return n.length > 14 ? n.slice(0, 13) + '…' : n })
    .attr('x', (d: any) => d.children ? -12 : 12)
    .attr('y', 4)
    .attr('text-anchor', (d: any) => d.children ? 'end' : 'start')
    .attr('font-size', '11px')
    .attr('fill', 'hsl(var(--foreground))')
    .attr('opacity', (d: any) => d.data.id === '__virtual__' ? 0 : 1)
    .style('pointer-events', 'none')



  // Click handlers for tree
  let clickTimer: number | null = null
  node
    .style('cursor', 'pointer')
    .on('click', (event: MouseEvent, d: any) => {
      if (d.data.id === '__virtual__') return
      if (event.shiftKey) {
        event.preventDefault()
        addNeighborsToCanvas(d.data)
        return
      }
      if (clickTimer !== null) {
        clearTimeout(clickTimer)
        clickTimer = null
        return
      }
      clickTimer = window.setTimeout(() => {
        clickTimer = null
        openDetail(d.data)
      }, 250)
    })
    .on('dblclick', (event: MouseEvent, d: any) => {
      if (d.data.id === '__virtual__') return
      event.preventDefault()
      if (clickTimer !== null) {
        clearTimeout(clickTimer)
        clickTimer = null
      }
      // Focus on tree node
      if (!currentSvg || !currentZoom || !container.value) return
      const w = container.value.clientWidth
      const h = container.value.clientHeight
      const scale = 1.5
      const transform = d3.zoomIdentity.translate(w / 2 - d.y * scale, h / 2 - d.x * scale).scale(scale)
      currentSvg.transition().duration(750).call(currentZoom.transform, transform)
    })
    .on('mouseenter', function(event: MouseEvent, d: any) {
      if (d.data.id !== '__virtual__') {
        showTooltip(event, d.data.name, d.data.id, d.data.nodeType)
      }
    })
    .on('mousemove', function(event: MouseEvent) { moveTooltip(event) })
    .on('mouseleave', function() {
      hideTooltip()
    })



  // Auto-fit
  const visible = root.descendants().filter((d: any) => d.data.id !== '__virtual__')
  const x0 = visible.reduce((min: number, d: any) => Math.min(min, d.x), Infinity)
  const x1 = visible.reduce((max: number, d: any) => Math.max(max, d.x), -Infinity)
  const y0 = visible.reduce((min: number, d: any) => Math.min(min, d.y), Infinity)
  const y1 = visible.reduce((max: number, d: any) => Math.max(max, d.y), -Infinity)
  const treeW = y1 - y0
  const treeH = x1 - x0
  if (treeW > 0 && treeH > 0) {
    const scale = Math.min(0.9, (width - 40) / treeW, (height - 40) / treeH)
    const tx = (width - treeW * scale) / 2 - y0 * scale
    const ty = (height - treeH * scale) / 2 - x0 * scale
    g.attr('transform', `translate(${tx},${ty}) scale(${scale})`)
  }
}

// ─── Toggle functions ───────────────────────────────────────────
function toggleLayout() {
  layoutMode.value = layoutMode.value === 'force' ? 'tree' : 'force'
  safeTimeout(renderGraph, 50)
}

function setFilter(bigTag: BigTagCategory | '') {
  filterBigTag.value = filterBigTag.value === bigTag ? '' : bigTag
}

function toggleArrows() {
  showArrows.value = !showArrows.value
  renderGraph()
}

function handleResize() {
  renderGraph()
}

// ─── Lifecycle ──────────────────────────────────────────────────
onMounted(() => {
  renderGraph()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  isUnmounted = true
  pendingTimers.forEach(id => window.clearTimeout(id))
  pendingTimers = []
  if (simulation) {
    simulation.on('tick', null)
    simulation.stop()
    simulation = null
  }
  if (container.value) {
    d3.select(container.value).selectAll('svg').remove()
  }
  window.removeEventListener('resize', handleResize)
})

watch(graph, () => {
  safeTimeout(renderGraph, 100)
})

watch(layoutMode, () => {
  safeTimeout(renderGraph, 50)
})

watch(showArrows, () => {
  // Already handled in toggleArrows via renderGraph
})
</script>

<template>
  <div class="space-y-4 animate-fade-in">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold tracking-tight font-display">知识图谱</h1>
      <div class="flex items-center gap-2">
        <button
          @click="fitToScreen"
          class="inline-flex items-center gap-1.5 px-3 py-2 bg-secondary text-secondary-foreground rounded-lg text-sm font-medium hover:bg-secondary/80 transition-all duration-200"
          title="适应屏幕"
        >
          <Maximize2 class="w-4 h-4" />
        </button>
        <button
          @click="toggleArrows"
          class="inline-flex items-center gap-1.5 px-3 py-2 bg-secondary text-secondary-foreground rounded-lg text-sm font-medium hover:bg-secondary/80 transition-all duration-200"
          :title="showArrows ? '隐藏箭头' : '显示箭头'"
        >
          <EyeOff v-if="showArrows" class="w-4 h-4" />
          <Eye v-else class="w-4 h-4" />
        </button>
        <button
          @click="toggleLayout"
          class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-all duration-200 shadow-sm hover:shadow-md active:scale-[0.98]"
        >
          {{ layoutMode === 'force' ? '切换思维导图' : '切换力导向图' }}
          <GitBranch v-if="layoutMode === 'force'" class="w-4 h-4" />
          <Network v-else class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Big tag filter buttons -->
    <div class="flex flex-wrap items-center gap-2">
      <span class="text-sm text-muted-foreground mr-1">筛选大标签：</span>
      <button
        @click="setFilter('')"
        :class="[
          'px-3 py-1.5 rounded-full text-xs font-medium border transition-all duration-200',
          !filterBigTag
            ? 'bg-primary text-primary-foreground border-primary shadow-sm'
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
          'inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all duration-200',
          filterBigTag === opt.value
            ? bigTagClass(opt.value) + ' shadow-sm'
            : 'bg-background text-muted-foreground border-border hover:border-muted-foreground'
        ]"
      >
        <component :is="opt.icon" class="w-3.5 h-3.5" />
        <span>{{ opt.label }}</span>
      </button>
    </div>

    <!-- Graph container -->
    <div
      ref="container"
      class="w-full h-[calc(100vh-14rem)] rounded-xl border border-border bg-card relative shadow-card overflow-hidden"
    >
      <div
        v-if="!graph?.nodes?.length"
        class="flex items-center justify-center h-full text-muted-foreground"
      >
        暂无图谱数据。添加更多记忆后，AI 会自动提取实体和关系。
      </div>

      <!-- Tooltip -->
      <div
        v-if="tooltip.visible"
        class="absolute z-50 px-3 py-1.5 text-xs bg-popover text-popover-foreground rounded-lg border border-border shadow-lg max-w-xs flex items-center gap-2 pointer-events-none"
        :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
      >
        <span
          class="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
          :style="{ backgroundColor: NODE_COLORS[tooltip.nodeType] || NODE_COLORS.other }"
        ></span>
        <span class="truncate">{{ tooltip.text }}</span>
      </div>

      <!-- Legend panel -->
      <div
        v-if="showLegend"
        class="absolute bottom-3 left-3 z-40 bg-popover/95 backdrop-blur-sm border border-border rounded-lg shadow-lg p-3 text-xs space-y-2 min-w-[140px]"
      >
        <div class="flex items-center justify-between mb-1">
          <span class="font-semibold text-sm text-popover-foreground">图例</span>
          <button @click="showLegend = false" class="text-muted-foreground hover:text-foreground transition-colors">
            <X class="w-3.5 h-3.5" />
          </button>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded-full flex-shrink-0" style="background-color: #3b82f6"></span>
          <span class="text-popover-foreground">摘要</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded-full flex-shrink-0" style="background-color: #22c55e"></span>
          <span class="text-popover-foreground">实体</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded-full flex-shrink-0" style="background-color: #eab308"></span>
          <span class="text-popover-foreground">概念</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="w-3 h-3 rounded-full flex-shrink-0" style="background-color: #9ca3af"></span>
          <span class="text-popover-foreground">其他</span>
        </div>
        <div class="border-t border-border pt-2 mt-1 space-y-1 text-muted-foreground">
          <div>单击 → 查看详情</div>
          <div>双击 → 聚焦节点</div>
          <div v-if="layoutMode === 'force'">Shift+单击 → 展开邻居</div>
          <div v-if="layoutMode === 'force'">节点 ⊕ → 展开邻居</div>
          <div>拖拽节点 → 调整位置</div>
          <div>拖拽空白 → 平移画布</div>
          <div>滚轮 → 缩放画布</div>
        </div>
      </div>

      <!-- Show legend button (when hidden) -->
      <button
        v-if="!showLegend"
        @click="showLegend = true"
        class="absolute bottom-3 left-3 z-40 bg-popover/95 backdrop-blur-sm border border-border rounded-lg shadow-lg p-2 text-muted-foreground hover:text-foreground transition-colors"
        title="显示图例"
      >
        <ChevronRight class="w-4 h-4" />
      </button>

      <!-- Detail panel (slide-in from right) -->
      <Transition name="slide">
        <div
          v-if="detailPanel.visible && detailPanel.node"
          class="absolute top-0 right-0 z-50 h-full w-80 bg-popover/98 backdrop-blur-sm border-l border-border shadow-xl overflow-y-auto"
        >
          <div class="p-4 space-y-4">
            <div class="flex items-center justify-between">
              <h3 class="text-lg font-semibold text-popover-foreground truncate">{{ detailPanel.node.name }}</h3>
              <button @click="closeDetail" class="text-muted-foreground hover:text-foreground transition-colors">
                <X class="w-5 h-5" />
              </button>
            </div>
            <div class="flex items-center gap-2">
              <span
                class="w-3 h-3 rounded-full flex-shrink-0"
                :style="{ backgroundColor: getNodeColor(detailPanel.node) }"
              ></span>
              <span class="text-sm text-muted-foreground">
                {{ NODE_LABELS[detailPanel.node.nodeType] || '未知' }}
              </span>
              <span class="text-sm text-muted-foreground">·</span>
              <span class="text-sm text-muted-foreground">{{ detailPanel.node.type }}</span>
            </div>
            <!-- Memory detail for summary nodes -->
            <div v-if="detailPanel.node.nodeType === 'summary'" class="space-y-3">
              <div v-if="detailLoading" class="text-sm text-muted-foreground">加载中...</div>
              <template v-else-if="detailMemory">
                <div class="text-sm text-muted-foreground">
                  <span class="font-medium text-popover-foreground">ID:</span>
                  {{ detailMemory.id?.slice(0, 12) }}...
                </div>
                <div v-if="detailMemory.content" class="space-y-1">
                  <span class="text-sm font-medium text-popover-foreground">内容</span>
                  <p class="text-sm text-muted-foreground line-clamp-6 whitespace-pre-wrap">{{ detailMemory.content }}</p>
                </div>
                <div v-if="detailMemory.tags?.length" class="space-y-1">
                  <span class="text-sm font-medium text-popover-foreground">标签</span>
                  <div class="flex flex-wrap gap-1">
                    <span
                      v-for="tag in detailMemory.tags"
                      :key="tag"
                      class="px-2 py-0.5 bg-secondary text-secondary-foreground rounded text-xs"
                    >{{ tag }}</span>
                  </div>
                </div>
                <div v-if="detailMemory.createdAt" class="text-sm text-muted-foreground">
                  <span class="font-medium text-popover-foreground">创建时间:</span>
                  {{ new Date(detailMemory.createdAt).toLocaleString() }}
                </div>
              </template>
            </div>
            <!-- Entity/concept detail -->
            <div v-else class="space-y-2">
              <div class="text-sm text-muted-foreground">
                <span class="font-medium text-popover-foreground">类型:</span>
                {{ detailPanel.node.type }}
              </div>
              <div class="text-sm text-muted-foreground">
                <span class="font-medium text-popover-foreground">分类:</span>
                {{ NODE_LABELS[detailPanel.node.nodeType] || '未知' }}
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>