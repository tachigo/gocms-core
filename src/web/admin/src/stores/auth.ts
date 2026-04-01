import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'
import type { UserProfile } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('cms_token') || '')
  const user = ref<UserProfile | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const res = await authApi.login({ username, password })
    token.value = res.data.token
    localStorage.setItem('cms_token', res.data.token)
    user.value = res.data.user as unknown as UserProfile
  }

  async function logout() {
    try { await authApi.logout() } catch { /* ignore */ }
    token.value = ''
    user.value = null
    localStorage.removeItem('cms_token')
  }

  async function fetchProfile() {
    try {
      const res = await authApi.getProfile()
      user.value = res.data
    } catch {
      await logout()
    }
  }

  return { token, user, isLoggedIn, login, logout, fetchProfile }
})
