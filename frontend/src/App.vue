<script setup lang="ts">
import { onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useMemoryStore } from '@/stores/memory'
import AppLayout from '@/components/AppLayout.vue'

const settings = useSettingsStore()
const memoryStore = useMemoryStore()

onMounted(() => {
  settings.load()
  document.documentElement.classList.toggle('dark', settings.darkMode)
  memoryStore.loadCachedMemories()
})
</script>

<template>
  <AppLayout>
    <router-view />
  </AppLayout>
</template>
