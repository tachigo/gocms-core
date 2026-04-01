import request from './request'
import type {
  ApiResponse, Role, RoleSimple, CreateRoleParams, UpdateRoleParams,
  PermissionGroup, AssignRolesParams,
} from '@/types'

/** 角色列表 */
export const getRoles = () =>
  request.get<any, ApiResponse<{ list: Role[] }>>('/admin/roles')

/** 角色详情（含权限列表） */
export const getRole = (id: number) =>
  request.get<any, ApiResponse<Role>>(`/admin/roles/${id}`)

/** 创建自定义角色 */
export const createRole = (data: CreateRoleParams) =>
  request.post<any, ApiResponse<{ id: number }>>('/admin/roles', data)

/** 编辑角色权限 */
export const updateRole = (data: UpdateRoleParams) =>
  request.put<any, ApiResponse>(`/admin/roles/${data.id}`, data)

/** 删除自定义角色 */
export const deleteRole = (id: number) =>
  request.delete<any, ApiResponse>(`/admin/roles/${id}`)

/** 获取所有可用权限（来自各 Module Schema） */
export const getAvailablePermissions = () =>
  request.get<any, ApiResponse<{ groups: PermissionGroup[] }>>('/admin/permissions/available')

/** 获取用户的角色列表 */
export const getUserRoles = (userId: number) =>
  request.get<any, ApiResponse<{ roles: RoleSimple[] }>>(`/admin/users/${userId}/roles`)

/** 为用户分配角色（全量替换） */
export const assignRoles = (data: AssignRolesParams) =>
  request.put<any, ApiResponse>(`/admin/users/${data.user_id}/roles`, { role_ids: data.role_ids })
