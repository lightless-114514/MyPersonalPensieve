import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  const darkMode = ref(true)
  const language = ref('zh')
  const apiKey = ref('')

  // Load from localStorage
  function load() {
    const saved = localStorage.getItem('pensieve-settings')
    if (saved) {
      const parsed = JSON.parse(saved)
      darkMode.value = parsed.darkMode ?? true
      language.value = parsed.language ?? 'zh'
      apiKey.value = parsed.apiKey ?? ''
    }
  }

  function save() {
    localStorage.setItem(
      'pensieve-settings',
      JSON.stringify({
        darkMode: darkMode.value,
        language: language.value,
        apiKey: apiKey.value,
      })
    )
  }

  // Toggle dark mode
  function toggleDarkMode() {
    darkMode.value = !darkMode.value
  }

  // Watch and sync to DOM
  watch(darkMode, (val) => {
    document.documentElement.classList.toggle('dark', val)
    save()
  })

  watch([language, apiKey], () => save())

  return { darkMode, language, apiKey, load, save, toggleDarkMode }
})
