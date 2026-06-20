<!-- Papelera.vue — registros eliminados (soft-delete): restaurar o purgar definitivamente -->
<template>
  <PageShell title="Papelera" icon="borrar" :padded="false">
    <template #actions>
      <select v-model="entidadKey" class="select !h-8 !py-0 text-sm w-56">
        <option v-for="e in ENTIDADES" :key="e.key" :value="e.key">{{ e.label }}</option>
      </select>
    </template>

    <div class="h-full min-h-0 p-4">
      <UiPanel :title="`${entidad.label} eliminados (${items.length})`" icon="borrar" body-class="!p-0">
        <table class="table">
          <thead><tr><th>Elemento</th><th class="w-44">Eliminado</th><th class="w-56 text-right pr-3">Acciones</th></tr></thead>
          <tbody>
            <tr v-for="it in items" :key="it.id">
              <td class="font-medium text-zinc-900">{{ entidad.etiqueta(it) || it.id }}</td>
              <td class="text-zinc-500 text-xs">{{ formatoFecha(it.deletedAt) }}</td>
              <td class="text-right pr-2">
                <UiButton variant="secondary" icon="refrescar" class="mr-1" @click="restaurar(it)">Restaurar</UiButton>
                <UiButton variant="danger" icon="borrar" @click="purgar(it)">Eliminar def.</UiButton>
              </td>
            </tr>
            <tr v-if="!items.length"><td colspan="3" class="text-center text-zinc-400 py-8">Nada en la papelera</td></tr>
          </tbody>
        </table>
      </UiPanel>
    </div>
  </PageShell>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useApolloClient } from '@vue/apollo-composable'
import { gql } from '@apollo/client/core'
import { useConfirm } from '@/composables/useConfirm'

const ENTIDADES = [
  { key: 'asociaciones', label: 'Asociaciones', tipo: 'Asociacion', campos: 'nombre siglas', etiqueta: (i) => i.nombre },
  { key: 'usuarios', label: 'Usuarios', tipo: 'Usuario', campos: 'nombre apellidos nombreUsuario', etiqueta: (i) => [i.nombre, i.apellidos].filter(Boolean).join(' ') || i.nombreUsuario },
  { key: 'administraciones', label: 'Administraciones', tipo: 'Administracion', campos: 'nombre', etiqueta: (i) => i.nombre },
  { key: 'notarias', label: 'Notarías', tipo: 'Notaria', campos: 'nombre codigoOficial', etiqueta: (i) => i.nombre },
  { key: 'registrosPropiedades', label: 'Registros de la propiedad', tipo: 'RegistroPropiedad', campos: 'nombre', etiqueta: (i) => i.nombre },
  { key: 'inmuebles', label: 'Inmuebles', tipo: 'Inmueble', campos: 'nombre', etiqueta: (i) => i.nombre },
  { key: 'entidadesReligiosas', label: 'Entidades religiosas', tipo: 'EntidadReligiosa', campos: 'nombre', etiqueta: (i) => i.nombre },
  { key: 'documentos', label: 'Documentos', tipo: 'Documento', campos: 'nombreArchivo descripcion', etiqueta: (i) => i.nombreArchivo || i.descripcion },
]

const { resolveClient } = useApolloClient()
const confirm = useConfirm()

const entidadKey = ref('asociaciones')
const entidad = computed(() => ENTIDADES.find(e => e.key === entidadKey.value))
const items = ref([])

const formatoFecha = (s) => s ? new Date(s).toLocaleString('es-ES') : '—'

async function cargar() {
  const e = entidad.value
  const q = gql(`query Papelera { ${e.key}(eliminados: true, limit: 500) { items { id ${e.campos} deletedAt } total } }`)
  try {
    const { data } = await resolveClient().query({ query: q, fetchPolicy: 'network-only' })
    items.value = data?.[e.key]?.items ?? []
  } catch (err) {
    console.error('[Papelera]', err.message); items.value = []
  }
}
watch(entidadKey, cargar, { immediate: true })

async function restaurar(it) {
  const e = entidad.value
  await resolveClient().mutate({ mutation: gql(`mutation R($id: ID!){ restaurar${e.tipo}(id: $id) }`), variables: { id: it.id } })
  await cargar()
}

async function purgar(it) {
  const e = entidad.value
  const ok = await confirm({
    titulo: 'Eliminar definitivamente',
    mensaje: `«${e.etiqueta(it) || it.id}» se borrará para siempre. Esta acción no se puede deshacer.`,
    variante: 'critica', etiquetaConfirmar: 'Eliminar definitivamente',
  })
  if (!ok) return
  await resolveClient().mutate({ mutation: gql(`mutation P($id: ID!){ purgar${e.tipo}(id: $id) }`), variables: { id: it.id } })
  await cargar()
}
</script>
