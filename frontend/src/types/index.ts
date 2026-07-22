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
  privacyStatus?: PrivacyStatus
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
  nodeType: 'summary' | 'entity' | 'concept' | 'other'
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

// ---- Insight / Self-Insight feature ----

export type PrivacyStatus = 'ANALYZE' | 'STORE' | 'LOCKED'
export type InsightType = 'WEEKLY' | 'MONTHLY'

export interface InsightReport {
  id: string
  reportType: InsightType
  dateStart: string
  dateEnd: string
  summary: string
  emotionCurve: string       // JSON string
  keywords: string           // JSON string
  lowPoint: string           // JSON string
  highPoint: string          // JSON string
  pattern: string            // 月报专用
  coreTheme: string          // 月报专用
  memoryCount: number
  isRead: boolean
  createdAt: string
  updatedAt: string
}

export interface InsightReportListItem {
  id: string
  reportType: InsightType
  dateStart: string
  dateEnd: string
  summary: string
  memoryCount: number
  isRead: boolean
  createdAt: string
}

export interface WeeklyStatus {
  weekStart: string
  exists: boolean
  reportId: string | null
  hasNewMemories: boolean
}

export interface InsightArchive {
  total: number
  items: InsightReportListItem[]
}

export interface EmotionCurvePoint {
  date?: string
  weekStart?: string
  score: number
  avgScore?: number
}

export interface KeywordPoint {
  date?: string
  title?: string
  preview?: string
  titlesSummary?: string
  weekStart?: string
}

// ---- Time Capsule feature ----

export type CapsuleStatus = 'SEALED' | 'OPENED' | 'FORCED_OPEN'

export interface TimeCapsule {
  id: string
  memoryId: string | null
  content: string | null
  title: string
  openDate: string
  buriedDate: string
  status: CapsuleStatus
  openedAt: string | null
  isForced: boolean
  message: string | null
  memoryTitle: string | null
  sourceType: 'memory' | 'custom'
  createdAt: string
  updatedAt: string
}

export interface TimeCapsuleDetail extends TimeCapsule {
  memoryContent: string | null
  memoryType: string | null
}

export interface CapsuleStats {
  waitingCount: number
  openedCount: number
  forcedCount: number
  readyCount: number
}

export interface CapsulePagedResult {
  content: TimeCapsule[]
  page: number
  size: number
  totalElements: number
  totalPages: number
  last: boolean
  first: boolean
}
