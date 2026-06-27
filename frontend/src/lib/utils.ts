import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { BigTagCategory } from '@/types'

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
      return 'text-green-400'
    case 'NEGATIVE':
      return 'text-red-400'
    default:
      return 'text-muted-foreground'
  }
}

export function sentimentBg(sentiment?: string): string {
  switch (sentiment) {
    case 'POSITIVE':
      return 'bg-green-500/10'
    case 'NEGATIVE':
      return 'bg-red-500/10'
    default:
      return 'bg-muted'
  }
}

export function typeIcon(type: string): string {
  switch (type) {
    case 'TEXT':
      return '📝'
    case 'IMAGE':
      return '🖼️'
    default:
      return '📋'
  }
}

// ---- Big Tag helpers ----

export const BIG_TAG_CONFIG: Record<BigTagCategory, { label: string; color: string; bg: string; border: string; icon: string }> = {
  KNOWLEDGE_POINT:    { label: '知识点',   color: 'text-blue-700',    bg: 'bg-blue-100',    border: 'border-blue-300',    icon: '📚' },
  FREEFORM_NOTE:      { label: '随心记述', color: 'text-emerald-700',  bg: 'bg-emerald-100',  border: 'border-emerald-300',  icon: '✍️' },
  INSPIRATION_FLASH:  { label: '灵感闪现', color: 'text-amber-700',   bg: 'bg-amber-100',   border: 'border-amber-300',   icon: '💡' },
  DECISION_DILEMMA:   { label: '决策纠结', color: 'text-rose-700',    bg: 'bg-rose-100',    border: 'border-rose-300',    icon: '⚖️' },
}

export const BIG_TAG_OPTIONS: { value: BigTagCategory; label: string; icon: string }[] = [
  { value: 'KNOWLEDGE_POINT',   label: '知识点',   icon: '📚' },
  { value: 'FREEFORM_NOTE',     label: '随心记述', icon: '✍️' },
  { value: 'INSPIRATION_FLASH', label: '灵感闪现', icon: '💡' },
  { value: 'DECISION_DILEMMA',  label: '决策纠结', icon: '⚖️' },
]

export function bigTagClass(bigTag?: BigTagCategory | null): string {
  if (!bigTag || !BIG_TAG_CONFIG[bigTag]) return ''
  const c = BIG_TAG_CONFIG[bigTag]
  return `${c.bg} ${c.color} ${c.border}`
}

export function bigTagLabel(bigTag?: BigTagCategory | null): string {
  if (!bigTag || !BIG_TAG_CONFIG[bigTag]) return ''
  const c = BIG_TAG_CONFIG[bigTag]
  return `${c.icon} ${c.label}`
}
