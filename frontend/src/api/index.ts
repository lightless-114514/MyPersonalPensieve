import axios from 'axios'
import type {
  Memory,
  SearchResult,
  KnowledgeGraph,
  SentimentTrend,
  ProcessingProgress,
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

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

api.interceptors.response.use((response) => {
  if (response.data) {
    response.data = convertKeys(response.data)
  }
  return response
})

// Memories
export async function createMemory(payload: {
  title: string
  content: string
  type: string
  sourceUrl?: string
  tags?: string[]
}) {
  const { data } = await api.post<Memory>('/memories', payload)
  return data
}

export async function getMemories(params: {
  page?: number
  size?: number
}) {
  const { data } = await api.get<SearchResult>('/memories', { params })
  return data
}

export async function getRecentMemories(limit: number = 10) {
  const { data } = await api.get<Memory[]>('/memories/recent', {
    params: { limit },
  })
  return data
}

export async function getMemory(id: string) {
  const { data } = await api.get<Memory>(`/memories/${id}`)
  return data
}

export async function deleteMemory(id: string) {
  await api.delete(`/memories/${id}`)
}

// Knowledge Graph
export async function getKnowledgeGraph() {
  const { data } = await api.get<KnowledgeGraph>('/graph')
  return data
}

// Sentiment
export async function getSentimentTrend(days: number = 30) {
  const { data } = await api.get<SentimentTrend[]>('/analytics/sentiment', {
    params: { days },
  })
  return data
}

// SSE progress
export function subscribeProgress(
  taskId: string,
  onProgress: (p: ProcessingProgress) => void,
  onError: (e: Event) => void
) {
  const es = new EventSource(`/api/memories/progress/${taskId}`)
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