import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { InsightReport, InsightReportListItem, WeeklyStatus } from '@/types'
import {
  getWeeklyStatus,
  getWeeklyReport,
  getMonthlyReport,
  getInsightArchive,
  getInsightReportDetail,
  generateWeeklyReport,
  generateMonthlyReport,
  deleteInsightReport,
} from '@/api'

export const useInsightStore = defineStore('insight', () => {
  // ---- 状态 ----
  const currentReport = ref<InsightReport | null>(null)
  const archiveItems = ref<InsightReportListItem[]>([])
  const archiveTotal = ref(0)
  const weeklyStatus = ref<WeeklyStatus | null>(null)
  const isGenerating = ref(false)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // ---- 侧边栏提示状态 ----
  const showWeeklyDot = ref(false)   // 蓝色小圆点：有新日记未生成周报
  const showMonthlyDot = ref(false)  // 绿色小圆点：可生成上月月报
  const hasUnreadArchive = ref(false) // 红色小圆点：有未读洞察

  // ---- 计算属性 ----
  const isCurrentWeekly = computed(() => currentReport.value?.reportType === 'WEEKLY')
  const isCurrentMonthly = computed(() => currentReport.value?.reportType === 'MONTHLY')

  // ---- 周报 ----

  async function fetchWeeklyStatus(weekStart: string) {
    try {
      weeklyStatus.value = await getWeeklyStatus(weekStart)
      // 根据状态更新侧边栏提示
      if (!weeklyStatus.value.exists) {
        showWeeklyDot.value = true
      } else if (weeklyStatus.value.hasNewMemories) {
        showWeeklyDot.value = true
      } else {
        showWeeklyDot.value = false
      }
    } catch {
      weeklyStatus.value = null
    }
  }

  async function fetchWeeklyReport(weekStart: string) {
    isLoading.value = true
    error.value = null
    try {
      currentReport.value = await getWeeklyReport(weekStart)
    } catch (e: any) {
      if (e?.response?.status === 404) {
        currentReport.value = null
      } else {
        error.value = '获取周报失败'
      }
    } finally {
      isLoading.value = false
    }
  }

  async function doGenerateWeekly(weekStart: string) {
    isGenerating.value = true
    error.value = null
    try {
      currentReport.value = await generateWeeklyReport(weekStart)
      // 生成后刷新状态
      await fetchWeeklyStatus(weekStart)
      // 刷新档案列表
      await fetchArchive()
      return true
    } catch (e: any) {
      const msg = e?.response?.data?.detail || '生成周报失败'
      error.value = msg
      return false
    } finally {
      isGenerating.value = false
    }
  }

  // ---- 月报 ----

  async function fetchMonthlyReport(monthStart: string) {
    isLoading.value = true
    error.value = null
    try {
      currentReport.value = await getMonthlyReport(monthStart)
    } catch (e: any) {
      if (e?.response?.status === 404) {
        currentReport.value = null
      } else {
        error.value = '获取月报失败'
      }
    } finally {
      isLoading.value = false
    }
  }

  async function doGenerateMonthly(monthStart: string) {
    isGenerating.value = true
    error.value = null
    try {
      currentReport.value = await generateMonthlyReport(monthStart)
      await fetchArchive()
      return true
    } catch (e: any) {
      const msg = e?.response?.data?.detail || '生成月报失败'
      error.value = msg
      return false
    } finally {
      isGenerating.value = false
    }
  }

  // ---- 档案 ----

  async function fetchArchive(page: number = 0, size: number = 20) {
    isLoading.value = true
    try {
      const result = await getInsightArchive(page, size)
      archiveItems.value = result.items
      archiveTotal.value = result.total
      hasUnreadArchive.value = result.items.some(item => !item.isRead)
    } catch {
      // 静默处理
    } finally {
      isLoading.value = false
    }
  }

  async function fetchReportDetail(reportId: string) {
    isLoading.value = true
    error.value = null
    try {
      currentReport.value = await getInsightReportDetail(reportId)
    } catch {
      error.value = '获取报告详情失败'
    } finally {
      isLoading.value = false
    }
  }

  async function doDeleteReport(reportId: string) {
    try {
      await deleteInsightReport(reportId)
      archiveItems.value = archiveItems.value.filter(item => item.id !== reportId)
      archiveTotal.value -= 1
      if (currentReport.value?.id === reportId) {
        currentReport.value = null
      }
      return true
    } catch {
      return false
    }
  }

  // ---- 提示检测 ----

  function checkMonthlyDot() {
    const now = new Date()
    const dayOfMonth = now.getDate()
    // 每月1-7日显示提示
    if (dayOfMonth <= 7) {
      showMonthlyDot.value = true
    }
  }

  function clearCurrentReport() {
    currentReport.value = null
    error.value = null
  }

  return {
    // 状态
    currentReport,
    archiveItems,
    archiveTotal,
    weeklyStatus,
    isGenerating,
    isLoading,
    error,
    showWeeklyDot,
    showMonthlyDot,
    hasUnreadArchive,
    // 计算属性
    isCurrentWeekly,
    isCurrentMonthly,
    // 动作
    fetchWeeklyStatus,
    fetchWeeklyReport,
    doGenerateWeekly,
    fetchMonthlyReport,
    doGenerateMonthly,
    fetchArchive,
    fetchReportDetail,
    doDeleteReport,
    checkMonthlyDot,
    clearCurrentReport,
  }
})