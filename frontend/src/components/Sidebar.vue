<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import {
  Brain,
  Search,
  GitGraph,
  BarChart3,
  Settings,
  Sun,
  Moon,
  Plus,
} from 'lucide-vue-next'

const route = useRoute()
const settings = useSettingsStore()

const navItems = [
  { to: '/', label: '首页', icon: Brain },
  { to: '/memories', label: '记忆', icon: Search },
  { to: '/graph', label: '图谱', icon: GitGraph },
  { to: '/analytics', label: '分析', icon: BarChart3 },
  { to: '/settings', label: '设置', icon: Settings },
]

function isActive(path: string) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}
</script>

<template>
  <aside class="w-56 border-r border-border bg-card flex flex-col shrink-0">
    <!-- Logo -->
    <div class="p-4 border-b border-border">
      <div class="flex items-center gap-2">
        <Brain class="w-6 h-6 text-primary" />
        <span class="font-semibold text-sm">Pensieve</span>
      </div>
    </div>

    <!-- Nav -->
    <nav class="flex-1 p-3 space-y-1">
      <router-link
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :class="[
          'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
          isActive(item.to)
            ? 'bg-primary/10 text-primary font-medium'
            : 'text-muted-foreground hover:bg-accent hover:text-foreground',
        ]"
      >
        <component :is="item.icon" class="w-4 h-4" />
        {{ item.label }}
      </router-link>
    </nav>

    <!-- Bottom -->
    <div class="p-3 border-t border-border space-y-2">
      <router-link
        to="/memories?new=true"
        class="flex items-center gap-2 px-3 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
      >
        <Plus class="w-4 h-4" />
        新建记忆
      </router-link>
      <button
        @click="settings.toggleDarkMode()"
        class="flex items-center gap-2 px-3 py-2 w-full rounded-lg text-sm text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
      >
        <Sun v-if="settings.darkMode" class="w-4 h-4" />
        <Moon v-else class="w-4 h-4" />
        {{ settings.darkMode ? '亮色模式' : '暗色模式' }}
      </button>
    </div>
  </aside>
</template>
