/**
 * 经验系统存储服务
 *
 * 统一封装所有经验数据的读写操作，模块只调用此服务，不直接操作 localStorage。
 *
 * 如需迁移 Electron，只需替换此服务的读写实现为 electron-store 或 fs，
 * 其他模块无需任何改动。
 */

import type { ExperienceData, TierName } from '@/types/experience'
import {
  EXP_STORAGE_KEY,
  DEFAULT_TIER_NAMES,
  TIER_THRESHOLDS,
  DAILY_SUBMIT_LIMIT,
  SUBMIT_REWARD_EXP,
  MAX_EXP,
} from '@/types/experience'

/** 获取今天的日期字符串 (YYYY-MM-DD) */
function todayStr(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** 默认经验数据 */
function createDefaultData(): ExperienceData {
  return {
    totalExp: 10,
    rebirthStar: 0,
    todaySubmissions: 0,
    lastSubmitDate: todayStr(),
    customTierNames: [] as TierName[],
    effectsEnabled: true,
  }
}

/**
 * storageService — 经验系统统一存储服务
 *
 * 所有模块通过此对象读写经验数据，不直接操作 localStorage。
 * 如需迁移 Electron，只需替换 get / set 的内部实现为 electron-store 或 fs。
 */
export const storageService = {
  /**
   * 读取经验数据
   * 如需迁移 Electron，将此方法内部替换为 electron-store.get() 或 fs.readFileSync()
   */
  get(): ExperienceData {
    try {
      const raw = localStorage.getItem(EXP_STORAGE_KEY)
      if (!raw) {
        const defaults = createDefaultData()
        this.set(defaults)
        return defaults
      }
      const parsed = JSON.parse(raw) as Partial<ExperienceData>
      return {
        ...createDefaultData(),
        ...parsed,
      }
    } catch {
      const defaults = createDefaultData()
      this.set(defaults)
      return defaults
    }
  },

  /**
   * 写入经验数据
   * 如需迁移 Electron，将此方法内部替换为 electron-store.set() 或 fs.writeFileSync()
   */
  set(data: ExperienceData): void {
    localStorage.setItem(EXP_STORAGE_KEY, JSON.stringify(data))
  },

  /**
   * 更新部分字段（浅合并）
   */
  update(partial: Partial<ExperienceData>): ExperienceData {
    const current = this.get()
    const merged = { ...current, ...partial }
    this.set(merged)
    return merged
  },

  /**
   * 根据总经验值计算当前阶级索引 (0-based)
   * 阈值: 0 → 0, 50 → 1, 200 → 2, 500 → 3, 1000 → 4, 2000 → 5
   */
  calcTierIndex(totalExp: number): number {
    for (let i = TIER_THRESHOLDS.length - 1; i >= 0; i--) {
      if (totalExp >= TIER_THRESHOLDS[i]) return i
    }
    return 0
  },

  /**
   * 获取当前阶级名称（优先使用自定义名称，空则回退默认）
   */
  getTierName(tierIndex: number, customNames?: TierName[]): string {
    if (customNames) {
      const custom = customNames.find((t) => t.index === tierIndex)
      if (custom && custom.name.trim()) return custom.name.trim()
    }
    return DEFAULT_TIER_NAMES[tierIndex] ?? '未知'
  },

  /**
   * 计算当前阶级内的进度百分比 (0~100)
   * 满级 (index=5) 时恒为 100
   */
  calcProgress(totalExp: number): number {
    const tierIndex = this.calcTierIndex(totalExp)
    if (tierIndex >= TIER_THRESHOLDS.length - 1) return 100
    const currentThreshold = TIER_THRESHOLDS[tierIndex]
    const nextThreshold = TIER_THRESHOLDS[tierIndex + 1]
    const expInTier = totalExp - currentThreshold
    const expNeeded = nextThreshold - currentThreshold
    return Math.min(100, Math.round((expInTier / expNeeded) * 100))
  },

  /**
   * 提交奖励：成功保存日记时调用
   * 每日限 DAILY_SUBMIT_LIMIT 次，每次奖励 SUBMIT_REWARD_EXP 经验
   */
  claimSubmitReward(): { rewarded: boolean; data: ExperienceData } {
    const data = this.get()
    const today = todayStr()
    if (data.lastSubmitDate !== today) {
      data.todaySubmissions = 0
      data.lastSubmitDate = today
    }
    if (data.todaySubmissions >= DAILY_SUBMIT_LIMIT) {
      return { rewarded: false, data }
    }
    data.todaySubmissions += 1
    data.totalExp += SUBMIT_REWARD_EXP
    this.set(data)
    return { rewarded: true, data }
  },

  /**
   * 重生：总经验减去 MAX_EXP，星级 +1
   * 返回更新后的数据；如果经验不足则返回 null
   */
  rebirth(): ExperienceData | null {
    const data = this.get()
    if (data.totalExp < MAX_EXP) return null
    data.totalExp -= MAX_EXP
    data.rebirthStar += 1
    this.set(data)
    return data
  },
}