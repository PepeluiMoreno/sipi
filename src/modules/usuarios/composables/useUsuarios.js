import { ref, computed } from 'vue'
import { useMutation, useQuery } from '@vue/apollo-composable'
import { useAgenteBaseStrawchemy } from '../../agentes/composables/useAgenteBaseStrawchemy'
import * as queries from '../graphql/usuarioQueries.js'

export function useUsuarios() {
  const base = useAgenteBaseStrawchemy('usuarios', queries)
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  // Custom Login Logic wrapping base or standalone
  const login = async (email, password) => {
    base.loading.value = true
    base.error.value = null
    try {
      const { mutate } = useMutation(queries.LOGIN)
      const { data } = await mutate({ email, password })

      if (data.login.success) {
        token.value = data.login.token
        user.value = data.login.user
        localStorage.setItem('token', token.value)
        localStorage.setItem('user', JSON.stringify(user.value))
      } else {
        throw new Error(data.login.message)
      }
      return data.login
    } catch (err) {
      base.error.value = err.message
      throw err
    } finally {
      base.loading.value = false
    }
  }

  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return {
    ...base,
    usuarios: base.items,
    usuario: base.item,
    login,
    logout,
    currentUser: user,
    token
  }
}