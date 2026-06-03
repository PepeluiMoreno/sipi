<!-- src/modules/usuarios/views/VerificarEmail.vue -->
<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-white p-8 rounded-lg shadow-md">
      <!-- Estado: Verificando -->
      <div v-if="verifying" class="text-center">
        <ArrowPathIcon class="mx-auto h-12 w-12 text-indigo-600 animate-spin" />
        <h2 class="mt-6 text-2xl font-extrabold text-gray-900">
          Verificando email...
        </h2>
        <p class="mt-2 text-sm text-gray-600">
          Estamos verificando tu dirección de correo electrónico.
        </p>
      </div>

      <!-- Estado: Éxito -->
      <div v-else-if="success" class="text-center">
        <CheckCircleIcon class="mx-auto h-16 w-16 text-green-500" />
        <h2 class="mt-6 text-2xl font-extrabold text-gray-900">
          ¡Email verificado!
        </h2>
        <p class="mt-2 text-sm text-gray-600">
          Tu dirección de correo ha sido verificada correctamente.
        </p>
        <div class="mt-8 space-y-4">
          <router-link 
            to="/login"
            class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Iniciar sesión
          </router-link>
        </div>
      </div>

      <!-- Estado: Error -->
      <div v-else-if="error" class="text-center">
        <ExclamationTriangleIcon class="mx-auto h-16 w-16 text-red-500" />
        <h2 class="mt-6 text-2xl font-extrabold text-gray-900">
          Error en la verificación
        </h2>
        <p class="mt-2 text-sm text-gray-600">
          {{ errorMessage }}
        </p>
        
        <!-- Botón para reenviar -->
        <div v-if="canResend" class="mt-8 space-y-4">
          <p class="text-sm text-gray-600">
            ¿El enlace ha expirado o no recibiste el email?
          </p>
          <button
            @click="handleResend"
            :disabled="resending"
            class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ArrowPathIcon v-if="resending" class="animate-spin -ml-1 mr-2 h-4 w-4" />
            {{ resending ? 'Reenviando...' : 'Solicitar nuevo enlace' }}
          </button>
          <router-link 
            to="/login"
            class="block w-full text-center text-sm text-indigo-600 hover:text-indigo-500"
          >
            Volver al login
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMutation } from '@vue/apollo-composable'
import { VERIFICAR_EMAIL } from '../graphql/usuarioQueries'
import { 
  ArrowPathIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon 
} from '@heroicons/vue/24/outline'

const route = useRoute()
const router = useRouter()

const verifying = ref(true)
const success = ref(false)
const error = ref(false)
const errorMessage = ref('')
const canResend = ref(false)
const resending = ref(false)

// Extraer token de la URL
const token = route.params.token

// Mutación de verificación
const { mutate: verifyEmail } = useMutation(VERIFICAR_EMAIL)

// Verificar email al montar el componente
onMounted(async () => {
  if (!token) {
    showError('Token de verificación no válido')
    return
  }

  try {
    const { data } = await verifyEmail({ token })
    
    if (data?.verificarEmail?.success) {
      showSuccess()
    } else {
      showError(data?.verificarEmail?.message || 'No se pudo verificar el email')
    }
  } catch (err) {
    console.error('Error verificando email:', err)
    showError(err.message || 'Error al verificar el email')
  }
})

const showSuccess = () => {
  success.value = true
  error.value = false
  verifying.value = false
  canResend.value = false
}

const showError = (message) => {
  error.value = true
  success.value = false
  verifying.value = false
  errorMessage.value = message
  canResend.value = true
}

const handleResend = () => {
  // Redirige al login donde el usuario puede solicitar un nuevo enlace
  router.push({ 
    path: '/login', 
    query: { 
      message: 'Por favor, inicia sesión para solicitar un nuevo enlace de verificación' 
    } 
  })
}
</script>