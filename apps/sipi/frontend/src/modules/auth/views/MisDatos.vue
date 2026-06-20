<!-- MisDatos.vue — autoservicio: el usuario edita sus propios datos personales -->
<template>
  <PageShell title="Mis datos" icon="usuarios" :padded="false">
    <template #actions>
      <UiButton variant="primary" icon="check" :loading="guardando" :disabled="!form.telefonoMovil" @click="guardar">
        Guardar
      </UiButton>
    </template>

    <div class="h-full min-h-0 overflow-auto p-4">
      <div class="card p-4 max-w-3xl mx-auto">
        <div class="grid grid-cols-2 md:grid-cols-3 gap-x-3 gap-y-2.5">
          <p class="ui-section col-span-full">Identidad</p>
          <div><label class="label">Usuario</label><input :value="me.nombreUsuario" disabled class="input font-mono opacity-60" /></div>
          <div><label class="label">Nombre</label><input v-model="form.nombre" type="text" class="input" /></div>
          <div><label class="label">Apellidos</label><input v-model="form.apellidos" type="text" class="input" /></div>
          <div class="col-span-2"><label class="label">Cargo</label><input v-model="form.cargo" type="text" class="input" /></div>

          <p class="ui-section col-span-full">Contacto</p>
          <div><label class="label">Email corporativo</label><input v-model="form.emailCorporativo" type="email" class="input" /></div>
          <div><label class="label">Email personal</label><input v-model="form.emailPersonal" type="email" class="input" /></div>
          <div><label class="label">Teléfono</label><input v-model="form.telefono" type="tel" class="input" /></div>
          <div>
            <label class="label">Teléfono móvil *</label>
            <input v-model="form.telefonoMovil" type="tel" class="input" :class="{ '!border-red-500': !form.telefonoMovil }" />
          </div>

          <label class="col-span-full flex items-center gap-2 text-sm text-zinc-700 mt-2">
            <input v-model="form.aceptaNotificaciones" type="checkbox"
                   class="rounded border-zinc-300 text-primary-600 focus:ring-primary-500" />
            Autoriza recibir notificaciones de eventos de la aplicación
          </label>
        </div>

        <p v-if="mensaje" class="text-sm mt-3" :class="ok ? 'text-emerald-600' : 'text-red-600'">{{ mensaje }}</p>
      </div>
    </div>
  </PageShell>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useQuery, useMutation } from '@vue/apollo-composable'
import { MIS_DATOS_QUERY, ACTUALIZAR_MIS_DATOS_MUTATION } from '../graphql/authQueries'
import { useAuth } from '../composables/useAuth'

const { cargarUsuarioActual } = useAuth()
const { result } = useQuery(MIS_DATOS_QUERY, null, { fetchPolicy: 'network-only' })
const me = computed(() => result.value?.me ?? {})

const form = reactive({ nombre: '', apellidos: '', cargo: '', emailCorporativo: '', emailPersonal: '', telefono: '', telefonoMovil: '', aceptaNotificaciones: false })
watch(me, (u) => {
  if (!u?.id) return
  form.nombre = u.nombre || ''; form.apellidos = u.apellidos || ''; form.cargo = u.cargo || ''
  form.emailCorporativo = u.emailCorporativo || ''; form.emailPersonal = u.emailPersonal || ''
  form.telefono = u.telefono || ''; form.telefonoMovil = u.telefonoMovil || ''
  form.aceptaNotificaciones = !!u.aceptaNotificaciones
}, { immediate: true })

const { mutate: actualizar } = useMutation(ACTUALIZAR_MIS_DATOS_MUTATION)
const guardando = ref(false)
const mensaje = ref('')
const ok = ref(false)

async function guardar() {
  if (!form.telefonoMovil) return
  guardando.value = true; mensaje.value = ''
  try {
    const { data } = await actualizar({ ...form })
    ok.value = !!data?.actualizarMisDatos?.ok
    mensaje.value = ok.value ? 'Datos guardados.' : (data?.actualizarMisDatos?.mensaje || 'No se pudo guardar')
    if (ok.value) cargarUsuarioActual()  // refresca el usuario del sidebar
  } finally {
    guardando.value = false
  }
}
</script>
