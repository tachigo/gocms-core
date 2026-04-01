import request from './request'
import type { ApiResponse, PageResult, MediaItem, MediaFolder, MediaListParams } from '@/types'

/** 媒体列表 */
export const getMediaList = (params?: MediaListParams) =>
  request.get<any, ApiResponse<PageResult<MediaItem>>>('/admin/media', { params })

/** 媒体详情 */
export const getMedia = (id: number) =>
  request.get<any, ApiResponse<MediaItem>>(`/admin/media/${id}`)

/** 上传文件 */
export const uploadMedia = (file: File, folderId?: number | null) => {
  const form = new FormData()
  form.append('file', file)
  if (folderId) form.append('folder_id', String(folderId))
  return request.post<any, ApiResponse<{ id: number; url: string }>>('/admin/media/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
}

/** 更新媒体元信息 */
export const updateMedia = (id: number, data: { alt?: string; title?: string }) =>
  request.put<any, ApiResponse>(`/admin/media/${id}`, data)

/** 删除媒体 */
export const deleteMedia = (id: number) =>
  request.delete<any, ApiResponse>(`/admin/media/${id}`)

/** 文件夹树 */
export const getFolders = () =>
  request.get<any, ApiResponse<{ list: MediaFolder[] }>>('/admin/media/folders')

/** 创建文件夹 */
export const createFolder = (name: string, parentId?: number | null) =>
  request.post<any, ApiResponse<{ id: number }>>('/admin/media/folders', { name, parent_id: parentId })

/** 重命名文件夹 */
export const renameFolder = (id: number, name: string) =>
  request.put<any, ApiResponse>(`/admin/media/folders/${id}`, { name })

/** 删除文件夹 */
export const deleteFolder = (id: number) =>
  request.delete<any, ApiResponse>(`/admin/media/folders/${id}`)
