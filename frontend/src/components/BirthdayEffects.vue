<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useBirthdayStore } from '@/stores/birthday'

const birthdayStore = useBirthdayStore()

// 粒子列表
interface Particle {
  id: number
  emoji: string
  x: number
  y: number
  vx: number
  vy: number
  scale: number
  opacity: number
  rotation: number
  lifetime: number
}

const particles = ref<Particle[]>([])
let particleId = 0
let animationFrame: number | null = null
let spawnTimer: number | null = null

const EMOJIS = ['✨', '🌟', '⭐', '🧁', '🎂', '🎈', '🎊', '💫', '🍰', '🎀']

/** 随机生成一个粒子 */
function spawnParticle() {
  const id = ++particleId
  const emoji = EMOJIS[Math.floor(Math.random() * EMOJIS.length)]
  const x = Math.random() * window.innerWidth
  const y = window.innerHeight + 20
  const vx = (Math.random() - 0.5) * 2
  const vy = -(2 + Math.random() * 3)
  const scale = 0.6 + Math.random() * 0.8
  const rotation = Math.random() * 360

  particles.value.push({
    id,
    emoji,
    x,
    y,
    vx,
    vy,
    scale,
    opacity: 1,
    rotation,
    lifetime: 0,
  })
}

/** 更新粒子位置 */
function updateParticles() {
  const toRemove: number[] = []
  for (const p of particles.value) {
    p.x += p.vx
    p.y += p.vy
    p.vy += 0.02 // 微弱重力
    p.rotation += 1
    p.lifetime++
    // 上升一段后开始淡出
    if (p.lifetime > 60) {
      p.opacity -= 0.02
    }
    if (p.opacity <= 0 || p.y < -50) {
      toRemove.push(p.id)
    }
  }
  if (toRemove.length) {
    particles.value = particles.value.filter(p => !toRemove.includes(p.id))
  }
  animationFrame = requestAnimationFrame(updateParticles)
}

onMounted(() => {
  if (birthdayStore.isBirthdayToday && birthdayStore.showEffects) {
    // 每 800ms 生成一个粒子
    spawnTimer = window.setInterval(spawnParticle, 800)
    animationFrame = requestAnimationFrame(updateParticles)
  }
})

onUnmounted(() => {
  if (spawnTimer) clearInterval(spawnTimer)
  if (animationFrame) cancelAnimationFrame(animationFrame)
})
</script>

<template>
  <div
    v-if="birthdayStore.isBirthdayToday && birthdayStore.showEffects"
    class="fixed inset-0 pointer-events-none z-[9998]"
    aria-hidden="true"
  >
    <div
      v-for="p in particles"
      :key="p.id"
      class="absolute select-none"
      :style="{
        left: p.x + 'px',
        top: p.y + 'px',
        transform: `scale(${p.scale}) rotate(${p.rotation}deg)`,
        opacity: p.opacity,
        fontSize: '1.2rem',
        willChange: 'transform, opacity',
      }"
    >
      {{ p.emoji }}
    </div>
  </div>
</template>