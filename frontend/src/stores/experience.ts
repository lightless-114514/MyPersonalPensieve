import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { storageService } from '@/services/storageService'
import {
  DEFAULT_TIER_NAMES,
  TIER_COLOR_CLASSES,
  TIER_BAR_COLOR_CLASSES,
  INPUT_REWARD_EXP,
  SUBMIT_REWARD_EXP,
} from '@/types/experience'
import type { ExperienceData } from '@/types/experience'

/** 飘字项 */
export interface FloatingText {
  id: number
  text: string
  amount: number
}

let floatingId = 0

export const useExperienceStore = defineStore('experience', () => {
  // ---- 核心响应式状态 ----
  const totalExp = ref(0)
  const rebirthStar = ref(0)
  const todaySubmissions = ref(0)
  const lastSubmitDate = ref('')
  const customTierNames = ref<{ index: number; name: string }[]>([])

  // ---- 飘字列表 ----
  const floatingTexts = ref<FloatingText[]>([])

  // ---- 初始化：从 storageService 加载 ----
  function load() {
    const data = storageService.get()
    totalExp.value = data.totalExp
    rebirthStar.value = data.rebirthStar
    todaySubmissions.value = data.todaySubmissions
    lastSubmitDate.value = data.lastSubmitDate
    customTierNames.value = data.customTierNames
  }

  // ---- 同步写入 storageService ----
  function persist() {
    storageService.set({
      totalExp: totalExp.value,
      rebirthStar: rebirthStar.value,
      todaySubmissions: todaySubmissions.value,
      lastSubmitDate: lastSubmitDate.value,
      customTierNames: customTierNames.value,
    })
  }

  // ---- 计算属性 ----
  const tierIndex = computed(() => storageService.calcTierIndex(totalExp.value))

  const tierName = computed(() => {
    const idx = tierIndex.value
    const custom = customTierNames.value.find((t) => t.index === idx)
    if (custom && custom.name) return custom.name
    return DEFAULT_TIER_NAMES[idx] ?? '未知'
  })

  const tierLevel = computed(() => tierIndex.value + 1)

  const tierColorClass = computed(() => TIER_COLOR_CLASSES[tierIndex.value] ?? 'text-gray-400')

  const tierBarColorClass = computed(() => TIER_BAR_COLOR_CLASSES[tierIndex.value] ?? 'bg-gray-400')

  const progress = computed(() => storageService.calcProgress(totalExp.value))

  const isMaxTier = computed(() => tierIndex.value >= DEFAULT_TIER_NAMES.length - 1)

  /** 显示文本，如 "Lv.1 麻瓜 | 10 EXP" */
  const displayText = computed(() => `Lv.${tierLevel.value} ${tierName.value} | ${totalExp.value} EXP`)

  // ---- 动作 ----

  /** 增加经验值（输入奖励等） */
  function addExp(amount: number) {
    const prevTier = tierIndex.value
    totalExp.value = Math.round((totalExp.value + amount) * 10) / 10
    persist()
    // 弹出飘字
    spawnFloating(amount)
    // 阶级变化无需额外处理，computed 自动更新
  }

  /** 输入事件奖励：+0.5 EXP */
  function onInput() {
    addExp(INPUT_REWARD_EXP)
  }

  /** 提交奖励：+30 EXP，每日限 5 次 */
  function claimSubmitReward(): boolean {
    const today = new Date().toISOString().slice(0, 10)
    // 跨日重置
    if (lastSubmitDate.value !== today) {
      todaySubmissions.value = 0
      lastSubmitDate.value = today
    }
    if (todaySubmissions.value >= 5) {
      return false
    }
    todaySubmissions.value += 1
    totalExp.value += SUBMIT_REWARD_EXP
    persist()
    spawnFloating(SUBMIT_REWARD_EXP)
    return true
  }

  /** 弹出飘字 */
  function spawnFloating(amount: number) {
    const id = ++floatingId
    floatingTexts.value.push({
      id,
      text: `+${amount} EXP`,
      amount,
    })
    // 1.5 秒后移除
    setTimeout(() => {
      floatingTexts.value = floatingTexts.value.filter((f) => f.id !== id)
    }, 1500)
  }

  return {
    // 状态
    totalExp,
    rebirthStar,
    todaySubmissions,
    lastSubmitDate,
    customTierNames,
    floatingTexts,
    // 计算属性
    tierIndex,
    tierName,
    tierLevel,
    tierColorClass,
    tierBarColorClass,
    progress,
    isMaxTier,
    displayText,
    // 动作
    load,
    addExp,
    onInput,
    claimSubmitReward,
    spawnFloating,
  }
})