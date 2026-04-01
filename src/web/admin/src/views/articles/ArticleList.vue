<script setup lang="ts">
/**
 * ArticleList - 文章管理列表
 * 由小美 (Desy) 维护表现层
 */
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getArticles, deleteArticle } from '@/api/articles'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Article } from '@/types'

const router = useRouter()
const loading = ref(false)
const tableData = ref<Article[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 20, status: '' as string })

const statusOptions = [
  { value: '', label: '全部状态' },
  { value: 'draft', label: '草稿' },
  { value: 'published', label: '已发布' },
  { value: 'archived', label: '已归档' },
]

const statusMap: Record<string, { label: string; type: string }> = {
  draft: { label: '草稿', type: 'info' },
  published: { label: '已发布', type: 'success' },
  archived: { label: '已归档', type: 'warning' },
}

async function fetchData() {
  loading.value = true
  try {
    const params: any = { page: query.page, page_size: query.page_size }
    if (query.status) params.status = query.status
    const res = await getArticles(params)
    tableData.value = res.data.list
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function handleFilter() {
  query.page = 1
  fetchData()
}

function handlePageChange(page: number) {
  query.page = page
  fetchData()
}

async function handleDelete(row: Article) {
  await ElMessageBox.confirm(`确定删除文章「${row.title}」？`, '提示', { type: 'warning' })
  await deleteArticle(row.id)
  ElMessage.success('删除成功')
  fetchData()
}

onMounted(fetchData)
</script>

<template>
  <div class="cms-page">
    <div class="cms-page-header">
      <h2>文章管理</h2>
      <el-button type="primary" @click="router.push('/articles/create')">
        <el-icon class="mr-1"><Plus /></el-icon> 新建文章
      </el-button>
    </div>

    <div class="cms-table-card">
      <!-- 筛选栏 -->
      <div class="cms-filter-bar">
        <el-select v-model="query.status" placeholder="状态筛选" clearable style="width:140px" @change="handleFilter">
          <el-option v-for="s in statusOptions" :key="s.value" :label="s.label" :value="s.value" />
        </el-select>
      </div>

      <!-- 表格 -->
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="flex items-center gap-1">
              <el-tag v-if="row.is_top" type="danger" size="small" effect="dark" class="mr-1">置顶</el-tag>
              <span>{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="(statusMap[row.status]?.type as any) || 'info'" size="small">
              {{ statusMap[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">
            {{ row.created_at?.slice(0, 16).replace('T', ' ') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="router.push(`/articles/${row.id}/edit`)">编辑</el-button>
            <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="flex justify-end mt-4">
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
</template>
