<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-200">
        <div class="flex justify-between items-center">
          <h2 class="text-lg font-semibold text-gray-900">Recuperar Contraseña</h2>
          <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
            <XMarkIcon class="w-6 h-6" />
          </button>
        </div>
      </div>

      <!-- Formulario -->
      <form @submit.prevent="handleForgotPassword" class="p-6 space-y-4">
        <div>
          <p class="text-sm text-gray-600 mb-4">
            Introduce tu email y te enviaremos un enlace para restablecer tu contraseña.
          </p>
          
          <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            v-model="form.email"
            type="email"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            placeholder="tu@email.com"
          >
        </div>

        <!-- Mensaje de éxito -->
        <div v-if="success" class="bg-green-50 border border-green-200 rounded-lg p-3">
          <p class="text-sm text-green-700">{{ success }}</p>
        </div>

        <!-- Errores -->
        <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-3">
          <p class="text-sm text-red-700">{{ error }}</p>
        </div>

        <!-- Botones -->
        <div class="flex justify-end space-x-3 pt-4">
          <button
            type="button"
            @click="$emit('close')"
            class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg text-sm"
          >
            Cancelar
          </button>
          <button
            type="submit"
            :disabled="loading"
            class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 text-sm"
          >
            {{ loading ? 'Enviando...' : 'Enviar Enlace' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'

const form = ref({
  email: ''
})

const loading = ref(false)
const error = ref('')
const success = ref('')

const emit = defineEmits(['close'])

const handleForgotPassword = async () => {
  loading.value = true
  error.value = ''
  success.value = ''

  try {
    // Simular envío de email
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    success.value = `Se ha enviado un enlace de recuperación a ${form.value.email}`
    form.value.email = ''
    
    setTimeout(() => {
      emit('close')
    }, 3000)
  } catch (err) {
    error.value = 'Error al enviar el email de recuperación'
  } finally {
    loading.value = false
  }
}
</script>