import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  BIRTHDAY_STORAGE_KEY,
  BIRTHDAY_WISHES_STORAGE_KEY,
  BIRTHDAY_GREETINGS,
} from '@/types/birthday'
import type { BirthdayData, BirthdayWish } from '@/types/birthday'

/** 获取今天的日期字符串 YYYY-MM-DD */
function todayStr(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** 创建默认生日数据 */
function createDefaultBirthdayData(): BirthdayData {
  return {
    birthday: '',
    hideYear: false,
    remindBefore: true,
    showGreetingModal: true,
    showEffects: true,
    doubleExp: true,
    showAiWish: true,
    showMemoryReview: true,
    lastGreetingShown: '',
    lastAiWishShown: '',
    lastReminderShown: '',
  }
}

export const useBirthdayStore = defineStore('birthday', () => {
  // ---- 核心状态 ----
  const birthday = ref('')
  const hideYear = ref(false)
  const remindBefore = ref(true)
  const showGreetingModal = ref(true)
  const showEffects = ref(true)
  const doubleExp = ref(true)
  const showAiWish = ref(true)
  const showMemoryReview = ref(true)
  const lastGreetingShown = ref('')
  const lastAiWishShown = ref('')
  const lastReminderShown = ref('')

  // ---- 愿望列表 ----
  const wishes = ref<BirthdayWish[]>([])

  // ---- 计算属性 ----

  /** 是否已设置生日 */
  const hasBirthday = computed(() => birthday.value.trim() !== '')

  /** 今天是否是生日 */
  const isBirthdayToday = computed(() => {
    if (!hasBirthday.value) return false
    const today = new Date()
    const [bMonth, bDay] = birthday.value.split('-').slice(1).map(Number)
    return today.getMonth() + 1 === bMonth && today.getDate() === bDay
  })

  /** 距离生日还有几天（-1 表示已过，0 表示今天） */
  const daysUntilBirthday = computed(() => {
    if (!hasBirthday.value) return -1
    const today = new Date()
    const [bMonth, bDay] = birthday.value.split('-').slice(1).map(Number)
    const thisYearBirthday = new Date(today.getFullYear(), bMonth - 1, bDay)
    // 如果今年生日已过，算明年
    if (thisYearBirthday < today) {
      // 检查是否今天
      if (today.getMonth() + 1 === bMonth && today.getDate() === bDay) return 0
      const nextYearBirthday = new Date(today.getFullYear() + 1, bMonth - 1, bDay)
      return Math.ceil((nextYearBirthday.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
    }
    return Math.ceil((thisYearBirthday.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
  })

  /** 是否需要显示生日前提醒（3天内） */
  const shouldShowReminder = computed(() => {
    if (!hasBirthday.value || !remindBefore.value) return false
    if (isBirthdayToday.value) return false
    const days = daysUntilBirthday.value
    return days > 0 && days <= 3
  })

  /** 用户年龄（若未填年份则返回 null） */
  const age = computed(() => {
    if (!hasBirthday.value) return null
    const parts = birthday.value.split('-').map(Number)
    const year = parts[0]
    if (!year || year === 0) return null
    const today = new Date()
    let a = today.getFullYear() - year
    const [bMonth, bDay] = [parts[1], parts[2]]
    if (today.getMonth() + 1 < bMonth || (today.getMonth() + 1 === bMonth && today.getDate() < bDay)) {
      a--
    }
    return a
  })

  /** 获取显示用的生日文本（如 "5月20日"） */
  const birthdayDisplayText = computed(() => {
    if (!hasBirthday.value) return ''
    const parts = birthday.value.split('-').map(Number)
    return `${parts[1]}月${parts[2]}日`
  })

  /** 是否需要在今天显示祝福弹窗 */
  const shouldShowGreeting = computed(() => {
    if (!isBirthdayToday.value || !showGreetingModal.value) return false
    return lastGreetingShown.value !== todayStr()
  })

  /** 是否需要在今天显示AI祝福卡 */
  const shouldShowAiWishCard = computed(() => {
    if (!isBirthdayToday.value || !showAiWish.value) return false
    return lastAiWishShown.value !== todayStr()
  })

  /** 是否需要在今天显示提醒条 */
  const shouldShowReminderBar = computed(() => {
    if (!shouldShowReminder.value) return false
    return lastReminderShown.value !== todayStr()
  })

  /** 获取随机生日祝福文案 */
  const randomGreeting = computed(() => {
    const idx = Math.floor(Math.random() * BIRTHDAY_GREETINGS.length)
    return BIRTHDAY_GREETINGS[idx]
  })

  // ---- 动作 ----

  /** 从 localStorage 加载数据 */
  function load() {
    try {
      const raw = localStorage.getItem(BIRTHDAY_STORAGE_KEY)
      if (raw) {
        const parsed = JSON.parse(raw) as Partial<BirthdayData>
        const defaults = createDefaultBirthdayData()
        birthday.value = parsed.birthday ?? defaults.birthday
        hideYear.value = parsed.hideYear ?? defaults.hideYear
        remindBefore.value = parsed.remindBefore ?? defaults.remindBefore
        showGreetingModal.value = parsed.showGreetingModal ?? defaults.showGreetingModal
        showEffects.value = parsed.showEffects ?? defaults.showEffects
        doubleExp.value = parsed.doubleExp ?? defaults.doubleExp
        showAiWish.value = parsed.showAiWish ?? defaults.showAiWish
        showMemoryReview.value = parsed.showMemoryReview ?? defaults.showMemoryReview
        lastGreetingShown.value = parsed.lastGreetingShown ?? defaults.lastGreetingShown
        lastAiWishShown.value = parsed.lastAiWishShown ?? defaults.lastAiWishShown
        lastReminderShown.value = parsed.lastReminderShown ?? defaults.lastReminderShown
      }
    } catch {
      // 静默处理
    }

    // 加载愿望
    try {
      const wishRaw = localStorage.getItem(BIRTHDAY_WISHES_STORAGE_KEY)
      if (wishRaw) {
        wishes.value = JSON.parse(wishRaw)
      }
    } catch {
      wishes.value = []
    }
  }

  /** 保存到 localStorage */
  function save() {
    const data: BirthdayData = {
      birthday: birthday.value,
      hideYear: hideYear.value,
      remindBefore: remindBefore.value,
      showGreetingModal: showGreetingModal.value,
      showEffects: showEffects.value,
      doubleExp: doubleExp.value,
      showAiWish: showAiWish.value,
      showMemoryReview: showMemoryReview.value,
      lastGreetingShown: lastGreetingShown.value,
      lastAiWishShown: lastAiWishShown.value,
      lastReminderShown: lastReminderShown.value,
    }
    localStorage.setItem(BIRTHDAY_STORAGE_KEY, JSON.stringify(data))
  }

  /** 保存愿望列表 */
  function saveWishes() {
    localStorage.setItem(BIRTHDAY_WISHES_STORAGE_KEY, JSON.stringify(wishes.value))
  }

  /** 设置生日日期 */
  function setBirthday(date: string) {
    birthday.value = date
    save()
  }

  /** 清空生日 */
  function clearBirthday() {
    birthday.value = ''
    save()
  }

  /** 标记祝福弹窗已显示 */
  function markGreetingShown() {
    lastGreetingShown.value = todayStr()
    save()
  }

  /** 标记AI祝福卡已显示 */
  function markAiWishShown() {
    lastAiWishShown.value = todayStr()
    save()
  }

  /** 标记提醒条已显示 */
  function markReminderShown() {
    lastReminderShown.value = todayStr()
    save()
  }

  /** 添加愿望 */
  function addWish(content: string) {
    const wish: BirthdayWish = {
      id: `wish_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      content,
      date: todayStr(),
      age: age.value,
    }
    wishes.value.unshift(wish)
    saveWishes()
  }

  /** 删除愿望 */
  function removeWish(id: string) {
    wishes.value = wishes.value.filter(w => w.id !== id)
    saveWishes()
  }

  /** 获取去年的今天（或最早年份的今日）的愿望 */
  function getLastYearWishes(): BirthdayWish[] {
    if (!isBirthdayToday.value) return []
    const today = new Date()
    const lastYear = today.getFullYear() - 1
    return wishes.value.filter(w => {
      const wishYear = new Date(w.date).getFullYear()
      return wishYear <= lastYear
    })
  }

  return {
    // 状态
    birthday,
    hideYear,
    remindBefore,
    showGreetingModal,
    showEffects,
    doubleExp,
    showAiWish,
    showMemoryReview,
    lastGreetingShown,
    lastAiWishShown,
    lastReminderShown,
    wishes,
    // 计算属性
    hasBirthday,
    isBirthdayToday,
    daysUntilBirthday,
    shouldShowReminder,
    age,
    birthdayDisplayText,
    shouldShowGreeting,
    shouldShowAiWishCard,
    shouldShowReminderBar,
    randomGreeting,
    // 动作
    load,
    save,
    setBirthday,
    clearBirthday,
    markGreetingShown,
    markAiWishShown,
    markReminderShown,
    addWish,
    removeWish,
    getLastYearWishes,
  }
})