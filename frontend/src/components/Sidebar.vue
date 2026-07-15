<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import { useExperienceStore } from '@/stores/experience'
import { useInsightStore } from '@/stores/insight'
import { useBirthdayStore } from '@/stores/birthday'
import { onMounted, ref } from 'vue'
import {
  Brain,
  Search,
  GitGraph,
  BarChart3,
  GitCompare,
  Settings,
  Sun,
  Moon,
  Plus,
  ArrowUpCircle,
  Zap,
  Sparkles,
  CalendarDays,
  CalendarRange,
  Archive,
  ChevronDown,
  ChevronRight,
  Loader2,
  Hourglass,
} from 'lucide-vue-next'

const route = useRoute()
const settings = useSettingsStore()
const exp = useExperienceStore()
const insight = useInsightStore()
const birthdayStore = useBirthdayStore()

const insightExpanded = ref(true)

onMounted(() => {
  exp.load()
  birthdayStore.load()
  // 检查周报/月报提示
  const now = new Date()
  const dayOfWeek = now.getDay() // 0=Sunday
  const monday = new Date(now)
  monday.setDate(now.getDate() - ((dayOfWeek + 6) % 7))
  const weekStart = monday.toISOString().slice(0, 10)
  insight.fetchWeeklyStatus(weekStart)
  insight.checkMonthlyDot()
  insight.fetchArchive()
})

const navItems = [
  { to: '/', label: '首页', icon: Brain },
  { to: '/memories', label: '记忆', icon: Search },
  { to: '/capsules', label: '时间胶囊', icon: Hourglass },
  { to: '/graph', label: '图谱', icon: GitGraph },
  { to: '/analytics', label: '分析', icon: BarChart3 },
  { to: '/compare', label: '对比', icon: GitCompare },
  { to: '/settings', label: '设置', icon: Settings },
]

function isActive(path: string) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<template>
  <aside class="w-64 border-r border-sidebar-border bg-sidebar flex flex-col shrink-0 no-select">
    <!-- Logo - Electron drag region -->
    <div class="p-4 border-b border-sidebar-border electron-drag">
      <div class="flex items-center gap-2.5 electron-no-drag">
        <div class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
          <Brain class="w-5 h-5 text-primary" />
        </div>
        <span class="font-bold text-base tracking-tight">Pensieve</span>
      </div>
    </div>

    <!-- Nav -->
    <nav class="flex-1 p-3 space-y-1 overflow-y-auto">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :class="[
          'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200',
          isActive(item.to)
            ? 'bg-primary/10 text-primary font-medium shadow-sm'
            : 'text-muted-foreground hover:bg-accent/80 hover:text-foreground',
        ]"
      >
        <component :is="item.icon" class="w-[18px] h-[18px]" :class="isActive(item.to) ? 'text-primary' : ''" />
        {{ item.label }}
      </router-link>

      <!-- 自我洞察模块 -->
      <div class="mt-3 border-t border-sidebar-border pt-3">
        <!-- 一级标题 -->
        <button
          @click="insightExpanded = !insightExpanded"
          class="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm font-semibold text-foreground hover:bg-accent/60 transition-all duration-200"
        >
          <Sparkles class="w-4 h-4 text-primary" />
          <span class="flex-1 text-left">自我洞察</span>
          <component
            :is="insightExpanded ? ChevronDown : ChevronRight"
            class="w-3.5 h-3.5 text-muted-foreground"
          />
        </button>

        <!-- 二级菜单 -->
        <Transition name="slide">
          <div v-if="insightExpanded" class="mt-1 space-y-0.5 pl-2">
            <!-- 周报 -->
            <router-link
              to="/insight/weekly"
              :class="[
                'flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] transition-all duration-200',
                isActive('/insight/weekly')
                  ? 'bg-primary/10 text-primary font-medium'
                  : 'text-muted-foreground hover:bg-accent/80 hover:text-foreground',
              ]"
            >
              <CalendarDays class="w-[16px] h-[16px]" />
              <span class="flex-1">周报</span>
              <!-- 生成中旋转动画 -->
              <Loader2 v-if="insight.isGenerating && insight.isCurrentWeekly" class="w-3.5 h-3.5 animate-spin text-primary" />
              <!-- 已生成标记 -->
              <span v-else-if="insight.weeklyStatus?.exists && !insight.weeklyStatus?.hasNewMemories" class="text-[10px] text-muted-foreground/60">已生成</span>
              <!-- 蓝色小圆点提示 -->
              <span v-else-if="insight.showWeeklyDot" class="w-2 h-2 rounded-full bg-blue-500 shrink-0" />
            </router-link>

            <!-- 月报 -->
            <router-link
              to="/insight/monthly"
              :class="[
                'flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] transition-all duration-200',
                isActive('/insight/monthly')
                  ? 'bg-primary/10 text-primary font-medium'
                  : 'text-muted-foreground hover:bg-accent/80 hover:text-foreground',
              ]"
            >
              <CalendarRange class="w-[16px] h-[16px]" />
              <span class="flex-1">月报</span>
              <!-- 生成中旋转动画 -->
              <Loader2 v-if="insight.isGenerating && insight.isCurrentMonthly" class="w-3.5 h-3.5 animate-spin text-primary" />
              <!-- 绿色小圆点提示 -->
              <span v-else-if="insight.showMonthlyDot" class="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
            </router-link>

            <!-- 洞察档案 -->
            <router-link
              to="/insight/archive"
              :class="[
                'flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] transition-all duration-200',
                isActive('/insight/archive')
                  ? 'bg-primary/10 text-primary font-medium'
                  : 'text-muted-foreground hover:bg-accent/80 hover:text-foreground',
              ]"
            >
              <Archive class="w-[16px] h-[16px]" />
              <span class="flex-1">洞察档案</span>
              <!-- 未读红点 -->
              <span v-if="insight.hasUnreadArchive" class="w-2 h-2 rounded-full bg-red-500 shrink-0" />
            </router-link>
          </div>
        </Transition>
      </div>
    </nav>

    <!-- 经验系统 -->
    <div class="px-3 py-3 border-t border-sidebar-border relative" :class="{ shake: exp.isShaking }">
      <!-- 全屏闪白 -->
      <Transition name="flash">
        <div v-if="exp.isFlashing" class="fixed inset-0 bg-white/80 z-[9999] pointer-events-none" />
      </Transition>

      <!-- 飘字特效 -->
      <TransitionGroup name="float">
        <div
          v-for="ft in exp.floatingTexts"
          :key="ft.id"
          class="absolute left-3 text-xs font-bold pointer-events-none float-up"
          :class="exp.tierColorClass"
          :style="{ bottom: '60px' }"
        >
          {{ ft.text }}
        </div>
      </TransitionGroup>

      <!-- 标题行 -->
      <div class="flex items-center gap-1.5 mb-1.5">
        <span class="text-[10px] font-semibold tracking-wider text-muted-foreground uppercase inline-flex items-center gap-1"><Zap class="w-3 h-3" />经验系统</span>
        <span class="text-[10px] text-muted-foreground/50">记录即成长</span>
        <!-- 生日徽章 -->
        <span
          v-if="birthdayStore.isBirthdayToday"
          class="ml-auto text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-pink-500/15 text-pink-500 animate-pulse"
        >
          🎂 {{ birthdayStore.badgeText }}
        </span>
      </div>

      <!-- 阶级文字 + 星级 + 重生按钮 -->
      <div class="flex items-center justify-between gap-1 mt-1.5">
        <div class="flex items-center gap-1.5 min-w-0">
          <span class="text-xs font-medium select-none transition-colors duration-300 truncate" :class="exp.tierColorClass">
            {{ exp.displayText }}
          </span>
          <span v-if="exp.starText" class="text-xs shrink-0">{{ exp.starText }}</span>
        </div>
        <button
          v-if="exp.canRebirth"
          @click="exp.doRebirth()"
          class="shrink-0 p-1 rounded-md text-muted-foreground hover:text-primary hover:bg-accent transition-colors"
          title="重生：扣减 2000 EXP，星级 +1"
        >
          <ArrowUpCircle class="w-4 h-4" />
        </button>
      </div>

      <!-- 进度条 -->
      <div class="mt-1.5 h-1.5 w-full rounded-full bg-muted overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-500 ease-out"
          :class="[
            exp.tierBarColorClass,
            exp.isMaxTier ? 'animate-pulse' : ''
          ]"
          :style="{ width: exp.progress + '%' }"
        />
      </div>

      <!-- 提示文字 -->
      <p class="mt-1 text-[10px] text-muted-foreground/40 leading-tight">
        输入 +1 EXP · 提交 +30 EXP · 每日最多10次提交奖励
      </p>
    </div>

    <!-- Bottom -->
    <div class="p-3 border-t border-sidebar-border space-y-2">
      <router-link
        to="/memories?new=true"
        class="flex items-center justify-center gap-2 px-3 py-2.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-all duration-200 shadow-sm hover:shadow-md active:scale-[0.98]"
      >
        <Plus class="w-4 h-4" />
        新建记忆
      </router-link>
      <button
        @click="settings.toggleDarkMode()"
        class="flex items-center gap-2 px-3 py-2 w-full rounded-lg text-sm text-muted-foreground hover:bg-accent hover:text-foreground transition-all duration-200"
      >
        <Sun v-if="settings.darkMode" class="w-4 h-4" />
        <Moon v-else class="w-4 h-4" />
        {{ settings.darkMode ? '亮色模式' : '暗色模式' }}
      </button>
    </div>
  </aside>
</template>

<style scoped>
/* 飘字入场动画 */
.float-enter-active {
  animation: floatUp 1.5s ease-out forwards;
}
.float-leave-active {
  animation: none;
}

@keyframes floatUp {
  0% {
    opacity: 1;
    transform: translateY(0);
  }
  100% {
    opacity: 0;
    transform: translateY(-32px);
  }
}

/* 晋升摇晃动画 0.3s */
.shake {
  animation: shake 0.3s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-4px); }
  40% { transform: translateX(4px); }
  60% { transform: translateX(-2px); }
  80% { transform: translateX(2px); }
}

/* 闪白动画 */
.flash-enter-active {
  animation: flashIn 0.2s ease-out;
}
.flash-leave-active {
  animation: none;
}

@keyframes flashIn {
  0% { opacity: 0; }
  50% { opacity: 1; }
  100% { opacity: 0; }
}

/* 自我洞察菜单展开/收起动画 */
.slide-enter-active {
  animation: slideDown 0.2s ease-out;
}
.slide-leave-active {
  animation: slideUp 0.15s ease-in;
}

@keyframes slideDown {
  from { opacity: 0; max-height: 0; }
  to { opacity: 1; max-height: 200px; }
}
@keyframes slideUp {
  from { opacity: 1; max-height: 200px; }
  to { opacity: 0; max-height: 0; }
}
</style>