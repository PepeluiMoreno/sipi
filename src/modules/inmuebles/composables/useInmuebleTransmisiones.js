import { ref, computed } from 'vue'
import { useMutation } from '@vue/apollo-composable'
import { useAgenteBaseStrawchemy } from '../../agentes/composables/useAgenteBaseStrawchemy'
import * as queries from '../graphql/InmuebleTransmisionQueries.js'

export function useInmuebleTransmisiones(inmuebleId) {
  // Corrected entity name 'transmisiones'
  const base = useAgenteBaseStrawchemy('transmisiones', queries)
  const generandoCedula = ref(false)

  const listar = async () => {
    return base.listar({ inmuebleId: { eq: inmuebleId } })
  }

  const crear = async (inputData) => {
    return base.crear({ ...inputData, inmuebleId })
  }

  // Custom method
  const generarCedula = async (transmisionId) => {
    generandoCedula.value = true
    base.error.value = null
    try {
      const { mutate } = useMutation(queries.GENERAR_CEDULA)
      const { data, errors } = await mutate({ transmisionId })
      if (errors) throw new Error(errors[0].message)
      return data.generarCedulaTransmision.documento
    } catch (err) {
      base.error.value = `Error al generar cédula: ${err.message}`
      throw err
    } finally {
      generandoCedula.value = false
    }
  }

  const transmisiones = computed(() => base.items.value)
  const transmision = computed(() => base.item.value)

  // Computed properties
  const transmisionesPorTipo = computed(() => {
    return transmisiones.value.reduce((acc, t) => {
      const tipo = t.tipoTransmision || 'Sin tipo'
      if (!acc[tipo]) acc[tipo] = []
      acc[tipo].push(t)
      return acc
    }, {})
  })

  const ultimaTransmision = computed(() => {
    return transmisiones.value.length > 0 ? transmisiones.value[0] : null
  })

  const transmisionesConDocumento = computed(() => {
    return transmisiones.value.filter(t => t.documento)
  })

  const tieneTransmisionesPendientes = computed(() => {
    return transmisiones.value.some(t =>
      t.estado === 'Pendiente' || t.estado === 'En trámite'
    )
  })

  return {
    ...base,
    transmisiones,
    transmision,
    generandoCedula,
    transmisionesPorTipo,
    ultimaTransmision,
    transmisionesConDocumento,
    tieneTransmisionesPendientes,
    listar,
    crear,
    generarCedula
  }
}