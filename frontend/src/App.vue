<script setup lang="ts">
import { onMounted } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { useMemoryStore } from '@/stores/memory'
import { useBirthdayStore } from '@/stores/birthday'
import AppLayout from '@/components/AppLayout.vue'
import BirthdayModal from '@/components/BirthdayModal.vue'
import BirthdayEffects from '@/components/BirthdayEffects.vue'

const settings = useSettingsStore()
const memoryStore = useMemoryStore()
const birthdayStore = useBirthdayStore()

onMounted(() => {
  settings.load()
  birthdayStore.load()
  document.documentElement.classList.toggle('dark', settings.darkMode)
  memoryStore.loadCachedMemories()
})
</script>

<template>
  <AppLayout>
    <router-view />
  </AppLayout>
  <!-- 生日祝福弹窗 -->
  <BirthdayModal />
  <!-- 生日粒子特效 -->
  <BirthdayEffects />
</template>
