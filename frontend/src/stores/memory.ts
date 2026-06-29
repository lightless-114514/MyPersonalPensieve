﻿import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Memory } from '@/types'
import { openDB } from 'idb'

export const useMemoryStore = defineStore('memory', () => {
  const memories = ref<Memory[]>([])
  const searchQuery = ref('')
  const selectedMemory = ref<Memory | null>(null)
  const isLoading = ref(false)

  const filteredMemories = computed(() => {
    if (!searchQuery.value) return memories.value
    const q = searchQuery.value.toLowerCase()
    return memories.value.filter(
      (m) =>
        m.title.toLowerCase().includes(q) ||
        m.content.toLowerCase().includes(q) ||
        m.tags.some((t) => t.toLowerCase().includes(q))
    )
  })

  const recentMemories = computed(() =>
    [...memories.value]
      .sort((a, b) => new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime())
      .slice(0, 10)
  )

  function setMemories(list: Memory[]) {
    memories.value = list
  }

  function addMemory(memory: Memory) {
    memories.value.unshift(memory)
  }

  function removeMemory(id: string) {
    memories.value = memories.value.filter((m) => m.id !== id)
  }

  // IndexedDB caching
  async function cacheMemories() {
    const db = await openDB('pensieve-cache', 1, {
      upgrade(db) {
        db.createObjectStore('memories', { keyPath: 'id' })
      },
    })
    const tx = db.transaction('memories', 'readwrite')
    for (const m of memories.value) {
      await tx.store.put(m)
    }
    await tx.done
  }

  async function loadCachedMemories() {
    const db = await openDB('pensieve-cache', 1, {
      upgrade(db) {
        db.createObjectStore('memories', { keyPath: 'id' })
      },
    })
    const cached = await db.getAll('memories')
    if (cached.length > 0) {
      memories.value = cached
    }
  }

  return {
    memories,
    searchQuery,
    selectedMemory,
    isLoading,
    filteredMemories,
    recentMemories,
    setMemories,
    addMemory,
    removeMemory,
    cacheMemories,
    loadCachedMemories,
  }
})
