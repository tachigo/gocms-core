<script setup lang="ts">
/**
 * PageEdit - 页面创建/编辑
 * 由小美 (Desy) 维护表现层
 */
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getPage, createPage, updatePage } from '@/api/pages'
import { ElMessage, type FormInstance } from 'element-plus'

const router = useRouter()
const route = useRoute()

const formRef = ref<FormInstance>()
const loading = ref(false)
const saving = ref(false)
const pageId = computed(() => Number(route.params.id) || 0)
const isEdit = computed(() => !!pageId.value)

const form = reactive({
  title: '',
  slug: '',
  body: '',
  excerpt: '',
  featured_image: '',
  template: 'default',
  sort_order: 0,
  page_meta: {
    meta_title: '',
    meta_description: '',
    meta_keywords: '',
    og_image: '',
  },
})

const rules = {
  title: [{ required: true, message: '请输入页面标题', trigger: 'blur' }],
  slug: [
    { required: true, message: '请输入 URL 别名', trigger: 'blur' },
    { pattern: /^[a-z0-9-]+$/, message: '仅支持小写字母、数字和连字符', trigger: 'blur' },
  ],
}

const templateOptions = [
  { value: 'default', label: '默认模板' },
  { value: 'full_width', label: '全宽模板' },
  { value: 'sidebar', label: '带侧边栏' },
]

function generateSlug() {
  if (!form.slug && form.title) {
    form.slug = form.title
      .toLowerCase()
      .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-')
      .replace(/^-|-$/g, '')
      .slice(0, 100)
  }
}

async function loadPage() {
  if (!isEdit.value) return
  loading.value = true
  try {
    const res = await getPage(pageId.value)
    const d = res.data
    Object.assign(form, {
      title: d.title,
      slug: d.slug,
      body: d.body || '',
      excerpt: d.excerpt || '',
      featured_image: d.featured_image || '',
      template: d.template || 'default',
      sort_order: d.sort_order || 0,
      page_meta: {
        meta_title: d.page_meta?.meta_title || '',
        meta_description: d.page_meta?.meta_description || '',
        meta_keywords: d.page_meta?.meta_keywords || '',
        og_image: d.page_meta?.og_image || '',
      },
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
      await updatePage({ id: pageId.value, ...form })
      ElMessage.success('更新成功')
    } else {
      const res = await createPage(form)
      ElMessage.success('创建成功')
      router.replace(`/pages/${res.data.id}/edit`)
    }
  } finally {
    saving.value = false
  }
}

onMounted(loadPage)
</script>

<template>
  <div class="cms-page" v-loading="loading">
    <div class="cms-page-header">
      <h2>{{ isEdit ? '编辑页面' : '创建页面' }}</h2>
      <div class="flex gap-2">
        <el-button @click="router.back()">返回</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </div>
    </div>

    <div class="flex gap-5 items-start">
      <!-- 左侧：主内容 -->
      <div class="cms-form-card flex-1">
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
          <el-form-item label="标题" prop="title">
            <el-input v-model="form.title" size="large" placeholder="页面标题" @blur="generateSlug" />
          </el-form-item>
          <el-form-item label="URL 别名" prop="slug">
            <el-input v-model="form.slug" placeholder="url-slug" />
          </el-form-item>
          <el-form-item label="摘要">
            <el-input v-model="form.excerpt" type="textarea" :rows="2" placeholder="页面摘要（可选）" />
          </el-form-item>
          <el-form-item label="正文">
            <el-input v-model="form.body" type="textarea" :rows="16" placeholder="页面内容（支持 HTML）" />
          </el-form-item>

          <el-collapse class="mt-4">
            <el-collapse-item title="SEO 设置" name="seo">
              <el-form-item label="SEO 标题">
                <el-input v-model="form.page_meta.meta_title" placeholder="自定义 SEO 标题" />
              </el-form-item>
              <el-form-item label="SEO 描述">
                <el-input v-model="form.page_meta.meta_description" type="textarea" :rows="2" placeholder="自定义 SEO 描述" />
              </el-form-item>
              <el-form-item label="SEO 关键词">
                <el-input v-model="form.page_meta.meta_keywords" placeholder="关键词，用逗号分隔" />
              </el-form-item>
            </el-collapse-item>
          </el-collapse>
        </el-form>
      </div>

      <!-- 右侧：设置面板 -->
      <div class="w-[280px] shrink-0 space-y-4">
        <div class="cms-card">
          <h4 class="text-sm font-semibold mb-3 text-gray-600">页面设置</h4>
          <el-form label-position="top">
            <el-form-item label="模板">
              <el-select v-model="form.template" class="w-full">
                <el-option v-for="t in templateOptions" :key="t.value" :label="t.label" :value="t.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="排序权重">
              <el-input-number v-model="form.sort_order" :min="0" controls-position="right" class="w-full" />
            </el-form-item>
            <el-form-item label="特色图片 URL">
              <el-input v-model="form.featured_image" placeholder="图片 URL" />
            </el-form-item>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>
