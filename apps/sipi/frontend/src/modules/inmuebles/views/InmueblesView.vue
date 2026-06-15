<!-- InmueblesView — lista de inmuebles con el FilterSidebar VERTICAL estándar (filtrado real server-side). -->
<template>
  <div class="flex h-full min-h-0 bg-zinc-100">
    <FilterSidebar
      con-geografia
      busqueda-placeholder="Nombre, dirección…"
      :facetas="facetas"
      @change="onFiltros"
    />

    <div class="flex-1 flex flex-col min-h-0 overflow-hidden">
      <InmuebleToolbar
        v-model:view="vistaActiva"
        :total="total"
        @nuevo="irANuevo"
      />

      <div class="flex-1 min-h-0 overflow-auto p-4">
        <UiEmptyState v-if="loading" loading loading-text="Cargando inmuebles…" />

        <UiEmptyState
          v-else-if="isEmpty"
          icon="inmueble"
          title="No hay inmuebles"
          description="Aún no hay inmuebles que coincidan con los filtros."
        />

        <div v-else-if="vistaActiva === 'cards'"
             class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <InmuebleCard
            v-for="inmueble in inmuebles"
            :key="inmueble.id"
            :inmueble="inmueble"
            @click="irADetalle(inmueble.id)"
          />
        </div>

        <InmuebleMapa
          v-else-if="vistaActiva === 'mapa'"
          :inmuebles="inmuebles"
          @select="irADetalle"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useApolloClient } from '@vue/apollo-composable'
import { gql } from '@apollo/client/core'
import { useInmueble } from '../composables/useInmueble'
import FilterSidebar from '@/modules/core/components/FilterSidebar.vue'
import InmuebleToolbar from '../components/InmuebleToolbar.vue'
import InmuebleCard from '../components/InmuebleCard.vue'
import InmuebleMapa from '../components/InmuebleMapa.vue'

const router = useRouter()
const { resolveClient } = useApolloClient()
const vistaActiva = ref('cards')
const total = ref(0)
const facetas = ref([])

const { inmuebles, loading, isEmpty, listar } = useInmueble()

const cargar = async (f = {}) => {
  const r = await listar(f)
  total.value = r?.total ?? 0
}
const onFiltros = (f) => cargar(f)

const irADetalle = (id) => router.push(`/inmuebles/${id}`)
const irANuevo = () => router.push('/inmuebles/nuevo')

const LISTAR_TIPOS = gql`query ListarTiposInmueble { tiposInmueble(limit: 100) { items { id nombre } } }`

onMounted(async () => {
  try {
    const { data } = await resolveClient().query({ query: LISTAR_TIPOS, fetchPolicy: 'cache-first' })
    const tipos = data?.tiposInmueble?.items ?? []
    facetas.value = [{ key: 'tipoInmuebleId', label: 'Tipo', tipo: 'checkboxes', opciones: tipos }]
  } catch (e) {
    console.error('Error cargando tipos de inmueble:', e)
  }
  await cargar()
})
</script>
