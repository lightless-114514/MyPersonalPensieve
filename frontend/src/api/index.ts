﻿import axios from 'axios'
import { useSettingsStore } from '@/stores/settings'
import type {
  Memory,
  SearchResult,
  KnowledgeGraph,
  SentimentTrend,
  ProcessingProgress,
  TagItem,
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

export async function updateMemory(id: string, payload: any) {
  const { data } = await api.put<Memory>(`/memories/${id}`, payload)
  return data
}

export async function getMemories(params: { page?: number; size?: number }) {
  const { data } = await api.get<SearchResult>('/memories', { params })
  return data
}

export async function getRecentMemories(limit: number = 10) {
  const { data } = await api.get<Memory[]>('/memories/recent', { params: { limit } })
  return data
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
