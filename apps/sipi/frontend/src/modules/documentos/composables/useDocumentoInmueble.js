import { ref } from 'vue'
import { useQuery, useMutation } from '@vue/apollo-composable'
import {
  LISTAR_DOCUMENTOS_INMUEBLE,
  AGREGAR_DOCUMENTO_INMUEBLE,
  QUITAR_DOCUMENTO_INMUEBLE,
  ACTUALIZAR_DOCUMENTO_INMUEBLE
} from '../graphql/documentoInmuebleQueries'

export function useDocumentoInmueble(inmuebleId) {
  const documentos = ref([])
  const loading = ref(false)
  const error = ref(null)

  const listar = async () => {
    loading.value = true
    error.value = null
    try {
      const { data, error: queryError } = await useQuery(LISTAR_DOCUMENTOS_INMUEBLE, {
        inmuebleId
      })
      if (queryError) throw queryError
      documentos.value = data.value?.inmuebleDocumentos?.items || []
      return documentos.value
    } catch (err) {
      error.value = `Error al cargar documentos del inmueble: ${err.message}`
      console.error('Error en listar DocumentosInmueble:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  const agregar = async (documentoId, descripcion = null) => {
    loading.value = true
    error.value = null
    try {
      const { mutate } = useMutation(AGREGAR_DOCUMENTO_INMUEBLE)
      const { data, errors } = await mutate({
        inmuebleId,
        documentoId,
        descripcion
      })
      if (errors) throw new Error(errors[0].message)
      const nuevo = data.agregarDocumentoInmueble.item
      documentos.value.push(nuevo)
      return nuevo
    } catch (err) {
      error.value = `Error al agregar documento al inmueble: ${err.message}`
      throw err
    } finally {
      loading.value = false
    }
  }

  const actualizar = async (documentoId, descripcion) => {
    loading.value = true
    error.value = null
    try {
      const { mutate } = useMutation(ACTUALIZAR_DOCUMENTO_INMUEBLE)
      const { data, errors } = await mutate({
        inmuebleId,
        documentoId,
        descripcion
      })
      if (errors) throw new Error(errors[0].message)
      const index = documentos.value.findIndex(d => d.documentoId === documentoId)
      if (index !== -1) {
        documentos.value[index].descripcion = descripcion
      }
      return data.actualizarDocumentoInmueble.item
    } catch (err) {
      error.value = `Error al actualizar documento del inmueble: ${err.message}`
      throw err
    } finally {
      loading.value = false
    }
  }

  const quitar = async (documentoId) => {
    loading.value = true
    error.value = null
    try {
      const { mutate } = useMutation(QUITAR_DOCUMENTO_INMUEBLE)
      const { data, errors } = await mutate({
        inmuebleId,
        documentoId
      })
      if (errors) throw new Error(errors[0].message)
      documentos.value = documentos.value.filter(
        d => d.documentoId !== documentoId
      )
      return data.quitarDocumentoInmueble.success
    } catch (err) {
      error.value = `Error al quitar documento del inmueble: ${err.message}`
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