import { ref, computed } from 'vue'
import { useApolloClient } from '@vue/apollo-composable'
import { useTipologiaBaseStrawchemy } from './useTipologiaBaseStrawchemy'
import * as queries from '../graphql/municipiosQueries'

/**
 * Composable para gestionar Municipios
 */
export function useMunicipio() {
    const base = useTipologiaBaseStrawchemy('municipios', queries)
    const { resolveClient } = useApolloClient()

    const municipios = computed(() => base.items.value)
    const municipio = computed(() => base.item.value)

    /**
     * Listar municipios filtrados por provincia
     * @param {String} provinciaId - ID de la provincia
     */
    const listarPorProvincia = async (provinciaId) => {
        if (!provinciaId) {
            return base.listar()
        }

        base.loading.value = true
        base.error.value = null

        try {
            const client = resolveClient()
            const { data } = await client.query({
                query: queries.LISTAR_POR_PROVINCIA,
                variables: { provinciaId, limit: 500 },
                fetchPolicy: 'network-only'
            })

            base.items.value = data?.municipios || []
            base.loading.value = false
            return base.items.value
        } catch (err) {
            base.error.value = `Error al cargar municipios: ${err.message}`
            console.error('Error en listarPorProvincia:', err)
            base.loading.value = false
            throw err
        }
    }

    return {
        ...base,
        municipios,
        municipio,
        listarPorProvincia
    }
}
