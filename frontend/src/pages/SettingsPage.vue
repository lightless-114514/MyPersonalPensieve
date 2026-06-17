<script setup lang="ts">
import { useSettingsStore } from '@/stores/settings'
import { ref } from 'vue'
import { Save } from 'lucide-vue-next'

const settings = useSettingsStore()
const saved = ref(false)

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
