import request from './request'
import type { ApiResponse, PageResult, PageInfo, PageListParams, CreatePageParams, UpdatePageParams } from '@/types'

/** 页面管理列表 */
export const getPages = (params?: PageListParams) =>
  request.get<any, ApiResponse<PageResult<PageInfo>>>('/admin/pages', { params })

/** 页面详情 */
export const getPage = (id: number) =>
  request.get<any, ApiResponse<PageInfo>>(`/admin/pages/${id}`)

/** 创建页面 */
export const createPage = (data: CreatePageParams) =>
  request.post<any, ApiResponse<{ id: number }>>('/admin/pages', data)

/** 编辑页面 */
export const updatePage = (data: UpdatePageParams) =>
  request.put<any, ApiResponse>(`/admin/pages/${data.id}`, data)

/** 删除页面 */
export const deletePage = (id: number) =>
  request.delete<any, ApiResponse>(`/admin/pages/${id}`)

/** 发布页面 */
export const publishPage = (id: number) =>
  request.post<any, ApiResponse>(`/admin/pages/${id}/publish`)

/** 取消发布 */
export const unpublishPage = (id: number) =>
  request.post<any, ApiResponse>(`/admin/pages/${id}/unpublish`)
