<template>
  <div class="space-y-6">
    <!-- Encabezado -->
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Configuración de Procesos</h1>
        <p class="text-gray-600">Gestione los tipos de procesos y su configuración</p>
      </div>
    </div>

    <!-- Tabs de navegación -->
    <div class="bg-white rounded-lg shadow-sm border border-gray-200">
      <div class="border-b border-gray-200">
        <nav class="-mb-px flex space-x-8 px-6" aria-label="Tabs">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="tabActiva = tab.id"
            :class="[
              tabActiva === tab.id
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
              'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm'
            ]"
          >
            {{ tab.nombre }}
          </button>
        </nav>
      </div>

      <!-- Contenido de tabs -->
      <div class="p-6">
        <!-- Tab: Tipos de Proceso -->
        <div v-if="tabActiva === 'tipos'" class="space-y-4">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-lg font-semibold text-gray-900">Procesos Definidos</h2>
            <button
              @click="crearNuevoProceso"
              class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              Nuevo Proceso
            </button>
          </div>

          <!-- Grid de tipos de proceso -->
          <div v-if="loading" class="text-center py-12">
            <svg class="w-8 h-8 mx-auto animate-spin text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <p class="mt-2 text-gray-500">Cargando...</p>
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div
              v-for="proceso in tiposProceso"
              :key="proceso.id"
              class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow bg-white"
            >
              <div class="flex justify-between items-start mb-2">
                <h3 class="font-semibold text-gray-900">{{ proceso.nombre }}</h3>
                <div class="flex space-x-1">
                  <button
                    @click="editarProceso(proceso)"
                    class="p-1 text-indigo-600 hover:bg-indigo-50 rounded"
                    title="Editar"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    v-if="!proceso.activo"
                    @click="activarProceso(proceso.id)"
                    class="p-1 text-green-600 hover:bg-green-50 rounded"
                    title="Activar"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    </svg>
                  </button>
                </div>
              </div>

              <p class="text-sm text-gray-600 mb-3">{{ proceso.descripcion }}</p>

              <div class="text-xs space-y-1">
                <div class="flex items-center text-gray-500">
                  <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  <span>{{ contarActores(proceso.id) }} agentes</span>
                </div>
                <div class="flex items-center text-gray-500">
                  <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>{{ contarDocumentos(proceso.id) }} documentos</span>
                </div>
              </div>

              <div class="mt-3 flex items-center justify-between">
                <span :class="[
                  proceso.activo ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800',
                  'text-xs px-2 py-1 rounded-full font-medium'
                ]">
                  {{ proceso.activo ? 'Activo' : 'Inactivo' }}
                </span>
                <button
                  @click="configurarProceso(proceso)"
                  class="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
                >
                  Configurar →
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab: Tipos de Actor -->
        <div v-if="tabActiva === 'actores'" class="space-y-4">
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-lg font-semibold text-gray-900">Agentes Involucrados</h2>
            <button
              @click="crearNuevoActor"
              class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              Nuevo Agente
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div
              v-for="actor in tiposActor"
              :key="actor.id"
              class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow bg-white"
            >
              <div class="flex justify-between items-start">
                <h3 class="font-semibold text-gray-900">{{ actor.nombre }}</h3>
                <button
                  @click="editarActor(actor)"
                  class="p-1 text-indigo-600 hover:bg-indigo-50 rounded"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
              </div>
              <p class="text-sm text-gray-600 mt-2">{{ actor.descripcion }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

// Estado
const tabActiva = ref('tipos')
const loading = ref(false)
const tiposProceso = ref([])
const tiposActor = ref([])
const actoresRequeridos = ref([])
const documentosRequeridos = ref([])

// Tabs
const tabs = [
  { id: 'tipos', nombre: 'Procesos Definidos' },
  { id: 'actores', nombre: 'Agentes Involucrados' }
]

// Funciones auxiliares
const contarActores = (procesoId) => {
  return actoresRequeridos.value.filter(a => a.tipo_proceso_id === procesoId).length
}

const contarDocumentos = (procesoId) => {
  return documentosRequeridos.value.filter(d => d.tipo_proceso_id === procesoId).length
}

// Funciones de carga
const cargarTiposProceso = async () => {
  loading.value = true
  try {
    // TODO: Conectar con API GraphQL
    // Por ahora datos de ejemplo
    tiposProceso.value = [
      {
        id: '1',
        codigo: 'INMATRICULACION',
        nombre: 'Inmatriculación',
        categoria: 'ADMINISTRATIVO',
        descripcion: 'Alta e inscripción de un inmueble en el Registro de la Propiedad',
        activo: true
      },
      {
        id: '2',
        codigo: 'VENTA',
        nombre: 'Compraventa',
        categoria: 'CAMBIO_TITULARIDAD',
        descripcion: 'Proceso de compraventa del inmueble',
        activo: true
      },
      {
        id: '3',
        codigo: 'ACTUACION_FISICA',
        nombre: 'Actuación Física',
        categoria: 'ACTUACION_FISICA',
        descripcion: 'Obras de rehabilitación o restauración',
        activo: true
      }
    ]
    actoresRequeridos.value = [
      { id: '1', tipo_proceso_id: '1', tipo_actor_id: 'a1' },
      { id: '2', tipo_proceso_id: '1', tipo_actor_id: 'a2' },
      { id: '3', tipo_proceso_id: '2', tipo_actor_id: 'a1' }
    ]
    documentosRequeridos.value = [
      { id: '1', tipo_proceso_id: '1', tipo_documento_id: 'd1' },
      { id: '2', tipo_proceso_id: '2', tipo_documento_id: 'd2' }
    ]
  } catch (error) {
    console.error('Error cargando tipos de proceso:', error)
  } finally {
    loading.value = false
  }
}

const cargarTiposActor = async () => {
  try {
    // TODO: Conectar con API GraphQL
    tiposActor.value = [
      {
        id: 'a1',
        codigo: 'PRIVADO',
        nombre: 'Privado',
        tabla_referencia: 'privados',
        descripcion: 'Persona física o jurídica privada',
        activo: true
      },
      {
        id: 'a2',
        codigo: 'ENTIDAD_RELIGIOSA',
        nombre: 'Entidad Religiosa',
        tabla_referencia: 'entidades_religiosas',
        descripcion: 'Orden, congregación o institución religiosa',
        activo: true
      }
    ]
  } catch (error) {
    console.error('Error cargando tipos de actor:', error)
  }
}

// Funciones de acciones
const crearNuevoProceso = () => {
  console.log('Crear nuevo proceso')
}

const editarProceso = (proceso) => {
  console.log('Editar proceso:', proceso)
}

const activarProceso = (id) => {
  console.log('Activar proceso:', id)
}

const configurarProceso = (proceso) => {
  console.log('Configurar proceso:', proceso)
  // TODO: Navegar a vista de configuración detallada
}

const crearNuevoActor = () => {
  console.log('Crear nuevo actor')
}

const editarActor = (actor) => {
  console.log('Editar actor:', actor)
}

// Lifecycle
onMounted(async () => {
  await Promise.all([
    cargarTiposProceso(),
    cargarTiposActor()
  ])
})
</script>

<style scoped>
code {
  font-family: 'Courier New', Courier, monospace;
}
</style>
