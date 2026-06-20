<!-- InmuebleFormBibliografia.vue -->
<template>
  <div class="bg-white rounded-lg border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-6">
      <h3 class="text-lg font-medium text-gray-900">Referencias bibliográficas</h3>
      <button
        @click="abrirNueva"
        class="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        <PlusIcon class="w-5 h-5" />
        <span>Añadir referencia</span>
      </button>
    </div>

    <!-- Lista de referencias -->
    <div v-if="referencias.length" class="space-y-4">
      <div
        v-for="referencia in referencias"
        :key="referencia.id"
        class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="flex items-center space-x-2 mb-2">
              <span class="inline-block px-2 py-0.5 bg-gray-100 text-gray-700 text-xs font-medium rounded">
                {{ referencia.tipo }}
              </span>
            </div>
            <h4 class="font-medium text-gray-900">{{ referencia.titulo }}</h4>
            <p class="text-sm text-gray-600 mt-1">
              {{ referencia.autores }} 
              <span v-if="referencia.anio">({{ referencia.anio }})</span>
            </p>
            <p v-if="referencia.editorial" class="text-sm text-gray-600">
              {{ referencia.editorial }}
              <span v-if="referencia.lugar_publicacion">, {{ referencia.lugar_publicacion }}</span>
            </p>
            <p v-if="referencia.paginas" class="text-sm text-gray-500 mt-1">pp. {{ referencia.paginas }}</p>
            <div class="flex items-center space-x-4 mt-3">
              <a v-if="referencia.isbn" :href="`https://www.worldcat.org/isbn/${referencia.isbn}`" target="_blank" class="text-xs text-blue-600 hover:underline">
                ISBN: {{ referencia.isbn }}
              </a>
              <a v-if="referencia.doi" :href="`https://doi.org/${referencia.doi}`" target="_blank" class="text-xs text-blue-600 hover:underline">
                DOI: {{ referencia.doi }}
              </a>
              <a v-if="referencia.url" :href="referencia.url" target="_blank" class="text-xs text-blue-600 hover:underline">
                Enlace externo
              </a>
            </div>
          </div>
          <button
            @click="eliminar(referencia.id)"
            class="p-2 text-gray-600 hover:text-red-600 rounded-lg hover:bg-red-50 ml-4"
          >
            <TrashIcon class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
    <!-- Empty state -->
    <div v-else class="text-center py-12">
      <BookOpenIcon class="w-16 h-16 text-gray-300 mx-auto mb-4" />
      <p class="text-gray-500">No hay referencias bibliográficas</p>
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

        <div class="fixed inset-0 flex items-center justify-center p-4 overflow-y-auto">
          <TransitionChild
            enter="duration-300 ease-out"
            enter-from="opacity-0 scale-95"
            enter-to="opacity-100 scale-100"
            leave="duration-200 ease-in"
            leave-from="opacity-100 scale-100"
            leave-to="opacity-0 scale-95"
          >
            <DialogPanel class="bg-white rounded-lg p-6 max-w-2xl w-full my-8">
              <DialogTitle class="text-lg font-semibold text-gray-900 mb-4">
                Añadir referencia bibliográfica
              </DialogTitle>

              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Tipo *</label>
                  <select
                    v-model="nuevaRef.tipo"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="">Seleccionar...</option>
                    <option value="Libro">Libro</option>
                    <option value="Artículo">Artículo</option>
                    <option value="Tesis">Tesis</option>
                    <option value="Capítulo">Capítulo de libro</option>
                    <option value="Conferencia">Actas de conferencia</option>
                    <option value="Web">Recurso web</option>
                  </select>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Título *</label>
                  <input
                    v-model="nuevaRef.titulo"
                    type="text"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Autor(es) *</label>
                  <input
                    v-model="nuevaRef.autores"
                    type="text"
                    placeholder="Apellido, N., Apellido2, M."
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div class="grid grid-cols-3 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Año *</label>
                    <input
                      v-model.number="nuevaRef.anio"
                      type="number"
                      min="1000"
                      max="2100"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div class="col-span-2">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Editorial</label>
                    <input
                      v-model="nuevaRef.editorial"
                      type="text"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Lugar publicación</label>
                    <input
                      v-model="nuevaRef.lugar_publicacion"
                      type="text"
                      placeholder="Madrid, Barcelona..."
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Páginas</label>
                    <input
                      v-model="nuevaRef.paginas"
                      type="text"
                      placeholder="ej. 120-145"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">ISBN</label>
                    <input
                      v-model="nuevaRef.isbn"
                      type="text"
                      placeholder="978-..."
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">DOI</label>
                    <input
                      v-model="nuevaRef.doi"
                      type="text"
                      placeholder="10.1000/..."
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">URL</label>
                  <input
                    v-model="nuevaRef.url"
                    type="url"
                    placeholder="https://..."
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Notas</label>
                  <textarea
                    v-model="nuevaRef.notas"
                    rows="2"
                    class="w-full px-3 py-2 border border-gray-300 rounded-lg"
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
                  :disabled="!nuevaRef.tipo || !nuevaRef.titulo || !nuevaRef.autores || !nuevaRef.anio"
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
import { PlusIcon, BookOpenIcon, TrashIcon } from '@heroicons/vue/24/outline'

defineProps({
  inmuebleId: [String, Number]
})

const referencias = ref([])
const mostrarModal = ref(false)
const nuevaRef = ref({
  tipo: '',
  titulo: '',
  autores: '',
  anio: null,
  editorial: '',
  lugar_publicacion: '',
  paginas: '',
  isbn: '',
  doi: '',
  url: '',
  notas: ''
})

const abrirNueva = () => {
  nuevaRef.value = {
    tipo: '',
    titulo: '',
    autores: '',
    anio: null,
    editorial: '',
    lugar_publicacion: '',
    paginas: '',
    isbn: '',
    doi: '',
    url: '',
    notas: ''
  }
  mostrarModal.value = true
}

const guardar = () => {
  console.log('Guardar referencia:', nuevaRef.value)
  mostrarModal.value = false
}

const eliminar = (id) => {
  console.log('Eliminar:', id)
}
</script>