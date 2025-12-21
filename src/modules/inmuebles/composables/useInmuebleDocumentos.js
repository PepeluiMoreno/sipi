import { computed } from 'vue'
import { useAgenteBaseStrawchemy } from '../../agentes/composables/useAgenteBaseStrawchemy'
import * as queries from '../graphql/inmuebleDocumentoQueries.js'

export function useInmuebleDocumentos(inmuebleId) {
  // Corrected entity name 'documentos'
  const base = useAgenteBaseStrawchemy('documentos', queries)

  const listar = async () => {
    return base.listar({ inmuebleId: { eq: inmuebleId } })
  }

  const crear = async (inputData) => {
    return base.crear({ ...inputData, inmuebleId })
  }

  // Computed properties
  const documentos = computed(() => base.items.value)
  const documento = computed(() => base.item.value)

  const documentosPorTipo = computed(() => {
    return documentos.value.reduce((acc, doc) => {
      const tipo = doc.tipo || 'Sin tipo'
      if (!acc[tipo]) acc[tipo] = []
      acc[tipo].push(doc)
      return acc
    }, {})
  })

  const tiposDocumentos = computed(() => {
    return [...new Set(documentos.value.map(doc => doc.tipo).filter(Boolean))]
  })

  return {
    ...base,
    documentos,
    documento,
    documentosPorTipo,
    tiposDocumentos,
    listar,
    crear
  }
}