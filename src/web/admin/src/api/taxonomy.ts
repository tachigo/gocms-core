import request from './request'
import type { ApiResponse, Taxonomy, TaxonomyTerm, CreateTermParams, UpdateTermParams } from '@/types'

/** 词汇表管理列表 */
export const getTaxonomies = () =>
  request.get<any, ApiResponse<{ list: Taxonomy[] }>>('/admin/taxonomies')

/** 术语管理列表（树形） */
export const getTerms = (vocabId: string) =>
  request.get<any, ApiResponse<{ list: TaxonomyTerm[] }>>(`/admin/taxonomies/${vocabId}/terms`)

/** 创建术语 */
export const createTerm = (vocabId: string, data: CreateTermParams) =>
  request.post<any, ApiResponse<{ id: number }>>(`/admin/taxonomies/${vocabId}/terms`, data)

/** 编辑术语 */
export const updateTerm = (vocabId: string, data: UpdateTermParams) =>
  request.put<any, ApiResponse>(`/admin/taxonomies/${vocabId}/terms/${data.id}`, data)

/** 删除术语 */
export const deleteTerm = (vocabId: string, id: number) =>
  request.delete<any, ApiResponse>(`/admin/taxonomies/${vocabId}/terms/${id}`)
