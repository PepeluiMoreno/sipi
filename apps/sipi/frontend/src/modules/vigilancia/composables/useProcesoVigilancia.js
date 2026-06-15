import { useAgenteBase } from '../../agentes/composables/useAgenteBase'
import { LISTAR, CREAR, ACTUALIZAR, ELIMINAR } from '../graphql/vigilanciaQueries'

// Reutiliza el composable CRUD genérico (DRY). Misma API que los agentes:
//   { items, loading, hasMore, listar, crear, actualizar, eliminar, cargarMas… }
export function useProcesoVigilancia() {
  return useAgenteBase('procesosVigilancia', { LISTAR, CREAR, ACTUALIZAR, ELIMINAR })
}
