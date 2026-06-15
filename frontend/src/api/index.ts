import axios from 'axios'
import type {
  Memory,
  SearchQuery,
  SearchResult,
  KnowledgeGraph,
  SentimentTrend,
  ProcessingProgress,
} from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Memories
export async function createMemory(formData: FormData) {
  const { data } = await api.post<ProcessingProgress>('/memories', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function searchMemories(query: SearchQuery) {
  const { data } = await api.post<SearchResult>('/memories/search', query)
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
