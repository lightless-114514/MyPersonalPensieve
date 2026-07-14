import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { storageService } from '@/services/storageService'
import {
  DEFAULT_TIER_NAMES,
  TIER_COLOR_CLASSES,
  TIER_BAR_COLOR_CLASSES,
  INPUT_REWARD_EXP,
  SUBMIT_REWARD_EXP,
  INPUT_DEBOUNCE_MS,
  MAX_EXP,
} from '@/types/experience'
import type { ExperienceData, TierName } from '@/types/experience'
import { useBirthdayStore } from '@/stores/birthday'

/** 飘字项 */
export interface FloatingText {
  id: number
  text: string
  amount: number
}

let floatingId = 0
let inputDebounceTimer: ReturnType<typeof setTimeout> | null = null
let pendingInputExp = 0

export const useExperienceStore = defineStore('experience', () => {
  // ---- 核心响应式状态 ----
  const totalExp = ref(0)
  const rebirthStar = ref(0)
  const todaySubmissions = ref(0)
  const lastSubmitDate = ref('')
  const customTierNames = ref<TierName[]>([])
  const effectsEnabled = ref(true)

  // ---- 飘字列表 ----
  const floatingTexts = ref<FloatingText[]>([])

  // ---- 晋升特效状态 ----
  const isShaking = ref(false)
  const isFlashing = ref(false)

  // ---- 初始化：从 storageService 加载 ----
  function load() {
    const data = storageService.get()
    totalExp.value = data.totalExp
    rebirthStar.value = data.rebirthStar
    todaySubmissions.value = data.todaySubmissions
    lastSubmitDate.value = data.lastSubmitDate
    customTierNames.value = data.customTierNames
    effectsEnabled.value = data.effectsEnabled ?? true
  }

  // ---- 同步写入 storageService ----
  function persist() {
    storageService.set({
      totalExp: totalExp.value,
      rebirthStar: rebirthStar.value,
      todaySubmissions: todaySubmissions.value,
      lastSubmitDate: lastSubmitDate.value,
      customTierNames: customTierNames.value,
      effectsEnabled: effectsEnabled.value,
    })
  }

  // ---- 计算属性 ----
  const tierIndex = computed(() => storageService.calcTierIndex(totalExp.value))

  const tierName = computed(() => {
    const idx = tierIndex.value
    const custom = customTierNames.value.find((t) => t.index === idx)
    if (custom && custom.name.trim()) return custom.name.trim()
    return DEFAULT_TIER_NAMES[idx] ?? '未知'
  })

  const tierLevel = computed(() => tierIndex.value + 1)

  const tierColorClass = computed(() => TIER_COLOR_CLASSES[tierIndex.value] ?? 'text-gray-400')

  const tierBarColorClass = computed(() => TIER_BAR_COLOR_CLASSES[tierIndex.value] ?? 'bg-gray-400')

  const progress = computed(() => storageService.calcProgress(totalExp.value))

  const isMaxTier = computed(() => tierIndex.value >= DEFAULT_TIER_NAMES.length - 1)

  const canRebirth = computed(() => totalExp.value >= MAX_EXP)

  /** 显示文本，如 "Lv.1 麻瓜 | 10 EXP" */
  const displayText = computed(() => `Lv.${tierLevel.value} ${tierName.value} | ${totalExp.value} EXP`)

  /** 星级显示文本，如 "2⭐"，0 星时为空 */
  const starText = computed(() => rebirthStar.value > 0 ? `${rebirthStar.value}⭐` : '')

  // ---- 监听阶级变化，触发晋升特效 ----
  let prevTierIdx = -1

  watch(tierIndex, (newIdx) => {
    if (prevTierIdx >= 0 && newIdx > prevTierIdx && effectsEnabled.value) {
      triggerPromotionEffect()
    }
    prevTierIdx = newIdx
  })

  function triggerPromotionEffect() {
    // 摇晃 0.3 秒
    isShaking.value = true
    setTimeout(() => { isShaking.value = false }, 300)
    // 全屏闪白
    isFlashing.value = true
    setTimeout(() => { isFlashing.value = false }, 200)
  }

  // ---- 动作 ----

  /** 增加经验值（立即写入，用于提交奖励等非防抖场景） */
  function addExpImmediate(amount: number) {
    const birthdayStore = useBirthdayStore()
    const isDouble = birthdayStore.isBirthdayToday && birthdayStore.doubleExp
    const finalAmount = isDouble ? amount * 2 : amount
    totalExp.value = Math.round((totalExp.value + finalAmount) * 10) / 10
    persist()
    spawnFloating(finalAmount, isDouble)
  }

  /** 输入事件奖励：防抖 2 秒后结算 */
  function onInput() {
    pendingInputExp += INPUT_REWARD_EXP
    if (inputDebounceTimer) clearTimeout(inputDebounceTimer)
    inputDebounceTimer = setTimeout(() => {
      if (pendingInputExp > 0) {
        addExpImmediate(pendingInputExp)
        pendingInputExp = 0
      }
      inputDebounceTimer = null
    }, INPUT_DEBOUNCE_MS)
  }

  /** 提交奖励：+30 EXP，每日限 5 次 */
  function claimSubmitReward(): boolean {
    const today = new Date().toISOString().slice(0, 10)
    if (lastSubmitDate.value !== today) {
      todaySubmissions.value = 0
      lastSubmitDate.value = today
    }
    if (todaySubmissions.value >= 5) {
      return false
    }
    todaySubmissions.value += 1
    addExpImmediate(SUBMIT_REWARD_EXP)
    return true
  }

  /** 重生：经验 ≥ 2000 时扣减 2000，星级 +1 */
  function doRebirth(): boolean {
    if (totalExp.value < MAX_EXP) return false
    totalExp.value -= MAX_EXP
    rebirthStar.value += 1
    persist()
    return true
  }

  /** 更新自定义阶级名称 */
  function updateCustomTierNames(names: TierName[]) {
    customTierNames.value = names
    persist()
  }

  /** 重置自定义名称为默认（清空自定义数组） */
  function resetCustomTierNames() {
    customTierNames.value = []
    persist()
  }

  /** 切换特效开关 */
  function toggleEffects() {
    effectsEnabled.value = !effectsEnabled.value
    persist()
  }

  /** 弹出飘字 */
  function spawnFloating(amount: number, isBirthdayDouble: boolean = false) {
    const id = ++floatingId
    const text = isBirthdayDouble ? `🎂 +${amount} EXP 双倍!` : `+${amount} EXP`
    floatingTexts.value.push({
      id,
      text,
      amount,
    })
    // 生日双倍时额外添加一个金色飘字
    if (isBirthdayDouble) {
      const goldId = ++floatingId
      floatingTexts.value.push({
        id: goldId,
        text: '🎉 生日快乐!',
        amount: 0,
      })
      setTimeout(() => {
        floatingTexts.value = floatingTexts.value.filter((f) => f.id !== goldId)
      }, 1500)
    }
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
    effectsEnabled,
    floatingTexts,
    isShaking,
    isFlashing,
    // 计算属性
    tierIndex,
    tierName,
    tierLevel,
    tierColorClass,
    tierBarColorClass,
    progress,
    isMaxTier,
    canRebirth,
    displayText,
    starText,
    // 动作
    load,
    addExpImmediate,
    onInput,
    claimSubmitReward,
    doRebirth,
    updateCustomTierNames,
    resetCustomTierNames,
    toggleEffects,
    spawnFloating,
  }
})