import { computed } from 'vue'
import { useTipologiaBaseStrawchemy } from './useTipologiaBaseStrawchemy'
import * as queries from '../graphql/provinciasQueries'

/**
 * Composable para gestionar Provincias
 */
export function useProvincia() {
    const base = useTipologiaBaseStrawchemy('provincias', queries)

    const provincias = computed(() => base.items.value)
    const provincia = computed(() => base.item.value)

    return {
        ...base,
        provincias,
        provincia
    }
}
