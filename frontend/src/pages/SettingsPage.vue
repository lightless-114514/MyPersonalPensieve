<script setup lang="ts">
import { useSettingsStore } from '@/stores/settings'
import { useExperienceStore } from '@/stores/experience'
import { ref, computed, onMounted } from 'vue'
import { Save, RotateCcw } from 'lucide-vue-next'
import { DEFAULT_TIER_NAMES } from '@/types/experience'
import type { TierName } from '@/types/experience'

const settings = useSettingsStore()
const exp = useExperienceStore()
const saved = ref(false)

// 自定义头衔编辑
const tierInputs = ref<string[]>([...DEFAULT_TIER_NAMES])

onMounted(() => {
  exp.load()
  syncTierInputs()
})

function syncTierInputs() {
  const names = [...DEFAULT_TIER_NAMES]
  for (const custom of exp.customTierNames) {
    if (custom.index >= 0 && custom.index < names.length) {
      names[custom.index] = custom.name
    }
  }
  tierInputs.value = names
}

function saveTierNames() {
  const customNames: TierName[] = []
  tierInputs.value.forEach((name, idx) => {
    if (name.trim() && name.trim() !== DEFAULT_TIER_NAMES[idx]) {
      customNames.push({ index: idx, name: name.trim() })
    }
  })
  exp.updateCustomTierNames(customNames)
}

function resetTierNames() {
  exp.resetCustomTierNames()
  tierInputs.value = [...DEFAULT_TIER_NAMES]
}

function saveSettings() {
  settings.save()
  saved.value = true
  setTimeout(() => saved.value = false, 2000)
}
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold">设置</h1>

    <div class="space-y-6">
      <!-- Appearance -->
      <section class="p-6 rounded-lg border border-border bg-card space-y-4">
        <h2 class="font-semibold">外观</h2>
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium">暗色模式</p>
            <p class="text-xs text-muted-foreground">切换暗色/亮色主题</p>
          </div>
                    <button
            @click="settings.toggleDarkMode()"
            :class="[
              'relative w-11 h-6 rounded-full overflow-hidden transition-colors duration-200',
              settings.darkMode ? 'bg-primary' : 'bg-border',
            ]"
          >
            <span
              :class="[
                'absolute top-0.5 left-0 h-5 w-5 rounded-full bg-white shadow-sm transition-transform duration-200',
                settings.darkMode ? 'translate-x-[22px]' : 'translate-x-0.5',
              ]"
            ></span>
          </button>
        </div>
      </section>

      <!-- API -->
      <section class="p-6 rounded-lg border border-border bg-card space-y-4">
        <h2 class="font-semibold">OpenAI API</h2>
        <p class="text-xs text-muted-foreground">
          用于 AI 记忆提取、情感分析和智能问答
        </p>
        <input
          v-model="settings.apiKey"
          type="password"
          placeholder="sk-..."
          class="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </section>

      <!-- Language -->
      <section class="p-6 rounded-lg border border-border bg-card space-y-4">
        <h2 class="font-semibold">语言</h2>
        <select
          v-model="settings.language"
          class="w-full px-3 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="zh">中文</option>
          <option value="en">English</option>
        </select>
      </section>

      <!-- 经验系统 -->
      <section class="p-6 rounded-lg border border-border bg-card space-y-4">
        <h2 class="font-semibold">经验系统</h2>

        <!-- 特效开关 -->
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium">晋升特效</p>
            <p class="text-xs text-muted-foreground">升级时的摇晃与闪白动画</p>
          </div>
          <button
            @click="exp.toggleEffects()"
            :class="[
              'relative w-11 h-6 rounded-full overflow-hidden transition-colors duration-200',
              exp.effectsEnabled ? 'bg-primary' : 'bg-border',
            ]"
          >
            <span
              :class="[
                'absolute top-0.5 left-0 h-5 w-5 rounded-full bg-white shadow-sm transition-transform duration-200',
                exp.effectsEnabled ? 'translate-x-[22px]' : 'translate-x-0.5',
              ]"
            ></span>
          </button>
        </div>

        <!-- 自定义头衔 -->
        <div class="space-y-2">
          <p class="text-sm font-medium">自定义头衔</p>
          <p class="text-xs text-muted-foreground">为每个阶级设置专属名称，留空则使用默认名称</p>
          <div class="grid gap-2">
            <div v-for="(name, idx) in tierInputs" :key="idx" class="flex items-center gap-2">
              <span class="text-xs text-muted-foreground w-6 shrink-0">Lv.{{ idx + 1 }}</span>
              <input
                v-model="tierInputs[idx]"
                :placeholder="DEFAULT_TIER_NAMES[idx]"
                class="flex-1 px-3 py-1.5 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
          </div>
          <div class="flex items-center gap-2 pt-1">
            <button
              @click="saveTierNames"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              <Save class="w-3.5 h-3.5" />
              保存头衔
            </button>
            <button
              @click="resetTierNames"
              class="inline-flex items-center gap-1.5 px-3 py-1.5 border border-border rounded-md text-sm font-medium text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
            >
              <RotateCcw class="w-3.5 h-3.5" />
              重置默认
            </button>
          </div>
        </div>
      </section>

      <!-- Save -->
      <button
        @click="saveSettings"
        class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
      >
        <Save class="w-4 h-4" />
        {{ saved ? '已保存 ✓' : '保存设置' }}
      </button>
    </div>
  </div>
</template>
