<!-- EntidadReligiosaForm.vue — formulario INLINE (no modal). Estándar: edición en panel embebido. -->
<template>
  <div class="card flex flex-col min-h-0 h-full">
    <div class="shrink-0 h-12 px-4 flex items-center justify-between border-b border-zinc-200">
      <h2 class="text-sm font-semibold text-zinc-800">{{ titulo }}</h2>
      <button @click="$emit('cancelar')" class="btn-ghost btn-icon" title="Cerrar">
        <UiIcon name="atras" size="sm" />
      </button>
    </div>

    <form @submit.prevent="handleSubmit" class="flex-1 min-h-0 overflow-auto p-4">
      <fieldset :disabled="readonly" class="space-y-4">
      <div class="field !mb-0">
        <label class="label">Nombre *</label>
        <input v-model="form.nombre" type="text" required class="input" />
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div class="field !mb-0">
          <label class="label">NIF</label>
          <input v-model="form.numeroIdentificacion" type="text" class="input" />
        </div>
        <div class="field !mb-0">
          <label class="label">Tipo de entidad</label>
          <select v-model="form.tipoEntidadId" class="select">
            <option value="">Seleccione un tipo</option>
            <option v-for="tipo in tiposEntidad" :key="tipo.id" :value="tipo.id">{{ tipo.nombre }}</option>
          </select>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div class="field !mb-0">
          <label class="label">Email</label>
          <input v-model="form.email" type="email" class="input" />
        </div>
        <div class="field !mb-0">
          <label class="label">Teléfono</label>
          <input v-model="form.telefono" type="text" class="input" />
        </div>
      </div>

      <div class="field !mb-0">
        <label class="label">Localidad *</label>
        <FiltroGeografico v-model="ubicacion" @change="onUbicacionChange" />
        <p v-if="submitted && !form.municipioId" class="text-xs text-red-600 mt-1">Seleccione el municipio.</p>
      </div>

      <div class="field !mb-0">
        <label class="label">Estado</label>
        <label class="flex items-center gap-2 text-sm text-zinc-700">
          <input v-model="form.activa" type="checkbox"
                 class="rounded border-zinc-300 text-primary-600 focus:ring-primary-500" />
          Activa
        </label>
      </div>
      </fieldset>

      <!-- Maestro-detalle: inmuebles de los que es titular/usufructuario (solo registro existente) -->
      <div v-if="form.id" class="border-t border-zinc-200 pt-4 mt-4">
        <EntidadReligiosaInmuebles :entidad-id="form.id" />
      </div>
    </form>

    <div class="shrink-0 p-3 border-t border-zinc-200 flex justify-end gap-2">
      <UiButton variant="secondary" @click="$emit('cancelar')">{{ readonly ? 'Cerrar' : 'Cancelar' }}</UiButton>
      <UiButton v-if="readonly" variant="primary" icon="editar" @click="$emit('editar')">Editar</UiButton>
      <UiButton v-else variant="primary" icon="check" :loading="loading" @click="handleSubmit">Guardar</UiButton>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import FiltroGeografico from '../../../core/components/FiltroGeografico.vue'
import EntidadReligiosaInmuebles from './EntidadReligiosaInmuebles.vue'
import { useGeografiaStore } from '@/stores/geografia'

const props = defineProps({
  entidad: Object,
  tiposEntidad: { type: Array, default: () => [] },
  loading: Boolean,
  readonly: { type: Boolean, default: false }
})
const emit = defineEmits(['cancelar', 'save', 'editar'])

const titulo = computed(() =>
  props.readonly ? 'Consultar entidad religiosa'
    : (form.value.id ? 'Editar entidad religiosa' : 'Nueva entidad religiosa'))

const geografiaStore = useGeografiaStore()

const VACIO = () => ({
  id: null, nombre: '', numeroIdentificacion: '', email: '', telefono: '',
  direccion: '', codigoPostal: '', municipioId: '', tipoEntidadId: '', fechaFundacion: '', activa: true
})

const form = ref(VACIO())
const ubicacion = ref({ comunidadAutonomaId: null, provinciaId: null, municipioId: null })
const submitted = ref(false)

const onUbicacionChange = (val) => { form.value.municipioId = val?.municipioId || '' }

watch(() => props.entidad, async (newVal) => {
  submitted.value = false
  if (newVal) {
    form.value = {
      ...VACIO(),
      id: newVal.id,
      nombre: newVal.nombre || '',
      numeroIdentificacion: newVal.numeroIdentificacion || newVal.nif || '',
      email: newVal.email || '',
      telefono: newVal.telefono || '',
      direccion: newVal.direccion || '',
      codigoPostal: newVal.codigoPostal || '',
      municipioId: newVal.municipioId || newVal.municipioSede?.id || '',
      tipoEntidadId: newVal.tipoEntidadId || newVal.tipoEntidad?.id || '',
      fechaFundacion: newVal.fechaFundacion || '',
      activa: newVal.activa ?? true
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
  emit('save', form.value)
}
</script>
