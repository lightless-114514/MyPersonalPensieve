import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { BigTagCategory } from '@/types'
import type { Component } from 'vue'
import { FileText, ImageIcon, File, BookOpen, PenLine, Lightbulb, Scale, FileSpreadsheet } from 'lucide-vue-next'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return d.toLocaleDateString('zh-CN')
}

export function sentimentColor(sentiment?: string): string {
  switch (sentiment) {
    case 'POSITIVE':
      return 'text-emerald-500'
    case 'NEGATIVE':
      return 'text-red-500'
    default:
      return 'text-muted-foreground'
  }
}

export function sentimentBg(sentiment?: string): string {
  switch (sentiment) {
    case 'POSITIVE':
      return 'bg-emerald-500/10'
    case 'NEGATIVE':
      return 'bg-red-500/10'
    default:
      return 'bg-muted'
  }
}

/** Returns a lucide-vue-next component for the given memory type */
export function typeIcon(type: string): Component {
  switch (type) {
    case 'TEXT':
      return FileText
    case 'IMAGE':
      return ImageIcon
    case 'FILE':
      return FileSpreadsheet
    default:
      return File
  }
}

/** 根据 MIME 类型返回文件类型图标名称 */
export function fileIconName(mimeType?: string | null): string {
  if (!mimeType) return 'file'
  if (mimeType.startsWith('image/')) return 'image'
  if (mimeType === 'application/pdf') return 'file-text'
  if (mimeType.includes('word') || mimeType.includes('document')) return 'file-text'
  if (mimeType === 'application/json') return 'file-json'
  if (mimeType.startsWith('text/')) return 'file-text'
  return 'file'
}

/** 格式化文件大小 */
export function formatFileSize(bytes?: number | null): string {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

// ---- Big Tag helpers ----

export const BIG_TAG_CONFIG: Record<BigTagCategory, { label: string; color: string; bg: string; border: string; icon: Component }> = {
  KNOWLEDGE_POINT:    { label: '知识点',   color: 'text-blue-700',    bg: 'bg-blue-100',    border: 'border-blue-300',    icon: BookOpen },
  FREEFORM_NOTE:      { label: '随心记述', color: 'text-emerald-700',  bg: 'bg-emerald-100',  border: 'border-emerald-300',  icon: PenLine },
  INSPIRATION_FLASH:  { label: '灵感闪现', color: 'text-amber-700',   bg: 'bg-amber-100',   border: 'border-amber-300',   icon: Lightbulb },
  DECISION_DILEMMA:   { label: '决策纠结', color: 'text-rose-700',    bg: 'bg-rose-100',    border: 'border-rose-300',    icon: Scale },
}

export const BIG_TAG_OPTIONS: { value: BigTagCategory; label: string; icon: Component }[] = [
  { value: 'KNOWLEDGE_POINT',   label: '知识点',   icon: BookOpen },
  { value: 'FREEFORM_NOTE',     label: '随心记述', icon: PenLine },
  { value: 'INSPIRATION_FLASH', label: '灵感闪现', icon: Lightbulb },
  { value: 'DECISION_DILEMMA',  label: '决策纠结', icon: Scale },
]

export function bigTagClass(bigTag?: BigTagCategory | null): string {
  if (!bigTag || !BIG_TAG_CONFIG[bigTag]) return ''
  const c = BIG_TAG_CONFIG[bigTag]
  return `${c.bg} ${c.color} ${c.border}`
}

export function bigTagLabel(bigTag?: BigTagCategory | null): string {
  if (!bigTag || !BIG_TAG_CONFIG[bigTag]) return ''
  return BIG_TAG_CONFIG[bigTag].label
}
