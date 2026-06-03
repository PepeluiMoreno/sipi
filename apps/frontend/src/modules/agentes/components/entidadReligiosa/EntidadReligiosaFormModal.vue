<template>
  <TransitionRoot :show="show" as="template">
    <Dialog as="div" class="relative z-50" @close="$emit('close')">
      <TransitionChild
        as="template"
        enter="ease-out duration-300"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="ease-in duration-200"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
      </TransitionChild>

      <div class="fixed inset-0 z-10 overflow-y-auto">
        <div class="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
          <TransitionChild
            as="template"
            enter="ease-out duration-300"
            enter-from="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            enter-to="opacity-100 translate-y-0 sm:scale-100"
            leave="ease-in duration-200"
            leave-from="opacity-100 translate-y-0 sm:scale-100"
            leave-to="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
          >
            <DialogPanel class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl sm:p-6">
              <div>
                <DialogTitle as="h3" class="text-lg font-semibold leading-6 text-gray-900 mb-4">
                  {{ form.id ? 'Editar' : 'Nueva' }} Entidad Religiosa
                </DialogTitle>

                <form @submit.prevent="handleSubmit" class="space-y-4">
                  <!-- Nombre -->
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                      Nombre *
                    </label>
                    <input
                      v-model="form.nombre"
                      type="text"
                      required
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>

                  <!-- NIF y Tipo -->
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">
                        NIF
                      </label>
                      <input
                        v-model="form.numeroIdentificacion"
                        type="text"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">
                        Tipo de Entidad
                      </label>
                      <select
                        v-model="form.tipoEntidadId"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      >
                        <option value="">Seleccione un tipo</option>
                        <option v-for="tipo in tiposEntidad" :key="tipo.id" :value="tipo.id">
                          {{ tipo.nombre }}
                        </option>
                      </select>
                    </div>
                  </div>

                  <!-- Email y Teléfono -->
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">
                        Email
                      </label>
                      <input
                        v-model="form.email"
                        type="email"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">
                        Teléfono
                      </label>
                      <input
                        v-model="form.telefono"
                        type="text"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      />
                    </div>
                  </div>

                  <!-- Dirección -->
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                      Dirección
                    </label>
                    <input
                      v-model="form.direccion"
                      type="text"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>

                  <!-- Localidad y CP -->
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">
                        Localidad *
                      </label>
                      <select
                        v-model="form.municipioId"
                        required
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      >
                        <option value="">Seleccione localidad</option>
                        <option v-for="localidad in localidades" :key="localidad.id" :value="localidad.id">
                          {{ localidad.nombre }}
                        </option>
                      </select>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">
                        Código Postal
                      </label>
                      <input
                        v-model="form.codigoPostal"
                        type="text"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      />
                    </div>
                  </div>

                  <!-- Fecha Fundación y Estado -->
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">
                        Fecha de Fundación
                      </label>
                      <input
                        v-model="form.fechaFundacion"
                        type="date"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">
                        Estado
                      </label>
                      <div class="flex items-center pt-2">
                        <input
                          v-model="form.activa"
                          type="checkbox"
                          class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                        />
                        <label class="ml-2 block text-sm text-gray-900">
                          Activa
                        </label>
                      </div>
                    </div>
                  </div>

                  <!-- Botones -->
                  <div class="mt-5 sm:mt-6 sm:grid sm:grid-flow-row-dense sm:grid-cols-2 sm:gap-3">
                    <button
                      type="submit"
                      :disabled="loading"
                      class="inline-flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 sm:col-start-2 disabled:opacity-50"
                    >
                      {{ loading ? 'Guardando...' : 'Guardar' }}
                    </button>
                    <button
                      type="button"
                      @click="$emit('close')"
                      class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:col-start-1 sm:mt-0"
                    >
                      Cancelar
                    </button>
                  </div>
                </form>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup>
import { ref, watch } from 'vue'
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  TransitionChild,
  TransitionRoot,
} from '@headlessui/vue'

const props = defineProps({
  show: Boolean,
  entidad: Object,
  localidades: {
    type: Array,
    default: () => []
  },
  tiposEntidad: {
    type: Array,
    default: () => []
  },
  loading: Boolean
})

const emit = defineEmits(['close', 'save'])

const form = ref({
  id: null,
  nombre: '',
  numeroIdentificacion: '',
  email: '',
  telefono: '',
  direccion: '',
  codigoPostal: '',
  municipioId: '',
  tipoEntidadId: '',
  fechaFundacion: '',
  activa: true
})

watch(() => props.entidad, (newVal) => {
  if (newVal) {
    form.value = {
      id: newVal.id,
      nombre: newVal.nombre || '',
      numeroIdentificacion: newVal.numeroIdentificacion || '',
      email: newVal.email || '',
      telefono: newVal.telefono || '',
      direccion: newVal.direccion || '',
      codigoPostal: newVal.codigoPostal || '',
      municipioId: newVal.municipioSede?.id || '',
      tipoEntidadId: newVal.tipoEntidad?.id || '',
      fechaFundacion: newVal.fechaFundacion || '',
      activa: newVal.activa ?? true
    }
  } else {
    form.value = {
      id: null,
      nombre: '',
      numeroIdentificacion: '',
      email: '',
      telefono: '',
      direccion: '',
      codigoPostal: '',
      municipioId: '',
      tipoEntidadId: '',
      fechaFundacion: '',
      activa: true
    }
  }
}, { immediate: true })

const handleSubmit = () => {
  emit('save', form.value)
}
</script>
