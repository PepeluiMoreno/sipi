import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useApolloClient } from '@vue/apollo-composable'
import { gql } from '@apollo/client/core'

// Queries para cargar datos geográficos
const CARGAR_CCAA = gql`
  query CargarComunidadesAutonomas {
    comunidadesAutonomas(limit: 50) {
      id
      nombre
    }
  }
`

const CARGAR_PROVINCIAS = gql`
  query CargarProvincias {
    provincias(limit: 100) {
      id
      nombre
      comunidadAutonomaId
    }
  }
`

const CARGAR_MUNICIPIOS = gql`
  query CargarMunicipios {
    municipios(limit: 10000) {
      id
      nombre
      provinciaId
    }
  }
`

export const useGeografiaStore = defineStore('geografia', () => {
  // State
  const comunidadesAutonomas = ref([])
  const provincias = ref([])
  const municipios = ref([])
  const loading = ref(false)
  const error = ref(null)
  const initialized = ref(false)

  // Getters computados para filtrar por jerarquía
  const provinciasPorCcaa = computed(() => {
    const mapa = {}
    for (const prov of provincias.value) {
      const ccaaId = prov.comunidadAutonomaId
      if (!mapa[ccaaId]) {
        mapa[ccaaId] = []
      }
      mapa[ccaaId].push(prov)
    }
    // Ordenar alfabéticamente
    for (const ccaaId in mapa) {
      mapa[ccaaId].sort((a, b) => a.nombre.localeCompare(b.nombre))
    }
    return mapa
  })

  const municipiosPorProvincia = computed(() => {
    const mapa = {}
    for (const muni of municipios.value) {
      const provId = muni.provinciaId
      if (!mapa[provId]) {
        mapa[provId] = []
      }
      mapa[provId].push(muni)
    }
    // Ordenar alfabéticamente
    for (const provId in mapa) {
      mapa[provId].sort((a, b) => a.nombre.localeCompare(b.nombre))
    }
    return mapa
  })

  // Helpers para obtener datos filtrados
  const getProvinciasDeCcaa = (ccaaId) => {
    if (!ccaaId) return []
    return provinciasPorCcaa.value[ccaaId] || []
  }

  const getMunicipiosDeProvincia = (provinciaId) => {
    if (!provinciaId) return []
    return municipiosPorProvincia.value[provinciaId] || []
  }

  const getMunicipiosDeCcaa = (ccaaId) => {
    if (!ccaaId) return []
    const provs = getProvinciasDeCcaa(ccaaId)
    const munis = []
    for (const prov of provs) {
      munis.push(...getMunicipiosDeProvincia(prov.id))
    }
    return munis
  }

  // Obtener IDs de municipios para filtros Strawchemy
  const getMunicipioIdsDeProvincia = (provinciaId) => {
    return getMunicipiosDeProvincia(provinciaId).map(m => m.id)
  }

  const getMunicipioIdsDeCcaa = (ccaaId) => {
    return getMunicipiosDeCcaa(ccaaId).map(m => m.id)
  }

  // Action principal: cargar todos los datos geográficos
  const cargarDatos = async () => {
    // Si ya está inicializado, no volver a cargar
    if (initialized.value) {
      return
    }

    loading.value = true
    error.value = null

    try {
      const { resolveClient } = useApolloClient()
      const client = resolveClient()

      // Cargar todo en paralelo
      const [ccaaResult, provResult, muniResult] = await Promise.all([
        client.query({ query: CARGAR_CCAA, fetchPolicy: 'network-only' }),
        client.query({ query: CARGAR_PROVINCIAS, fetchPolicy: 'network-only' }),
        client.query({ query: CARGAR_MUNICIPIOS, fetchPolicy: 'network-only' })
      ])

      comunidadesAutonomas.value = [...(ccaaResult.data?.comunidadesAutonomas || [])]
        .sort((a, b) => a.nombre.localeCompare(b.nombre))

      provincias.value = provResult.data?.provincias || []
      municipios.value = muniResult.data?.municipios || []

      initialized.value = true
      console.log(`[GeografiaStore] Datos cargados: ${comunidadesAutonomas.value.length} CCAA, ${provincias.value.length} provincias, ${municipios.value.length} municipios`)
    } catch (err) {
      error.value = `Error cargando datos geográficos: ${err.message}`
      console.error('[GeografiaStore]', error.value)
    } finally {
      loading.value = false
    }
  }

  // Forzar recarga de datos
  const recargar = async () => {
    initialized.value = false
    await cargarDatos()
  }

  return {
    // State
    comunidadesAutonomas,
    provincias,
    municipios,
    loading,
    error,
    initialized,

    // Getters
    provinciasPorCcaa,
    municipiosPorProvincia,

    // Helpers
    getProvinciasDeCcaa,
    getMunicipiosDeProvincia,
    getMunicipiosDeCcaa,
    getMunicipioIdsDeProvincia,
    getMunicipioIdsDeCcaa,

    // Actions
    cargarDatos,
    recargar
  }
})
