<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useBirthdayStore } from '@/stores/birthday'
import { useSettingsStore } from '@/stores/settings'

const birthdayStore = useBirthdayStore()
const settings = useSettingsStore()

const visible = ref(false)
const fadeOut = ref(false)
const greeting = ref('')

onMounted(() => {
  if (birthdayStore.shouldShowGreeting) {
    greeting.value = birthdayStore.randomGreeting
    visible.value = true
    // 2秒后自动淡出
    setTimeout(() => {
      startClose()
    }, 4000)
  }
})

function startClose() {
  if (!visible.value) return
  fadeOut.value = true
  setTimeout(() => {
    visible.value = false
    fadeOut.value = false
    birthdayStore.markGreetingShown()
  }, 600)
}
</script>

<template>
  <Transition name="birthday-modal">
    <div
      v-if="visible"
      class="fixed inset-0 z-[10000] flex items-center justify-center cursor-pointer"
      @click="startClose"
    >
      <!-- 背景遮罩 -->
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" :class="{ 'modal-fade-out': fadeOut }"></div>

      <!-- 弹窗内容 -->
      <div
        class="relative z-10 text-center px-8 py-10 max-w-md mx-4"
        :class="{ 'content-fade-out': fadeOut }"
      >
        <!-- 蛋糕 + 气球装饰 -->
        <div class="birthday-decorations">
          <span class="decoration balloon balloon-1">🎈</span>
          <span class="decoration balloon balloon-2">🎈</span>
          <span class="decoration balloon balloon-3">🎈</span>
          <span class="decoration confetti confetti-1">🎊</span>
          <span class="decoration confetti confetti-2">🎉</span>
          <span class="decoration confetti confetti-3">✨</span>
        </div>

        <!-- 蛋糕图标 -->
        <div class="text-6xl mb-4 animate-bounce-slow">🎂</div>

        <!-- 祝福标题 -->
        <h1 class="text-3xl font-bold mb-3 font-display birthday-title">
          <template v-if="settings.apiKey">
            生日快乐！
          </template>
          <template v-else>
            今天是你生日，生日快乐！
          </template>
        </h1>

        <!-- 祝福文案 -->
        <p class="text-lg text-white/80 mb-4 leading-relaxed">
          {{ greeting }}
        </p>

        <!-- 年龄显示 -->
        <p v-if="birthdayStore.age" class="text-sm text-white/50">
          🎂 记录于你第 {{ birthdayStore.age + 1 }} 岁的第一天
        </p>

        <!-- 提示 -->
        <p class="text-xs text-white/30 mt-6">点击任意处关闭</p>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
/* 弹窗入场/出场动画 */
.birthday-modal-enter-active {
  animation: modalIn 0.5s ease-out;
}
.birthday-modal-leave-active {
  animation: modalOut 0.6s ease-in;
}

@keyframes modalIn {
  0% {
    opacity: 0;
  }
  100% {
    opacity: 1;
  }
}

@keyframes modalOut {
  0% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}

.modal-fade-out {
  animation: bgFadeOut 0.6s ease-in forwards;
}

@keyframes bgFadeOut {
  to { opacity: 0; }
}

.content-fade-out {
  animation: contentFadeOut 0.6s ease-in forwards;
}

@keyframes contentFadeOut {
  to {
    opacity: 0;
    transform: translateY(-20px);
  }
}

/* 标题渐变色 */
.birthday-title {
  background: linear-gradient(135deg, #ff6b6b, #ffd93d, #6bcb77, #4d96ff);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradientShift 3s ease infinite;
}

@keyframes gradientShift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

/* 蛋糕慢弹跳 */
.animate-bounce-slow {
  animation: bounceSlow 2s ease-in-out infinite;
}

@keyframes bounceSlow {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

/* 装饰物容器 */
.birthday-decorations {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.decoration {
  position: absolute;
  font-size: 1.5rem;
  animation: float 3s ease-in-out infinite;
}

/* 气球 */
.balloon-1 {
  top: 10%;
  left: 10%;
  animation-delay: 0s;
}
.balloon-2 {
  top: 5%;
  right: 15%;
  animation-delay: 0.5s;
}
.balloon-3 {
  top: 15%;
  right: 5%;
  animation-delay: 1s;
}

/* 彩带 */
.confetti-1 {
  bottom: 15%;
  left: 5%;
  animation-delay: 0.3s;
}
.confetti-2 {
  bottom: 10%;
  right: 10%;
  animation-delay: 0.8s;
}
.confetti-3 {
  top: 30%;
  left: 5%;
  animation-delay: 1.5s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-15px) rotate(10deg);
  }
}
</style>