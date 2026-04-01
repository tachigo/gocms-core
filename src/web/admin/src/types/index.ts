/**
 * GoCMS v2.0 Admin - TypeScript 类型定义
 * 基于 OpenAPI 3.0 文档自动整理
 */

/* ========== 通用响应类型 ========== */
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

export interface PageResult<T = any> {
  list: T[]
  total: number
  page: number
  page_size: number
}

export interface PageParams {
  page?: number
  page_size?: number
}

/* ========== Auth 认证 ========== */
export interface LoginParams {
  username: string
  password: string
}

export interface LoginResult {
  token: string
  user: UserInfo
}

export interface ChangePasswordParams {
  old_password: string
  new_password: string
}

export interface UserProfile {
  id: number
  username: string
  email: string
  nickname: string
  avatar: string
}

export interface UpdateProfileParams {
  nickname?: string
  avatar?: string
}

/* ========== User 用户 ========== */
export interface UserInfo {
  id: number
  username: string
  email: string
  nickname: string
  avatar: string
  status: 'active' | 'disabled'
  created_at: string
}

export interface CreateUserParams {
  username: string
  email: string
  password: string
  nickname?: string
}

export interface UpdateUserParams {
  id: number
  username?: string
  email?: string
  nickname?: string
  status?: 'active' | 'disabled'
}

/* ========== Permission 权限 ========== */
export interface Role {
  id: number
  name: string
  label: string
  description: string
  is_system: boolean
  permissions: PermissionDetail[]
  created_at: string
}

export interface RoleSimple {
  id: number
  name: string
  label: string
}

export interface PermissionDetail {
  id: number
  module: string
  action: string
  scope: string
}

export interface PermissionInput {
  module: string
  action: string
  scope?: 'own' | 'all'
}

export interface CreateRoleParams {
  name: string
  label: string
  description?: string
  permissions?: PermissionInput[]
}

export interface UpdateRoleParams {
  id: number
  label?: string
  description?: string
  permissions?: PermissionInput[]
}

export interface PermissionGroup {
  module: string
  permissions: PermissionDef[]
}

export interface PermissionDef {
  action: string
  description: string
  scopes: string[]
}

export interface AssignRolesParams {
  user_id: number
  role_ids: number[]
}

/* ========== Article 文章 ========== */
export interface Article {
  id: number
  title: string
  slug: string
  summary: string
  body: string
  cover_image?: number | null
  cover_image_url?: string
  author_id: number
  author?: UserInfo
  status: 'draft' | 'published' | 'archived'
  published_at?: string | null
  is_top: boolean
  seo_title: string
  seo_desc: string
  categories?: TaxonomyTerm[]
  tags?: TaxonomyTerm[]
  created_by: number
  updated_by?: number | null
  created_at: string
  updated_at: string
}

export interface ArticleListParams extends PageParams {
  status?: string
  keyword?: string
}

export interface CreateArticleParams {
  title: string
  slug: string
  summary?: string
  body: string
  cover_image?: number | null
  status?: 'draft' | 'published' | 'archived'
  is_top?: boolean
  seo_title?: string
  seo_desc?: string
  category_ids?: number[]
  tag_ids?: number[]
}

export interface UpdateArticleParams extends Partial<CreateArticleParams> {
  id: number
}

/* ========== Page 页面 ========== */
export interface PageInfo {
  id: number
  title: string
  slug: string
  body: string
  excerpt: string
  featured_image: string
  author_id: number
  template: string
  sort_order: number
  status: 'draft' | 'published'
  page_meta?: PageMeta
  published_at?: string | null
  created_at: string
  updated_at: string
}

export interface PageMeta {
  meta_title?: string
  meta_description?: string
  meta_keywords?: string
  og_image?: string
}

export interface PageListParams extends PageParams {
  status?: string
}

export interface CreatePageParams {
  title: string
  slug: string
  body?: string
  excerpt?: string
  featured_image?: string
  template?: string
  sort_order?: number
  page_meta?: PageMeta
}

export interface UpdatePageParams extends Partial<CreatePageParams> {
  id: number
}

/* ========== Menu 菜单 ========== */
export interface Menu {
  id: string
  name: string
  source: 'yaml' | 'database'
  items: MenuItem[]
  created_at: string
  updated_at: string
}

export interface MenuItem {
  id: number
  menu_id: string
  item_id: string
  label: string
  url: string
  parent_id?: number | null
  sort: number
  external: boolean
  target: '_self' | '_blank'
  content_type: string
  icon: string
  children?: MenuItem[]
}

export interface MenuItemInput {
  item_id: string
  label: string
  url: string
  parent_id?: number | null
  sort: number
  external?: boolean
  target?: '_self' | '_blank'
  icon?: string
  children?: MenuItemInput[]
}

/* ========== Taxonomy 分类 ========== */
export interface Taxonomy {
  id: string
  name: string
  description: string
  hierarchical: boolean
  created_at: string
  updated_at: string
}

export interface TaxonomyTerm {
  id: number
  taxonomy_id: string
  name: string
  slug: string
  description: string
  parent_id?: number | null
  sort: number
  seo_title: string
  seo_desc: string
  children?: TaxonomyTerm[]
  created_at: string
  updated_at: string
}

export interface CreateTermParams {
  name: string
  slug: string
  description?: string
  parent_id?: number | null
  sort?: number
  seo_title?: string
  seo_desc?: string
}

export interface UpdateTermParams extends Partial<CreateTermParams> {
  id: number
}

/* ========== Media 媒体 ========== */
export interface MediaItem {
  id: number
  filename: string
  url: string
  mime_type: string
  size: number
  width?: number
  height?: number
  alt: string
  title: string
  styles?: Record<string, string>
  uploaded_by: number
  folder_id?: number | null
  created_at: string
}

export interface MediaFolder {
  id: number
  name: string
  parent_id?: number | null
  sort: number
  children?: MediaFolder[]
}

export interface MediaListParams extends PageParams {
  folder_id?: number | null
  mime_prefix?: string
}

/* ========== Settings 设置 ========== */
export interface SiteSettings {
  name: string
  description: string
  url: string
  logo: string
  favicon: string
  language: string
  timezone: string
  seo: {
    title_suffix: string
    description: string
    keywords: string
  }
  pagination: {
    default_page_size: number
    max_page_size: number
  }
  image_styles: Record<string, {
    width: number
    height: number
    mode: string
    quality: number
  }>
  contact?: {
    email: string
    phone: string
  }
}
