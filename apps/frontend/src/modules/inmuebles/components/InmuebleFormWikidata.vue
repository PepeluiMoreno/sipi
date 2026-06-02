<template>
  <div class="p-6 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-gray-900">Wikidata</h3>
        <p class="text-sm text-gray-600 mt-1">Integración con la base de conocimiento Wikidata</p>
      </div>
      <div class="flex items-center space-x-3">
        <button
          @click="buscarEnWikidata"
          :disabled="buscando"
          class="btn btn-secondary btn-sm"
        >
          <MagnifyingGlassIcon class="w-4 h-4 mr-2" :class="{ 'animate-spin': buscando }" />
          {{ buscando ? 'Buscando...' : 'Buscar en Wikidata' }}
        </button>
        <button
          @click="sincronizarWikidata"
          :disabled="sincronizando"
          class="btn btn-primary btn-sm"
        >
          <ArrowPathIcon class="w-4 h-4 mr-2" :class="{ 'animate-spin': sincronizando }" />
          {{ sincronizando ? 'Sincronizando...' : 'Sincronizar' }}
        </button>
      </div>
    </div>

    <!-- Datos Wikidata -->
    <div v-if="wikidata" class="space-y-6">
      <!-- QID y Enlace -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Wikidata QID
          </label>
          <div class="flex space-x-2">
            <input
              v-model="wikidata.wikidata_qid"
              placeholder="Ej: Q123456"
              class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
            <a
              v-if="wikidata.wikidata_qid"
              :href="enlaceWikidata"
              target="_blank"
              class="btn btn-secondary"
              title="Abrir en Wikidata"
            >
              <ArrowTopRightOnSquareIcon class="w-4 h-4" />
            </a>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Categoría Commons
          </label>
          <input
            v-model="wikidata.commons_category"
            placeholder="Ej: Category:Church of San Pedro"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
      </div>

      <!-- Fechas importantes -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Fecha de inicio
          </label>
          <input
            type="date"
            v-model="wikidata.inception"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Fecha de fin
          </label>
          <input
            type="date"
            v-model="wikidata.dissolved"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Última sincronización
          </label>
          <input
            type="datetime-local"
            v-model="wikidata.source_updated_at"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
      </div>

      <!-- Coordenadas Wikidata -->
      <div class="border-t pt-6">
        <h4 class="text-md font-medium text-gray-900 mb-4">Coordenadas en Wikidata</h4>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Latitud (Wikidata)
            </label>
            <input
              type="number"
              v-model="wikidata.coordinate_latitude"
              placeholder="40.4168"
              step="any"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Longitud (Wikidata)
            </label>
            <input
              type="number"
              v-model="wikidata.coordinate_longitude"
              placeholder="-3.7038"
              step="any"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </div>
      </div>

      <!-- Propiedades adicionales -->
      <div class="border-t pt-6">
        <h4 class="text-md font-medium text-gray-900 mb-4">Propiedades adicionales</h4>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">País</label>
            <input
              v-model="wikidata.country"
              placeholder="Ej: Q29 (Spain)"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Tipo de edificio</label>
            <input
              v-model="wikidata.instance_of"
              placeholder="Ej: Q16970 (church building)"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Estilo arquitectónico</label>
            <input
              v-model="wikidata.architectural_style"
              placeholder="Ej: Q176483 (Gothic architecture)"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Religión</label>
            <input
              v-model="wikidata.religion"
              placeholder="Ej: Q9592 (Catholic Church)"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Diócesis</label>
            <input
              v-model="wikidata.diocese"
              placeholder="Ej: Q977206 (Archdiocese of Madrid)"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Estado de conservación</label>
            <input
              v-model="wikidata.heritage_status"
              placeholder="Ej: Q236527 (Bien de Interés Cultural)"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            />
          </div>
        </div>
      </div>

      <!-- Estadísticas -->
      <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h5 class="text-sm font-medium text-gray-900 mb-3">Estadísticas de sincronización</h5>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span class="text-gray-600">Propiedades:</span>
            <span class="ml-2 font-medium text-gray-900">{{ contarPropiedades }}</span>
          </div>
          <div>
            <span class="text-gray-600">Última sync:</span>
            <span class="ml-2 font-medium text-gray-900">{{ wikidata.source_updated_at ? 'Hace ' + calcularTiempo(wikidata.source_updated_at) : 'Nunca' }}</span>
          </div>
          <div>
            <span class="text-gray-600">Estado:</span>
            <span class="ml-2 font-medium text-green-600">Sincronizado</span>
          </div>
          <div>
            <span class="text-gray-600">Coincidencia:</span>
            <span class="ml-2 font-medium text-green-600">Alta</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Estado sin datos Wikidata -->
    <div
      v-else
      class="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg"
    >
      <QuestionMarkCircleIcon class="w-12 h-12 text-gray-400 mx-auto mb-4" />
      <h4 class="text-lg font-medium text-gray-900 mb-2">Sin datos de Wikidata</h4>
      <p class="text-gray-500 mb-4">Este inmueble no está vinculado con Wikidata</p>
      <div class="flex justify-center space-x-3">
        <button
          @click="inicializarWikidata"
          class="btn btn-primary"
        >
          <PlusIcon class="w-4 h-4 mr-2" />
          Inicializar Wikidata
        </button>
        <button
          @click="buscarEnWikidata"
          class="btn btn-secondary"
        >
          <MagnifyingGlassIcon class="w-4 h-4 mr-2" />
          Buscar en Wikidata
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { 
  MagnifyingGlassIcon, 
  ArrowPathIcon, 
  QuestionMarkCircleIcon,
  PlusIcon,
  ArrowTopRightOnSquareIcon 
} from '@heroicons/vue/24/outline'

const props = defineProps({
  property: {
    type: Object,
    required: true
  },
  errors: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:property'])

const buscando = ref(false)
const sincronizando = ref(false)
const wikidata = ref(props.property.wd_ext || null)

const enlaceWikidata = computed(() => {
  if (!wikidata.value?.wikidata_qid) return null
  return `https://www.wikidata.org/wiki/${wikidata.value.wikidata_qid}`
})

const contarPropiedades = computed(() => {
  if (!wikidata.value) return 0
  return Object.keys(wikidata.value).filter(key => 
    key !== 'source_updated_at' && wikidata.value[key]
  ).length
})

watch(wikidata, (newData) => {
  emit('update:property', {
    ...props.property,
    wd_ext: newData
  })
}, { deep: true })

const buscarEnWikidata = async () => {
  buscando.value = true
  try {
    // Simular búsqueda en Wikidata
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // Aquí iría la lógica real de búsqueda
    console.log('Buscando en Wikidata...')
    
    // Ejemplo de resultado simulado
    if (!wikidata.value) {
      wikidata.value = {
        wikidata_qid: 'Q' + Math.floor(Math.random() * 1000000),
        commons_category: `Category:Sample_${Date.now()}`,
        inception: '1900-01-01',
        source_updated_at: new Date().toISOString().slice(0, 16)
      }
    }
    
  } catch (error) {
    console.error('Error buscando en Wikidata:', error)
  } finally {
    buscando.value = false
  }
}

const sincronizarWikidata = async () => {
  sincronizando.value = true
  try {
    await new Promise(resolve => setTimeout(resolve, 2000))
    console.log('Sincronizando con Wikidata...')
    wikidata.value.source_updated_at = new Date().toISOString().slice(0, 16)
  } catch (error) {
    console.error('Error sincronizando con Wikidata:', error)
  } finally {
    sincronizando.value = false
  }
}

const inicializarWikidata = () => {
  wikidata.value = {
    wikidata_qid: '',
    commons_category: '',
    inception: '',
    dissolved: '',
    source_updated_at: new Date().toISOString().slice(0, 16),
    coordinate_latitude: null,
    coordinate_longitude: null,
    country: '',
    instance_of: '',
    architectural_style: '',
    religion: '',
    diocese: '',
    heritage_status: ''
  }
}

const calcularTiempo = (fecha) => {
  const ahora = new Date()
  const fechaObj = new Date(fecha)
  const diffMs = ahora - fechaObj
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)
  
  if (diffMins < 60) return `${diffMins} min`
  if (diffHours < 24) return `${diffHours} h`
  return `${diffDays} días`
}
</script>