<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">
          Cambiar Foto de Perfil
        </h2>
        <p class="text-sm text-gray-500 mt-1">Selecciona una nueva imagen para {{ user.nombre }}</p>
      </div>

      <!-- Contenido -->
      <div class="p-6">
        <!-- Vista previa -->
        <div class="flex flex-col items-center mb-6">
          <div class="w-32 h-32 bg-gray-300 rounded-lg flex items-center justify-center mb-4">
            <CameraIcon class="w-12 h-12 text-white" />
          </div>
          <p class="text-sm text-gray-500">Vista previa</p>
        </div>

        <!-- Opciones de carga -->
        <div class="space-y-4">
          <!-- Subir desde archivo -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Subir desde archivo
            </label>
            <div class="flex items-center space-x-3">
              <input
                ref="fileInput"
                type="file"
                accept="image/*"
                class="hidden"
                @change="onFileSelected"
              />
              <button
                @click="triggerFileInput"
                class="flex-1 bg-white border border-gray-300 rounded-lg px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Seleccionar archivo
              </button>
              <span class="text-xs text-gray-500">JPG, PNG, GIF</span>
            </div>
          </div>

          <!-- O desde URL -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              O desde URL
            </label>
            <input
              v-model="imageUrl"
              type="url"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 text-sm"
              placeholder="https://ejemplo.com/foto.jpg"
            />
          </div>

          <!-- Mostrar errores -->
          <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-3">
            <p class="text-sm text-red-700">{{ error }}</p>
          </div>
        </div>
      </div>

      <!-- Botones -->
      <div class="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-end space-x-3">
        <button
          type="button"
          @click="$emit('close')"
          class="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
        >
          Cancelar
        </button>
        <button
          type="button"
          @click="savePhoto"
          :disabled="!hasPhoto"
          class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          Guardar Foto
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { CameraIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  user: Object
})

const emit = defineEmits(['photo-updated', 'close'])

const fileInput = ref(null)
const imageUrl = ref('')
const selectedFile = ref(null)
const error = ref('')

const triggerFileInput = () => {
  fileInput.value?.click()
}

const onFileSelected = (event) => {
  const file = event.target.files[0]
  if (file) {
    // Validar tipo de archivo
    if (!file.type.startsWith('image/')) {
      error.value = 'Por favor, selecciona un archivo de imagen válido'
      return
    }

    // Validar tamaño (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      error.value = 'La imagen no puede ser mayor a 5MB'
      return
    }

    selectedFile.value = file
    imageUrl.value = '' // Limpiar URL si se selecciona archivo
    error.value = ''
  }
}

const hasPhoto = () => {
  return selectedFile.value || imageUrl.value.trim()
}

const savePhoto = async () => {
  try {
    let photoUrl = ''

    if (selectedFile.value) {
      // En una aplicación real, aquí subirías el archivo al servidor
      // Por ahora simulamos una URL temporal
      photoUrl = URL.createObjectURL(selectedFile.value)
    } else if (imageUrl.value.trim()) {
      // Validar URL de imagen
      if (!isValidImageUrl(imageUrl.value)) {
        error.value = 'Por favor, introduce una URL de imagen válida'
        return
      }
      photoUrl = imageUrl.value
    }

    const updatedUser = {
      ...props.user,
      avatar: photoUrl
    }

    emit('photo-updated', updatedUser)
  } catch (err) {
    error.value = 'Error al guardar la foto: ' + err.message
  }
}

const isValidImageUrl = (url) => {
  try {
    const urlObj = new URL(url)
    return urlObj.protocol === 'http:' || urlObj.protocol === 'https:'
  } catch {
    return false
  }
}
</script>