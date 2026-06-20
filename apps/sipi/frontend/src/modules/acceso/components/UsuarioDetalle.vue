<!-- UsuarioDetalle.vue — ficha compacta de usuario (datos + contacto + credenciales + roles) -->
<template>
  <UiPanel :title="esNuevo ? 'Nuevo usuario' : (form.nombre || form.nombreUsuario || 'Usuario')" icon="usuarios">
    <div class="grid grid-cols-2 md:grid-cols-4 gap-x-3 gap-y-2.5">
      <!-- Datos personales -->
      <p class="ui-section col-span-full">Datos personales</p>
      <div><label class="label">Nombre *</label><input v-model="form.nombre" type="text" class="input" /></div>
      <div><label class="label">Apellidos</label><input v-model="form.apellidos" type="text" class="input" /></div>
      <div><label class="label">DNI / ID</label><input v-model="form.identificacion" type="text" class="input font-mono" /></div>
      <div><label class="label">Cargo</label><input v-model="form.cargo" type="text" class="input" /></div>

      <!-- Contacto -->
      <p class="ui-section col-span-full">Contacto</p>
      <div><label class="label">Email corporativo</label><input v-model="form.emailCorporativo" type="email" class="input" /></div>
      <div><label class="label">Email personal</label><input v-model="form.emailPersonal" type="email" class="input" /></div>
      <div><label class="label">Teléfono</label><input v-model="form.telefono" type="tel" class="input" /></div>
      <div>
        <label class="label">Teléfono móvil *</label>
        <input v-model="form.telefonoMovil" type="tel" class="input" :class="{ '!border-red-500': !form.telefonoMovil }" />
      </div>

      <!-- Acceso -->
      <p class="ui-section col-span-full">Acceso</p>
      <div class="col-span-2">
        <label class="label">Asociación</label>
        <select v-model="form.asociacionId" class="select">
          <option :value="null">— Especial / sistema</option>
          <option v-for="a in asociaciones" :key="a.id" :value="a.id">{{ a.nombre }}</option>
        </select>
      </div>
      <div><label class="label">Nombre de usuario *</label><input v-model="form.nombreUsuario" type="text" class="input font-mono" /></div>
      <div>
        <label class="label">{{ esNuevo ? 'Contraseña *' : 'Nueva contraseña' }}</label>
        <div class="flex items-center gap-1">
          <input v-model="nuevaContrasena" type="password" class="input" autocomplete="new-password"
                 :placeholder="esNuevo ? '' : '(no cambiar)'" />
          <UiButton v-if="!esNuevo" variant="secondary" :disabled="!nuevaContrasena" @click="cambiarContrasena">Cambiar</UiButton>
        </div>
      </div>

      <label class="col-span-full flex items-center gap-2 text-sm text-zinc-700 mt-1">
        <input v-model="form.aceptaNotificaciones" type="checkbox"
               class="rounded border-zinc-300 text-primary-600 focus:ring-primary-500" />
        Autoriza recibir notificaciones de eventos de la aplicación
      </label>
    </div>

    <div class="flex items-center gap-2 pt-3">
      <UiButton v-if="esNuevo" variant="primary" icon="check"
                :disabled="!puedeGuardar || !nuevaContrasena" @click="registrar">Registrar</UiButton>
      <template v-else>
        <UiButton variant="primary" icon="check" :disabled="!puedeGuardar" @click="guardar">Guardar</UiButton>
        <UiButton variant="danger" icon="borrar" :disabled="usuario?.isSistema" @click="eliminar">Eliminar</UiButton>
      </template>
      <UiButton variant="ghost" class="ml-auto" @click="$emit('cerrar')">Cerrar ficha</UiButton>
    </div>
    <p v-if="error" class="text-xs text-red-600 mt-1">{{ error }}</p>

    <!-- Roles (alta: selección local; edición: asignación inmediata) -->
    <div class="pt-2 mt-2 border-t border-zinc-100">
      <p class="ui-section !mt-0">Roles</p>
      <div class="grid grid-cols-2 md:grid-cols-3 gap-x-3">
        <label v-for="r in roles" :key="r.id" class="flex items-center gap-2 text-sm text-zinc-700 px-1 py-1 rounded hover:bg-zinc-50">
          <input type="checkbox"
                 :checked="esNuevo ? rolesNuevos.has(r.id) : tieneRol(usuario.id, r.id)"
                 @change="onToggleRol(r.id, $event.target.checked)"
                 class="rounded border-zinc-300 text-primary-600 focus:ring-primary-500" />
          <span class="font-medium truncate">{{ r.nombre }}</span>
        </label>
      </div>
    </div>
  </UiPanel>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useQuery, useMutation } from '@vue/apollo-composable'
import {
  ROLES, USUARIO_ROLES, ASOCIACIONES,
  REGISTRAR_USUARIO, ESTABLECER_CONTRASENA, ACTUALIZAR_USUARIO, BORRAR_USUARIO,
  CREAR_USUARIO_ROL, BORRAR_USUARIO_ROL,
} from '../graphql/accesoQueries'
import { useConfirm } from '@/composables/useConfirm'

const confirm = useConfirm()

const props = defineProps({
  usuario: { type: Object, default: null },          // null → alta
  presetAsociacionId: { type: String, default: null },
  presetSistema: { type: Boolean, default: false },
})
const emit = defineEmits(['changed', 'cerrar'])

const esNuevo = computed(() => !props.usuario)
const VACIO = () => ({ asociacionId: props.presetSistema ? null : (props.presetAsociacionId ?? null),
                      nombre: '', apellidos: '', identificacion: '', cargo: '', emailCorporativo: '',
                      emailPersonal: '', telefono: '', telefonoMovil: '', nombreUsuario: '', aceptaNotificaciones: false })
const form = ref(VACIO())
const nuevaContrasena = ref('')
const error = ref('')
const rolesNuevos = ref(new Set())   // selección de roles en el alta (aún sin id de usuario)

// Móvil requerido.
const puedeGuardar = computed(() => !!form.value.nombre && !!form.value.nombreUsuario && !!form.value.telefonoMovil)

watch(() => props.usuario, (u) => {
  nuevaContrasena.value = ''; error.value = ''; rolesNuevos.value = new Set()
  form.value = u
    ? { asociacionId: u.asociacionId ?? null, nombre: u.nombre || '', apellidos: u.apellidos || '',
        identificacion: u.identificacion || '', cargo: u.cargo || '', emailCorporativo: u.emailCorporativo || '',
        emailPersonal: u.emailPersonal || '', telefono: u.telefono || '', telefonoMovil: u.telefonoMovil || '',
        nombreUsuario: u.nombreUsuario || '', aceptaNotificaciones: !!u.aceptaNotificaciones }
    : VACIO()
}, { immediate: true })

const { result: rRoles } = useQuery(ROLES)
const { result: rAsoc } = useQuery(ASOCIACIONES)
const { result: rUsuRol, refetch: refetchUsuRol } = useQuery(USUARIO_ROLES)
const roles = computed(() => [...(rRoles.value?.roles?.items ?? [])].sort((a, b) => (a.nombre || '').localeCompare(b.nombre || '')))
const asociaciones = computed(() => rAsoc.value?.asociaciones?.items ?? [])
const usuRolIndex = computed(() => {
  const m = new Map()
  for (const x of (rUsuRol.value?.usuarioRoles?.items ?? [])) m.set(x.usuarioId + '|' + x.rolId, x.id)
  return m
})
const tieneRol = (uid, rid) => usuRolIndex.value.has(uid + '|' + rid)

const { mutate: registrarUsuario } = useMutation(REGISTRAR_USUARIO)
const { mutate: establecerContrasena } = useMutation(ESTABLECER_CONTRASENA)
const { mutate: actualizarUsuario } = useMutation(ACTUALIZAR_USUARIO)
const { mutate: borrarUsuario } = useMutation(BORRAR_USUARIO)
const { mutate: crearUsuRol } = useMutation(CREAR_USUARIO_ROL)
const { mutate: borrarUsuRol } = useMutation(BORRAR_USUARIO_ROL)

async function registrar() {
  error.value = ''
  const f = form.value
  const { data } = await registrarUsuario({
    nombreUsuario: f.nombreUsuario, contrasena: nuevaContrasena.value, nombre: f.nombre,
    asociacionId: f.asociacionId || null, apellidos: f.apellidos || null,
    identificacion: f.identificacion || null, emailCorporativo: f.emailCorporativo || null,
    emailPersonal: f.emailPersonal || null, telefono: f.telefono || null, telefonoMovil: f.telefonoMovil || null,
    cargo: f.cargo || null, aceptaNotificaciones: !!f.aceptaNotificaciones, isSistema: !f.asociacionId,
  })
  const res = data?.registrarUsuario
  if (!res?.ok) { error.value = res?.mensaje || 'No se pudo registrar'; return }
  // Asignar los roles marcados en el alta.
  for (const rid of rolesNuevos.value) {
    await crearUsuRol({ data: { usuarioId: res.id, rolId: rid, fechaAsignacion: null, asignadoPor: null } })
  }
  await refetchUsuRol()
  emit('changed', { tipo: 'usuario', id: res.id })
  nuevaContrasena.value = ''
}

async function guardar() {
  error.value = ''
  const f = form.value
  await actualizarUsuario({ data: {
    id: props.usuario.id, nombreUsuario: f.nombreUsuario || null, hashedContrasena: null, emailVerificado: null, isSistema: null,
    asociacionId: f.asociacionId || null, cargo: f.cargo || null, tipoIdentificacion: null,
    identificacion: f.identificacion || null, nombre: f.nombre || null, apellidos: f.apellidos || null,
    identificacionExtranjera: null, emailPersonal: f.emailPersonal || null, emailCorporativo: f.emailCorporativo || null,
    telefono: f.telefono || null, telefonoMovil: f.telefonoMovil || null, fax: null, sitioWeb: null, notas: null,
    aceptaNotificaciones: !!f.aceptaNotificaciones,
  } })
  emit('changed', { tipo: 'usuario', id: props.usuario.id })
}

async function cambiarContrasena() {
  if (!nuevaContrasena.value || !props.usuario) return
  const { data } = await establecerContrasena({ usuarioId: props.usuario.id, contrasena: nuevaContrasena.value })
  if (data?.establecerContrasena?.ok) { nuevaContrasena.value = ''; error.value = '' }
  else error.value = data?.establecerContrasena?.mensaje || 'No se pudo cambiar la contraseña'
}

async function eliminar() {
  const ok = await confirm({
    titulo: '¿Eliminar usuario?',
    mensaje: `«${form.value.nombre || form.value.nombreUsuario}» se moverá a la papelera; podrás restaurarlo desde ahí.`,
    variante: 'critica', etiquetaConfirmar: 'Eliminar',
  })
  if (!ok) return
  await borrarUsuario({ id: props.usuario.id })
  emit('changed', { tipo: 'usuario-borrado', asociacionId: props.usuario.asociacionId })
}

async function toggleRol(uid, rid, on) {
  if (on) await crearUsuRol({ data: { usuarioId: uid, rolId: rid, fechaAsignacion: null, asignadoPor: null } })
  else { const id = usuRolIndex.value.get(uid + '|' + rid); if (id) await borrarUsuRol({ id }) }
  await refetchUsuRol()
  emit('changed', { silencioso: true })
}

function toggleRolNuevo(rid, on) {
  const s = new Set(rolesNuevos.value)
  on ? s.add(rid) : s.delete(rid)
  rolesNuevos.value = s
}
function onToggleRol(rid, on) {
  if (esNuevo.value) toggleRolNuevo(rid, on)
  else toggleRol(props.usuario.id, rid, on)
}
</script>
