<!-- InmuebleDetalleView.vue -->
<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header fijo con info del inmueble -->
    <InmuebleDetailHeader v-if="inmueble" :inmueble="inmueble" />

    <!-- Header acciones -->
    <div class="sticky top-0 z-10 bg-white border-b border-gray-200 px-6 py-4">
      <div class="max-w-7xl mx-auto flex items-center justify-between">
        <button @click="volver" class="flex items-center space-x-2 text-gray-600 hover:text-gray-900">
          <ArrowLeftIcon class="w-5 h-5" />
          <span>Volver</span>
        </button>

        <div class="flex items-center space-x-3">
          <button
            v-if="!isNuevo"
            @click="confirmarEliminar"
            class="px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50"
          >
            Eliminar
          </button>
          <button
            @click="volver"
            class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            @click="guardar"
            :disabled="loading"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {{ loading ? 'Guardando...' : 'Guardar' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Contenido -->
    <div class="max-w-7xl mx-auto px-6 py-8">
      <TabGroup @change="cambiarTab">
        <TabList class="flex space-x-1 bg-white rounded-lg p-1 border border-gray-200 mb-6">
          <Tab v-slot="{ selected }" as="template">
            <button
              :class="[
                'w-full py-2.5 text-sm font-medium rounded-lg transition-colors',
                selected
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              ]"
            >
              Datos Generales
            </button>
          </Tab>
          <Tab v-slot="{ selected }" as="template">
            <button
              :class="[
                'w-full py-2.5 text-sm font-medium rounded-lg transition-colors',
                selected
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              ]"
            >
              Documentos
            </button>
          </Tab>
          <Tab v-slot="{ selected }" as="template">
            <button
              :class="[
                'w-full py-2.5 text-sm font-medium rounded-lg transition-colors',
                selected
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              ]"
            >
              Hemeroteca
            </button>
          </Tab>
          <Tab v-slot="{ selected }" as="template">
            <button
              :class="[
                'w-full py-2.5 text-sm font-medium rounded-lg transition-colors',
                selected
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              ]"
            >
              Bibliografía
            </button>
          </Tab>
        </TabList>

        <TabPanels>
          <TabPanel>
            <InmuebleFormDatosGenerales
              :modelValue="formData"
              @update:modelValue="formData = $event"
              :catalogos="catalogos"
              :errores="errores"
            />
          </TabPanel>
          <TabPanel>
            <InmuebleFormDocumentos
              :inmueble-id="inmuebleId"
            />
          </TabPanel>
          <TabPanel>
            <InmuebleFormHemeroteca
              :inmueble-id="inmuebleId"
            />
          </TabPanel>
          <TabPanel>
            <InmuebleFormBibliografia
              :inmueble-id="inmuebleId"
            />
          </TabPanel>
        </TabPanels>
      </TabGroup>
    </div>

    <!-- Modal confirmación eliminar -->
    <TransitionRoot :show="mostrarConfirmEliminar" as="template">
      <Dialog @close="mostrarConfirmEliminar = false">
        <TransitionChild
          enter="duration-300 ease-out"
          enter-from="opacity-0"
          enter-to="opacity-100"
          leave="duration-200 ease-in"
          leave-from="opacity-100"
          leave-to="opacity-0"
        >
          <div class="fixed inset-0 bg-black/30" />
        </TransitionChild>

        <div class="fixed inset-0 flex items-center justify-center p-4">
          <TransitionChild
            enter="duration-300 ease-out"
            enter-from="opacity-0 scale-95"
            enter-to="opacity-100 scale-100"
            leave="duration-200 ease-in"
            leave-from="opacity-100 scale-100"
            leave-to="opacity-0 scale-95"
          >
            <DialogPanel class="bg-white rounded-lg p-6 max-w-md w-full">
              <DialogTitle class="text-lg font-semibold text-gray-900 mb-2">
                ¿Eliminar inmueble?
              </DialogTitle>
              <DialogDescription class="text-sm text-gray-600 mb-6">
                Esta acción no se puede deshacer. Se eliminarán todos los datos asociados.
              </DialogDescription>
              <div class="flex justify-end space-x-3">
                <button
                  @click="mostrarConfirmEliminar = false"
                  class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  @click="eliminar"
                  class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                >
                  Eliminar
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </Dialog>
    </TransitionRoot>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { TabGroup, TabList, Tab, TabPanels, TabPanel, Dialog, DialogPanel, DialogTitle, DialogDescription, TransitionRoot, TransitionChild } from '@headlessui/vue'
import { ArrowLeftIcon } from '@heroicons/vue/24/outline'
import { useInmueble } from '../composables/useInmueble'
import InmuebleDetailHeader from '../components/InmuebleDetailHeader.vue'
import InmuebleFormDatosGenerales from '../components/InmuebleFormDatosGenerales.vue'
import InmuebleFormDocumentos from '../components/InmuebleFormDocumentos.vue'
import InmuebleFormHemeroteca from '../components/InmuebleFormHemeroteca.vue'
import InmuebleFormBibliografia from '../components/InmuebleFormBibliografia.vue'

const route = useRoute()
const router = useRouter()

const inmuebleId = computed(() => route.params.id)
const isNuevo = computed(() => inmuebleId.value === 'nuevo')

const formData = ref({})
const catalogos = ref({})
const errores = ref({})
const mostrarConfirmEliminar = ref(false)

const {
  inmueble,
  loading,
  obtener,
  crear,
  actualizar,
  eliminar: eliminarInmueble,
  obtenerCatalogos
} = useInmueble()

const cambiarTab = (index) => {
  // Validar antes de cambiar tab si es necesario
}

const guardar = async () => {
  try {
    errores.value = {}
    
    if (isNuevo.value) {
      const nuevo = await crear(formData.value)
      router.push(`/inmuebles/${nuevo.id}`)
    } else {
      await actualizar(inmuebleId.value, formData.value)
    }
  } catch (err) {
    errores.value = err.errors || { general: err.message }
  }
}

const confirmarEliminar = () => {
  mostrarConfirmEliminar.value = true
}

const eliminar = async () => {
  try {
    await eliminarInmueble(inmuebleId.value)
    router.push('/inmuebles')
  } catch (err) {
    console.error(err)
  }
}

const volver = () => {
  router.push('/inmuebles')
}

onMounted(async () => {
  catalogos.value = await obtenerCatalogos()
  
  if (!isNuevo.value) {
    await obtener(inmuebleId.value)
    formData.value = { ...inmueble.value }
  }
})
</script>