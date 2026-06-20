import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getToken, setToken as persistToken, clearToken } from '../modules/auth/token'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null)
  const token = ref(getToken())
  const isAuthenticated = computed(() => !!token.value && !!user.value)

  // Actions
  const setUser = (userData) => {
    user.value = userData
    if (userData) {
      localStorage.setItem('user_data', JSON.stringify(userData))
    } else {
      localStorage.removeItem('user_data')
    }
  }

  const setToken = (newToken, remember = true) => {
    token.value = newToken
    persistToken(newToken, remember)
  }

  const clearAuth = () => {
    user.value = null
    token.value = null
    clearToken()
    localStorage.removeItem('user_data')
  }

  const logout = () => {
    clearAuth()
  }

  // Inicializar desde localStorage
  const initializeFromStorage = () => {
    const storedToken = getToken()
    const storedUser = localStorage.getItem('user_data')

    if (storedToken) {
      token.value = storedToken
    }
    
    if (storedUser) {
      try {
        user.value = JSON.parse(storedUser)
      } catch {
        user.value = null
      }
    }
  }

  // Inicializar al crear el store
  initializeFromStorage()

  return {
    // State
    user,
    token,
    isAuthenticated,
    
    // Actions
    setUser,
    setToken,
    clearAuth,
    logout,
    initializeFromStorage
  }
})