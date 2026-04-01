import request from './request'
import type { ApiResponse, PageResult, Article, ArticleListParams, CreateArticleParams, UpdateArticleParams } from '@/types'

/** 文章管理列表（全部状态） */
export const getArticles = (params?: ArticleListParams) =>
  request.get<any, ApiResponse<PageResult<Article>>>('/admin/articles', { params })

/** 文章详情 */
export const getArticle = (id: number) =>
  request.get<any, ApiResponse<Article>>(`/admin/articles/${id}`)

/** 创建文章 */
export const createArticle = (data: CreateArticleParams) =>
  request.post<any, ApiResponse<{ id: number }>>('/admin/articles', data)

/** 编辑文章 */
export const updateArticle = (data: UpdateArticleParams) =>
  request.put<any, ApiResponse>(`/admin/articles/${data.id}`, data)

/** 删除文章 */
export const deleteArticle = (id: number) =>
  request.delete<any, ApiResponse>(`/admin/articles/${id}`)
