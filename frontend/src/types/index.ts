export interface Memory {
  id: string
  title: string
  content: string
  type: 'TEXT' | 'IMAGE'
  source_url?: string | null
  file_path?: string | null
  sentiment?: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL' | null
  sentiment_score?: number | null
  processing_status: string
  tags: string[]
  big_tag?: BigTagCategory | null
  created_at: string
  updated_at: string
  // convenience aliases
  sourceUrl?: string
  filePath?: string
  sentimentScore?: number
  processingStatus?: string
  bigTag?: BigTagCategory | null
  favorite?: boolean
  createdAt?: string
  updatedAt?: string
  entities?: Entity[]
}

export type BigTagCategory = 'KNOWLEDGE_POINT' | 'FREEFORM_NOTE' | 'INSPIRATION_FLASH' | 'DECISION_DILEMMA'

export interface Entity {
  id: string
  name: string
  type: 'PERSON' | 'PLACE' | 'ORG' | 'EVENT' | 'TOPIC' | 'TECHNOLOGY' | 'OTHER'
}

export interface Relationship {
  id: string
  sourceId: string
  targetId: string
  type: string
  strength: number
}

export interface TagItem {
  tag: string
  count: number
}

export interface SearchResult {
  content: Memory[]
  total_elements: number
  total_pages: number
  page: number
  size: number
  last: boolean
  first: boolean
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
