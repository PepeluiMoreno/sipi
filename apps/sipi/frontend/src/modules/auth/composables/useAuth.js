import { ref, computed } from 'vue'
import { useMutation, useLazyQuery } from '@vue/apollo-composable'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../../stores/auth'
import { useOrgConfigStore } from '../../../stores/orgConfig'
import { stopSessionGuard } from '../../../composables/useSessionGuard'
import { LOGIN_MUTATION, GET_CURRENT_USER_QUERY } from '../graphql/authQueries'
import { CONFIGURACIONES } from '../../configuracion/graphql/configQueries'

export function useAuth() {
  const router = useRouter()
  const authStore = useAuthStore()
  const loading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => authStore.isAuthenticated)

  const orgConfig = useOrgConfigStore()
  const { mutate: loginMutation } = useMutation(LOGIN_MUTATION)
  const { load: cargarConfig, onResult: onConfig } = useLazyQuery(CONFIGURACIONES, null, { fetchPolicy: 'network-only' })
  onConfig((r) => orgConfig.aplicarConfiguraciones(r.data?.configuraciones?.items ?? []))
  const { load: cargarMe, onResult: onMe } = useLazyQuery(
    GET_CURRENT_USER_QUERY, null, { fetchPolicy: 'network-only' }
  )
  onMe((r) => {
    if (r.data?.me) {
      authStore.setUser(r.data.me)
    } else if (authStore.token) {
      // Token inválido/caducado: limpiar y exigir login de nuevo.
      authStore.clearAuth()
      if (router.currentRoute.value.name !== 'Login') router.push('/login')
    }
  })

  // Restaura/actualiza el usuario actual (roles incluidos) usando el token vigente.
  const cargarUsuarioActual = () => { if (authStore.token) cargarMe() }

  const login = async ({ nombreUsuario, contrasena, remember = true }) => {
    loading.value = true
    error.value = null
    try {
      const { data } = await loginMutation({ nombreUsuario, contrasena })
      const res = data?.login
      if (res?.ok && res.token) {
        authStore.setToken(res.token, remember)
        authStore.setUser({ id: res.usuarioId, nombreUsuario: res.nombreUsuario, roles: [] })
        cargarMe()       // enriquece con nombre/roles
        cargarConfig()   // parámetros de sesión (timeout)
        router.push('/')
        return { success: true }
      }
      error.value = res?.mensaje || 'Usuario o contraseña incorrectos'
      return { success: false, error: error.value }
    } catch (err) {
      error.value = err.message
      return { success: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  // Logout es cliente: detener la vigilancia y descartar el token.
  const logout = () => {
    stopSessionGuard()
    authStore.clearAuth()
    router.push('/login')
  }

  // El alta de usuarios la hace un administrador (Control de acceso), no auto-registro.
  const register = async () => ({ success: false, error: 'El alta de usuarios la realiza un administrador.' })

  return {
    user: computed(() => authStore.user),
    token: computed(() => authStore.token),
    loading,
    error,
    isAuthenticated,
    login,
    logout,
    register,
    cargarUsuarioActual,
  }
}
