// src/modules/inmuebles/composables/useInmueble.js
import { ref, computed } from 'vue'
import { useMutation, useQuery } from '@vue/apollo-composable'
import { 
  GET_INMUEBLES, 
  GET_INMUEBLE, 
  CREATE_INMUEBLE, 
  UPDATE_INMUEBLE, 
  DELETE_INMUEBLE 
} from '../graphql/inmuebleQueries'
import { mockInmuebles } from '@/mocks'

const USE_MOCK = import.meta.env.DEV

export function useInmueble() {
  const inmuebles = ref([])
  const inmueble = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const filters = ref({
    search: '',
    estados: {},
    comunidadAutonoma: null,
    provincia: null,
    localidad: null,
    tipoInmueble: null
  })

  const hasInmuebles = computed(() => inmuebles.value.length > 0)
  const isEmpty = computed(() => !loading.value && !inmuebles.value.length)
  const filteredCount = computed(() => inmuebles.value.length)

  const { refetch: refetchInmuebles } = useQuery(GET_INMUEBLES, null, {
    enabled: !USE_MOCK,
    fetchPolicy: 'cache-and-network'
  })

  const { mutate: createMutation } = useMutation(CREATE_INMUEBLE)
  const { mutate: updateMutation } = useMutation(UPDATE_INMUEBLE)
  const { mutate: deleteMutation } = useMutation(DELETE_INMUEBLE)

  const listar = async (filterParams = {}) => {
    loading.value = true
    error.value = null

    try {
      if (USE_MOCK) {
        await new Promise(resolve => setTimeout(resolve, 300))
        let result = [...mockInmuebles]

        if (filterParams.search) {
          const term = filterParams.search.toLowerCase()
          result = result.filter(i => 
            i.denominacion_principal?.toLowerCase().includes(term) ||
            i.direccion?.toLowerCase().includes(term) ||
            i.codigo_bien_interes_cultural?.toLowerCase().includes(term)
          )
        }

        if (filterParams.estados && Object.values(filterParams.estados).some(Boolean)) {
          const activos = Object.entries(filterParams.estados)
            .filter(([_, v]) => v)
            .map(([k]) => k)
          result = result.filter(i => activos.includes(i.estado))
        }

        if (filterParams.comunidadAutonoma) {
          result = result.filter(i => i.comunidad_autonoma === filterParams.comunidadAutonoma)
        }

        if (filterParams.provincia) {
          result = result.filter(i => i.provincia === filterParams.provincia)
        }

        if (filterParams.localidad) {
          result = result.filter(i => i.localidad === filterParams.localidad)
        }

        if (filterParams.tipoInmueble) {
          result = result.filter(i => i.tipo_inmueble === filterParams.tipoInmueble)
        }

        inmuebles.value = result
        Object.assign(filters.value, filterParams)
        return { items: result, total: result.length }
      }

      const { data } = await refetchInmuebles(filterParams)
      inmuebles.value = data?.inmuebles?.items || []
      return data?.inmuebles
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const obtener = async (id) => {
    loading.value = true
    error.value = null

    try {
      if (USE_MOCK) {
        await new Promise(resolve => setTimeout(resolve, 200))
        inmueble.value = mockInmuebles.find(i => i.id == id) || null
        return inmueble.value
      }

      const { data } = await useQuery(GET_INMUEBLE, { id }).refetch()
      inmueble.value = data?.inmueble
      return inmueble.value
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const crear = async (input) => {
    loading.value = true
    error.value = null

    try {
      if (USE_MOCK) {
        await new Promise(resolve => setTimeout(resolve, 500))
        const nuevo = { id: Date.now(), ...input, created_at: new Date().toISOString() }
        mockInmuebles.push(nuevo)
        inmueble.value = nuevo
        return nuevo
      }

      const { data } = await createMutation({ input })
      inmueble.value = data?.createInmueble
      await listar(filters.value)
      return inmueble.value
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const actualizar = async (id, input) => {
    loading.value = true
    error.value = null

    try {
      if (USE_MOCK) {
        await new Promise(resolve => setTimeout(resolve, 500))
        const index = mockInmuebles.findIndex(i => i.id == id)
        if (index !== -1) {
          mockInmuebles[index] = { ...mockInmuebles[index], ...input, updated_at: new Date().toISOString() }
          inmueble.value = mockInmuebles[index]
        }
        return inmueble.value
      }

      const { data } = await updateMutation({ id, input })
      inmueble.value = data?.updateInmueble
      await listar(filters.value)
      return inmueble.value
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const eliminar = async (id) => {
    loading.value = true
    error.value = null

    try {
      if (USE_MOCK) {
        await new Promise(resolve => setTimeout(resolve, 500))
        const index = mockInmuebles.findIndex(i => i.id == id)
        if (index !== -1) mockInmuebles.splice(index, 1)
        return true
      }

      await deleteMutation({ id })
      await listar(filters.value)
      return true
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const limpiarFiltros = () => {
    filters.value = {
      search: '',
      estados: {},
      comunidadAutonoma: null,
      provincia: null,
      localidad: null,
      tipoInmueble: null
    }
    listar()
  }

  const obtenerCatalogos = async () => {
    if (USE_MOCK) {
      const { 
        ESTADOS, 
        TIPOS_INMUEBLE, 
        COMUNIDADES_AUTONOMAS, 
        PROVINCIAS, 
        LOCALIDADES, 
        REGISTROS_PROPIEDAD,
        TIPOS_DOCUMENTO,
        ESTADOS_CONSERVACION
      } = await import('@/mocks')
      
      return {
        estados: ESTADOS,
        tiposInmueble: TIPOS_INMUEBLE,
        comunidadesAutonomas: COMUNIDADES_AUTONOMAS,
        provincias: PROVINCIAS,
        localidades: LOCALIDADES,
        registrosPropiedad: REGISTROS_PROPIEDAD,
        tiposDocumento: TIPOS_DOCUMENTO,
        estadosConservacion: ESTADOS_CONSERVACION
      }
    }
    
    return { 
      estados: [], 
      tiposInmueble: [], 
      comunidadesAutonomas: [], 
      provincias: [], 
      localidades: [], 
      registrosPropiedad: [],
      tiposDocumento: [],
      estadosConservacion: []
    }
  }

  return {
    inmuebles,
    inmueble,
    loading,
    error,
    filters,
    hasInmuebles,
    isEmpty,
    filteredCount,
    listar,
    obtener,
    crear,
    actualizar,
    eliminar,
    limpiarFiltros,
    obtenerCatalogos
  }
}