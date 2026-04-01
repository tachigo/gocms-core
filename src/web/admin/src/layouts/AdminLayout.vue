<script setup lang="ts">
/**
 * AdminLayout - 后台管理布局
 * 左侧导航 + 顶栏 + 主内容区
 * 由小美 (Desy) 维护表现层
 */
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const app = useAppStore()

// 侧边栏菜单项（从路由 meta 读取，过滤 hidden）
const menuItems = computed(() => {
  const layoutRoute = router.options.routes.find((r) => r.path === '/')
  return (layoutRoute?.children || []).filter((r) => !r.meta?.hidden)
})

const activeMenu = computed(() => {
  // 子页面高亮父级菜单
  const path = route.path
  if (path.startsWith('/articles')) return '/articles'
  if (path.startsWith('/pages')) return '/pages'
  if (path.startsWith('/users')) return '/users'
  if (path.startsWith('/roles')) return '/roles'
  return path
})

function handleMenuSelect(path: string) {
  router.push(path)
}

async function handleLogout() {
  await ElMessageBox.confirm('确定退出登录？', '提示', { type: 'warning' })
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="admin-layout flex h-screen overflow-hidden">
    <!-- 侧边栏 -->
    <aside
      class="admin-sidebar flex flex-col shrink-0 transition-all duration-300"
      :style="{ width: app.sidebarCollapsed ? '64px' : '220px' }"
    >
      <!-- Logo -->
      <div class="sidebar-logo flex items-center h-14 px-4 border-b border-gray-700">
        <span class="text-xl">🏠</span>
        <span v-if="!app.sidebarCollapsed" class="ml-2 text-white font-semibold text-base whitespace-nowrap">
          GoCMS
        </span>
      </div>

      <!-- 导航菜单 -->
      <el-menu
        :default-active="activeMenu"
        :collapse="app.sidebarCollapsed"
        :collapse-transition="false"
        background-color="#1d1e1f"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        class="sidebar-menu flex-1 border-none"
        @select="handleMenuSelect"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="'/' + item.path"
          :index="'/' + item.path"
        >
          <el-icon><component :is="item.meta?.icon || 'Document'" /></el-icon>
          <template #title>{{ item.meta?.title }}</template>
        </el-menu-item>
      </el-menu>
    </aside>

    <!-- 右侧区域 -->
    <div class="flex flex-col flex-1 overflow-hidden">
      <!-- 顶栏 -->
      <header class="admin-header flex items-center justify-between h-14 px-4 bg-white border-b shrink-0 shadow-card">
        <div class="flex items-center gap-3">
          <!-- 折叠按钮 -->
          <el-icon
            class="cursor-pointer text-lg text-gray-500 hover:text-primary transition-colors"
            @click="app.toggleSidebar"
          >
            <component :is="app.sidebarCollapsed ? 'Expand' : 'Fold'" />
          </el-icon>

          <!-- 面包屑 -->
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.meta.title">
              {{ route.meta.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <!-- 用户信息 -->
        <el-dropdown trigger="click">
          <div class="flex items-center gap-2 cursor-pointer text-gray-600 hover:text-primary transition-colors">
            <el-avatar :size="28" :src="auth.user?.avatar || undefined">
              {{ auth.user?.nickname?.[0] || auth.user?.username?.[0] || 'A' }}
            </el-avatar>
            <span class="text-sm">{{ auth.user?.nickname || auth.user?.username || '管理员' }}</span>
            <el-icon><ArrowDown /></el-icon>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="router.push('/settings')">
                <el-icon><Setting /></el-icon> 站点设置
              </el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">
                <el-icon><SwitchButton /></el-icon> 退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </header>

      <!-- 主内容区 -->
      <main class="flex-1 overflow-y-auto bg-[var(--cms-bg-page)] p-5">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<style scoped lang="scss">
.admin-sidebar {
  background: var(--cms-bg-sidebar);
  z-index: 10;
}

.sidebar-menu {
  :deep(.el-menu-item) {
    height: 48px;
    line-height: 48px;
    &.is-active {
      background-color: rgba(64, 158, 255, 0.15) !important;
    }
    &:hover {
      background-color: rgba(255, 255, 255, 0.05) !important;
    }
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
