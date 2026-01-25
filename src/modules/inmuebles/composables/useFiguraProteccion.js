import { computed } from 'vue'
import { useAgenteBase } from '../../agentes/composables/useAgenteBase'
import * as queries from '../graphql/inmuebleProteccionQueries.js'

export function useInmuebleProteccion(inmuebleId) {
  // Corrected entity name 'figuraProtecciones'
  const base = useAgenteBase('figuraProtecciones', queries)

  const listar = async () => {
    return base.listar({ inmuebleId: { eq: inmuebleId } })
  }

  const crear = async (inputData) => {
    return base.crear({ ...inputData, inmuebleId })
  }

  const figurasProteccion = computed(() => base.items.value)
  const figuraProteccion = computed(() => base.item.value)
  const tieneProteccion = computed(() => figurasProteccion.value.length > 0)

  const nivelMaximoProteccion = computed(() => {
    if (!figurasProteccion.value.length) return null

    const niveles = {
      'BIC': 4,
      'Bien de Interés Cultural': 4,
      'Bien Inventariado': 3,
      'Bien Catalogado': 3,
      'Bien Protegido': 2,
      'Área de Protección': 1
    }

    return figurasProteccion.value.reduce((max, figura) => {
      const nivel = niveles[figura.tipo] || 0
      return nivel > max ? nivel : max
    }, 0)
  })

  return {
    ...base,
    figurasProteccion,
    figuraProteccion,
    tieneProteccion,
    nivelMaximoProteccion,
    listar,
    crear
  }
}