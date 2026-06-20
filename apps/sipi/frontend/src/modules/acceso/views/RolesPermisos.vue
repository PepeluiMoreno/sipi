<!-- RolesPermisos.vue — matriz rol × permiso (funcionalidad). El ojo despliega las transacciones del permiso. -->
<template>
  <PageShell title="Roles y permisos" icon="config" :padded="false">
    <div class="h-full min-h-0 p-4 grid grid-cols-3 gap-4">
      <!-- Roles -->
      <UiPanel title="Roles" icon="usuarios" body-class="!p-0">
        <ul class="divide-y divide-zinc-100">
          <li v-for="r in roles" :key="r.id" @click="rolSel = r"
              :class="['px-3 py-2 cursor-pointer hover:bg-zinc-50', rolSel?.id === r.id && 'bg-primary-50']">
            <div class="flex items-center justify-between gap-2">
              <span class="font-medium text-zinc-900 text-sm">{{ r.nombre }}</span>
              <span class="badge" :class="r.sistema && 'badge-warn'">{{ r.tipo }}</span>
            </div>
            <p class="text-xs text-zinc-400 truncate">{{ r.descripcion || r.codigo }}</p>
          </li>
        </ul>
      </UiPanel>

      <!-- Permisos (funcionalidades) del rol -->
      <UiPanel :title="rolSel ? 'Permisos · ' + rolSel.nombre : 'Permisos'" icon="config" class="col-span-2">
        <template v-if="rolSel" #actions>
          <UiButton variant="ghost" :icon="todasExpandidas ? 'chevron-up' : 'chevron-down'" @click="toggleExpandAll">
            {{ todasExpandidas ? 'Colapsar todo' : 'Expandir todo' }}
          </UiButton>
        </template>
        <UiEmptyState v-if="!rolSel" icon="config" title="Selecciona un rol"
                      description="Para conceder o revocar sus permisos." />
        <template v-else>
          <p v-if="esAdmin" class="badge badge-warn mb-2">admin: acceso total (todos los permisos)</p>
          <div v-for="(funcs, modulo) in funcsPorModulo" :key="modulo" class="mb-3">
            <p class="ui-section !mt-0">{{ modulo }}</p>
            <div v-for="f in funcs" :key="f.id">
              <div class="flex items-center gap-2 text-sm text-zinc-700 px-1 py-1 rounded hover:bg-zinc-50">
                <input type="checkbox" :checked="esAdmin || tienePermiso(rolSel.id, f.id)" :disabled="esAdmin"
                       @change="togglePermiso(rolSel.id, f.id, $event.target.checked)"
                       class="rounded border-zinc-300 text-primary-600 focus:ring-primary-500" />
                <span class="flex-1 font-medium">{{ f.nombre }}</span>
                <span class="text-xs text-zinc-400">{{ (txsPorFunc[f.id] || []).length }} tx</span>
                <button type="button" class="text-zinc-400 hover:text-primary-600" :title="expandidas.has(f.id) ? 'Ocultar transacciones' : 'Ver transacciones'"
                        @click="toggleExpand(f.id)">
                  <UiIcon name="ver" class="w-4 h-4" />
                </button>
              </div>
              <ul v-show="expandidas.has(f.id)" class="ml-7 mb-1 border-l border-zinc-100">
                <li v-for="t in (txsPorFunc[f.id] || [])" :key="t.id" class="flex items-center gap-2 px-2 py-0.5 text-xs">
                  <span class="font-mono text-zinc-500 w-52 shrink-0">{{ t.codigo }}</span>
                  <span class="text-zinc-600">{{ t.nombre }}</span>
                </li>
              </ul>
            </div>
          </div>
        </template>
      </UiPanel>
    </div>
  </PageShell>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useQuery, useMutation } from '@vue/apollo-composable'
import {
  ROLES, TRANSACCIONES, FUNCIONALIDADES, FUNCIONALIDAD_TRANSACCIONES, ROL_FUNCIONALIDADES,
  CREAR_ROL_FUNCIONALIDAD, BORRAR_ROL_FUNCIONALIDAD,
} from '../graphql/accesoQueries'

const rolSel = ref(null)
const expandidas = ref(new Set())
const items = (r, key) => r?.value?.[key]?.items ?? []

const { result: rRoles } = useQuery(ROLES)
const { result: rTx } = useQuery(TRANSACCIONES)
const { result: rFunc } = useQuery(FUNCIONALIDADES)
const { result: rFT } = useQuery(FUNCIONALIDAD_TRANSACCIONES)
const { result: rRF, refetch: refetchRF } = useQuery(ROL_FUNCIONALIDADES)

const roles = computed(() => [...items(rRoles, 'roles')].sort((a, b) => (a.nombre || '').localeCompare(b.nombre || '')))
const esAdmin = computed(() => rolSel.value?.codigo === 'admin')

const funcionalidades = computed(() => [...items(rFunc, 'funcionalidades')].sort((a, b) => (a.orden ?? 0) - (b.orden ?? 0)))
const funcsPorModulo = computed(() => {
  const g = {}
  for (const f of funcionalidades.value) (g[f.modulo] ??= []).push(f)
  return g
})

const txById = computed(() => {
  const m = {}
  for (const t of items(rTx, 'transacciones')) m[t.id] = t
  return m
})
const txsPorFunc = computed(() => {
  const m = {}
  for (const ft of items(rFT, 'funcionalidadTransacciones')) {
    const t = txById.value[ft.transaccionId]
    if (t) (m[ft.funcionalidadId] ??= []).push(t)
  }
  for (const k in m) m[k].sort((a, b) => (a.codigo || '').localeCompare(b.codigo || ''))
  return m
})

const rolFuncIndex = computed(() => {
  const m = new Map()
  for (const x of items(rRF, 'rolFuncionalidades')) m.set(x.rolId + '|' + x.funcionalidadId, x.id)
  return m
})
const tienePermiso = (rid, fid) => rolFuncIndex.value.has(rid + '|' + fid)

const toggleExpand = (fid) => {
  const s = new Set(expandidas.value)
  s.has(fid) ? s.delete(fid) : s.add(fid)
  expandidas.value = s
}

// Al cambiar de rol es otra consulta: colapsar todo de nuevo.
watch(rolSel, () => { expandidas.value = new Set() })

const todasExpandidas = computed(() =>
  funcionalidades.value.length > 0 && funcionalidades.value.every(f => expandidas.value.has(f.id)))
const toggleExpandAll = () => {
  expandidas.value = todasExpandidas.value ? new Set() : new Set(funcionalidades.value.map(f => f.id))
}

const { mutate: crearRF } = useMutation(CREAR_ROL_FUNCIONALIDAD)
const { mutate: borrarRF } = useMutation(BORRAR_ROL_FUNCIONALIDAD)

async function togglePermiso(rid, fid, on) {
  if (on) await crearRF({ data: { rolId: rid, funcionalidadId: fid } })
  else { const id = rolFuncIndex.value.get(rid + '|' + fid); if (id) await borrarRF({ id }) }
  await refetchRF()
}
</script>
