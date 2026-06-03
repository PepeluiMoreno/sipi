<template>
  <div class="h-[calc(100vh-8rem)] overflow-hidden">
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Gestión de Tipologías</h1>
    
    <div class="flex h-full">
      <!-- Lista lateral de tipologías -->
      <div class="w-80 bg-white rounded-lg shadow mr-6 flex flex-col flex-shrink-0">
        <div class="p-4 border-b border-gray-200">
          <h2 class="font-semibold text-gray-900">Tipologías disponibles</h2>
        </div>
        <div class="flex-1 overflow-y-auto p-2">
          <button
            v-for="catalogo in tipologias"
            :key="catalogo.key"
            @click="selectCatalogo(catalogo)"
            class="w-full text-left p-3 rounded-lg hover:bg-indigo-50 flex items-center space-x-3 mb-1 transition-colors"
            :class="{ 'bg-indigo-50 border-l-4 border-indigo-600': selectedCatalogo?.key === catalogo.key }"
          >
            <component :is="catalogo.icon" class="w-5 h-5 text-gray-600 flex-shrink-0" />
            <div class="flex-1 min-w-0">
              <h3 class="text-sm font-medium text-gray-900 truncate">{{ catalogo.name }}</h3>
              <p class="text-xs text-gray-500">{{ catalogo.count }} registros</p>
            </div>
          </button>
        </div>
      </div>

      <!-- Panel derecho: Manager del tipología seleccionado -->
      <div class="flex-1 overflow-y-auto">
        <div v-if="selectedCatalogo" class="bg-white rounded-lg shadow">
          <CatalogoManager
            :title="selectedCatalogo.name"
            :singular-title="selectedCatalogo.singularName"
            :api-endpoint="selectedCatalogo.key"
            :display-fields="selectedCatalogo.displayFields"
            :form-fields="selectedCatalogo.formFields"
          />
        </div>
        
        <!-- Estado vacío -->
        <div v-else class="bg-white rounded-lg shadow h-full flex items-center justify-center">
          <div class="text-center py-12 px-6">
            <Cog6ToothIcon class="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 class="text-lg font-medium text-gray-900 mb-2">Selecciona un tipología</h3>
            <p class="text-gray-500">Elige un tipología de la lista para gestionar sus registros</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Cog6ToothIcon } from '@heroicons/vue/24/outline'
import CatalogoManager from '../components/CatalogoManager.vue'
import {
  HomeIcon, DocumentTextIcon, ShieldCheckIcon, UserIcon, KeyIcon,
  BuildingOfficeIcon, InboxIcon, UsersIcon, ArrowsRightLeftIcon,
  MapPinIcon, DocumentDuplicateIcon
} from '@heroicons/vue/24/outline'

const selectedCatalogo = ref(null)

const tipologias = [
  { 
    key: 'estados-conservacion', 
    name: 'Estados de Conservación', 
    singularName: 'Estado de Conservación',
    icon: HomeIcon,
    count: 8,
    displayFields: [
      { key: 'nombre', label: 'Nombre' },
      { key: 'descripcion', label: 'Descripción' }
    ],
    formFields: [
      { key: 'nombre', label: 'Nombre', type: 'text' },
      { key: 'descripcion', label: 'Descripción', type: 'textarea' }
    ]
  },
  { 
    key: 'tipos-documento', 
    name: 'Tipos de Documento', 
    singularName: 'Tipo de Documento',
    icon: InboxIcon,
    count: 25,
    displayFields: [
      { key: 'nombre', label: 'Nombre' },
      { key: 'descripcion', label: 'Descripción' }
    ],
    formFields: [
      { key: 'nombre', label: 'Nombre', type: 'text' },
      { key: 'descripcion', label: 'Descripción', type: 'textarea' }
    ]
  },
  { 
    key: 'tipos-mime', 
    name: 'Tipos MIME', 
    singularName: 'Tipo MIME',
    icon: DocumentDuplicateIcon,
    count: 42,
    displayFields: [
      { key: 'tipo_mime', label: 'MIME Type' },
      { key: 'extension', label: 'Extensión' },
      { key: 'descripcion', label: 'Descripción' }
    ],
    formFields: [
      { key: 'tipo_mime', label: 'MIME Type', type: 'text' },
      { key: 'extension', label: 'Extensión', type: 'text' },
      { key: 'descripcion', label: 'Descripción', type: 'textarea' }
    ]
  },
  { 
    key: 'tipos-inmueble', 
    name: 'Tipos de Inmueble', 
    singularName: 'Tipo de Inmueble',
    icon: BuildingOfficeIcon,
    count: 18,
    displayFields: [
      { key: 'nombre', label: 'Nombre' },
      { key: 'descripcion', label: 'Descripción' }
    ],
    formFields: [
      { key: 'nombre', label: 'Nombre', type: 'text' },
      { key: 'descripcion', label: 'Descripción', type: 'textarea' }
    ]
  }
]

const selectCatalogo = (catalogo) => {
  selectedCatalogo.value = catalogo
}
</script>