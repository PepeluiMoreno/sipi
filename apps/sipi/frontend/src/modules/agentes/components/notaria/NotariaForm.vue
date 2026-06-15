<!-- NotariaForm.vue — formulario INLINE (no modal). Localidad vía FiltroGeografico (store). -->
<template>
  <div class="card flex flex-col min-h-0 h-full">
    <div class="shrink-0 h-12 px-4 flex items-center justify-between border-b border-zinc-200">
      <h2 class="text-sm font-semibold text-zinc-800">{{ form.id ? 'Editar' : 'Nueva' }} notaría</h2>
      <button @click="$emit('cancelar')" class="btn-ghost btn-icon" title="Cerrar">
        <UiIcon name="atras" size="sm" />
      </button>
    </div>

    <form @submit.prevent="handleSubmit" class="flex-1 min-h-0 overflow-auto p-4 space-y-4">
      <div class="field !mb-0">
        <label class="label">Ubicación *</label>
        <FiltroGeografico v-model="ubicacion" @change="onUbicacionChange" />
        <p v-if="submitted && !form.localidadId" class="text-xs text-red-600 mt-1">Seleccione el municipio.</p>
      </div>

      <div class="field !mb-0">
        <label class="label">Nombre del notario *</label>
        <input v-model="form.nombreNotario" type="text" required class="input" />
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div class="field !mb-0">
          <label class="label">Número ID *</label>
          <input v-model="form.numeroIdentificacion" type="text" required class="input" />
        </div>
        <div class="field !mb-0">
          <label class="label">Colegio profesional</label>
          <select v-model="form.colegioProfesionalId" class="select">
            <option value="">Seleccione colegio</option>
            <option v-for="c in colegiosProfesionales" :key="c.id" :value="c.id">{{ c.nombre }}</option>
          </select>
        </div>
        <div class="field !mb-0">
          <label class="label">Email</label>
          <input v-model="form.email" type="email" class="input" />
        </div>
        <div class="field !mb-0">
          <label class="label">Teléfono</label>
          <input v-model="form.telefono" type="tel" class="input" />
        </div>
        <div class="field !mb-0 col-span-2">
          <label class="label">Dirección</label>
          <input v-model="form.direccion" type="text" class="input" />
        </div>
        <div class="field !mb-0">
          <label class="label">Código Postal</label>
          <input v-model="form.codigoPostal" type="text" class="input" />
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
import { useColegioProfesional } from '../../composables/useColegioProfesional'

const props = defineProps({ notaria: Object, loading: Boolean })
const emit = defineEmits(['cancelar', 'save'])

const geografiaStore = useGeografiaStore()
const colegioService = useColegioProfesional()
const colegiosProfesionales = ref([])
colegioService.listar().then(r => { colegiosProfesionales.value = r.items })

const VACIO = () => ({
  id: null, nombreNotario: '', numeroIdentificacion: '', colegioProfesionalId: '',
  email: '', telefono: '', direccion: '', codigoPostal: '', localidadId: ''
})

const form = ref(VACIO())
const ubicacion = ref({ comunidadAutonomaId: null, provinciaId: null, municipioId: null })
const submitted = ref(false)

const onUbicacionChange = (v) => { form.value.localidadId = v?.municipioId || '' }

watch(() => props.notaria, async (n) => {
  submitted.value = false
  if (n) {
    form.value = {
      ...VACIO(),
      id: n.id,
      nombreNotario: n.nombreNotario || '',
      numeroIdentificacion: n.numeroIdentificacion || '',
      colegioProfesionalId: n.colegioProfesionalId || '',
      email: n.email || '',
      telefono: n.telefono || '',
      direccion: n.direccion || '',
      codigoPostal: n.codigoPostal || '',
      localidadId: n.localidadId || n.municipio?.id || ''
    }
    await geografiaStore.cargarDatos()
    ubicacion.value = geografiaStore.getUbicacionDeMunicipio(form.value.localidadId)
  } else {
    form.value = VACIO()
    ubicacion.value = { comunidadAutonomaId: null, provinciaId: null, municipioId: null }
  }
}, { immediate: true })

const handleSubmit = () => {
  submitted.value = true
  if (!form.value.localidadId) return
  emit('save', { ...form.value })
}
</script>
