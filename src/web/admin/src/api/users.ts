import request from './request'
import type { ApiResponse, PageResult, UserInfo, CreateUserParams, UpdateUserParams, PageParams } from '@/types'

/** 用户列表 */
export const getUsers = (params?: PageParams) =>
  request.get<any, ApiResponse<PageResult<UserInfo>>>('/admin/users', { params })

/** 用户详情 */
export const getUser = (id: number) =>
  request.get<any, ApiResponse<UserInfo>>(`/admin/users/${id}`)

/** 创建用户 */
export const createUser = (data: CreateUserParams) =>
  request.post<any, ApiResponse<{ id: number }>>('/admin/users', data)

/** 编辑用户 */
export const updateUser = (data: UpdateUserParams) =>
  request.put<any, ApiResponse>(`/admin/users/${data.id}`, data)

/** 删除用户 */
export const deleteUser = (id: number) =>
  request.delete<any, ApiResponse>(`/admin/users/${id}`)
