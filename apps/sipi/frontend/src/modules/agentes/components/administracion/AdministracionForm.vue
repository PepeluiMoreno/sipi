<!-- AdministracionForm.vue — formulario INLINE (no modal). Geografía vía FiltroGeografico (store). -->
<template>
  <div class="card flex flex-col min-h-0 h-full">
    <div class="shrink-0 h-12 px-4 flex items-center justify-between border-b border-zinc-200">
      <h2 class="text-sm font-semibold text-zinc-800">
        {{ form.id ? 'Editar' : 'Nueva' }} administración
      </h2>
      <button @click="$emit('cancelar')" class="btn-ghost btn-icon" title="Cerrar">
        <UiIcon name="atras" size="sm" />
      </button>
    </div>

    <form @submit.prevent="handleSubmit" class="flex-1 min-h-0 overflow-auto p-4 space-y-4">
      <div class="field !mb-0">
        <label class="label">Ubicación *</label>
        <FiltroGeografico v-model="ubicacion" @change="onUbicacionChange" />
        <p v-if="submitted && !form.municipioId" class="text-xs text-red-600 mt-1">Seleccione el municipio.</p>
      </div>

      <div class="grid grid-cols-12 gap-4">
        <div class="field !mb-0 col-span-7">
          <label class="label">Nombre *</label>
          <input v-model="form.nombre" type="text" required class="input" />
        </div>
        <div class="field !mb-0 col-span-5">
          <label class="label">Ámbito *</label>
          <select v-model="form.ambito" required class="select">
            <option value="municipal">Municipal</option>
            <option value="provincial">Provincial</option>
            <option value="autonomico">Autonómico</option>
            <option value="estatal">Estatal</option>
          </select>
        </div>
        <div class="field !mb-0 col-span-7">
          <label class="label">Dirección</label>
          <input v-model="form.direccion" type="text" class="input" />
        </div>
        <div class="field !mb-0 col-span-2">
          <label class="label">C.P.</label>
          <input v-model="form.codigoPostal" type="text" maxlength="5" class="input" />
        </div>
        <div class="field !mb-0 col-span-3">
          <label class="label">Teléfono</label>
          <input v-model="form.telefono" type="tel" class="input" />
        </div>
        <div class="field !mb-0 col-span-12">
          <label class="label">Email</label>
          <input v-model="form.email" type="email" class="input" />
        </div>
      </div>

      <div class="border-t border-zinc-200 pt-4">
        <h3 class="text-sm font-medium text-zinc-700 mb-3">Responsable actual</h3>
        <div class="grid grid-cols-12 gap-4">
          <div class="field !mb-0 col-span-5">
            <label class="label">Nombre del responsable</label>
            <input v-model="form.titular.nombre" type="text" class="input" />
          </div>
          <div class="field !mb-0 col-span-3">
            <label class="label">NIF</label>
            <input v-model="form.titular.nif" type="text" maxlength="9" class="input" />
          </div>
          <div class="field !mb-0 col-span-4">
            <label class="label">Fecha desde</label>
            <input v-model="form.titular.fechaDesde" type="date" class="input" />
          </div>
          <div class="field !mb-0 col-span-9">
            <label class="label">Email</label>
            <input v-model="form.titular.email" type="email" class="input" />
          </div>
          <div class="field !mb-0 col-span-3">
            <label class="label">Teléfono</label>
            <input v-model="form.titular.telefono" type="tel" class="input" />
          </div>
        </div>
      </div>
    </form>

    <div class="shrink-0 p-3 border-t border-zinc-200 flex justify-end gap-2">
      <UiButton variant="secondary" @click="$emit('cancelar')">Cancelar</UiButton>
      <UiButton variant="primary" icon="check" :loading="loading" @click="handleSubmit">Guardar</UiButton>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import FiltroGeografico from '../../../core/components/FiltroGeografico.vue'
import { useGeografiaStore } from '@/stores/geografia'

const props = defineProps({
  administracion: Object,
  loading: Boolean
})
const emit = defineEmits(['cancelar', 'save'])

const geografiaStore = useGeografiaStore()

const VACIO = () => ({
  id: null, nombre: '', ambito: 'municipal', email: '', telefono: '', direccion: '',
  codigoPostal: '', comunidadAutonomaId: '', provinciaId: '', municipioId: '',
  titular: { nombre: '', nif: '', email: '', telefono: '', fechaDesde: '' }
})

const form = ref(VACIO())
const ubicacion = ref({ comunidadAutonomaId: null, provinciaId: null, municipioId: null })
const submitted = ref(false)

const onUbicacionChange = (v) => {
  form.value.comunidadAutonomaId = v?.comunidadAutonomaId || ''
  form.value.provinciaId = v?.provinciaId || ''
  form.value.municipioId = v?.municipioId || ''
}

watch(() => props.administracion, async (a) => {
  submitted.value = false
  if (a) {
    const t = a.titularActual || {}
    form.value = {
      ...VACIO(),
      id: a.id,
      nombre: a.nombre || '',
      ambito: a.ambito || 'municipal',
      email: a.email || '',
      telefono: a.telefono || '',
      direccion: a.direccion || '',
      codigoPostal: a.codigoPostal || '',
      comunidadAutonomaId: a.comunidadAutonomaId || '',
      provinciaId: a.provinciaId || '',
      municipioId: a.municipioId || '',
      titular: {
        nombre: t.nombre || '', nif: t.identificacion || '', email: t.email || '',
        telefono: t.telefono || '', fechaDesde: t.fechaInicio || ''
      }
    }
    await geografiaStore.cargarDatos()
    ubicacion.value = geografiaStore.getUbicacionDeMunicipio(form.value.municipioId)
  } else {
    form.value = VACIO()
    ubicacion.value = { comunidadAutonomaId: null, provinciaId: null, municipioId: null }
  }
}, { immediate: true })

const handleSubmit = () => {
  submitted.value = true
  if (!form.value.municipioId) return
  emit('save', { ...form.value })
}
</script>
