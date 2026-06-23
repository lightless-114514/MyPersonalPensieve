import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

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

  if (minutes < 1) return '??'
  if (minutes < 60) return `${minutes}????`
  if (hours < 24) return `${hours}????`
  if (days < 7) return `${days}???`
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
      return '??'
    case 'IMAGE':
      return '???'
    default:
      return '??'
  }
}