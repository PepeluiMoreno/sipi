<!-- InmuebleFormHemeroteca.vue -->
<template>
  <div class="bg-white rounded-lg border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-6">
      <h3 class="text-lg font-medium text-gray-900">Hemeroteca</h3>
      <button
        @click="abrirNuevo"
        class="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        <PlusIcon class="w-5 h-5" />
        <span>Añadir recorte</span>
      </button>
    </div>

    <!-- Lista de recortes -->
    <div v-if="recortes.length" class="space-y-4">
      <div
        v-for="recorte in recortes"
        :key="recorte.id"
        class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <h4 class="font-medium text-gray-900">{{ recorte.titular }}</h4>
            <p class="text-sm text-gray-600 mt-1">{{ recorte.publicacion }} • {{ formatFecha(recorte.fecha) }}</p>
            <p v-if="recorte.resumen" class="text-sm text-gray-700 mt-2">{{ recorte.resumen }}</p>
            <div class="flex items-center space-x-4 mt-3 text-xs text-gray-500">
              <span v-if="recorte.autor">Autor: {{ recorte.autor }}</span>
              <span v-if="recorte.pagina">Pág. {{ recorte.pagina }}</span>
            </div>
          </div>
          <div class="flex items-center space-x-2 ml-4">
            <button
              v-if="recorte.archivo_url"
              @click="descargar(recorte)"
              class="p-2 text-gray-600 hover:text-blue-600 rounded-lg hover:bg-blue-50"
            >
              <ArrowDownTrayIcon class="w-5 h-5" />
            </button>
            <button
              @click="eliminar(recorte.id)"
              class="p-2 text-gray-600 hover:text-red-600 rounded-lg hover:bg-red-50"
            >
              <TrashIcon class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="text-center py-12">
      <NewspaperIcon class="w-16 h-16 text-gray-300 mx-auto mb-4" />
      <p class="text-gray-500 mb-4">No hay recortes de prensa</p>
      <button
        @click="abrirNuevo"
        class="text-blue-600 hover:text-blue-700 font-medium"
      >
        Añadir primer recorte
      </button>
    </div>

    <!-- Modal -->
    <TransitionRoot :show="mostrarModal" as="template">
      <Dialog @close="mostrarModal = false">
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
            <DialogPanel class="bg-white rounded-lg p-6 max-w-2xl w-full">
              <DialogTitle class="text-lg font-semibold text-gray-900 mb-4">
                Añadir recorte de prensa
              </DialogTitle>

              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Titular *</label>
                  <input
                    v-model="nuevoRecorte.titular"
                    type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Publicación *</label>
                    <input
                      v-model="nuevoRecorte.publicacion"
                      type="text"
                      placeholder="El País, ABC, La Vanguardia..."
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Fecha publicación *</label>
                    <input
                      v-model="nuevoRecorte.fecha"
                      type="date"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Autor</label>
                    <input
                      v-model="nuevoRecorte.autor"
                      type="text"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Página</label>
                    <input
                      v-model="nuevoRecorte.pagina"
                      type="text"
                      placeholder="ej. 12"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Resumen</label>
                  <textarea
                    v-model="nuevoRecorte.resumen"
                    rows="3"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">URL noticia</label>
                  <input
                    v-model="nuevoRecorte.url"
                    type="url"
                    placeholder="https://..."
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Archivo (PDF, imagen)</label>
                  <input
                    ref="fileInput"
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    @change="seleccionarArchivo"
                    class="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                  />
                </div>
              </div>

              <div class="flex justify-end space-x-3 mt-6">
                <button
                  @click="mostrarModal = false"
                  class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  @click="guardar"
                  :disabled="!nuevoRecorte.titular || !nuevoRecorte.publicacion || !nuevoRecorte.fecha"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  Guardar
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
import { ref } from 'vue'
import { Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild } from '@headlessui/vue'
import { PlusIcon, NewspaperIcon, ArrowDownTrayIcon, TrashIcon } from '@heroicons/vue/24/outline'

defineProps({
  inmuebleId: [String, Number]
})

const recortes = ref([])
const mostrarModal = ref(false)
const fileInput = ref(null)
const nuevoRecorte = ref({
  titular: '',
  publicacion: '',
  fecha: '',
  autor: '',
  pagina: '',
  resumen: '',
  url: '',
  archivo: null
})

const abrirNuevo = () => {
  nuevoRecorte.value = {
    titular: '',
    publicacion: '',
    fecha: '',
    autor: '',
    pagina: '',
    resumen: '',
    url: '',
    archivo: null
  }
  mostrarModal.value = true
}

const seleccionarArchivo = (event) => {
  nuevoRecorte.value.archivo = event.target.files[0]
}

const guardar = () => {
  // TODO: Implementar guardado
  console.log('Guardar recorte:', nuevoRecorte.value)
  mostrarModal.value = false
}

const descargar = (recorte) => {
  console.log('Descargar:', recorte)
}

const eliminar = (id) => {
  console.log('Eliminar:', id)
}

const formatFecha = (fecha) => {
  if (!fecha) return ''
  return new Date(fecha).toLocaleDateString('es-ES', { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  })
}
</script>