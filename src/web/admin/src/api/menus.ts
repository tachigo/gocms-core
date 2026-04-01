import request from './request'
import type { ApiResponse, Menu } from '@/types'

/** 菜单管理列表 */
export const getMenus = () =>
  request.get<any, ApiResponse<{ list: Menu[] }>>('/admin/menus')

/** 菜单详情（含菜单项树） */
export const getMenu = (menuId: string) =>
  request.get<any, ApiResponse<Menu>>(`/admin/menus/${menuId}`)

/** 更新菜单（整体替换菜单项） */
export const updateMenu = (menuId: string, items: any[]) =>
  request.put<any, ApiResponse>(`/admin/menus/${menuId}`, { items })

/** 重置菜单为 YAML 配置 */
export const resetMenu = (menuId: string) =>
  request.post<any, ApiResponse>(`/admin/menus/${menuId}/reset`)
