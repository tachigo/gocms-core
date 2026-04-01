<script setup lang="ts">
/**
 * SiteSettings - 站点设置表单
 * 由小美 (Desy) 维护表现层
 */
import { ref, reactive, onMounted } from 'vue'
import { getAdminSettings, updateSettings } from '@/api/settings'
import { ElMessage } from 'element-plus'
import type { SiteSettings } from '@/types'

const loading = ref(false)
const saving = ref(false)

const form = reactive<SiteSettings>({
  name: '',
  description: '',
  url: '',
  logo: '',
  favicon: '',
  language: 'zh-CN',
  timezone: 'Asia/Shanghai',
  seo: {
    title_suffix: '',
    description: '',
    keywords: '',
  },
  pagination: {
    default_page_size: 20,
    max_page_size: 100,
  },
  image_styles: {
    thumbnail: { width: 150, height: 150, mode: 'crop', quality: 80 },
    medium: { width: 300, height: 300, mode: 'resize', quality: 85 },
    large: { width: 800, height: 800, mode: 'resize', quality: 90 },
  },
  contact: {
    email: '',
    phone: '',
  },
})

async function loadSettings() {
  loading.value = true
  try {
    const res = await getAdminSettings()
    Object.assign(form, res.data)
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    // TODO: 等待后端实现 settings 更新接口
    // await updateSettings(form)
    ElMessage.info('保存接口待后端实现')
  } finally {
    saving.value = false
  }
}

onMounted(loadSettings)
</script>

<template>
  <div class="cms-page" v-loading="loading">
    <div class="cms-page-header">
      <h2>站点设置</h2>
      <el-button type="primary" :loading="saving" @click="handleSave">保存设置</el-button>
    </div>

    <div class="cms-form-card" style="max-width: 100%">
      <el-form :model="form" label-position="top">
        <el-row :gutter="30">
          <el-col :span="12">
            <h3 class="text-base font-semibold mb-4">基本信息</h3>
            <el-form-item label="站点名称">
              <el-input v-model="form.name" placeholder="GoCMS" />
            </el-form-item>
            <el-form-item label="站点描述">
              <el-input v-model="form.description" type="textarea" :rows="2" placeholder="站点简介" />
            </el-form-item>
            <el-form-item label="站点 URL">
              <el-input v-model="form.url" placeholder="https://example.com" />
            </el-form-item>
            <el-form-item label="Logo URL">
              <el-input v-model="form.logo" placeholder="https://..." />
            </el-form-item>
            <el-form-item label="Favicon URL">
              <el-input v-model="form.favicon" placeholder="https://..." />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <h3 class="text-base font-semibold mb-4">SEO 设置</h3>
            <el-form-item label="标题后缀">
              <el-input v-model="form.seo.title_suffix" placeholder=" - GoCMS" />
            </el-form-item>
            <el-form-item label="默认描述">
              <el-input v-model="form.seo.description" type="textarea" :rows="2" placeholder="默认 SEO 描述" />
            </el-form-item>
            <el-form-item label="关键词">
              <el-input v-model="form.seo.keywords" placeholder="用逗号分隔" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider />

        <el-row :gutter="30">
          <el-col :span="12">
            <h3 class="text-base font-semibold mb-4">系统设置</h3>
            <el-form-item label="语言">
              <el-select v-model="form.language" class="w-full">
                <el-option label="简体中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
              </el-select>
            </el-form-item>
            <el-form-item label="时区">
              <el-select v-model="form.timezone" class="w-full">
                <el-option label="Asia/Shanghai" value="Asia/Shanghai" />
                <el-option label="UTC" value="UTC" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <h3 class="text-base font-semibold mb-4">联系方式</h3>
            <el-form-item label="邮箱">
              <el-input v-model="form.contact.email" placeholder="contact@example.com" />
            </el-form-item>
            <el-form-item label="电话">
              <el-input v-model="form.contact.phone" placeholder="+86 xxx xxxx xxxx" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </div>
  </div>
</template>
