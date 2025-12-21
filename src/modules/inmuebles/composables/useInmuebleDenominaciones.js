import { computed } from 'vue'
import { toRefs } from 'vue'
import { useAgenteBaseStrawchemy } from '../../agentes/composables/useAgenteBaseStrawchemy'
import * as queries from '../graphql/inmuebleDenominacionQueries.js'

export function useInmuebleDenominaciones(inmuebleId) {
  // Inicializamos base con la entidad 'inmuebleDenominaciones'
  // Nota: inmuebleId se pasará en el filtro al listar
  const base = useAgenteBaseStrawchemy('inmuebleDenominaciones', queries)

  // Desestructurar lo que necesitemos explícitamente o usar base.

  /**
   * Listar denominaciones de un inmueble específico
   */
  const listar = async () => {
    // Forzamos filtro para este inmueble
    return base.listar({
      inmuebleId: { eq: inmuebleId }
    })
  }

  /**
   * Crear vinculada al inmueble
   */
  const crear = async (inputData) => {
    return base.crear({
      ...inputData,
      inmuebleId // Aseguramos que se vincule
    })
  }

  // Establecer principal (simulada por ahora)
  const establecerPrincipal = async (id) => {
    // TODO: Implementar lógica idealmente en backend
    // Por ahora solo actualizamos la local a true
    return base.actualizar(id, { esPrincipal: true })
  }

  // Computed properties específicas
  const denominacionPrincipal = computed(() => {
    return base.items.value.find(d => d.esPrincipal) || null
  })

  const denominacionesAlternativas = computed(() => {
    return base.items.value.filter(d => !d.esPrincipal)
  })

  return {
    ...base,
    // Alias legacy
    denominaciones: base.items,
    denominacion: base.item,

    // Extensions
    denominacionPrincipal,
    denominacionesAlternativas,

    // Overrides
    listar,
    crear,
    establecerPrincipal
  }
}