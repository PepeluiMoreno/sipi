<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
    <!-- Header con acciones -->
    <div class="p-4 border-b border-gray-200 flex justify-between items-center">
      <h2 class="text-lg font-semibold text-gray-900">Entidades Religiosas</h2>
      <button
        @click="$emit('create')"
        class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center"
      >
        <PlusIcon class="w-4 h-4 mr-2" />
        Nueva Entidad
      </button>
    </div>

    <!-- Tabla -->
    <div v-if="hasItems" class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">NIF</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Localidad</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="entidad in items" :key="entidad.id" class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm font-medium text-gray-900">{{ entidad.nombre }}</div>
              <div v-if="entidad.email" class="text-sm text-gray-500">{{ entidad.email }}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm text-gray-900">{{ entidad.tipoEntidad?.nombre || '-' }}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ entidad.numeroIdentificacion || '-' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ entidad.municipioSede?.nombre || '-' }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span :class="[
                entidad.activa ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800',
                'px-2 inline-flex text-xs leading-5 font-semibold rounded-full'
              ]">
                {{ entidad.activa ? 'Activa' : 'Inactiva' }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
              <button
                @click="$emit('edit', entidad.id)"
                class="text-indigo-600 hover:text-indigo-900 mr-3"
              >
                <PencilIcon class="w-4 h-4 inline" />
              </button>
              <button
                @click="$emit('delete', entidad.id)"
                class="text-red-600 hover:text-red-900"
              >
                <TrashIcon class="w-4 h-4 inline" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Estado vacío -->
    <div v-else-if="!loading" class="p-12 text-center">
      <BuildingLibraryIcon class="w-12 h-12 mx-auto text-gray-300 mb-4" />
      <p class="text-gray-500">No se encontraron entidades religiosas</p>
      <button
        @click="$emit('create')"
        class="mt-4 text-indigo-600 hover:text-indigo-700 font-medium"
      >
        Crear la primera entidad religiosa
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="p-12 text-center">
      <ArrowPathIcon class="w-8 h-8 mx-auto animate-spin text-gray-400" />
      <p class="mt-2 text-gray-500">Cargando...</p>
    </div>

    <!-- Paginación -->
    <div v-if="hasItems && pagination.totalPages > 1"
         class="p-4 border-t border-gray-200 flex justify-between items-center">
      <div class="text-sm text-gray-600">
        Mostrando {{ items.length }} de {{ pagination.total }} resultados
      </div>
      <div class="flex space-x-2">
        <button
          @click="$emit('change-page', pagination.page - 1)"
          :disabled="pagination.page <= 1"
          class="px-3 py-1 rounded border border-gray-300 disabled:opacity-50"
        >
          Anterior
        </button>
        <span class="px-3 py-1 bg-indigo-600 text-white rounded">
          Pág. {{ pagination.page }}
        </span>
        <button
          @click="$emit('change-page', pagination.page + 1)"
          :disabled="pagination.page >= pagination.totalPages"
          class="px-3 py-1 rounded border border-gray-300 disabled:opacity-50"
        >
          Siguiente
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  PlusIcon,
  BuildingLibraryIcon,
  ArrowPathIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/vue/24/outline'

const props = defineProps({
  items: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  pagination: {
    type: Object,
    default: () => ({})
  }
})

const hasItems = computed(() => props.items.length > 0)

defineEmits(['create', 'edit', 'delete', 'change-page'])
</script>
