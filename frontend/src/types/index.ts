export interface Memory {
  id: string
  title: string
  content: string
  type: 'TEXT' | 'IMAGE' | 'FILE'
  source_url?: string | null
  file_path?: string | null
  file_size?: number | null
  mime_type?: string | null
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
  fileSize?: number
  mimeType?: string
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

export interface HeatmapDay {
  date: string
  memory_count: number
  word_count: number
}

export interface WordCloudItem {
  word: string
  count: number
}

export interface StatsSummary {
  total_memories: number
  total_words: number
  streak_days: number
  this_month: number
}

// ---- Compare feature ----

export interface ComparePoint {
  content: string
  sourceRefs?: string[]
  targetRefs?: string[]
}

export interface CompareResult {
  similarities: ComparePoint[]
  differences: ComparePoint[]
  sourceSummary: string
  targetSummary: string
  timeSpanDays: number | null
  earliestDate: string | null
  latestDate: string | null
  sourceCount: number
  targetCount: number
  sourceTags: string[]
  targetTags: string[]
  growthInsight: string | null
}
