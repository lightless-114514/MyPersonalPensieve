/**
 * 经验系统类型定义
 */

/** 六个阶级的默认名称 */
export const DEFAULT_TIER_NAMES = [
  '麻瓜',   // Lv.1
  '学徒',   // Lv.2
  '行者',   // Lv.3
  '智者',   // Lv.4
  '大师',   // Lv.5
  '传奇',   // Lv.6
] as const

/** 阶级自定义名称项 */
export interface TierName {
  index: number
  name: string
}

/** 经验数据完整结构 */
export interface ExperienceData {
  /** 总经验值 */
  totalExp: number
  /** 重生星级 */
  rebirthStar: number
  /** 今日提交次数 */
  todaySubmissions: number
  /** 上次提交日期 (YYYY-MM-DD) */
  lastSubmitDate: string
  /** 六个阶级的自定义名称，空数组表示使用默认 */
  customTierNames: TierName[]
}

/** localStorage 存储键名 */
export const EXP_STORAGE_KEY = 'app_exp_data'