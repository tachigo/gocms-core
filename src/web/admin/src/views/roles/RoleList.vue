<script setup lang="ts">
/**
 * RoleList - 角色管理列表
 * 由小美 (Desy) 维护表现层
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getRoles, deleteRole } from '@/api/roles'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Role } from '@/types'

const router = useRouter()
const loading = ref(false)
const tableData = ref<Role[]>([])

async function fetchData() {
  loading.value = true
  try {
    const res = await getRoles()
    tableData.value = res.data.list || []
  } finally {
    loading.value = false
  }
}

async function handleDelete(row: Role) {
  if (row.is_system) {
    ElMessage.warning('系统角色不可删除')
    return
  }
  await ElMessageBox.confirm(`确定删除角色「${row.label}」？关联用户将失去该角色权限。`, '提示', { type: 'warning' })
  await deleteRole(row.id)
  ElMessage.success('删除成功')
  fetchData()
}

onMounted(fetchData)
</script>

<template>
  <div class="cms-page">
    <div class="cms-page-header">
      <h2>角色权限</h2>
      <el-button type="primary" @click="router.push('/roles/create')">
        <el-icon class="mr-1"><Plus /></el-icon> 新建角色
      </el-button>
    </div>

    <div class="cms-table-card">
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="label" label="角色名称" min-width="150">
          <template #default="{ row }">
            <div class="flex items-center gap-2">
              <el-tag v-if="row.is_system" type="warning" size="small" effect="plain">系统</el-tag>
              <span class="font-medium">{{ row.label }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="标识" width="150">
          <template #default="{ row }">
            <code class="text-xs bg-gray-100 px-1.5 py-0.5 rounded text-gray-600">{{ row.name }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="权限数" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.permissions?.length || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">
            {{ row.created_at?.slice(0, 16).replace('T', ' ') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="router.push(`/roles/${row.id}/edit`)">
              {{ row.is_system ? '查看' : '编辑' }}
            </el-button>
            <el-button
              v-if="!row.is_system"
              text
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>
