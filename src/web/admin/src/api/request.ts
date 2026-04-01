/**
 * Axios 实例封装
 * JWT 自动注入 · 统一错误处理 · 401 自动跳转
 */
import axios, { type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// 请求拦截：注入 Token
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('cms_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截：统一处理业务码 + HTTP 错误
request.interceptors.response.use(
  (response: AxiosResponse) => {
    const { code, message, data } = response.data
    if (code !== undefined && code !== 0) {
      ElMessage.error(message || '请求失败')
      if (code === 401) {
        localStorage.removeItem('cms_token')
        router.push('/login')
      }
      return Promise.reject(new Error(message))
    }
    // 返回 data 部分，外层不再需要 .data
    return response.data
  },
  (error) => {
    const status = error.response?.status
    const msg = error.response?.data?.message
    if (status === 401) {
      localStorage.removeItem('cms_token')
      router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
    } else if (status === 403) {
      ElMessage.error(msg || '没有操作权限')
    } else if (status === 404) {
      ElMessage.error(msg || '资源不存在')
    } else if (status && status >= 500) {
      ElMessage.error('服务器错误，请稍后重试')
    } else {
      ElMessage.error(error.message || '网络错误')
    }
    return Promise.reject(error)
  },
)

export default request
