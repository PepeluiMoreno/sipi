import { ref } from 'vue'
import { useQuery, useMutation } from '@vue/apollo-composable'
import {
  OBTENER_INMATRICULACION,
  CREAR_INMATRICULACION,
  ACTUALIZAR_INMATRICULACION,
  ELIMINAR_INMATRICULACION
} from '../graphql/inmatriculacionQueries'

export function useInmatriculacion(inmuebleId) {
  const inmatriculacion = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const obtener = async () => {
    loading.value = true
    error.value = null
    try {
      const { data, error: queryError } = await useQuery(OBTENER_INMATRICULACION, { inmuebleId })
      if (queryError) throw queryError
      inmatriculacion.value = data.value?.inmatriculacion?.item || null
      return inmatriculacion.value
    } catch (err) {
      error.value = `Error al cargar inmatriculación: ${err.message}`
      console.error('Error en obtener Inmatriculacion:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const crear = async (inputData) => {
    loading.value = true
    error.value = null
    try {
      const { mutate } = useMutation(CREAR_INMATRICULACION)
      const { data, errors } = await mutate({
        inmuebleId,
        input: inputData
      })
      if (errors) throw new Error(errors[0].message)
      inmatriculacion.value = data.crearInmatriculacion.item
      return inmatriculacion.value
    } catch (err) {
      error.value = `Error al crear inmatriculación: ${err.message}`
      console.error('Error en crear Inmatriculacion:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const actualizar = async (inputData) => {
    loading.value = true
    error.value = null
    try {
      const { mutate } = useMutation(ACTUALIZAR_INMATRICULACION)
      const { data, errors } = await mutate({
        inmuebleId,
        input: inputData
      })
      if (errors) throw new Error(errors[0].message)
      inmatriculacion.value = data.actualizarInmatriculacion.item
      return inmatriculacion.value
    } catch (err) {
      error.value = `Error al actualizar inmatriculación: ${err.message}`
      console.error('Error en actualizar Inmatriculacion:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const eliminar = async () => {
    loading.value = true
    error.value = null
    try {
      const { mutate } = useMutation(ELIMINAR_INMATRICULACION)
      const { data, errors } = await mutate({ inmuebleId })
      if (errors) throw new Error(errors[0].message)
      inmatriculacion.value = null
      return data.eliminarInmatriculacion.success
    } catch (err) {
      error.value = `Error al eliminar inmatriculación: ${err.message}`
      console.error('Error en eliminar Inmatriculacion:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    inmatriculacion,
    loading,
    error,
    obtener,
    crear,
    actualizar,
    eliminar
  }
}