import { ref } from 'vue'
import { useQuery, useMutation } from '@vue/apollo-composable'
import {
  LISTAR_DOCUMENTOS_ACTUACION,
  AGREGAR_DOCUMENTO_ACTUACION,
  QUITAR_DOCUMENTO_ACTUACION,
  ACTUALIZAR_DOCUMENTO_ACTUACION
} from '../graphql/documentoActuacionQueries'

export function useDocumentoActuacion(actuacionId) {
  const documentos = ref([])
  const loading = ref(false)
  const error = ref(null)

  const listar = async () => {
    loading.value = true
    error.value = null
    try {
      const { data, error: queryError } = await useQuery(LISTAR_DOCUMENTOS_ACTUACION, {
        actuacionId
      })
      if (queryError) throw queryError
      documentos.value = data.value?.actuacionDocumentos?.items || []
      return documentos.value
    } catch (err) {
      error.value = `Error al cargar documentos de la actuación: ${err.message}`
      console.error('Error en listar DocumentosActuacion:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const agregar = async (documentoId, descripcion = null) => {
    loading.value = true
    error.value = null
    try {
      const { mutate } = useMutation(AGREGAR_DOCUMENTO_ACTUACION)
      const { data, errors } = await mutate({
        actuacionId,
        documentoId,
        descripcion
      })
      if (errors) throw new Error(errors[0].message)
      const nuevo = data.agregarDocumentoActuacion.item
      documentos.value.push(nuevo)
      return nuevo
    } catch (err) {
      error.value = `Error al agregar documento a la actuación: ${err.message}`
      throw err
    } finally {
      loading.value = false
    }
  }

  const actualizar = async (documentoId, descripcion) => {
    loading.value = true
    error.value = null
    try {
      const { mutate } = useMutation(ACTUALIZAR_DOCUMENTO_ACTUACION)
      const { data, errors } = await mutate({
        actuacionId,
        documentoId,
        descripcion
      })
      if (errors) throw new Error(errors[0].message)
      const index = documentos.value.findIndex(d => d.documentoId === documentoId)
      if (index !== -1) {
        documentos.value[index].descripcion = descripcion
      }
      return data.actualizarDocumentoActuacion.item
    } catch (err) {
      error.value = `Error al actualizar documento de la actuación: ${err.message}`
      throw err
    } finally {
      loading.value = false
    }
  }

  const quitar = async (documentoId) => {
    loading.value = true
    error.value = null
    try {
      const { mutate } = useMutation(QUITAR_DOCUMENTO_ACTUACION)
      const { data, errors } = await mutate({
        actuacionId,
        documentoId
      })
      if (errors) throw new Error(errors[0].message)
      documentos.value = documentos.value.filter(
        d => d.documentoId !== documentoId
      )
      return data.quitarDocumentoActuacion.success
    } catch (err) {
      error.value = `Error al quitar documento de la actuación: ${err.message}`
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    documentos,
    loading,
    error,
    listar,
    agregar,
    actualizar,
    quitar
  }
}