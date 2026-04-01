<script setup lang="ts">
/**
 * ArticleEdit - 文章创建/编辑
 * 由小美 (Desy) 维护表现层
 */
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getArticle, createArticle, updateArticle } from '@/api/articles'
import { getTaxonomies, getTerms } from '@/api/taxonomy'
import { ElMessage, type FormInstance } from 'element-plus'
import type { TaxonomyTerm } from '@/types'

const router = useRouter()
const route = useRoute()

const formRef = ref<FormInstance>()
const loading = ref(false)
const saving = ref(false)
const articleId = computed(() => Number(route.params.id) || 0)
const isEdit = computed(() => !!articleId.value)

const form = reactive({
  title: '',
  slug: '',
  summary: '',
  body: '',
  status: 'draft' as 'draft' | 'published' | 'archived',
  is_top: false,
  cover_image: null as number | null,
  seo_title: '',
  seo_desc: '',
  category_ids: [] as number[],
  tag_ids: [] as number[],
})

const rules = {
  title: [{ required: true, message: '请输入文章标题', trigger: 'blur' }],
  slug: [
    { required: true, message: '请输入 URL 别名', trigger: 'blur' },
    { pattern: /^[a-z0-9-]+$/, message: '仅支持小写字母、数字和连字符', trigger: 'blur' },
  ],
  body: [{ required: true, message: '请输入文章内容', trigger: 'blur' }],
}

// 分类/标签选项
const categories = ref<TaxonomyTerm[]>([])
const tags = ref<TaxonomyTerm[]>([])

// 自动生成 slug
function generateSlug() {
  if (!form.slug && form.title) {
    form.slug = form.title
      .toLowerCase()
      .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-')
      .replace(/^-|-$/g, '')
      .slice(0, 100)
  }
}

async function loadTaxonomies() {
  try {
    const taxRes = await getTaxonomies()
    const vocabs = taxRes.data.list || []
    for (const v of vocabs) {
      const termsRes = await getTerms(v.id)
      if (v.hierarchical) {
        categories.value = termsRes.data.list || []
      } else {
        tags.value = termsRes.data.list || []
      }
    }
  } catch { /* 分类加载失败不阻塞 */ }
}

async function loadArticle() {
  if (!isEdit.value) return
  loading.value = true
  try {
    const res = await getArticle(articleId.value)
    const data = res.data
    Object.assign(form, {
      title: data.title,
      slug: data.slug,
      summary: data.summary || '',
      body: data.body,
      status: data.status,
      is_top: data.is_top,
      cover_image: data.cover_image || null,
      seo_title: data.seo_title || '',
      seo_desc: data.seo_desc || '',
      category_ids: data.categories?.map((c) => c.id) || [],
      tag_ids: data.tags?.map((t) => t.id) || [],
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
      await updateArticle({ id: articleId.value, ...form })
      ElMessage.success('更新成功')
    } else {
      const res = await createArticle(form)
      ElMessage.success('创建成功')
      router.replace(`/articles/${res.data.id}/edit`)
    }
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadTaxonomies()
  loadArticle()
})
</script>

<template>
  <div class="cms-page" v-loading="loading">
    <div class="cms-page-header">
      <h2>{{ isEdit ? '编辑文章' : '创建文章' }}</h2>
      <div class="flex gap-2">
        <el-button @click="router.back()">返回</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">
          {{ saving ? '保存中...' : '保存' }}
        </el-button>
      </div>
    </div>

    <div class="flex gap-5 items-start">
      <!-- 左侧：主内容 -->
      <div class="cms-form-card flex-1">
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
          <el-form-item label="标题" prop="title">
            <el-input v-model="form.title" size="large" placeholder="文章标题" @blur="generateSlug" />
          </el-form-item>

          <el-form-item label="URL 别名" prop="slug">
            <el-input v-model="form.slug" placeholder="url-slug" />
          </el-form-item>

          <el-form-item label="摘要">
            <el-input v-model="form.summary" type="textarea" :rows="3" placeholder="文章摘要（可选）" />
          </el-form-item>

          <el-form-item label="正文" prop="body">
            <el-input
              v-model="form.body"
              type="textarea"
              :rows="16"
              placeholder="文章正文（支持 HTML）"
            />
          </el-form-item>

          <!-- SEO 设置 -->
          <el-collapse class="mt-4">
            <el-collapse-item title="SEO 设置" name="seo">
              <el-form-item label="SEO 标题">
                <el-input v-model="form.seo_title" placeholder="自定义 SEO 标题" />
              </el-form-item>
              <el-form-item label="SEO 描述">
                <el-input v-model="form.seo_desc" type="textarea" :rows="2" placeholder="自定义 SEO 描述" />
              </el-form-item>
            </el-collapse-item>
          </el-collapse>
        </el-form>
      </div>

      <!-- 右侧：设置面板 -->
      <div class="w-[280px] shrink-0 space-y-4">
        <!-- 发布设置 -->
        <div class="cms-card">
          <h4 class="text-sm font-semibold mb-3 text-gray-600">发布设置</h4>
          <el-form label-position="top">
            <el-form-item label="状态">
              <el-select v-model="form.status" class="w-full">
                <el-option label="草稿" value="draft" />
                <el-option label="已发布" value="published" />
                <el-option label="已归档" value="archived" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-checkbox v-model="form.is_top">置顶文章</el-checkbox>
            </el-form-item>
          </el-form>
        </div>

        <!-- 分类 -->
        <div class="cms-card" v-if="categories.length">
          <h4 class="text-sm font-semibold mb-3 text-gray-600">分类</h4>
          <el-checkbox-group v-model="form.category_ids">
            <el-checkbox v-for="cat in categories" :key="cat.id" :value="cat.id" class="!block mb-1">
              {{ cat.name }}
            </el-checkbox>
          </el-checkbox-group>
        </div>

        <!-- 标签 -->
        <div class="cms-card" v-if="tags.length">
          <h4 class="text-sm font-semibold mb-3 text-gray-600">标签</h4>
          <el-select v-model="form.tag_ids" multiple filterable class="w-full" placeholder="选择标签">
            <el-option v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.id" />
          </el-select>
        </div>
      </div>
    </div>
  </div>
</template>
