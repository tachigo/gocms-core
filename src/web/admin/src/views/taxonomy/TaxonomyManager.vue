<script setup lang="ts">
/**
 * TaxonomyManager - 分类管理（词汇表 + 术语树）
 * 由小美 (Desy) 维护表现层
 */
import { ref, reactive, computed, onMounted } from 'vue'
import { getTaxonomies, getTerms, createTerm, updateTerm, deleteTerm } from '@/api/taxonomy'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Taxonomy, TaxonomyTerm } from '@/types'

const taxonomies = ref<Taxonomy[]>([])
const currentVocabId = ref('')
const terms = ref<TaxonomyTerm[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)

const form = reactive({
  id: 0,
  name: '',
  slug: '',
  description: '',
  parent_id: null as number | null,
  seo_title: '',
  seo_desc: '',
})

const currentVocab = computed(() => taxonomies.value.find(t => t.id === currentVocabId.value))

async function loadTaxonomies() {
  const res = await getTaxonomies()
  taxonomies.value = res.data.list || []
  if (taxonomies.value.length && !currentVocabId.value) {
    currentVocabId.value = taxonomies.value[0].id
    await loadTerms()
  }
}

async function loadTerms() {
  if (!currentVocabId.value) return
  loading.value = true
  try {
    const res = await getTerms(currentVocabId.value)
    terms.value = res.data.list || []
  } finally {
    loading.value = false
  }
}

function handleVocabChange() {
  loadTerms()
}

// 构建树形数据
function buildTree(items: TaxonomyTerm[]): TaxonomyTerm[] {
  const map = new Map<number, TaxonomyTerm>()
  const roots: TaxonomyTerm[] = []
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

const treeData = computed(() => buildTree(terms.value))

function openCreate(parentId?: number) {
  isEdit.value = false
  Object.assign(form, {
    id: 0,
    name: '',
    slug: '',
    description: '',
    parent_id: parentId || null,
    seo_title: '',
    seo_desc: '',
  })
  dialogVisible.value = true
}

function openEdit(item: TaxonomyTerm) {
  isEdit.value = true
  Object.assign(form, {
    id: item.id,
    name: item.name,
    slug: item.slug,
    description: item.description,
    parent_id: item.parent_id,
    seo_title: item.seo_title,
    seo_desc: item.seo_desc,
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.name || !form.slug) {
    ElMessage.warning('请填写名称和别名')
    return
  }
  try {
    if (isEdit.value) {
      await updateTerm(currentVocabId.value, { ...form })
      ElMessage.success('更新成功')
    } else {
      await createTerm(currentVocabId.value, { ...form })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadTerms()
  } catch { /* 错误已在拦截器处理 */ }
}

async function handleDelete(item: TaxonomyTerm) {
  await ElMessageBox.confirm(`确定删除「${item.name}」？子项也会被删除`, '提示', { type: 'warning' })
  await deleteTerm(currentVocabId.value, item.id)
  ElMessage.success('删除成功')
  loadTerms()
}

// 渲染树
function renderTree(items: TaxonomyTerm[], level = 0): any {
  return items.map(item => ({
    key: item.id,
    label: () => h('div', { class: 'flex items-center justify-between w-full py-1' }, [
      h('span', { class: `text-${14 - level}px` }, item.name),
      h('div', { class: 'flex gap-1' }, [
        currentVocab.value?.hierarchical && h(ElButton, { text: true, size: 'small', onClick: () => openCreate(item.id) }, () => '添加子项'),
        h(ElButton, { text: true, type: 'primary', size: 'small', onClick: () => openEdit(item) }, () => '编辑'),
        h(ElButton, { text: true, type: 'danger', size: 'small', onClick: () => handleDelete(item) }, () => '删除'),
      ]),
    ]),
    children: item.children?.length ? renderTree(item.children, level + 1) : undefined,
  }))
}

import { h } from 'vue'
import { ElButton } from 'element-plus'

onMounted(loadTaxonomies)
</script>

<template>
  <div class="cms-page">
    <div class="cms-page-header">
      <h2>分类管理</h2>
    </div>

    <div class="flex gap-4">
      <!-- 左侧：词汇表 -->
      <div class="w-[200px]">
        <div class="cms-card">
          <h4 class="text-sm font-semibold mb-3">词汇表</h4>
          <el-menu :default-active="currentVocabId" @select="(id: string) => { currentVocabId = id; handleVocabChange() }">
            <el-menu-item v-for="t in taxonomies" :key="t.id" :index="t.id">
              <div class="flex flex-col">
                <span>{{ t.name }}</span>
                <span class="text-xs text-gray-400">{{ t.hierarchical ? '层级分类' : '扁平标签' }}</span>
              </div>
            </el-menu-item>
          </el-menu>
        </div>
      </div>

      <!-- 右侧：术语列表 -->
      <div class="flex-1">
        <div class="cms-card">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-base font-semibold m-0">{{ currentVocab?.name }}</h3>
              <p class="text-sm text-gray-400 m-0 mt-1">{{ currentVocab?.description }}</p>
            </div>
            <el-button type="primary" @click="openCreate()">
              <el-icon class="mr-1"><Plus /></el-icon> 添加{{ currentVocab?.hierarchical ? '分类' : '标签' }}
            </el-button>
          </div>

          <el-tree
            v-if="treeData.length"
            :data="treeData"
            :props="{ label: 'name', children: 'children' }"
            node-key="id"
            default-expand-all
            v-loading="loading"
          >
            <template #default="{ node, data }">
              <div class="flex items-center justify-between w-full">
                <span>{{ data.name }}</span>
                <div class="flex gap-1">
                  <el-button
                    v-if="currentVocab?.hierarchical"
                    text
                    size="small"
                    @click.stop="openCreate(data.id)"
                  >添加子项</el-button>
                  <el-button text type="primary" size="small" @click.stop="openEdit(data)">编辑</el-button>
                  <el-button text type="danger" size="small" @click.stop="handleDelete(data)">删除</el-button>
                </div>
              </div>
            </template>
          </el-tree>

          <el-empty v-else description="暂无术语" />
        </div>
      </div>
    </div>

    <!-- 编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑术语' : '添加术语'" width="500px">
      <el-form label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="显示名称" />
        </el-form-item>
        <el-form-item label="别名">
          <el-input v-model="form.slug" placeholder="url-slug" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="描述（可选）" />
        </el-form-item>
        <el-collapse class="mt-2">
          <el-collapse-item title="SEO 设置" name="seo">
            <el-form-item label="SEO 标题">
              <el-input v-model="form.seo_title" placeholder="SEO 标题（可选）" />
            </el-form-item>
            <el-form-item label="SEO 描述">
              <el-input v-model="form.seo_desc" type="textarea" :rows="2" placeholder="SEO 描述（可选）" />
            </el-form-item>
          </el-collapse-item>
        </el-collapse>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
