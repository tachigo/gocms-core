<script setup lang="ts">
/**
 * Dashboard - 概览仪表盘
 * 由小美 (Desy) 维护表现层
 */
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getArticles } from '@/api/articles'
import { getPages } from '@/api/pages'
import { getUsers } from '@/api/users'
import { getMediaList } from '@/api/media'
import type { Article } from '@/types'

const router = useRouter()

const stats = ref({
  articles: 0,
  pages: 0,
  users: 0,
  media: 0,
})
const recentArticles = ref<Article[]>([])
const loading = ref(true)

const statCards = [
  { key: 'articles', label: '文章', icon: 'Document', color: '#409eff', route: '/articles' },
  { key: 'pages', label: '页面', icon: 'Notebook', color: '#67c23a', route: '/pages' },
  { key: 'users', label: '用户', icon: 'User', color: '#e6a23c', route: '/users' },
  { key: 'media', label: '媒体', icon: 'Picture', color: '#f56c6c', route: '/media' },
]

onMounted(async () => {
  try {
    const [articlesRes, pagesRes, usersRes, mediaRes] = await Promise.allSettled([
      getArticles({ page: 1, page_size: 5 }),
      getPages({ page: 1, page_size: 1 }),
      getUsers({ page: 1, page_size: 1 }),
      getMediaList({ page: 1, page_size: 1 }),
    ])

    if (articlesRes.status === 'fulfilled') {
      stats.value.articles = articlesRes.value.data.total
      recentArticles.value = articlesRes.value.data.list
    }
    if (pagesRes.status === 'fulfilled') stats.value.pages = pagesRes.value.data.total
    if (usersRes.status === 'fulfilled') stats.value.users = usersRes.value.data.total
    if (mediaRes.status === 'fulfilled') stats.value.media = mediaRes.value.data.total
  } finally {
    loading.value = false
  }
})

const statusMap: Record<string, { label: string; type: string }> = {
  draft: { label: '草稿', type: 'info' },
  published: { label: '已发布', type: 'success' },
  archived: { label: '已归档', type: 'warning' },
}
</script>

<template>
  <div class="cms-page">
    <div class="cms-page-header">
      <h2>仪表盘</h2>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
      <div
        v-for="card in statCards"
        :key="card.key"
        class="cms-card flex items-center gap-4 cursor-pointer hover:shadow-dropdown transition-shadow"
        @click="router.push(card.route)"
      >
        <div
          class="w-12 h-12 rounded-lg flex items-center justify-center text-white text-xl"
          :style="{ backgroundColor: card.color }"
        >
          <el-icon :size="24"><component :is="card.icon" /></el-icon>
        </div>
        <div>
          <div class="text-2xl font-bold text-gray-800">
            <el-skeleton v-if="loading" :rows="0" animated style="width:40px;height:28px" />
            <span v-else>{{ stats[card.key as keyof typeof stats] }}</span>
          </div>
          <div class="text-sm text-gray-400">{{ card.label }}</div>
        </div>
      </div>
    </div>

    <!-- 最近文章 -->
    <div class="cms-table-card">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-base font-semibold m-0">最近文章</h3>
        <el-button text type="primary" @click="router.push('/articles')">查看全部</el-button>
      </div>

      <el-table :data="recentArticles" v-loading="loading" stripe>
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="(statusMap[row.status]?.type as any) || 'info'" size="small">
              {{ statusMap[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ row.created_at?.slice(0, 16).replace('T', ' ') }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button text type="primary" size="small" @click="router.push(`/articles/${row.id}/edit`)">
              编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 快捷操作 -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
      <el-button class="h-16" @click="router.push('/articles/create')">
        <el-icon class="mr-1"><Edit /></el-icon> 写文章
      </el-button>
      <el-button class="h-16" @click="router.push('/pages/create')">
        <el-icon class="mr-1"><DocumentAdd /></el-icon> 创建页面
      </el-button>
      <el-button class="h-16" @click="router.push('/media')">
        <el-icon class="mr-1"><Upload /></el-icon> 上传媒体
      </el-button>
      <el-button class="h-16" @click="router.push('/settings')">
        <el-icon class="mr-1"><Setting /></el-icon> 站点设置
      </el-button>
    </div>
  </div>
</template>
