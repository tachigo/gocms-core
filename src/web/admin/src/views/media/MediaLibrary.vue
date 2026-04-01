<script setup lang="ts">
/**
 * MediaLibrary - 媒体库（上传、文件夹、网格预览）
 * 由小美 (Desy) 维护表现层
 */
import { ref, reactive, onMounted, computed } from 'vue'
import {
  getMediaList, uploadMedia, deleteMedia,
  getFolders, createFolder, renameFolder, deleteFolder,
  updateMedia,
} from '@/api/media'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { MediaItem, MediaFolder } from '@/types'

const loading = ref(false)
const uploading = ref(false)
const mediaList = ref<MediaItem[]>([])
const folders = ref<MediaFolder[]>([])
const currentFolderId = ref<number | null>(null)
const total = ref(0)
const query = reactive({ page: 1, page_size: 24 })

// 上传引用
const uploadRef = ref<any>()

// 文件夹对话框
const folderDialogVisible = ref(false)
const folderForm = reactive({ id: 0, name: '' })
const isEditFolder = ref(false)

// 编辑媒体对话框
const mediaDialogVisible = ref(false)
const editingMedia = reactive<Partial<MediaItem>>({ id: 0, filename: '', alt: '', title: '' })

// 计算属性
const currentFolderName = computed(() => {
  if (!currentFolderId.value) return '全部文件'
  const folder = folders.value.find(f => f.id === currentFolderId.value)
  return folder?.name || '未知文件夹'
})

const breadcrumbFolders = computed(() => {
  const result: MediaFolder[] = []
  let current = folders.value.find(f => f.id === currentFolderId.value)
  while (current) {
    result.unshift(current)
    current = folders.value.find(f => f.id === current.parent_id)
  }
  return result
})

async function fetchData() {
  loading.value = true
  try {
    const params: any = { page: query.page, page_size: query.page_size }
    if (currentFolderId.value) params.folder_id = currentFolderId.value
    const res = await getMediaList(params)
    mediaList.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function loadFolders() {
  const res = await getFolders()
  folders.value = res.data.list || []
}

function selectFolder(folderId: number | null) {
  currentFolderId.value = folderId
  query.page = 1
  fetchData()
}

function handlePageChange(page: number) {
  query.page = page
  fetchData()
}

// 上传处理
async function handleUpload(file: File) {
  uploading.value = true
  try {
    await uploadMedia(file, currentFolderId.value)
    ElMessage.success('上传成功')
    fetchData()
  } catch {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

function beforeUpload(file: File) {
  const maxSize = 10 * 1024 * 1024 // 10MB
  if (file.size > maxSize) {
    ElMessage.warning('文件大小不能超过 10MB')
    return false
  }
  handleUpload(file)
  return false // 阻止自动上传
}

// 媒体项操作
function openEditMedia(item: MediaItem) {
  Object.assign(editingMedia, { ...item })
  mediaDialogVisible.value = true
}

async function handleSaveMedia() {
  if (!editingMedia.id) return
  await updateMedia(editingMedia.id, {
    alt: editingMedia.alt,
    title: editingMedia.title,
  })
  ElMessage.success('更新成功')
  mediaDialogVisible.value = false
  fetchData()
}

async function handleDeleteMedia(item: MediaItem) {
  await ElMessageBox.confirm(`确定删除「${item.filename}」？`, '提示', { type: 'warning' })
  await deleteMedia(item.id)
  ElMessage.success('删除成功')
  fetchData()
}

function copyUrl(url: string) {
  navigator.clipboard.writeText(url)
  ElMessage.success('链接已复制')
}

// 文件夹操作
function openCreateFolder() {
  isEditFolder.value = false
  folderForm.id = 0
  folderForm.name = ''
  folderDialogVisible.value = true
}

function openEditFolder(folder: MediaFolder) {
  isEditFolder.value = true
  folderForm.id = folder.id
  folderForm.name = folder.name
  folderDialogVisible.value = true
}

async function handleSaveFolder() {
  if (!folderForm.name.trim()) {
    ElMessage.warning('请输入文件夹名称')
    return
  }
  try {
    if (isEditFolder.value) {
      await renameFolder(folderForm.id, folderForm.name)
      ElMessage.success('重命名成功')
    } else {
      await createFolder(folderForm.name, currentFolderId.value)
      ElMessage.success('创建成功')
    }
    folderDialogVisible.value = false
    loadFolders()
  } catch { /* 错误已在拦截器处理 */ }
}

async function handleDeleteFolder(folder: MediaFolder) {
  await ElMessageBox.confirm(`确定删除文件夹「${folder.name}」？文件夹内的文件将被移出。`, '提示', { type: 'warning' })
  await deleteFolder(folder.id)
  ElMessage.success('删除成功')
  loadFolders()
  if (currentFolderId.value === folder.id) {
    currentFolderId.value = null
    fetchData()
  }
}

// 格式化文件大小
function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

onMounted(() => {
  loadFolders()
  fetchData()
})
</script>

<template>
  <div class="cms-page">
    <div class="cms-page-header">
      <h2>媒体库</h2>
      <div class="flex gap-2">
        <el-button type="primary" @click="uploadRef?.$el.querySelector('input')?.click()">
          <el-icon class="mr-1"><Upload /></el-icon> 上传文件
        </el-button>
        <el-button @click="openCreateFolder">
          <el-icon class="mr-1"><FolderAdd /></el-icon> 新建文件夹
        </el-button>
      </div>
    </div>

    <div class="flex gap-4 h-[calc(100vh-180px)]">
      <!-- 左侧：文件夹树 -->
      <div class="w-[220px] shrink-0">
        <div class="cms-card h-full">
          <h4 class="text-sm font-semibold mb-3">文件夹</h4>
          <div class="space-y-1">
            <div
              class="flex items-center justify-between px-3 py-2 rounded cursor-pointer transition-colors"
              :class="currentFolderId === null ? 'bg-primary/10 text-primary' : 'hover:bg-gray-100'"
              @click="selectFolder(null)"
            >
              <span class="flex items-center gap-2">
                <el-icon><Folder /></el-icon> 全部文件
              </span>
            </div>
            <div
              v-for="folder in folders"
              :key="folder.id"
              class="flex items-center justify-between px-3 py-2 rounded cursor-pointer transition-colors group"
              :class="currentFolderId === folder.id ? 'bg-primary/10 text-primary' : 'hover:bg-gray-100'"
              @click="selectFolder(folder.id)"
            >
              <span class="flex items-center gap-2 truncate">
                <el-icon><Folder /></el-icon> {{ folder.name }}
              </span>
              <el-dropdown trigger="click" @command="(cmd: string) => cmd === 'edit' ? openEditFolder(folder) : handleDeleteFolder(folder)">
                <el-icon class="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-gray-200 rounded"><MoreFilled /></el-icon>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="edit"><el-icon><Edit /></el-icon> 重命名</el-dropdown-item>
                    <el-dropdown-item command="delete" divided><el-icon><Delete /></el-icon> 删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：文件网格 -->
      <div class="flex-1 min-w-0">
        <div class="cms-card h-full flex flex-col">
          <!-- 面包屑 -->
          <div class="flex items-center gap-2 mb-4 text-sm">
            <span class="cursor-pointer text-primary hover:underline" @click="selectFolder(null)">全部文件</span>
            <template v-for="folder in breadcrumbFolders" :key="folder.id">
              <el-icon><ArrowRight /></el-icon>
              <span class="cursor-pointer text-primary hover:underline" @click="selectFolder(folder.id)">{{ folder.name }}</span>
            </template>
            <span class="text-gray-400">({{ total }} 个文件)</span>
          </div>

          <!-- 上传输入框（隐藏） -->
          <el-upload
            ref="uploadRef"
            class="hidden-upload"
            :auto-upload="false"
            :show-file-list="false"
            :before-upload="beforeUpload"
            multiple
          />

          <!-- 文件网格 -->
          <div class="flex-1 overflow-y-auto" v-loading="loading || uploading">
            <el-empty v-if="mediaList.length === 0 && !loading" description="暂无文件，点击上方上传" />
            
            <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
              <div
                v-for="item in mediaList"
                :key="item.id"
                class="media-card group relative bg-white border rounded-lg overflow-hidden hover:shadow-lg transition-all cursor-pointer"
              >
                <!-- 预览图 -->
                <div class="aspect-square bg-gray-50 flex items-center justify-center overflow-hidden">
                  <img
                    v-if="item.mime_type?.startsWith('image/')"
                    :src="item.url"
                    :alt="item.alt || item.filename"
                    class="w-full h-full object-cover"
                    loading="lazy"
                  />
                  <el-icon v-else class="text-4xl text-gray-400"><Document /></el-icon>
                </div>

                <!-- 信息 -->
                <div class="p-2">
                  <p class="text-xs truncate text-gray-700" :title="item.filename">{{ item.filename }}</p>
                  <p class="text-xs text-gray-400">{{ formatSize(item.size) }}</p>
                </div>

                <!-- 悬停操作 -->
                <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                  <el-button circle size="small" @click.stop="openEditMedia(item)">
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button circle size="small" @click.stop="copyUrl(item.url)">
                    <el-icon><Link /></el-icon>
                  </el-button>
                  <el-button circle size="small" type="danger" @click.stop="handleDeleteMedia(item)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>

          <!-- 分页 -->
          <div class="flex justify-end mt-4 pt-4 border-t" v-if="total > query.page_size">
            <el-pagination
              v-model:current-page="query.page"
              :page-size="query.page_size"
              :total="total"
              layout="total, prev, pager, next"
              @current-change="handlePageChange"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 文件夹对话框 -->
    <el-dialog v-model="folderDialogVisible" :title="isEditFolder ? '重命名文件夹' : '新建文件夹'" width="400px">
      <el-form label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="folderForm.name" placeholder="文件夹名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="folderDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveFolder">确定</el-button>
      </template>
    </el-dialog>

    <!-- 编辑媒体对话框 -->
    <el-dialog v-model="mediaDialogVisible" title="编辑媒体信息" width="500px">
      <el-form label-width="80px">
        <el-form-item label="文件名">
          <el-input v-model="editingMedia.filename" disabled />
        </el-form-item>
        <el-form-item label="Alt 文本">
          <el-input v-model="editingMedia.alt" placeholder="图片替代文本（用于无障碍）" />
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="editingMedia.title" placeholder="图片标题（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="mediaDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveMedia">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.media-card:hover {
  border-color: var(--el-color-primary);
}
.hidden-upload {
  display: none;
}
</style>