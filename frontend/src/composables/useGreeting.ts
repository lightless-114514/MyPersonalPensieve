import { computed } from 'vue'

const greetings = {
  morning: [
    '早上好！新的一天，新的灵感 ☀️',
    '早上好！今天有什么想记录的吗？ 🌅',
    '一日之计在于晨，早安！ ✨',
  ],
  afternoon: [
    '下午好！别忘了给大脑补充能量 🍵',
    '下午好！今天已经积累了不少想法吧？ 💡',
    '午后时光正好，来记录点什么吧 📝',
  ],
  evening: [
    '晚上好！回顾一下今天的收获吧 🌙',
    '晚上好！安静的时刻最适合沉淀思绪 🧘',
    '夜色温柔，来写下今天的故事吧 🌟',
  ],
  midnight: [
    '夜深了，但还是可以记录灵感 🌃',
    '凌晨了，思绪飘到哪里了？ 🌌',
    '睡不着吗？不如把想法写下来吧 🌠',
  ],
}

function getTimePeriod(): 'morning' | 'afternoon' | 'evening' | 'midnight' {
  const hour = new Date().getHours()
  if (hour >= 6 && hour < 12) return 'morning'
  if (hour >= 12 && hour < 18) return 'afternoon'
  if (hour >= 18 && hour < 23) return 'evening'
  return 'midnight'
}

function pickGreeting(list: string[]): string {
  const index = Math.floor(Math.random() * list.length)
  return list[index]
}

export function useGreeting() {
  const greeting = computed(() => {
    const period = getTimePeriod()
    return pickGreeting(greetings[period])
  })

  return { greeting }
}
