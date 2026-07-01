/**
 * 经验系统存储服务
 *
 * 统一封装所有经验数据的读写操作，模块只调用此服务，不直接操作 localStorage。
 *
 * 如需迁移 Electron，只需替换此服务的读写实现为 electron-store 或 fs，
 * 其他模块无需任何改动。
 */

import type { ExperienceData, TierName } from '@/types/experience'
import { EXP_STORAGE_KEY, DEFAULT_TIER_NAMES } from '@/types/experience'

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
        // 首次访问，写入默认值
        const defaults = createDefaultData()
        this.set(defaults)
        return defaults
      }
      const parsed = JSON.parse(raw) as Partial<ExperienceData>
      // 合并默认值，防止字段缺失
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
   * 获取当前阶级名称（优先使用自定义名称，否则用默认）
   */
  getTierName(tierIndex: number): string {
    const data = this.get()
    const custom = data.customTierNames.find((t) => t.index === tierIndex)
    if (custom && custom.name) return custom.name
    return DEFAULT_TIER_NAMES[tierIndex] ?? '未知'
  },

  /**
   * 根据总经验值计算当前阶级索引 (0-based)
   * 阶级划分: 0-99 → 0, 100-299 → 1, 300-599 → 2, 600-999 → 3, 1000-1499 → 4, 1500+ → 5
   */
  calcTierIndex(totalExp: number): number {
    if (totalExp < 100) return 0
    if (totalExp < 300) return 1
    if (totalExp < 600) return 2
    if (totalExp < 1000) return 3
    if (totalExp < 1500) return 4
    return 5
  },
}