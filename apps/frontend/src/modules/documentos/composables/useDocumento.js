import { useAgenteBase } from '../../agentes/composables/useAgenteBase'
import * as queries from '../graphql/documentoQueries.js'

export function useDocumento() {
  const base = useAgenteBase('documentos', queries)

  return {
    ...base,
    documentos: base.items,
    documento: base.item
  }
}