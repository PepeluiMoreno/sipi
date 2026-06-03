<template>
  <div class="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8">
      <!-- Header -->
      <div>
        <div class="mx-auto h-12 w-12 bg-indigo-600 rounded-lg flex items-center justify-center">
          <KeyIcon class="h-8 w-8 text-white" />
        </div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
          Nueva Contraseña
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600">
          Crea una nueva contraseña para tu cuenta
        </p>
      </div>

      <!-- Formulario -->
      <form class="mt-8 space-y-6" @submit.prevent="handleResetPassword">
        <div class="space-y-4">
          <div>
            <label for="password" class="sr-only">Nueva Contraseña</label>
            <input
              id="password"
              v-model="form.password"
              name="password"
              type="password"
              autocomplete="new-password"
              required
              class="relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="Nueva contraseña"
            >
          </div>
          <div>
            <label for="password_confirmation" class="sr-only">Confirmar Contraseña</label>
            <input
              id="password_confirmation"
              v-model="form.password_confirmation"
              name="password_confirmation"
              type="password"
              autocomplete="new-password"
              required
              class="relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="Confirmar contraseña"
            >
          </div>
        </div>

        <!-- Mensaje de éxito -->
        <div v-if="success" class="bg-green-50 border border-green-200 rounded-md p-4">
          <div class="flex">
            <CheckCircleIcon class="h-5 w-5 text-green-400" />
            <div class="ml-3">
              <h3 class="text-sm font-medium text-green-800">
                Contraseña actualizada
              </h3>
              <div class="mt-2 text-sm text-green-700">
                <p>{{ success }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Errores -->
        <div v-if="error" class="bg-red-50 border border-red-200 rounded-md p-4">
          <div class="flex">
            <ExclamationCircleIcon class="h-5 w-5 text-red-400" />
            <div class="ml-3">
              <h3 class="text-sm font-medium text-red-800">
                Error
              </h3>
              <div class="mt-2 text-sm text-red-700">
                <p>{{ error }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Botón -->
        <div>
          <button
            type="submit"
            :disabled="loading"
            class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            <span v-if="loading" class="flex items-center">
              <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Actualizando...
            </span>
            <span v-else>
              Actualizar Contraseña
            </span>
          </button>
        </div>

        <!-- Volver al login -->
        <div class="text-center">
          <router-link to="/login" class="font-medium text-indigo-600 hover:text-indigo-500 text-sm">
            ← Volver al inicio de sesión
          </router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { KeyIcon, CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/vue/24/outline'

const router = useRouter()
const route = useRoute()

const form = ref({
  password: '',
  password_confirmation: '',
  token: ''
})

const loading = ref(false)
const error = ref('')
const success = ref('')

onMounted(() => {
  form.value.token = route.params.token || ''
})

const handleResetPassword = async () => {
  loading.value = true
  error.value = ''
  success.value = ''

  try {
    // Validaciones
    if (form.value.password.length < 6) {
      throw new Error('La contraseña debe tener al menos 6 caracteres')
    }

    if (form.value.password !== form.value.password_confirmation) {
      throw new Error('Las contraseñas no coinciden')
    }

    // Simular actualización
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    success.value = 'Contraseña actualizada correctamente'
    
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}
</script>