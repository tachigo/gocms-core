import request from './request'
import type { LoginParams, LoginResult, UserProfile, UpdateProfileParams, ChangePasswordParams, ApiResponse } from '@/types'

/** 登录 */
export const login = (data: LoginParams) =>
  request.post<any, ApiResponse<LoginResult>>('/auth/login', data)

/** 登出 */
export const logout = () =>
  request.post<any, ApiResponse>('/auth/logout')

/** 获取当前用户信息 */
export const getProfile = () =>
  request.get<any, ApiResponse<UserProfile>>('/auth/profile')

/** 更新个人信息 */
export const updateProfile = (data: UpdateProfileParams) =>
  request.put<any, ApiResponse>('/auth/profile', data)

/** 修改密码 */
export const changePassword = (data: ChangePasswordParams) =>
  request.put<any, ApiResponse>('/auth/password', data)
