import { ref } from 'vue'
import { useQuery, useMutation } from '@vue/apollo-composable'
import {
  LISTAR_ANUNCIANTES,
  AGREGAR_ANUNCIANTE,
  QUITAR_ANUNCIANTE
} from '../graphql/transmisionAnuncianteQueries'

export function useTransmisionAnunciante(transmisionId) {
  const anunciantes = ref([])
  const loading = ref(false)
  const error = ref(null)

  const listar = async () => {
    loading.value = true
    error.value = null
    try {
      const { data, error: queryError } = await useQuery(LISTAR_ANUNCIANTES, {
        transmisionId
      })
      if (queryError) throw queryError
      anunciantes.value = data.value?.transmisionAnunciantes?.items || []
      return anunciantes.value
    } catch (err) {
      error.value = `Error al cargar anunciantes: ${err.message}`
      console.error('Error en listar Anunciantes:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const agregar = async (agenciaInmobiliariaId) => {
    loading.value = true
    error.value = null
    try {
      const { mutate } = useMutation(AGREGAR_ANUNCIANTE)
      const { data, errors } = await mutate({
        transmisionId,
        agenciaInmobiliariaId
      })
      if (errors) throw new Error(errors[0].message)
      const nuevo = data.agregarAnunciante.item
      anunciantes.value.push(nuevo)
      return nuevo
    } catch (err) {
      error.value = `Error al agregar anunciante: ${err.message}`
      throw err
    } finally {
      loading.value = false
    }
  }

  const quitar = async (agenciaInmobiliariaId) => {
    loading.value = true
    error.value = null
    try {
      const { mutate } = useMutation(QUITAR_ANUNCIANTE)
      const { data, errors } = await mutate({
        transmisionId,
        agenciaInmobiliariaId
      })
      if (errors) throw new Error(errors[0].message)
      anunciantes.value = anunciantes.value.filter(
        a => a.agenciaInmobiliariaId !== agenciaInmobiliariaId
      )
      return data.quitarAnunciante.success
    } catch (err) {
      error.value = `Error al quitar anunciante: ${err.message}`
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    anunciantes,
    loading,
    error,
    listar,
    agregar,
    quitar
  }
}