import request from './request'
import type { ApiResponse, SiteSettings } from '@/types'

/** 获取完整站点配置（管理员） */
export const getAdminSettings = () =>
  request.get<any, ApiResponse<SiteSettings>>('/admin/settings')

/** 获取公开站点配置 */
export const getPublicSettings = () =>
  request.get<any, ApiResponse<SiteSettings>>('/settings')

/** 更新站点配置 */
export const updateSettings = (data: Partial<SiteSettings>) =>
  request.put<any, ApiResponse>('/admin/settings', data)
