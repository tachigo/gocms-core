<script setup lang="ts">
/**
 * UserList - 用户管理列表
 * 由小美 (Desy) 维护表现层
 */
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getUsers, deleteUser } from '@/api/users'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UserInfo } from '@/types'

const router = useRouter()
const loading = ref(false)
const tableData = ref<UserInfo[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 20, status: '' as string, keyword: '' })

const statusOptions = [
  { value: '', label: '全部状态' },
  { value: 'active', label: '正常' },
  { value: 'disabled', label: '已禁用' },
]

const statusMap: Record<string, { label: string; type: string }> = {
  active: { label: '正常', type: 'success' },
  disabled: { label: '已禁用', type: 'danger' },
}

async function fetchData() {
  loading.value = true
  try {
    const params: any = { page: query.page, page_size: query.page_size }
    if (query.status) params.status = query.status
    if (query.keyword) params.keyword = query.keyword
    const res = await getUsers(params)
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

function handleSearch() {
  query.page = 1
  fetchData()
}

function handlePageChange(page: number) {
  query.page = page
  fetchData()
}

async function handleDelete(row: UserInfo) {
  await ElMessageBox.confirm(`确定删除用户「${row.username}」？此操作不可恢复。`, '提示', { type: 'warning' })
  await deleteUser(row.id)
  ElMessage.success('删除成功')
  fetchData()
}

onMounted(fetchData)
</script>

<template>
  <div class="cms-page">
    <div class="cms-page-header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="router.push('/users/create')">
        <el-icon class="mr-1"><Plus /></el-icon> 新建用户
      </el-button>
    </div>

    <div class="cms-table-card">
      <!-- 筛选栏 -->
      <div class="cms-filter-bar">
        <el-input
          v-model="query.keyword"
          placeholder="搜索用户名/邮箱"
          clearable
          style="width: 220px"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="query.status" placeholder="状态筛选" clearable style="width: 140px" @change="handleFilter">
          <el-option v-for="s in statusOptions" :key="s.value" :label="s.label" :value="s.value" />
        </el-select>
      </div>

      <!-- 表格 -->
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="用户" min-width="200">
          <template #default="{ row }">
            <div class="flex items-center gap-3">
              <el-avatar :size="32" :src="row.avatar || undefined">
                {{ row.nickname?.[0] || row.username?.[0] || 'U' }}
              </el-avatar>
              <div>
                <div class="font-medium text-sm">{{ row.nickname || row.username }}</div>
                <div class="text-xs text-gray-400">{{ row.username }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="(statusMap[row.status]?.type as any) || 'info'" size="small">
              {{ statusMap[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="170">
          <template #default="{ row }">
            {{ row.created_at?.slice(0, 16).replace('T', ' ') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="router.push(`/users/${row.id}/edit`)">编辑</el-button>
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
