<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { Upload, X, FileText, ImageIcon, File, FileSpreadsheet } from 'lucide-vue-next'

interface Props {
  accept?: string
  maxSize?: number // in bytes
  modelValue?: File | null
}

const props = withDefaults(defineProps<Props>(), {
  accept: 'image/*,.pdf,.doc,.docx,.md,.txt,.json,.csv',
  maxSize: 20 * 1024 * 1024, // 20MB default
})

const emit = defineEmits<{
  (e: 'update:modelValue', file: File | null): void
}>()

const isDragging = ref(false)
const error = ref('')
const selectedFile = computed(() => props.modelValue)

// 对象 URL 管理：创建预览 URL 并在文件变更/组件卸载时自动释放
let objectUrl = ''

const previewUrl = computed(() => {
  // 释放旧的 object URL
  if (objectUrl) {
    URL.revokeObjectURL(objectUrl)
    objectUrl = ''
  }
  const file = selectedFile.value
  if (file && file.type.startsWith('image/')) {
    objectUrl = URL.createObjectURL(file)
    return objectUrl
  }
  return ''
})

onUnmounted(() => {
  if (objectUrl) {
    URL.revokeObjectURL(objectUrl)
    objectUrl = ''
  }
})

function onDragOver(e: DragEvent) {
  e.preventDefault()
  isDragging.value = true
}

function onDragLeave(e: DragEvent) {
  e.preventDefault()
  isDragging.value = false
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  isDragging.value = false
  error.value = ''

  const files = e.dataTransfer?.files
  if (!files || files.length === 0) return

  validateAndSelect(files[0])
}

function onFileInput(e: Event) {
  const target = e.target as HTMLInputElement
  const files = target.files
  if (!files || files.length === 0) return

  error.value = ''
  validateAndSelect(files[0])
  // 重置 input 以便选择同一文件
  target.value = ''
}

function validateAndSelect(file: File) {
  // 校验大小
  if (file.size > props.maxSize) {
    const maxMB = Math.round(props.maxSize / 1024 / 1024)
    error.value = `文件大小超过限制（最大 ${maxMB}MB）`
    return
  }

  // 校验类型
  const allowedTypes = props.accept.split(',').map(t => t.trim())
  const fileExt = '.' + file.name.split('.').pop()?.toLowerCase()
  const isAllowed = allowedTypes.some(allowed => {
    if (allowed.startsWith('.')) {
      return fileExt === allowed.toLowerCase()
    }
    if (allowed.endsWith('/*')) {
      const prefix = allowed.slice(0, -2)
      return file.type.startsWith(prefix)
    }
    return file.type === allowed
  })

  if (!isAllowed) {
    error.value = `不支持的文件类型: ${file.name.split('.').pop()}`
    return
  }

  emit('update:modelValue', file)
}

function removeFile() {
  emit('update:modelValue', null)
  error.value = ''
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function fileIcon(file: File) {
  if (file.type.startsWith('image/')) return ImageIcon
  if (file.type === 'application/pdf') return FileText
  if (file.type.includes('word') || file.type.includes('document')) return FileText
  if (file.type === 'application/json') return FileSpreadsheet
  if (file.type.startsWith('text/')) return FileText
  return File
}
</script>

<template>
  <div class="space-y-2">
    <!-- 拖拽区域 -->
    <div
      v-if="!selectedFile"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
      :class="[
        'relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed transition-all duration-200 cursor-pointer min-h-[160px]',
        isDragging
          ? 'border-primary bg-primary/5 scale-[1.02]'
          : 'border-border hover:border-primary/50 hover:bg-accent/30',
        error ? 'border-red-300 bg-red-50/50' : ''
      ]"
      @click="($refs.fileInput as HTMLInputElement)?.click()"
    >
      <input
        ref="fileInput"
        type="file"
        :accept="accept"
        class="hidden"
        @change="onFileInput"
      />
      <div class="flex flex-col items-center gap-2 py-6 text-muted-foreground">
        <Upload class="w-8 h-8" :class="isDragging ? 'text-primary animate-bounce' : ''" />
        <p class="text-sm font-medium">
          {{ isDragging ? '松开以上传' : '拖拽文件到此处，或点击选择' }}
        </p>
        <p class="text-xs text-muted-foreground/70">
          支持图片、PDF、Word、Markdown、TXT、JSON 等格式
        </p>
        <p class="text-xs text-muted-foreground/50">
          图片最大 10MB，文档最大 20MB
        </p>
      </div>
    </div>

    <!-- 已选文件预览 -->
    <div
      v-else
      class="flex items-center gap-3 p-3 rounded-xl border border-border bg-card"
    >
      <!-- 图片缩略图 -->
      <div v-if="selectedFile.type.startsWith('image/')" class="shrink-0">
        <img
          :src="previewUrl"
          :alt="selectedFile.name"
          class="w-16 h-16 object-cover rounded-lg border border-border"
        />
      </div>
      <!-- 文件图标 -->
      <div v-else class="shrink-0 w-16 h-16 flex items-center justify-center rounded-lg bg-accent/50 border border-border">
        <component :is="fileIcon(selectedFile)" class="w-8 h-8 text-muted-foreground" />
      </div>

      <!-- 文件信息 -->
      <div class="flex-1 min-w-0">
        <p class="text-sm font-medium truncate">{{ selectedFile.name }}</p>
        <p class="text-xs text-muted-foreground">{{ formatSize(selectedFile.size) }}</p>
      </div>

      <!-- 删除按钮 -->
      <button
        @click="removeFile"
        class="shrink-0 p-1.5 rounded-lg hover:bg-red-100 hover:text-red-500 transition-colors"
        title="移除文件"
      >
        <X class="w-4 h-4" />
      </button>
    </div>

    <!-- 错误提示 -->
    <p v-if="error" class="text-xs text-red-500">{{ error }}</p>
  </div>
</template>