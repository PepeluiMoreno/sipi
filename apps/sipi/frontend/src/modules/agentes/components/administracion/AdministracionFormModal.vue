<template>
  <div v-if="show" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-screen overflow-y-auto">
      <!-- Header -->
      <div class="p-6 border-b border-gray-200 flex justify-between items-center">
        <h2 class="text-xl font-semibold text-gray-900">
          {{ isEdit ? 'Editar Administración' : 'Nueva Administración' }}
        </h2>
        <button 
          @click="close"
          class="p-2 text-gray-400 hover:text-gray-600"
        >
          <XMarkIcon class="w-5 h-5" />
        </button>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="p-6 space-y-6">
        <!-- Geografía en una línea -->
        <div class="grid grid-cols-12 gap-4">
          <!-- Comunidad Autónoma -->
          <div class="col-span-4">
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Comunidad Autónoma
            </label>
            <select
              v-model="form.comunidadAutonomaId"
              @change="onComunidadChange"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Seleccione comunidad</option>
              <option
                v-for="ccaa in comunidadesAutonomas"
                :key="ccaa.id"
                :value="ccaa.id"
              >
                {{ ccaa.nombre }}
              </option>
            </select>
          </div>

          <!-- Provincia -->
          <div class="col-span-3">
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Provincia
            </label>
            <select
              v-model="form.provinciaId"
              @change="onProvinciaChange"
              :disabled="!form.comunidadAutonomaId"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="">Seleccione provincia</option>
              <option
                v-for="provincia in provinciasFiltradas"
                :key="provincia.id"
                :value="provincia.id"
              >
                {{ provincia.nombre }}
              </option>
            </select>
          </div>

          <!-- Localidad/Municipio -->
          <div class="col-span-5">
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Localidad
            </label>
            <select
              v-model="form.municipioId"
              :disabled="!form.provinciaId"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              <option value="">Seleccione localidad</option>
              <option
                v-for="municipio in municipiosFiltrados"
                :key="municipio.id"
                :value="municipio.id"
              >
                {{ municipio.nombre }}
              </option>
            </select>
          </div>
        </div>

        <!-- Datos de la Administración -->
        <div class="border-t pt-4">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Datos de la Administración</h3>
          <div class="grid grid-cols-12 gap-4">
            <!-- Nombre -->
            <div class="col-span-7">
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

            <!-- Ámbito -->
            <div class="col-span-5">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Ámbito *
              </label>
              <select
                v-model="form.ambito"
                required
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="municipal">Municipal</option>
                <option value="provincial">Provincial</option>
                <option value="autonomico">Autonómico</option>
                <option value="estatal">Estatal</option>
              </select>
            </div>

            <!-- Dirección -->
            <div class="col-span-7">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Dirección
              </label>
              <input
                v-model="form.direccion"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <!-- Código Postal -->
            <div class="col-span-2">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                C.P.
              </label>
              <input
                v-model="form.codigoPostal"
                type="text"
                maxlength="5"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <!-- Teléfono de la Administración -->
            <div class="col-span-3">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Teléfono
              </label>
              <input
                v-model="form.telefono"
                type="tel"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <!-- Email de la Administración -->
            <div class="col-span-12">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                v-model="form.email"
                type="email"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>
        </div>

        <!-- Datos del Responsable/Titular -->
        <div class="border-t pt-4">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Responsable Actual</h3>
          <div class="grid grid-cols-12 gap-4">
            <!-- Nombre del responsable -->
            <div class="col-span-5">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Nombre del responsable
              </label>
              <input
                v-model="form.titular.nombre"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <!-- NIF del responsable -->
            <div class="col-span-3">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                NIF
              </label>
              <input
                v-model="form.titular.nif"
                type="text"
                maxlength="9"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <!-- Fecha desde -->
            <div class="col-span-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Fecha desde
              </label>
              <input
                v-model="form.titular.fechaDesde"
                type="date"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <!-- Email del responsable -->
            <div class="col-span-9">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                v-model="form.titular.email"
                type="email"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <!-- Teléfono del responsable -->
            <div class="col-span-3">
              <label class="block text-sm font-medium text-gray-700 mb-1">
                Teléfono
              </label>
              <input
                v-model="form.titular.telefono"
                type="tel"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex justify-end space-x-3 pt-6 border-t border-gray-200">
          <button 
            type="button"
            @click="close"
            class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button 
            type="submit"
            :disabled="loading"
            class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            <ArrowPathIcon v-if="loading" class="w-4 h-4 mr-2 animate-spin" />
            {{ isEdit ? 'Guardar cambios' : 'Crear administración' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import {
  XMarkIcon,
  ArrowPathIcon
} from '@heroicons/vue/24/outline'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  administracion: {
    type: Object,
    default: null
  },
  comunidadesAutonomas: {
    type: Array,
    default: () => []
  },
  provincias: {
    type: Array,
    default: () => []
  },
  municipios: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'save'])

const isEdit = ref(false)
const form = ref({
  nombre: '',
  ambito: 'municipal',
  email: '',
  telefono: '',
  direccion: '',
  codigoPostal: '',
  comunidadAutonomaId: '',
  provinciaId: '',
  municipioId: '',
  titular: {
    nombre: '',
    nif: '',
    email: '',
    telefono: '',
    fechaDesde: ''
  }
})

// Filtrado en cascada
const provinciasFiltradas = computed(() => {
  if (!form.value.comunidadAutonomaId) return []
  return props.provincias.filter(p => p.comunidadAutonomaId === form.value.comunidadAutonomaId)
})

const municipiosFiltrados = computed(() => {
  if (!form.value.provinciaId) return []
  return props.municipios.filter(m => m.provinciaId === form.value.provinciaId)
})

const onComunidadChange = () => {
  // Resetear provincia y municipio cuando cambia la comunidad
  form.value.provinciaId = ''
  form.value.municipioId = ''
}

const onProvinciaChange = () => {
  // Resetear municipio cuando cambia la provincia
  form.value.municipioId = ''
}

watch(() => props.show, (newVal) => {
  if (newVal && props.administracion) {
    // Modo edición
    isEdit.value = true
    const titularActual = props.administracion.titularActual || {}
    form.value = {
      nombre: props.administracion.nombre,
      ambito: props.administracion.ambito,
      email: props.administracion.email || '',
      telefono: props.administracion.telefono || '',
      direccion: props.administracion.direccion || '',
      codigoPostal: props.administracion.codigoPostal || '',
      comunidadAutonomaId: props.administracion.comunidadAutonomaId || '',
      provinciaId: props.administracion.provinciaId || '',
      municipioId: props.administracion.municipioId || '',
      titular: {
        nombre: titularActual.nombre || '',
        nif: titularActual.identificacion || '',
        email: titularActual.email || '',
        telefono: titularActual.telefono || '',
        fechaDesde: titularActual.fechaInicio || ''
      }
    }
  } else if (newVal) {
    // Modo creación
    isEdit.value = false
    form.value = {
      nombre: '',
      ambito: 'municipal',
      email: '',
      telefono: '',
      direccion: '',
      codigoPostal: '',
      comunidadAutonomaId: '',
      provinciaId: '',
      municipioId: '',
      titular: {
        nombre: '',
        nif: '',
        email: '',
        telefono: '',
        fechaDesde: ''
      }
    }
  }
})

const close = () => {
  emit('close')
}

const handleSubmit = () => {
  emit('save', { ...form.value, id: props.administracion?.id })
}
</script>