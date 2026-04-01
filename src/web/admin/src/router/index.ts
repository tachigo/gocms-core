import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/AdminLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: { title: '仪表盘', icon: 'Odometer' },
      },
      // 文章管理
      {
        path: 'articles',
        name: 'ArticleList',
        component: () => import('@/views/articles/ArticleList.vue'),
        meta: { title: '文章管理', icon: 'Document' },
      },
      {
        path: 'articles/create',
        name: 'ArticleCreate',
        component: () => import('@/views/articles/ArticleEdit.vue'),
        meta: { title: '创建文章', hidden: true },
      },
      {
        path: 'articles/:id/edit',
        name: 'ArticleEdit',
        component: () => import('@/views/articles/ArticleEdit.vue'),
        meta: { title: '编辑文章', hidden: true },
      },
      // 页面管理
      {
        path: 'pages',
        name: 'PageList',
        component: () => import('@/views/pages/PageList.vue'),
        meta: { title: '页面管理', icon: 'Notebook' },
      },
      {
        path: 'pages/create',
        name: 'PageCreate',
        component: () => import('@/views/pages/PageEdit.vue'),
        meta: { title: '创建页面', hidden: true },
      },
      {
        path: 'pages/:id/edit',
        name: 'PageEdit',
        component: () => import('@/views/pages/PageEdit.vue'),
        meta: { title: '编辑页面', hidden: true },
      },
      // 菜单管理
      {
        path: 'menus',
        name: 'Menus',
        component: () => import('@/views/menus/MenuEditor.vue'),
        meta: { title: '菜单管理', icon: 'Menu' },
      },
      // 分类管理
      {
        path: 'taxonomy',
        name: 'Taxonomy',
        component: () => import('@/views/taxonomy/TaxonomyManager.vue'),
        meta: { title: '分类管理', icon: 'Collection' },
      },
      // 媒体库
      {
        path: 'media',
        name: 'Media',
        component: () => import('@/views/media/MediaLibrary.vue'),
        meta: { title: '媒体库', icon: 'Picture' },
      },
      // 用户管理
      {
        path: 'users',
        name: 'UserList',
        component: () => import('@/views/users/UserList.vue'),
        meta: { title: '用户管理', icon: 'User' },
      },
      {
        path: 'users/create',
        name: 'UserCreate',
        component: () => import('@/views/users/UserEdit.vue'),
        meta: { title: '创建用户', hidden: true },
      },
      {
        path: 'users/:id/edit',
        name: 'UserEdit',
        component: () => import('@/views/users/UserEdit.vue'),
        meta: { title: '编辑用户', hidden: true },
      },
      // 角色权限
      {
        path: 'roles',
        name: 'RoleList',
        component: () => import('@/views/roles/RoleList.vue'),
        meta: { title: '角色权限', icon: 'Lock' },
      },
      {
        path: 'roles/create',
        name: 'RoleCreate',
        component: () => import('@/views/roles/RoleEdit.vue'),
        meta: { title: '创建角色', hidden: true },
      },
      {
        path: 'roles/:id/edit',
        name: 'RoleEdit',
        component: () => import('@/views/roles/RoleEdit.vue'),
        meta: { title: '编辑角色', hidden: true },
      },
      // 站点设置
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/SiteSettings.vue'),
        meta: { title: '站点设置', icon: 'Setting' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory('/admin/'),
  routes,
})

// 路由守卫
router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (to.meta.public) return true

  if (!auth.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  if (!auth.user) {
    await auth.fetchProfile()
  }

  return true
})

export default router
