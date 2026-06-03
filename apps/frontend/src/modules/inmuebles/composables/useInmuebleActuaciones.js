import { computed } from 'vue'
import { useAgenteBase } from '../../agentes/composables/useAgenteBase'
import * as queries from '../graphql/InmuebleActuacionQueries.js'

export function useInmuebleActuaciones(inmuebleId) {
  // Corrected entity name 'actuaciones'
  const base = useAgenteBase('actuaciones', queries)

  const listar = async () => {
    return base.listar({ inmuebleId: { eq: inmuebleId } })
  }

  const crear = async (inputData) => {
    return base.crear({ ...inputData, inmuebleId })
  }

  const actuaciones = computed(() => base.items.value)
  const actuacion = computed(() => base.item.value)
  
  const actuacionesActivas = computed(() => {
    return actuaciones.value.filter(a => a.estado === 'En curso' || a.estado === 'Pendiente')
  })
  
  const actuacionesCompletadas = computed(() => {
    return actuaciones.value.filter(a => a.estado === 'Finalizada')
  })

  return {
    ...base,
    actuaciones,
    actuacion,
    actuacionesActivas,
    actuacionesCompletadas,
    listar,
    crear
  }
}
