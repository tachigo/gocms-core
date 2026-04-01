<script setup lang="ts">
/**
 * RoleEdit - 角色创建/编辑（含权限矩阵）
 * 由小美 (Desy) 维护表现层
 */
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getRole, createRole, updateRole, getAvailablePermissions } from '@/api/roles'
import { ElMessage, type FormInstance } from 'element-plus'
import type { PermissionGroup, PermissionInput } from '@/types'

const router = useRouter()
const route = useRoute()

const formRef = ref<FormInstance>()
const loading = ref(false)
const saving = ref(false)
const roleId = computed(() => Number(route.params.id) || 0)
const isEdit = computed(() => !!roleId.value)
const isSystem = ref(false)

const form = reactive({
  name: '',
  label: '',
  description: '',
})

const rules = {
  name: [
    { required: true, message: '请输入角色标识', trigger: 'blur' },
    { pattern: /^[a-z0-9_]+$/, message: '仅支持小写字母、数字和下划线', trigger: 'blur' },
  ],
  label: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
}

// 权限矩阵数据
const availablePermissions = ref<PermissionGroup[]>([])
const selectedPermissions = ref<Map<string, Set<string>>>(new Map())

const actions = ['create', 'read', 'update', 'delete', 'manage']

function permKey(module: string, action: string) {
  return `${module}.${action}`
}

function isChecked(module: string, action: string): boolean {
  return selectedPermissions.value.get(module)?.has(action) || false
}

function togglePermission(module: string, action: string) {
  if (isSystem.value) return
  const modulePerms = selectedPermissions.value.get(module) || new Set()
  if (modulePerms.has(action)) {
    modulePerms.delete(action)
  } else {
    modulePerms.add(action)
  }
  selectedPermissions.value.set(module, modulePerms)
}

function isActionAvailable(module: string, action: string): boolean {
  const group = availablePermissions.value.find(g => g.module === module)
  return !!group?.permissions.find(p => p.action === action)
}

function toggleAllModule(module: string) {
  if (isSystem.value) return
  const group = availablePermissions.value.find(g => g.module === module)
  if (!group) return
  const modulePerms = selectedPermissions.value.get(module) || new Set()
  const allChecked = group.permissions.every(p => modulePerms.has(p.action))
  if (allChecked) {
    selectedPermissions.value.set(module, new Set())
  } else {
    selectedPermissions.value.set(module, new Set(group.permissions.map(p => p.action)))
  }
}

function isModuleAllChecked(module: string): boolean {
  const group = availablePermissions.value.find(g => g.module === module)
  if (!group) return false
  const modulePerms = selectedPermissions.value.get(module) || new Set()
  return group.permissions.every(p => modulePerms.has(p.action))
}

function buildPermissionInputs(): PermissionInput[] {
  const result: PermissionInput[] = []
  selectedPermissions.value.forEach((actions, module) => {
    actions.forEach(action => {
      result.push({ module, action, scope: 'all' })
    })
  })
  return result
}

async function loadAvailablePermissions() {
  const res = await getAvailablePermissions()
  availablePermissions.value = res.data.groups || []
}

async function loadRole() {
  if (!isEdit.value) return
  loading.value = true
  try {
    const res = await getRole(roleId.value)
    const data = res.data
    form.name = data.name
    form.label = data.label
    form.description = data.description || ''
    isSystem.value = data.is_system

    const permMap = new Map<string, Set<string>>()
    for (const p of data.permissions || []) {
      const set = permMap.get(p.module) || new Set()
      set.add(p.action)
      permMap.set(p.module, set)
    }
    selectedPermissions.value = permMap
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (!formRef.value) return
  await formRef.value.validate()
  saving.value = true
  try {
    const permissions = buildPermissionInputs()
    if (isEdit.value) {
      await updateRole({ id: roleId.value, label: form.label, description: form.description, permissions })
      ElMessage.success('更新成功')
    } else {
      await createRole({ ...form, permissions })
      ElMessage.success('创建成功')
      router.back()
    }
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await loadAvailablePermissions()
  await loadRole()
})
</script>

<template>
  <div class="cms-page" v-loading="loading">
    <div class="cms-page-header">
      <h2>{{ isEdit ? (isSystem ? '查看角色' : '编辑角色') : '创建角色' }}</h2>
      <div class="flex gap-2">
        <el-button @click="router.back()">返回</el-button>
        <el-button v-if="!isSystem" type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </div>
    </div>

    <!-- 基本信息 -->
    <div class="cms-form-card mb-5" style="max-width:100%">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="max-w-lg">
        <el-form-item label="角色标识" prop="name">
          <el-input v-model="form.name" placeholder="如 editor、custom_reviewer" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="角色名称" prop="label">
          <el-input v-model="form.label" placeholder="如 编辑、自定义审核员" :disabled="isSystem" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="角色描述（可选）" :disabled="isSystem" />
        </el-form-item>
      </el-form>
    </div>

    <!-- 权限矩阵 -->
    <div class="cms-table-card">
      <h3 class="text-base font-semibold mb-4">权限分配</h3>
      <el-table :data="availablePermissions" stripe border>
        <el-table-column label="模块" width="140" fixed>
          <template #default="{ row }">
            <el-checkbox
              :model-value="isModuleAllChecked(row.module)"
              :disabled="isSystem"
              @change="toggleAllModule(row.module)"
            >
              <span class="font-medium">{{ row.module }}</span>
            </el-checkbox>
          </template>
        </el-table-column>
        <el-table-column
          v-for="action in actions"
          :key="action"
          :label="action"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <el-checkbox
              v-if="isActionAvailable(row.module, action)"
              :model-value="isChecked(row.module, action)"
              :disabled="isSystem"
              @change="togglePermission(row.module, action)"
            />
            <span v-else class="text-gray-300">—</span>
          </template>
        </el-table-column>
      </el-table>
      <p v-if="isSystem" class="text-sm text-gray-400 mt-3">
        ⚠️ 系统内置角色的权限不可修改
      </p>
    </div>
  </div>
</template>
