<!-- InmuebleDetalleView.vue — detalle a altura completa, pestañas sin scroll de página -->
<template>
  <div class="h-full min-h-0 flex flex-col bg-zinc-100">
    <!-- Barra de acciones -->
    <header class="shrink-0 h-12 bg-white border-b border-zinc-200 px-4 flex items-center justify-between">
      <UiButton variant="ghost" icon="atras" @click="volver">Volver</UiButton>
      <div class="flex items-center gap-2">
        <UiButton v-if="!isNuevo" variant="danger" icon="borrar" @click="confirmarEliminar">Eliminar</UiButton>
        <UiButton variant="secondary" @click="volver">Cancelar</UiButton>
        <UiButton variant="primary" icon="check" :loading="loading" @click="guardar">Guardar</UiButton>
      </div>
    </header>

    <!-- Resumen compacto del inmueble (media anchura) -->
    <div v-if="inmueble" class="shrink-0 px-4 bg-white border-b border-zinc-200">
      <InmuebleDetailHeader :inmueble="inmueble" class="w-1/2 max-w-xl" />
    </div>

    <!-- Solapas a ancho completo -->
    <TabGroup as="div" class="flex-1 min-h-0 flex flex-col" @change="cambiarTab">
      <TabList class="shrink-0 flex items-center gap-1 px-4 bg-white border-b border-zinc-200">
        <Tab v-for="t in tabs" :key="t" v-slot="{ selected }" as="template">
          <button :class="['tab', selected && 'is-active']">{{ t }}</button>
        </Tab>
      </TabList>

      <TabPanels class="flex-1 min-h-0 overflow-auto p-4">
        <TabPanel class="h-full">
          <InmuebleFormDatosGenerales
            :modelValue="formData"
            @update:modelValue="formData = $event"
            :catalogos="catalogos"
            :errores="errores"
            @geolocalizar="onGeolocalizar"
          />
        </TabPanel>
        <TabPanel><InmuebleFormDocumentos :inmueble-id="inmuebleId" /></TabPanel>
        <TabPanel><InmuebleFormHemeroteca :inmueble-id="inmuebleId" /></TabPanel>
        <TabPanel><InmuebleFormBibliografia :inmueble-id="inmuebleId" /></TabPanel>
      </TabPanels>
    </TabGroup>

    <!-- Modal confirmación eliminar -->
    <TransitionRoot :show="mostrarConfirmEliminar" as="template">
      <Dialog @close="mostrarConfirmEliminar = false" class="relative z-50">
        <TransitionChild enter="duration-200 ease-out" enter-from="opacity-0" enter-to="opacity-100"
                         leave="duration-150 ease-in" leave-from="opacity-100" leave-to="opacity-0">
          <div class="fixed inset-0 bg-zinc-900/40" />
        </TransitionChild>
        <div class="fixed inset-0 flex items-center justify-center p-4">
          <TransitionChild enter="duration-200 ease-out" enter-from="opacity-0 scale-95" enter-to="opacity-100 scale-100"
                           leave="duration-150 ease-in" leave-from="opacity-100 scale-100" leave-to="opacity-0 scale-95">
            <DialogPanel class="card p-5 max-w-md w-full">
              <DialogTitle class="text-base font-semibold text-zinc-900 mb-1">¿Eliminar inmueble?</DialogTitle>
              <DialogDescription class="text-sm text-zinc-500 mb-5">
                Esta acción no se puede deshacer. Se eliminarán todos los datos asociados.
              </DialogDescription>
              <div class="flex justify-end gap-2">
                <UiButton variant="secondary" @click="mostrarConfirmEliminar = false">Cancelar</UiButton>
                <UiButton variant="danger" icon="borrar" @click="eliminar">Eliminar</UiButton>
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
import { useInmueble } from '../composables/useInmueble'

const tabs = ['Datos Generales', 'Documentos', 'Hemeroteca', 'Bibliografía']
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

// Pendiente: cablear al servicio de geolocalización del backend (cascada fusión OSM →
// geocoder con validación point-in-polygon). NO inventa coordenadas. Por ahora solo
// registra la petición con el contexto de dirección.
const onGeolocalizar = (contexto) => {
  console.info('[geolocalizar] solicitud pendiente de cascada backend', contexto)
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