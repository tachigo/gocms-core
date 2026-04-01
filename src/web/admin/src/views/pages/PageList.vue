<script setup lang="ts">
/**
 * PageList - 页面管理列表
 * 由小美 (Desy) 维护表现层
 */
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getPages, deletePage, publishPage, unpublishPage } from '@/api/pages'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { PageInfo } from '@/types'

const router = useRouter()
const loading = ref(false)
const tableData = ref<PageInfo[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 20, status: '' })

const statusMap: Record<string, { label: string; type: string }> = {
  draft: { label: '草稿', type: 'info' },
  published: { label: '已发布', type: 'success' },
}

async function fetchData() {
  loading.value = true
  try {
    const params: any = { page: query.page, page_size: query.page_size }
    if (query.status) params.status = query.status
    const res = await getPages(params)
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

async function handleTogglePublish(row: PageInfo) {
  if (row.status === 'published') {
    await unpublishPage(row.id)
    ElMessage.success('已取消发布')
  } else {
    await publishPage(row.id)
    ElMessage.success('已发布')
  }
  fetchData()
}

async function handleDelete(row: PageInfo) {
  await ElMessageBox.confirm(`确定删除页面「${row.title}」？`, '提示', { type: 'warning' })
  await deletePage(row.id)
  ElMessage.success('删除成功')
  fetchData()
}

onMounted(fetchData)
</script>

<template>
  <div class="cms-page">
    <div class="cms-page-header">
      <h2>页面管理</h2>
      <el-button type="primary" @click="router.push('/pages/create')">
        <el-icon class="mr-1"><Plus /></el-icon> 新建页面
      </el-button>
    </div>

    <div class="cms-table-card">
      <div class="cms-filter-bar">
        <el-select v-model="query.status" placeholder="状态筛选" clearable style="width:140px" @change="handleFilter">
          <el-option label="全部状态" value="" />
          <el-option label="草稿" value="draft" />
          <el-option label="已发布" value="published" />
        </el-select>
      </div>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="slug" label="Slug" width="160" show-overflow-tooltip />
        <el-table-column prop="template" label="模板" width="110" />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="(statusMap[row.status]?.type as any) || 'info'" size="small">
              {{ statusMap[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="70" align="center" />
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="router.push(`/pages/${row.id}/edit`)">编辑</el-button>
            <el-button text :type="row.status === 'published' ? 'warning' : 'success'" size="small" @click="handleTogglePublish(row)">
              {{ row.status === 'published' ? '取消发布' : '发布' }}
            </el-button>
            <el-button text type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="flex justify-end mt-4">
        <el-pagination
          v-model:current-page="query.page"
          :page-size="query.page_size"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="(p: number) => { query.page = p; fetchData() }"
        />
      </div>
    </div>
  </div>
</template>
