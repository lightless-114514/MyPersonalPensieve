<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import Sidebar from './Sidebar.vue'

const route = useRoute()
const settings = useSettingsStore()

// 确保离开页面时清理可能阻塞的动画状态
function onBeforeLeave() {
  // 强制移除可能残留的过渡类，防止卡住
  document.querySelectorAll('.page-enter-active, .page-leave-active').forEach(el => {
    el.classList.remove('page-enter-active', 'page-leave-active')
  })
}
</script>

<template>
  <div class="flex h-screen overflow-hidden">
    <Sidebar />
    <main class="flex-1 overflow-y-auto p-6">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in" @before-leave="onBeforeLeave">
          <component :is="Component" :key="$route.path" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<style scoped>
.page-enter-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
  will-change: opacity, transform;
}
.page-leave-active {
  transition: opacity 0.15s ease;
  will-change: opacity;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(4px);
}
.page-leave-to {
  opacity: 0;
}
</style>