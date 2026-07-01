/**
 * 经验系统类型定义
 */

/** 六个阶级的默认名称 */
export const DEFAULT_TIER_NAMES = [
  '麻瓜',       // Lv.1  (0~49 EXP)
  '新生',       // Lv.2  (50~199 EXP)
  '级长',       // Lv.3  (200~499 EXP)
  '魁地奇队长', // Lv.4  (500~999 EXP)
  '傲罗',       // Lv.5  (1000~1999 EXP)
  '梅林勋章',   // Lv.6  (2000+ EXP)
] as const

/** 阶级阈值：经验值达到对应值即升入该阶级 */
export const TIER_THRESHOLDS = [0, 50, 200, 500, 1000, 2000] as const

/** 满级所需经验 */
export const MAX_EXP = 2000

/** 阶级颜色 CSS 类名（按阶级索引 0~5） */
export const TIER_COLOR_CLASSES = [
  'text-gray-400',    // 白（灰白）
  'text-green-400',   // 绿
  'text-blue-400',    // 蓝
  'text-purple-400',  // 紫
  'text-yellow-400',  // 金
  'text-red-400',     // 红
] as const

/** 进度条颜色 CSS 类名（按阶级索引 0~5） */
export const TIER_BAR_COLOR_CLASSES = [
  'bg-gray-400',    // 白
  'bg-green-400',   // 绿
  'bg-blue-400',    // 蓝
  'bg-purple-400',  // 紫
  'bg-yellow-400',  // 金
  'bg-red-400',     // 红
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
  /** 全局特效开关 */
  effectsEnabled: boolean
}

/** localStorage 存储键名 */
export const EXP_STORAGE_KEY = 'app_exp_data'

/** 每日提交奖励上限 */
export const DAILY_SUBMIT_LIMIT = 5

/** 每次提交奖励经验 */
export const SUBMIT_REWARD_EXP = 30

/** 每次有效输入奖励经验 */
export const INPUT_REWARD_EXP = 0.5

/** 输入防抖延迟（毫秒） */
export const INPUT_DEBOUNCE_MS = 2000