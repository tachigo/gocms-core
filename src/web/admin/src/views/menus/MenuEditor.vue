<script setup lang="ts">
/**
 * MenuEditor - 菜单编辑器（树形拖拽）
 * 由小美 (Desy) 维护表现层
 */
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getMenus, getMenu, updateMenu, resetMenu } from '@/api/menus'
import { ElMessage, ElMessageBox } from 'element-plus'
import draggable from 'vuedraggable'
import type { Menu, MenuItem } from '@/types'

const router = useRouter()
const menus = ref<Menu[]>([])
const currentMenuId = ref('')
const menuItems = ref<MenuItem[]>([])
const loading = ref(false)
const saving = ref(false)

// 当前编辑的菜单项
const editingItem = reactive<Partial<MenuItem>>({
  item_id: '',
  label: '',
  url: '',
  icon: '',
  external: false,
  target: '_self',
  parent_id: null,
})
const isEditing = ref(false)

const currentMenu = computed(() => menus.value.find(m => m.id === currentMenuId.value))

async function loadMenus() {
  const res = await getMenus()
  menus.value = res.data.list || []
  if (menus.value.length && !currentMenuId.value) {
    currentMenuId.value = menus.value[0].id
    await loadMenuItems()
  }
}

async function loadMenuItems() {
  if (!currentMenuId.value) return
  loading.value = true
  try {
    const res = await getMenu(currentMenuId.value)
    menuItems.value = res.data.items || []
  } finally {
    loading.value = false
  }
}

function handleMenuChange() {
  loadMenuItems()
  isEditing.value = false
}

function buildTree(items: MenuItem[]): MenuItem[] {
  const map = new Map<number, MenuItem>()
  const roots: MenuItem[] = []
  items.forEach(item => {
    map.set(item.id, { ...item, children: [] })
  })
  map.forEach(item => {
    if (item.parent_id && map.has(item.parent_id)) {
      const parent = map.get(item.parent_id)!
      parent.children = parent.children || []
      parent.children.push(item)
    } else {
      roots.push(item)
    }
  })
  return roots
}

function flattenTree(items: MenuItem[]): MenuItem[] {
  const result: MenuItem[] = []
  const walk = (list: MenuItem[], parentId?: number) => {
    list.forEach((item, index) => {
      const { children, ...rest } = item
      result.push({ ...rest, parent_id: parentId || null, sort: index })
      if (children?.length) walk(children, item.id)
    })
  }
  walk(items)
  return result
}

const treeData = computed(() => buildTree(menuItems.value))

function addItem(parentId?: number) {
  Object.assign(editingItem, {
    item_id: `item_${Date.now()}`,
    label: '新菜单项',
    url: '/',
    icon: '',
    external: false,
    target: '_self',
    parent_id: parentId || null,
  })
  isEditing.value = true
}

function editItem(item: MenuItem) {
  Object.assign(editingItem, { ...item })
  isEditing.value = true
}

function removeItem(id: number) {
  menuItems.value = menuItems.value.filter(i => i.id !== id)
  isEditing.value = false
}

function saveItem() {
  if (!editingItem.label || !editingItem.url) {
    ElMessage.warning('请填写完整信息')
    return
  }
  const idx = menuItems.value.findIndex(i => i.id === editingItem.id)
  if (idx > -1) {
    menuItems.value[idx] = { ...menuItems.value[idx], ...editingItem } as MenuItem
  } else {
    menuItems.value.push({
      id: Date.now(),
      menu_id: currentMenuId.value,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      ...editingItem,
    } as MenuItem)
  }
  isEditing.value = false
}

async function handleSave() {
  saving.value = true
  try {
    const flat = flattenTree(treeData.value)
    await updateMenu(currentMenuId.value, flat)
    ElMessage.success('保存成功')
  } finally {
    saving.value = false
  }
}

async function handleReset() {
  await ElMessageBox.confirm('确定重置为 YAML 配置？所有更改将丢失', '警告', { type: 'warning' })
  await resetMenu(currentMenuId.value)
  ElMessage.success('已重置')
  loadMenuItems()
}

onMounted(loadMenus)
</script>

<template>
  <div class="cms-page">
    <div class="cms-page-header">
      <h2>菜单管理</h2>
      <div class="flex gap-2">
        <el-button @click="handleReset">重置</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </div>
    </div>

    <div class="flex gap-4 h-[calc(100vh-180px)]">
      <!-- 左侧：菜单选择 -->
      <div class="w-[200px] shrink-0">
        <div class="cms-card h-full">
          <h4 class="text-sm font-semibold mb-3">选择菜单</h4>
          <el-menu :default-active="currentMenuId" @select="(id: string) => { currentMenuId = id; handleMenuChange() }">
            <el-menu-item v-for="m in menus" :key="m.id" :index="m.id">
              {{ m.name }}
            </el-menu-item>
          </el-menu>
        </div>
      </div>

      <!-- 中间：菜单项树 -->
      <div class="flex-1 min-w-0">
        <div class="cms-card h-full flex flex-col">
          <div class="flex items-center justify-between mb-4">
            <h4 class="text-sm font-semibold">{{ currentMenu?.name }} - 菜单项</h4>
            <el-button type="primary" size="small" @click="addItem()">
              <el-icon class="mr-1"><Plus /></el-icon> 添加项
            </el-button>
          </div>

          <div class="flex-1 overflow-auto" v-loading="loading">
            <div v-if="treeData.length === 0" class="text-center text-gray-400 py-10">
              暂无菜单项，点击上方按钮添加
            </div>
            <nested-draggable v-else :items="treeData" @edit="editItem" @remove="removeItem" @add-child="addItem" />
          </div>
        </div>
      </div>

      <!-- 右侧：编辑面板 -->
      <div class="w-[320px] shrink-0">
        <div class="cms-card h-full" v-if="isEditing">
          <h4 class="text-sm font-semibold mb-4">编辑菜单项</h4>
          <el-form label-position="top" size="small">
            <el-form-item label="显示文本">
              <el-input v-model="editingItem.label" />
            </el-form-item>
            <el-form-item label="URL">
              <el-input v-model="editingItem.url" />
            </el-form-item>
            <el-form-item label="图标">
              <el-input v-model="editingItem.icon" placeholder="ElementPlus 图标名" />
            </el-form-item>
            <el-form-item>
              <el-checkbox v-model="editingItem.external">外部链接</el-checkbox>
            </el-form-item>
            <el-form-item label="打开方式" v-if="editingItem.external">
              <el-radio-group v-model="editingItem.target">
                <el-radio label="_self">当前页</el-radio>
                <el-radio label="_blank">新窗口</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveItem">保存</el-button>
              <el-button @click="isEditing = false">取消</el-button>
            </el-form-item>
          </el-form>
        </div>
        <div v-else class="cms-card h-full flex items-center justify-center text-gray-400">
          选择菜单项进行编辑
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
:deep(.el-menu) {
  border-right: none;
}
</style>
