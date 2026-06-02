import { ref } from 'vue'
import { useQuery, useMutation } from '@vue/apollo-composable'
import {
  LISTAR_DOCUMENTOS_TRANSMISION,
  AGREGAR_DOCUMENTO_TRANSMISION,
  QUITAR_DOCUMENTO_TRANSMISION,
  ACTUALIZAR_DOCUMENTO_TRANSMISION
} from '../graphql/documentoTransmisionQueries'

export function useDocumentoTransmision(transmisionId) {
  const documentos = ref([])
  const loading = ref(false)
  const error = ref(null)

  const listar = async () => {
    loading.value = true
    error.value = null
    try {
      const { data, error: queryError } = await useQuery(LISTAR_DOCUMENTOS_TRANSMISION, {
        transmisionId
      })
      if (queryError) throw queryError
      documentos.value = data.value?.transmisionDocumentos?.items || []
      return documentos.value
    } catch (err) {
      error.value = `Error al cargar documentos de la transmisión: ${err.message}`
      console.error('Error en listar DocumentosTransmision:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const agregar = async (documentoId, descripcion = null) => {
    loading.value = true
    error.value = null
    try {
      const { mutate } = useMutation(AGREGAR_DOCUMENTO_TRANSMISION)
      const { data, errors } = await mutate({
        transmisionId,
        documentoId,
        descripcion
      })
      if (errors) throw new Error(errors[0].message)
      const nuevo = data.agregarDocumentoTransmision.item
      documentos.value.push(nuevo)
      return nuevo
    } catch (err) {
      error.value = `Error al agregar documento a la transmisión: ${err.message}`
      throw err
    } finally {
      loading.value = false
    }
  }

  const actualizar = async (documentoId, descripcion) => {
    loading.value = true
    error.value = null
    try {
      const { mutate } = useMutation(ACTUALIZAR_DOCUMENTO_TRANSMISION)
      const { data, errors } = await mutate({
        transmisionId,
        documentoId,
        descripcion
      })
      if (errors) throw new Error(errors[0].message)
      const index = documentos.value.findIndex(d => d.documentoId === documentoId)
      if (index !== -1) {
        documentos.value[index].descripcion = descripcion
      }
      return data.actualizarDocumentoTransmision.item
    } catch (err) {
      error.value = `Error al actualizar documento de la transmisión: ${err.message}`
      throw err
    } finally {
      loading.value = false
    }
  }

  const quitar = async (documentoId) => {
    loading.value = true
    error.value = null
    try {
      const { mutate } = useMutation(QUITAR_DOCUMENTO_TRANSMISION)
      const { data, errors } = await mutate({
        transmisionId,
        documentoId
      })
      if (errors) throw new Error(errors[0].message)
      documentos.value = documentos.value.filter(
        d => d.documentoId !== documentoId
      )
      return data.quitarDocumentoTransmision.success
    } catch (err) {
      error.value = `Error al quitar documento de la transmisión: ${err.message}`
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