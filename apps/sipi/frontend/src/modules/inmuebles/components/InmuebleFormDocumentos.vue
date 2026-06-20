<!-- InmuebleFormDocumentos.vue -->
<template>
  <div class="bg-white rounded-lg border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-6">
      <h3 class="text-lg font-medium text-gray-900">Documentos</h3>
      <button
        @click="abrirUpload"
        class="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        <PlusIcon class="w-5 h-5" />
        <span>Añadir documento</span>
      </button>
    </div>

    <!-- Lista de documentos -->
    <div v-if="documentos.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <DocumentoCard
        v-for="doc in documentos"
        :key="doc.id"
        :documento="doc"
        @view="verDocumento"
        @download="descargarDocumento"
        @delete="confirmarEliminar"
      />
    </div>

    <!-- Empty state -->
    <div v-else class="text-center py-12">
      <DocumentIcon class="w-16 h-16 text-gray-300 mx-auto mb-4" />
      <p class="text-gray-500">No hay documentos asociados</p>
    </div>

    <!-- Upload modal -->
    <TransitionRoot :show="mostrarUpload" as="template">
      <Dialog @close="mostrarUpload = false">
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
              <DialogTitle class="text-lg font-semibold text-gray-900 mb-4">
                Subir documento
              </DialogTitle>

              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Tipo de documento
                  </label>
                  <select
                    v-model="nuevoDoc.tipo"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="">Seleccionar...</option>
                    <option v-for="tipo in tiposDocumento" :key="tipo" :value="tipo">{{ tipo }}</option>
                  </select>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Archivo
                  </label>
                  <input
                    ref="fileInput"
                    type="file"
                    @change="seleccionarArchivo"
                    class="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Fecha publicación
                  </label>
                  <input
                    v-model="nuevoDoc.fecha_publicacion"
                    type="date"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">
                    Descripción
                  </label>
                  <textarea
                    v-model="nuevoDoc.descripcion"
                    rows="3"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>

              <div class="flex justify-end space-x-3 mt-6">
                <button
                  @click="mostrarUpload = false"
                  class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  @click="subirDocumento"
                  :disabled="!nuevoDoc.archivo || !nuevoDoc.tipo"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  Subir
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
import { ref, onMounted } from 'vue'
import { Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild } from '@headlessui/vue'
import { PlusIcon, DocumentIcon } from '@heroicons/vue/24/outline'
import DocumentoCard from './DocumentoCard.vue'

const props = defineProps({
  inmuebleId: [String, Number]
})

const documentos = ref([])
const tiposDocumento = ref([])
const mostrarUpload = ref(false)
const fileInput = ref(null)
const nuevoDoc = ref({
  tipo: '',
  archivo: null,
  fecha_publicacion: '',
  descripcion: ''
})

onMounted(async () => {
  // Pendiente: cablear a la query real de documentos del inmueble.
  // Sin mock: se parte de listas vacías.
  void props.inmuebleId
  tiposDocumento.value = []
  documentos.value = []
})

const abrirUpload = () => {
  nuevoDoc.value = {
    tipo: '',
    archivo: null,
    fecha_publicacion: '',
    descripcion: ''
  }
  mostrarUpload.value = true
}

const seleccionarArchivo = (event) => {
  nuevoDoc.value.archivo = event.target.files[0]
}

const subirDocumento = async () => {
  console.log('Subir documento:', nuevoDoc.value)
  mostrarUpload.value = false
}

const verDocumento = (doc) => {
  console.log('Ver:', doc)
}

const descargarDocumento = (doc) => {
  console.log('Descargar:', doc)
}

const confirmarEliminar = (doc) => {
  if (confirm(`¿Eliminar documento "${doc.nombre}"?`)) {
    console.log('Eliminar:', doc)
  }
}
</script>