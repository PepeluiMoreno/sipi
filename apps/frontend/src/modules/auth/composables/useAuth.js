import { ref, computed } from 'vue'
import { useMutation, useQuery } from '@vue/apollo-composable'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../../stores/auth'
import { 
  LOGIN_MUTATION, 
  LOGOUT_MUTATION, 
  REGISTER_MUTATION,
  REFRESH_TOKEN_MUTATION,
  GET_CURRENT_USER_QUERY 
} from '../graphql/authQueries'

export function useAuth() {
  const router = useRouter()
  const authStore = useAuthStore()
  const loading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => authStore.isAuthenticated)

  // Query para obtener el usuario actual
  const { onResult: onUserResult } = useQuery(GET_CURRENT_USER_QUERY, null, {
    enabled: isAuthenticated.value,
    fetchPolicy: 'network-only'
  })

  onUserResult((result) => {
    if (result.data?.currentUser) {
      authStore.setUser(result.data.currentUser)
    }
  })

  // Mutation de login
  const { mutate: loginMutation } = useMutation(LOGIN_MUTATION)
  
  const login = async (credentials) => {
    loading.value = true
    error.value = null
    
    try {
      const { data } = await loginMutation(credentials)
      
      if (data?.login?.success) {
        const { token: newToken, user: userData } = data.login
        authStore.setToken(newToken)
        authStore.setUser(userData)
        
        router.push('/')
        return { success: true }
      } else {
        error.value = data?.login?.message || 'Error en el login'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = err.message
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  // Mutation de registro
  const { mutate: registerMutation } = useMutation(REGISTER_MUTATION)
  
  const register = async (userData) => {
    loading.value = true
    error.value = null
    
    try {
      const { data } = await registerMutation({ input: userData })
      
      if (data?.register?.success) {
        return { success: true, message: data.register.message }
      } else {
        error.value = data?.register?.message || 'Error en el registro'
        return { success: false, error: error.value }
      }
    } catch (err) {
      error.value = err.message
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  // Logout
  const { mutate: logoutMutation } = useMutation(LOGOUT_MUTATION)
  
  const logout = async () => {
    try {
      await logoutMutation()
    } catch (err) {
      console.error('Error en logout:', err)
    } finally {
      authStore.clearAuth()
      router.push('/login')
    }
  }

  // Refresh token
  const { mutate: refreshTokenMutation } = useMutation(REFRESH_TOKEN_MUTATION)
  
  const refreshToken = async () => {
    try {
      const { data } = await refreshTokenMutation()
      if (data?.refreshToken?.success) {
        authStore.setToken(data.refreshToken.token)
        return true
      }
    } catch (err) {
      console.error('Error refreshing token:', err)
      logout()
    }
    return false
  }

  return {
    user: computed(() => authStore.user),
    token: computed(() => authStore.token),
    loading,
    error,
    isAuthenticated,
    login,
    register,
    logout,
    refreshToken
  }
}