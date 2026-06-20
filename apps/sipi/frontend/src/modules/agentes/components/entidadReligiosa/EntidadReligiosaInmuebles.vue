<!-- Inmuebles de los que la entidad religiosa es titular o usufructuaria (maestro-detalle embebido). -->
<template>
  <div>
    <h3 class="text-sm font-medium text-zinc-700 mb-2">
      Inmuebles vinculados
      <span v-if="items.length" class="text-xs text-zinc-400">({{ items.length }})</span>
    </h3>

    <div v-if="loading" class="text-xs text-zinc-400 py-2">Cargando…</div>

    <table v-else-if="items.length" class="min-w-full text-sm border border-gray-200 rounded overflow-hidden">
      <thead class="bg-gray-50">
        <tr>
          <th class="px-3 py-1.5 text-left text-xs font-medium text-gray-500">Inmueble</th>
          <th class="px-3 py-1.5 text-left text-xs font-medium text-gray-500">Localidad</th>
          <th class="px-3 py-1.5 text-left text-xs font-medium text-gray-500">Relación</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-100">
        <tr v-for="i in items" :key="i.id" @click="ir(i.id)" class="hover:bg-gray-50 cursor-pointer">
          <td class="px-3 py-1.5 text-gray-900">{{ i.nombre || 'Sin denominación' }}</td>
          <td class="px-3 py-1.5 text-gray-500">{{ i.municipio?.nombre || '—' }}</td>
          <td class="px-3 py-1.5">
            <span class="px-2 inline-flex text-xs leading-5 rounded-full bg-indigo-50 text-indigo-700">{{ i.rol }}</span>
          </td>
        </tr>
      </tbody>
    </table>

    <p v-else class="text-xs text-zinc-400 py-2">Sin inmuebles vinculados.</p>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useApolloClient } from '@vue/apollo-composable'
import { GET_INMUEBLES } from '@/modules/inmuebles/graphql/inmuebleQueries'

const props = defineProps({ entidadId: { type: String, default: null } })
const { resolveClient } = useApolloClient()
const router = useRouter()

const items = ref([])
const loading = ref(false)

// Dos consultas (titular + usufructuario) — el esquema auto-generado no soporta OR — y se fusionan.
const cargar = async (id) => {
  if (!id) { items.value = []; return }
  loading.value = true
  try {
    const c = resolveClient()
    const q = (campo) => c.query({
      query: GET_INMUEBLES,
      variables: { limit: 200, filters: [{ field: campo, operator: 'EQ', value: id }] },
      fetchPolicy: 'network-only'
    })
    const [prop, usu] = await Promise.all([q('propietarioActorId'), q('usufructuarioActorId')])
    const map = new Map()
    for (const i of (prop.data?.inmuebles?.items || [])) map.set(i.id, { ...i, rol: 'Titular' })
    for (const i of (usu.data?.inmuebles?.items || [])) {
      if (map.has(i.id)) map.get(i.id).rol = 'Titular y usufructuario'
      else map.set(i.id, { ...i, rol: 'Usufructuario' })
    }
    items.value = [...map.values()]
  } catch (e) {
    console.error('Error cargando inmuebles de la entidad:', e)
    items.value = []
  } finally {
    loading.value = false
  }
}

watch(() => props.entidadId, cargar, { immediate: true })
const ir = (id) => router.push(`/inmuebles/${id}`)
</script>
