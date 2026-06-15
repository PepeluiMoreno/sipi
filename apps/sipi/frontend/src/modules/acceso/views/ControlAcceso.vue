<!-- ControlAcceso.vue — máster-detalle: tipo de usuario + árbol Asociación→Usuario (navegación) + detalle -->
<template>
  <PageShell title="Control de acceso" icon="usuarios" :padded="false">
    <template #actions>
      <div class="flex items-center bg-zinc-100 rounded p-0.5">
        <button v-for="t in tipos" :key="t.id" @click="setTipo(t.id)"
                :class="['btn-icon px-2.5 text-sm font-medium', tipo === t.id ? 'bg-white text-zinc-900 shadow-sm rounded' : 'text-zinc-500 hover:text-zinc-800']">
          {{ t.label }}
        </button>
      </div>
    </template>

    <div class="h-full min-h-0 p-4 grid grid-cols-4 gap-4">
      <!-- ===== Árbol de navegación ===== -->
      <UiPanel :title="tipo === 'sistema' ? 'Usuarios de sistema' : 'Asociaciones'" icon="lista" body-class="!p-1" class="col-span-1">
        <template #actions>
          <UiButton variant="primary" icon="plus" @click="nuevoTop">{{ tipo === 'sistema' ? 'Usuario' : 'Asociación' }}</UiButton>
        </template>

        <!-- Organizaciones adscritas: Asociación ▸ usuarios -->
        <ul v-if="tipo === 'organizaciones'" class="text-sm">
          <li v-for="a in asociaciones" :key="a.id">
            <div @click="selAsoc(a)"
                 :class="['group flex items-center gap-1 px-2 py-1.5 rounded cursor-pointer hover:bg-zinc-50', esSel('asociacion', a.id) && 'bg-primary-50']">
              <UiIcon :name="expanded.has(a.id) ? 'chevron-down' : 'chevron-right'" class="w-4 h-4 text-zinc-400 shrink-0" />
              <span class="font-medium text-zinc-800 truncate flex-1">{{ a.siglas || a.nombre }}</span>
              <span class="text-xs text-zinc-400">{{ (usuariosPorAsoc[a.id] || []).length }}</span>
              <button type="button" title="Dar de alta usuario en esta asociación"
                      class="opacity-0 group-hover:opacity-100 text-zinc-400 hover:text-primary-600 shrink-0"
                      @click.stop="nuevoUsuarioEn(a)">
                <UiIcon name="plus" class="w-4 h-4" />
              </button>
            </div>
            <ul v-show="expanded.has(a.id)" class="ml-5 border-l border-zinc-100">
              <li v-for="u in (usuariosPorAsoc[a.id] || [])" :key="u.id" @click="selUsuario(u)"
                  :class="['px-2 py-1 rounded cursor-pointer hover:bg-zinc-50 truncate', esSel('usuario', u.id) && 'bg-primary-50 text-primary-700']">
                {{ [u.nombre, u.apellidos].filter(Boolean).join(' ') || u.nombreUsuario }}
              </li>
              <li v-if="!(usuariosPorAsoc[a.id] || []).length" class="px-2 py-1 text-xs text-zinc-400">sin usuarios</li>
            </ul>
          </li>
          <li v-if="!asociaciones.length" class="px-2 py-4 text-center text-zinc-400">Sin asociaciones</li>
        </ul>

        <!-- Sistema: usuarios especiales (planos) -->
        <ul v-else class="text-sm">
          <li v-for="u in usuariosSistema" :key="u.id" @click="selUsuario(u)"
              :class="['flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer hover:bg-zinc-50', esSel('usuario', u.id) && 'bg-primary-50 text-primary-700']">
            <UiIcon name="config" class="w-4 h-4 text-zinc-400 shrink-0" />
            <span class="truncate flex-1">{{ u.nombre || u.nombreUsuario }}</span>
            <span class="badge badge-warn">sistema</span>
          </li>
          <li v-if="!usuariosSistema.length" class="px-2 py-4 text-center text-zinc-400">Sin usuarios de sistema</li>
        </ul>
      </UiPanel>

      <!-- ===== Detalle ===== -->
      <div class="col-span-3 min-h-0">
        <AsociacionDetalle v-if="sel.kind === 'asociacion' || sel.kind === 'asociacion-nueva'" :key="detKey"
          :asociacion="asocActual" :usuarios="usuariosPorAsoc[sel.id] || []" :roles-por-usuario="rolesPorUsuario"
          :usuario-activo-id="sel.usuarioId || null" :nuevo-usuario="!!sel.nuevoUsuario"
          @changed="onChanged" @select-usuario="selUsuarioEnAsoc" @nuevo-usuario="nuevoUsuarioDeAsoc"
          @cerrar-usuario="cerrarUsuario" @cancelar="sel = { kind: null }" />

        <UsuarioDetalle v-else-if="sel.kind === 'usuario' || sel.kind === 'usuario-nuevo'" :key="detKey"
          :usuario="usuarioActual" :preset-asociacion-id="sel.asociacionId" :preset-sistema="!!sel.sistema"
          @changed="onChanged" @cerrar="sel = { kind: null }" />

        <div v-else class="h-full flex items-center justify-center">
          <UiEmptyState icon="usuarios" title="Selecciona en el árbol"
            :description="tipo === 'sistema' ? 'Un usuario de sistema, o crea uno.' : 'Una asociación o un usuario.'" />
        </div>
      </div>
    </div>
  </PageShell>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useQuery } from '@vue/apollo-composable'
import { ASOCIACIONES, USUARIOS, ROLES, USUARIO_ROLES } from '../graphql/accesoQueries'
import AsociacionDetalle from '../components/AsociacionDetalle.vue'
import UsuarioDetalle from '../components/UsuarioDetalle.vue'

const tipos = [
  { id: 'sistema', label: 'Sistema' },
  { id: 'organizaciones', label: 'Organizaciones adscritas' },
]
const tipo = ref('organizaciones')
const sel = ref({ kind: null })
const expanded = ref(new Set())

const { result: rAsoc, refetch: refetchAsoc } = useQuery(ASOCIACIONES)
const { result: rUsuarios, refetch: refetchUsuarios } = useQuery(USUARIOS)
const { result: rRoles } = useQuery(ROLES)
const { result: rUsuRol, refetch: refetchUsuRol } = useQuery(USUARIO_ROLES)

const asociaciones = computed(() => [...(rAsoc.value?.asociaciones?.items ?? [])].sort((a, b) => (a.nombre || '').localeCompare(b.nombre || '')))
const usuarios = computed(() => rUsuarios.value?.usuarios?.items ?? [])
const usuariosPorAsoc = computed(() => {
  const m = {}
  for (const u of usuarios.value) if (u.asociacionId) (m[u.asociacionId] ??= []).push(u)
  return m
})
const usuariosSistema = computed(() => usuarios.value.filter(u => u.isSistema || !u.asociacionId))

const rolesById = computed(() => {
  const m = {}
  for (const r of (rRoles.value?.roles?.items ?? [])) m[r.id] = r
  return m
})
const rolesPorUsuario = computed(() => {
  const m = {}
  for (const x of (rUsuRol.value?.usuarioRoles?.items ?? [])) {
    const r = rolesById.value[x.rolId]
    if (r) (m[x.usuarioId] ??= []).push(r.codigo || r.nombre)
  }
  return m
})

const asocActual = computed(() => sel.value.kind === 'asociacion' ? asociaciones.value.find(a => a.id === sel.value.id) ?? null : null)
const usuarioActual = computed(() => sel.value.kind === 'usuario' ? usuarios.value.find(u => u.id === sel.value.id) ?? null : null)
// La key NO incluye usuarioId: al cambiar el usuario activo no remonta la asociación.
const detKey = computed(() => `${sel.value.kind}:${sel.value.id ?? sel.value.asociacionId ?? 'nuevo'}`)

const esSel = (kind, id) => sel.value.kind === kind && sel.value.id === id

function setTipo(t) { tipo.value = t; sel.value = { kind: null } }
function selAsoc(a) { sel.value = { kind: 'asociacion', id: a.id }; expanded.value = new Set([...expanded.value, a.id]) }
// Click en un usuario del árbol: si es de una asociación, lo edita embebido en ella; si es de sistema, ficha aparte.
function selUsuario(u) {
  if (u.asociacionId) { sel.value = { kind: 'asociacion', id: u.asociacionId, usuarioId: u.id }; expanded.value = new Set([...expanded.value, u.asociacionId]) }
  else sel.value = { kind: 'usuario', id: u.id }
}
function nuevoTop() {
  sel.value = tipo.value === 'sistema' ? { kind: 'usuario-nuevo', sistema: true } : { kind: 'asociacion-nueva' }
}
// Selección de usuario dentro del detalle de la asociación (embebido).
function selUsuarioEnAsoc(u) { sel.value = { kind: 'asociacion', id: sel.value.id, usuarioId: u.id } }
function nuevoUsuarioDeAsoc() {
  if (sel.value.kind === 'asociacion') sel.value = { kind: 'asociacion', id: sel.value.id, nuevoUsuario: true }
}
function cerrarUsuario() { if (sel.value.kind === 'asociacion') sel.value = { kind: 'asociacion', id: sel.value.id } }
function nuevoUsuarioEn(a) {
  expanded.value = new Set([...expanded.value, a.id])
  sel.value = { kind: 'asociacion', id: a.id, nuevoUsuario: true }
}

async function onChanged(p) {
  await Promise.all([refetchAsoc(), refetchUsuarios(), refetchUsuRol()])
  if (!p || p.silencioso) return
  if (p.tipo === 'usuario' && p.id) {
    sel.value = sel.value.kind === 'asociacion'
      ? { kind: 'asociacion', id: sel.value.id, usuarioId: p.id }
      : { kind: 'usuario', id: p.id }
  } else if (p.tipo === 'usuario-borrado') {
    sel.value = p.asociacionId ? { kind: 'asociacion', id: p.asociacionId } : { kind: null }
  } else if (p.tipo === 'asociacion' && p.id) {
    sel.value = { kind: 'asociacion', id: p.id }; expanded.value = new Set([...expanded.value, p.id])
  } else if (p.tipo === 'none') {
    sel.value = { kind: null }
  }
}
</script>
