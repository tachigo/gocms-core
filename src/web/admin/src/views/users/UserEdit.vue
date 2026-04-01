<script setup lang="ts">
/**
 * UserEdit - 用户创建/编辑
 * 由小美 (Desy) 维护表现层
 */
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getUser, createUser, updateUser } from '@/api/users'
import { getRoles, getUserRoles, assignRoles } from '@/api/roles'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import type { RoleSimple } from '@/types'

const router = useRouter()
const route = useRoute()

const formRef = ref<FormInstance>()
const loading = ref(false)
const saving = ref(false)
const userId = computed(() => Number(route.params.id) || 0)
const isEdit = computed(() => !!userId.value)

const form = reactive({
  username: '',
  email: '',
  password: '',
  nickname: '',
  status: 'active' as 'active' | 'disabled',
})

const roleIds = ref<number[]>([])
const allRoles = ref<RoleSimple[]>([])

const rules = reactive<FormRules>({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 30, message: '用户名长度为 3-30 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '仅支持字母、数字和下划线', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效邮箱地址', trigger: 'blur' },
  ],
  password: isEdit.value
    ? []
    : [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码至少 6 个字符', trigger: 'blur' },
      ],
})

async function loadRoles() {
  try {
    const res = await getRoles()
    allRoles.value = (res.data.list || []).map((r) => ({
      id: r.id,
      name: r.name,
      label: r.label,
    }))
  } catch { /* 角色列表加载失败不阻塞 */ }
}

async function loadUserRoles() {
  if (!isEdit.value) return
  try {
    const res = await getUserRoles(userId.value)
    roleIds.value = (res.data.roles || []).map(r => r.id)
  } catch { /* 用户角色加载失败不阻塞 */ }
}

async function loadUser() {
  if (!isEdit.value) return
  loading.value = true
  try {
    const res = await getUser(userId.value)
    const data = res.data
    Object.assign(form, {
      username: data.username,
      email: data.email,
      password: '',
      nickname: data.nickname || '',
      status: data.status,
    })
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  if (!formRef.value) return
  await formRef.value.validate()
  saving.value = true
  try {
    if (isEdit.value) {
      const updateData: any = {
        id: userId.value,
        username: form.username,
        email: form.email,
        nickname: form.nickname,
        status: form.status,
      }
      await updateUser(updateData)
      // 同步角色
      await assignRoles({ user_id: userId.value, role_ids: roleIds.value })
      ElMessage.success('更新成功')
    } else {
      const res = await createUser({
        username: form.username,
        email: form.email,
        password: form.password,
        nickname: form.nickname,
      })
      // 创建后分配角色
      if (roleIds.value.length) {
        await assignRoles({ user_id: res.data.id, role_ids: roleIds.value })
      }
      ElMessage.success('创建成功')
      router.replace(`/users/${res.data.id}/edit`)
    }
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadRoles()
  loadUser()
  loadUserRoles()
})
</script>

<template>
  <div class="cms-page" v-loading="loading">
    <div class="cms-page-header">
      <h2>{{ isEdit ? '编辑用户' : '创建用户' }}</h2>
      <div class="flex gap-2">
        <el-button @click="router.back()">返回</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          {{ saving ? '保存中...' : '保存' }}
        </el-button>
      </div>
    </div>

    <div class="flex gap-5 items-start">
      <!-- 左侧：主表单 -->
      <div class="cms-form-card flex-1">
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" placeholder="用户名" :disabled="isEdit" />
          </el-form-item>

          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" placeholder="user@example.com" />
          </el-form-item>

          <el-form-item :label="isEdit ? '修改密码' : '密码'" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              show-password
              :placeholder="isEdit ? '留空则不修改密码' : '请输入密码'"
            />
          </el-form-item>

          <el-form-item label="昵称">
            <el-input v-model="form.nickname" placeholder="显示名称（可选）" />
          </el-form-item>
        </el-form>
      </div>

      <!-- 右侧：设置面板 -->
      <div class="w-[280px] shrink-0 space-y-4">
        <!-- 账号状态 -->
        <div class="cms-card">
          <h4 class="text-sm font-semibold mb-3 text-gray-600">账号设置</h4>
          <el-form label-position="top">
            <el-form-item label="状态">
              <el-select v-model="form.status" class="w-full">
                <el-option label="正常" value="active" />
                <el-option label="已禁用" value="disabled" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <!-- 角色分配 -->
        <div class="cms-card" v-if="allRoles.length">
          <h4 class="text-sm font-semibold mb-3 text-gray-600">角色分配</h4>
          <el-checkbox-group v-model="roleIds">
            <el-checkbox
              v-for="role in allRoles"
              :key="role.id"
              :value="role.id"
              class="!block mb-2"
            >
              {{ role.label || role.name }}
            </el-checkbox>
          </el-checkbox-group>
        </div>
      </div>
    </div>
  </div>
</template>
