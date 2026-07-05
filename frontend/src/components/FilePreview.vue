<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { getFilePreviewUrl } from '@/api'
import { formatFileSize } from '@/lib/utils'
import { Download, X, ZoomIn, ZoomOut, FileText, ImageIcon, File } from 'lucide-vue-next'

interface Props {
  memoryId: string
  filePath?: string | null
  mimeType?: string | null
  fileSize?: number | null
  title?: string
}

const props = defineProps<Props>()

const previewUrl = computed(() => getFilePreviewUrl(props.memoryId))
const isImage = computed(() => props.mimeType?.startsWith('image/') ?? false)
const isPdf = computed(() => props.mimeType === 'application/pdf')
const isText = computed(() => {
  if (!props.mimeType) return false
  return props.mimeType.startsWith('text/') || props.mimeType === 'application/json'
})
const isWord = computed(() => {
  if (!props.mimeType) return false
  return props.mimeType.includes('word') || props.mimeType.includes('document')
})
const isPreviewable = computed(() => isImage.value || isPdf.value || isText.value)

// 图片缩放
const zoom = ref(1)
function zoomIn() { zoom.value = Math.min(zoom.value + 0.25, 3) }
function zoomOut() { zoom.value = Math.max(zoom.value - 0.25, 0.25) }

// 文本内容预览
const textContent = ref('')
const textLoading = ref(false)

async function loadTextContent() {
  if (!isText.value) return
  textLoading.value = true
  try {
    const resp = await fetch(previewUrl.value)
    if (resp.ok) {
      textContent.value = await resp.text()
      // JSON 格式化
      if (props.mimeType === 'application/json') {
        try {
          textContent.value = JSON.stringify(JSON.parse(textContent.value), null, 2)
        } catch { /* keep original */ }
      }
    }
  } catch (e) {
    textContent.value = '加载失败'
  } finally {
    textLoading.value = false
  }
}

watch(() => props.memoryId, () => {
  textContent.value = ''
  zoom.value = 1
  loadTextContent()
}, { immediate: true })

// 全屏预览
const isFullscreen = ref(false)
function toggleFullscreen() { isFullscreen.value = !isFullscreen.value }
function closeFullscreen() { isFullscreen.value = false }

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && isFullscreen.value) {
    closeFullscreen()
  }
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))

function downloadFile() {
  const a = document.createElement('a')
  a.href = previewUrl.value
  a.download = props.title || 'download'
  a.target = '_blank'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

function fileIcon() {
  if (isImage.value) return ImageIcon
  if (isPdf.value || isWord.value || isText.value) return FileText
  return File
}
</script>

<template>
  <div class="space-y-3">
    <!-- 文件信息栏 -->
    <div class="flex items-center justify-between p-3 rounded-lg bg-accent/50 border border-border/50">
      <div class="flex items-center gap-2.5">
        <component :is="fileIcon()" class="w-5 h-5 text-muted-foreground shrink-0" />
        <div class="min-w-0">
          <p class="text-sm font-medium truncate">{{ title || '附件' }}</p>
          <p class="text-xs text-muted-foreground">
            {{ mimeType || '未知类型' }}
            <span v-if="fileSize" class="ml-2">{{ formatFileSize(fileSize) }}</span>
          </p>
        </div>
      </div>
      <div class="flex items-center gap-1">
        <button
          v-if="isPreviewable"
          @click="toggleFullscreen"
          class="p-2 rounded-lg text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors"
          title="全屏预览"
        >
          <ZoomIn class="w-4 h-4" />
        </button>
        <button
          @click="downloadFile"
          class="p-2 rounded-lg text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors"
          title="下载"
        >
          <Download class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- 内联预览 -->
    <div v-if="isPreviewable" class="rounded-xl border border-border overflow-hidden bg-card">
      <!-- 图片预览 -->
      <div v-if="isImage" class="relative flex items-center justify-center p-2 bg-muted/30 min-h-[200px]">
        <img
          :src="previewUrl"
          :alt="title || '图片'"
          :style="{ transform: `scale(${zoom})`, transformOrigin: 'center' }"
          class="max-w-full max-h-[500px] object-contain transition-transform duration-200 rounded-lg cursor-zoom-in"
          @click="toggleFullscreen"
        />
        <div class="absolute bottom-2 right-2 flex gap-1 bg-background/80 backdrop-blur-sm rounded-lg p-1 border border-border">
          <button @click="zoomOut" class="p-1 rounded hover:bg-accent transition-colors" title="缩小">
            <ZoomOut class="w-4 h-4" />
          </button>
          <span class="text-xs px-2 py-1 tabular-nums">{{ Math.round(zoom * 100) }}%</span>
          <button @click="zoomIn" class="p-1 rounded hover:bg-accent transition-colors" title="放大">
            <ZoomIn class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- PDF 预览 -->
      <div v-else-if="isPdf" class="h-[600px]">
        <iframe
          :src="previewUrl"
          class="w-full h-full border-0"
          title="PDF 预览"
        />
      </div>

      <!-- 文本预览 -->
      <div v-else-if="isText" class="max-h-[500px] overflow-auto">
        <div v-if="textLoading" class="p-6 text-center text-muted-foreground">加载中...</div>
        <pre v-else class="p-4 text-sm font-mono whitespace-pre-wrap break-words leading-relaxed">{{ textContent }}</pre>
      </div>
    </div>

    <!-- 不可预览的文件类型 -->
    <div v-else class="p-6 rounded-xl border border-border bg-card text-center">
      <component :is="fileIcon()" class="w-12 h-12 mx-auto text-muted-foreground/50 mb-3" />
      <p class="text-sm text-muted-foreground mb-2">此文件类型不支持在线预览</p>
      <button
        @click="downloadFile"
        class="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-all duration-200"
      >
        <Download class="w-4 h-4" />
        下载文件
      </button>
    </div>

    <!-- 全屏预览弹窗 -->
    <Teleport to="body">
      <div
        v-if="isFullscreen"
        class="fixed inset-0 z-[9999] bg-black/90 flex items-center justify-center"
        @click.self="closeFullscreen"
      >
        <button
          @click="closeFullscreen"
          class="absolute top-4 right-4 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
        >
          <X class="w-6 h-6" />
        </button>

        <!-- 全屏图片 -->
        <img
          v-if="isImage"
          :src="previewUrl"
          :alt="title || '图片'"
          :style="{ transform: `scale(${zoom})`, transformOrigin: 'center' }"
          class="max-w-[90vw] max-h-[90vh] object-contain transition-transform duration-200"
        />

        <!-- 全屏 PDF -->
        <iframe
          v-else-if="isPdf"
          :src="previewUrl"
          class="w-[90vw] h-[90vh] border-0 rounded-lg"
          title="PDF 预览"
        />

        <!-- 全屏文本 -->
        <div v-else-if="isText" class="w-[90vw] h-[90vh] bg-white rounded-lg overflow-auto p-6">
          <pre class="text-sm font-mono whitespace-pre-wrap break-words leading-relaxed text-gray-800">{{ textContent }}</pre>
        </div>
      </div>
    </Teleport>
  </div>
</template>