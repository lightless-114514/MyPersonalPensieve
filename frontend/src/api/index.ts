﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿import axios from 'axios'
import { useSettingsStore } from '@/stores/settings'
import type {
  Memory,
  SearchResult,
  KnowledgeGraph,
  SentimentTrend,
  ProcessingProgress,
  TagItem,
  HeatmapDay,
  WordCloudItem,
  StatsSummary,
  CompareResult,
  InsightReport,
  InsightReportListItem,
  WeeklyStatus,
  InsightArchive,
  TimeCapsule,
  TimeCapsuleDetail,
  CapsuleStats,
  CapsulePagedResult,
} from '@/types'

function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, c) => c.toUpperCase())
}

function convertKeys(obj: any): any {
  if (Array.isArray(obj)) return obj.map(convertKeys)
  if (obj !== null && typeof obj === 'object' && !(obj instanceof FormData)) {
    const converted: any = {}
    for (const [key, value] of Object.entries(obj)) {
      converted[snakeToCamel(key)] = convertKeys(value)
    }
    return converted
  }
  return obj
}

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const settings = useSettingsStore()
  if (settings.apiKey) {
    config.headers['X-API-Key'] = settings.apiKey
  }
  return config
})

api.interceptors.response.use((response) => {
  if (response.data) {
    response.data = convertKeys(response.data)
  }
  return response
})

export async function createMemory(payload: any) {
  const { data } = await api.post<Memory>('/memories', payload)
  return data
}

export async function uploadMemoryFile(file: File, options: {
  title?: string
  content?: string
  sourceUrl?: string
  tags?: string[]
  bigTag?: string
} = {}) {
  const formData = new FormData()
  formData.append('file', file)
  if (options.title) formData.append('title', options.title)
  if (options.content) formData.append('content', options.content)
  if (options.sourceUrl) formData.append('source_url', options.sourceUrl)
  if (options.tags?.length) formData.append('tags', options.tags.join(','))
  if (options.bigTag) formData.append('big_tag', options.bigTag)
  const { data } = await api.post<Memory>('/files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
  return data
}

export function getFilePreviewUrl(memoryId: string): string {
  // 添加时间戳防止浏览器缓存旧的 404 响应
  return `${API_BASE}/files/${memoryId}/download?t=${Date.now()}`
}

export async function updateMemory(id: string, payload: any) {
  const { data } = await api.put<Memory>(`/memories/${id}`, payload)
  return data
}

export async function getMemories(params: { page?: number; size?: number; favorite?: boolean }) {
  const { data } = await api.get<SearchResult>('/memories', { params })
  return data
}

export async function getRecentMemories(limit: number = 10) {
  const { data } = await api.get<Memory[]>('/memories/recent', { params: { limit } })
  return data
}

export async function getAllMemoriesForExport(): Promise<Memory[]> {
  const all: Memory[] = []
  let page = 0
  let last = false
  while (!last) {
    const res = await getMemories({ page, size: 100 })
    if (res.content?.length) all.push(...res.content)
    last = res.last
    page++
  }
  return all
}

export async function getMemory(id: string) {
  const { data } = await api.get<Memory>(`/memories/${id}`)
  return data
}

export async function deleteMemory(id: string) {
  await api.delete(`/memories/${id}`)
}

export async function getTags(q?: string, limit?: number) {
  const { data } = await api.get<TagItem[]>('/memories/tags', { params: { q, limit } })
  return data
}

export async function getKnowledgeGraph(bigTag?: string) {
  const { data } = await api.get<KnowledgeGraph>('/graph', {
    params: bigTag ? { big_tag: bigTag } : {},
  })
  return data
}

export async function getSentimentTrend(days: number = 30, bigTag?: string) {
  const { data } = await api.get<SentimentTrend[]>('/analytics/sentiment', {
    params: { days, ...(bigTag ? { big_tag: bigTag } : {}) },
  })
  return data
}

export async function toggleFavoriteMemory(id: string, favorite: boolean) {
  const { data } = await api.put<Memory>(`/memories/${id}`, { favorite })
  return data
}

export async function getHeatmap(year?: number) {
  const params: any = {}
  if (year) params.year = year
  const { data } = await api.get<HeatmapDay[]>('/analytics/heatmap', { params })
  return data
}

export async function getWordCloud(period: string = 'month', limit: number = 80) {
  const { data } = await api.get<WordCloudItem[]>('/analytics/wordcloud', {
    params: { period, limit },
  })
  return data
}

export async function getStats() {
  const { data } = await api.get<StatsSummary>('/analytics/stats')
  return data
}

export async function compareMemories(sourceIds: string[], targetIds: string[]) {
  const { data } = await api.post<CompareResult>('/compare', {
    source_ids: sourceIds,
    target_ids: targetIds,
  }, { timeout: 120000 })
  return data
}

export function subscribeProgress(
  taskId: string,
  onProgress: (p: ProcessingProgress) => void,
  onError: (e: Event) => void
) {
  const es = new EventSource(`${API_BASE}/memories/progress/${taskId}`)
  es.onmessage = (event) => {
    const progress: ProcessingProgress = JSON.parse(event.data)
    onProgress(progress)
    if (progress.status === 'COMPLETED' || progress.status === 'FAILED') {
      es.close()
    }
  }
  es.onerror = (e) => {
    onError(e)
    es.close()
  }
  return es
}

// ---- Insight / Self-Insight APIs ----

export async function getWeeklyStatus(weekStart: string) {
  const { data } = await api.get<WeeklyStatus>('/insight/weekly/status', {
    params: { weekStart },
  })
  return data
}

export async function getWeeklyReport(weekStart: string) {
  const { data } = await api.get<InsightReport>('/insight/weekly', {
    params: { weekStart },
  })
  return data
}

export async function getMonthlyReport(monthStart: string) {
  const { data } = await api.get<InsightReport>('/insight/monthly', {
    params: { monthStart },
  })
  return data
}

export async function getInsightArchive(page: number = 0, size: number = 20) {
  const { data } = await api.get<InsightArchive>('/insight/archive', {
    params: { page, size },
  })
  return data
}

export async function getInsightReportDetail(reportId: string) {
  const { data } = await api.get<InsightReport>(`/insight/archive/${reportId}`)
  return data
}

export async function generateWeeklyReport(weekStart: string) {
  const { data } = await api.post<InsightReport>('/insight/generate/weekly', {
    week_start: weekStart,
  }, { timeout: 120000 })
  return data
}

export async function generateMonthlyReport(monthStart: string) {
  const { data } = await api.post<InsightReport>('/insight/generate/monthly', {
    month_start: monthStart,
  }, { timeout: 300000 })
  return data
}

export async function deleteInsightReport(reportId: string) {
  await api.delete(`/insight/archive/${reportId}`)
}

// ---- Birthday APIs ----

export interface BirthdayWishResponse {
  wish: string
  fallback: boolean
}

export async function generateBirthdayWish() {
  const { data } = await api.post<BirthdayWishResponse>('/birthday/wish', {}, { timeout: 30000 })
  return data
}

// ---- Time Capsule APIs ----

export async function createCapsule(payload: {
  memoryId: string
  title: string
  openDate: string
  message?: string
}) {
  const { data } = await api.post<TimeCapsule>('/capsules', {
    memory_id: payload.memoryId,
    title: payload.title,
    open_date: payload.openDate,
    message: payload.message || null,
  })
  return data
}

export async function getCapsuleStats() {
  const { data } = await api.get<CapsuleStats>('/capsules/stats')
  return data
}

export async function checkReadyCapsules() {
  const { data } = await api.get<Array<{
    id: string
    title: string
    openDate: string
    buriedDate: string
  }>>('/capsules/check-ready')
  return data
}

export async function getCapsules(params: {
  page?: number
  size?: number
  status?: string
  search?: string
}) {
  const { data } = await api.get<CapsulePagedResult>('/capsules', { params })
  return data
}

export async function getCapsuleDetail(capsuleId: string) {
  const { data } = await api.get<TimeCapsuleDetail>(`/capsules/${capsuleId}`)
  return data
}

export async function openCapsule(capsuleId: string) {
  const { data } = await api.post<TimeCapsuleDetail>(`/capsules/${capsuleId}/open`)
  return data
}

export async function forceOpenCapsule(capsuleId: string) {
  const { data } = await api.post<TimeCapsuleDetail>(`/capsules/${capsuleId}/force-open`)
  return data
}

export async function deleteCapsule(capsuleId: string) {
  await api.delete(`/capsules/${capsuleId}`)
}
