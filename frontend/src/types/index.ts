export interface Memory {
  id: string
  title: string
  content: string
  type: 'TEXT' | 'IMAGE' | 'AUDIO' | 'LINK'
  sourceUrl?: string
  filePath?: string
  sentiment?: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL'
  sentimentScore?: number
  entities: Entity[]
  tags: string[]
  createdAt: string
  updatedAt: string
}

export interface Entity {
  id: string
  name: string
  type: 'PERSON' | 'PLACE' | 'ORG' | 'EVENT' | 'TOPIC' | 'OTHER'
  relationships: Relationship[]
}

export interface Relationship {
  id: string
  sourceId: string
  targetId: string
  type: string
  strength: number
}

export interface SearchQuery {
  query: string
  type?: string
  sentiment?: string
  tags?: string[]
  entities?: string[]
  startDate?: string
  endDate?: string
  page?: number
  size?: number
}

export interface SearchResult {
  content: Memory[]
  totalElements: number
  totalPages: number
  page: number
}

export interface KnowledgeGraph {
  nodes: GraphNode[]
  links: GraphLink[]
}

export interface GraphNode {
  id: string
  name: string
  type: string
  group: number
}

export interface GraphLink {
  source: string
  target: string
  type: string
  strength: number
}

export interface SentimentTrend {
  date: string
  positive: number
  negative: number
  neutral: number
  average: number
}

export interface ProcessingProgress {
  taskId: string
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
  progress: number
  message: string
}
