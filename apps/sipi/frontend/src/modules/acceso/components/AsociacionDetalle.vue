<!-- AsociacionDetalle.vue — datos de la asociación + sus usuarios (con roles) + CRUD de usuario embebido -->
<template>
  <div class="h-full min-h-0 overflow-auto flex flex-col gap-4 pr-1">
    <!-- Datos de la asociación -->
    <UiPanel :title="esNueva ? 'Nueva asociación' : (asociacion?.nombre || 'Asociación')" icon="config" class="!h-auto shrink-0">
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div class="col-span-2"><label class="label">Nombre *</label><input v-model="form.nombre" type="text" class="input" /></div>
        <div><label class="label">Siglas</label><input v-model="form.siglas" type="text" class="input" /></div>
        <div><label class="label">CIF</label><input v-model="form.cif" type="text" class="input font-mono" /></div>
        <div class="col-span-2"><label class="label">Email</label><input v-model="form.emailCorporativo" type="email" class="input" /></div>
        <div><label class="label">Teléfono</label><input v-model="form.telefono" type="text" class="input" /></div>
        <div><label class="label">Sitio web</label><input v-model="form.sitioWeb" type="text" class="input" /></div>
        <div class="col-span-full flex items-center justify-between">
          <label class="flex items-center gap-2 text-sm text-zinc-700">
            <input v-model="form.activa" type="checkbox" class="rounded border-zinc-300 text-primary-600 focus:ring-primary-500" />
            Activa
          </label>
          <div class="flex items-center gap-2">
            <UiButton variant="primary" icon="check" :disabled="!form.nombre" @click="guardar">Guardar</UiButton>
            <UiButton v-if="!esNueva" variant="danger" icon="borrar" @click="eliminar">Eliminar</UiButton>
            <UiButton v-else variant="ghost" @click="$emit('cancelar')">Cancelar</UiButton>
          </div>
        </div>
      </div>
    </UiPanel>

    <!-- Usuarios de la asociación + sus roles (colapsable) -->
    <UiPanel v-if="!esNueva" :title="`Usuarios y roles (${usuarios.length})`" icon="usuarios" class="!h-auto shrink-0" body-class="!p-0">
      <template #actions>
        <button type="button" class="text-zinc-400 hover:text-zinc-700" :title="gridColapsado ? 'Mostrar' : 'Colapsar'"
                @click="gridColapsado = !gridColapsado">
          <UiIcon :name="gridColapsado ? 'chevron-down' : 'chevron-up'" class="w-4 h-4" />
        </button>
        <UiButton variant="primary" icon="plus" @click="$emit('nuevoUsuario')">Nuevo usuario</UiButton>
      </template>
      <table v-show="!gridColapsado" class="table">
        <thead><tr><th>Usuario</th><th class="w-32">Acceso</th><th class="w-32">Móvil</th><th class="w-28">Cargo</th><th>Roles</th></tr></thead>
        <tbody>
          <tr v-for="u in usuarios" :key="u.id" @click="$emit('selectUsuario', u)"
              :class="['cursor-pointer', usuarioActivoId === u.id && 'is-selected']">
            <td class="font-medium text-zinc-900">{{ [u.nombre, u.apellidos].filter(Boolean).join(' ') || u.nombreUsuario }}</td>
            <td class="font-mono text-xs text-zinc-600">{{ u.nombreUsuario }}</td>
            <td class="font-mono text-xs text-primary-700">{{ u.telefonoMovil || '—' }}</td>
            <td class="text-zinc-500">{{ u.cargo || '—' }}</td>
            <td>
              <span v-for="r in (rolesPorUsuario[u.id] || [])" :key="r" class="badge mr-1">{{ r }}</span>
              <span v-if="!(rolesPorUsuario[u.id] || []).length" class="text-zinc-400">sin roles</span>
            </td>
          </tr>
          <tr v-if="!usuarios.length"><td colspan="5" class="text-center text-zinc-400 py-6">Sin usuarios. Pulsa «Nuevo usuario» para añadir.</td></tr>
        </tbody>
      </table>
    </UiPanel>

    <!-- Ficha de usuario (embebida) -->
    <UsuarioDetalle v-if="!esNueva && mostrarForm" :key="usuarioActivoId || 'nuevo'" class="!h-auto shrink-0"
      :usuario="usuarioActivo" :preset-asociacion-id="asociacion.id"
      @changed="$emit('changed', $event)" @cerrar="$emit('cerrarUsuario')" />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useMutation } from '@vue/apollo-composable'
import { CREAR_ASOCIACION, ACTUALIZAR_ASOCIACION, BORRAR_ASOCIACION } from '../graphql/accesoQueries'
import UsuarioDetalle from './UsuarioDetalle.vue'
import { useConfirm } from '@/composables/useConfirm'

const confirm = useConfirm()

const props = defineProps({
  asociacion: { type: Object, default: null },         // null → nueva
  usuarios: { type: Array, default: () => [] },
  rolesPorUsuario: { type: Object, default: () => ({}) },
  usuarioActivoId: { type: String, default: null },
  nuevoUsuario: { type: Boolean, default: false },
})
const emit = defineEmits(['changed', 'selectUsuario', 'nuevoUsuario', 'cerrarUsuario', 'cancelar'])

const esNueva = computed(() => !props.asociacion)
const mostrarForm = computed(() => !!props.usuarioActivoId || props.nuevoUsuario)
const usuarioActivo = computed(() => props.usuarios.find(u => u.id === props.usuarioActivoId) ?? null)

// Al abrir una ficha (alta/edición) se colapsa el grid de usuarios para dejar sitio.
const gridColapsado = ref(false)
watch(mostrarForm, (v) => { gridColapsado.value = v }, { immediate: true })

const VACIO = () => ({ nombre: '', siglas: '', cif: '', emailCorporativo: '', telefono: '', sitioWeb: '', descripcion: '', activa: true })
const form = ref(VACIO())

watch(() => props.asociacion, (a) => {
  form.value = a ? { ...VACIO(), ...a } : VACIO()
}, { immediate: true })

const { mutate: crear } = useMutation(CREAR_ASOCIACION)
const { mutate: actualizar } = useMutation(ACTUALIZAR_ASOCIACION)
const { mutate: borrar } = useMutation(BORRAR_ASOCIACION)

const payload = () => {
  const f = form.value
  return {
    nombre: f.nombre, siglas: f.siglas || null, cif: f.cif || null,
    descripcion: f.descripcion || null, activa: !!f.activa,
    emailPersonal: null, emailCorporativo: f.emailCorporativo || null,
    telefono: f.telefono || null, telefonoMovil: null, fax: null,
    sitioWeb: f.sitioWeb || null, notas: null,
  }
}

async function guardar() {
  if (!form.value.nombre) return
  if (esNueva.value) {
    const { data } = await crear({ data: payload() })
    emit('changed', { tipo: 'asociacion', id: data?.createAsociacion?.id })
  } else {
    await actualizar({ data: { id: props.asociacion.id, ...payload() } })
    emit('changed', { tipo: 'asociacion', id: props.asociacion.id })
  }
}

async function eliminar() {
  const ok = await confirm({
    titulo: '¿Eliminar asociación?',
    mensaje: `«${props.asociacion.nombre}» y su acceso se moverán a la papelera.`,
    variante: 'critica', etiquetaConfirmar: 'Eliminar',
  })
  if (!ok) return
  await borrar({ id: props.asociacion.id })
  emit('changed', { tipo: 'none' })
}
</script>
