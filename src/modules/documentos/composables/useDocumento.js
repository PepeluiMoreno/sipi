import { useAgenteBaseStrawchemy } from '../../agentes/composables/useAgenteBaseStrawchemy'
import * as queries from '../graphql/documentoQueries.js'

export function useDocumento() {
  const base = useAgenteBaseStrawchemy('documentos', queries)

  return {
    ...base,
    documentos: base.items,
    documento: base.item
  }
}