/**
 * 生日功能类型定义
 *
 * 所有生日数据仅存储在本地 localStorage，不上传云端。
 */

/** 生日数据结构 */
export interface BirthdayData {
  /** 生日日期，格式 YYYY-MM-DD，空字符串表示未设置 */
  birthday: string
  /** 是否公开年份（仅展示月日），默认 false */
  hideYear: boolean
  /** 生日前3天提醒，默认 true */
  remindBefore: boolean
  /** 生日祝福弹窗开关，默认 true */
  showGreetingModal: boolean
  /** 生日特效（星星/彩蛋）开关，默认 true */
  showEffects: boolean
  /** 生日经验翻倍开关，默认 true */
  doubleExp: boolean
  /** AI 生日祝福开关，默认 true */
  showAiWish: boolean
  /** 生日记忆回顾开关，默认 true */
  showMemoryReview: boolean
  /** 今年生日弹窗是否已显示过（防止重复弹出），格式 YYYY-MM-DD，记录上次弹出日期 */
  lastGreetingShown: string
  /** 今年AI祝福卡是否已显示过，格式 YYYY-MM-DD */
  lastAiWishShown: string
  /** 今年生日提醒是否已显示过，格式 YYYY-MM-DD */
  lastReminderShown: string
}

/** 愿望卡片 */
export interface BirthdayWish {
  /** 唯一ID */
  id: string
  /** 愿望内容 */
  content: string
  /** 创建日期 YYYY-MM-DD */
  date: string
  /** 对应的年龄（若可计算） */
  age: number | null
}

/** 预设生日祝福文案池 */
export const BIRTHDAY_GREETINGS = [
  '愿你的每一天都充满阳光与欢笑 🌟',
  '新的一岁，愿所有美好如期而至 ✨',
  '生日快乐！愿你在新的一岁里遇见更好的自己 🎁',
  '又长一岁，愿你越来越闪耀 💫',
  '今天是属于你的日子，尽情享受吧！🎉',
  '愿你的生活像蛋糕一样甜蜜 🍰',
  '新岁启程，愿你一路繁花 🌸',
  '生日快乐！愿你被这世界温柔以待 🎀',
  '又是一个美好的开始，生日快乐！🥳',
  '愿你永远年轻，永远热泪盈眶 🎊',
] as const

/** localStorage 存储键名 */
export const BIRTHDAY_STORAGE_KEY = 'pensieve-birthday'

/** 愿望存储键名 */
export const BIRTHDAY_WISHES_STORAGE_KEY = 'pensieve-birthday-wishes'