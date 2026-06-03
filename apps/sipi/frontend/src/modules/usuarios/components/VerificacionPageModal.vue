<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-200">
        <div class="flex justify-between items-center">
          <h2 class="text-lg font-semibold text-gray-900">Página de Verificación de Email</h2>
          <button 
            @click="$emit('close')"
            class="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon class="w-6 h-6" />
          </button>
        </div>
        <p class="text-sm text-gray-500 mt-1">Vista previa de la página que ven los usuarios al verificar su email</p>
      </div>

      <!-- Contenido simulado de la página de verificación -->
      <div class="p-6">
        <!-- Simulación de diferentes estados -->
        <div class="mb-6">
          <h3 class="text-md font-medium text-gray-900 mb-3">Estados de la página:</h3>
          <div class="flex space-x-2 mb-4">
            <button 
              @click="currentState = 'loading'"
              class="px-3 py-1 text-xs bg-gray-200 rounded hover:bg-gray-300"
              :class="{ 'bg-indigo-600 text-white': currentState === 'loading' }"
            >
              Cargando
            </button>
            <button 
              @click="currentState = 'success'"
              class="px-3 py-1 text-xs bg-gray-200 rounded hover:bg-gray-300"
              :class="{ 'bg-indigo-600 text-white': currentState === 'success' }"
            >
              Éxito
            </button>
            <button 
              @click="currentState = 'error'"
              class="px-3 py-1 text-xs bg-gray-200 rounded hover:bg-gray-300"
              :class="{ 'bg-indigo-600 text-white': currentState === 'error' }"
            >
              Error
            </button>
          </div>
        </div>

        <!-- Simulación de la página real -->
        <div class="border-2 border-dashed border-gray-300 rounded-lg p-8 bg-gray-50">
          <div class="max-w-md mx-auto">
            <!-- Estado: Cargando -->
            <div v-if="currentState === 'loading'" class="text-center">
              <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
              <h2 class="text-xl font-bold text-gray-900 mb-2">Verificando tu email...</h2>
              <p class="text-gray-600">Estamos procesando tu solicitud de verificación.</p>
            </div>

            <!-- Estado: Éxito -->
            <div v-else-if="currentState === 'success'" class="text-center">
              <CheckCircleIcon class="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h2 class="text-xl font-bold text-gray-900 mb-2">¡Email Verificado!</h2>
              <p class="text-gray-600 mb-6">Tu dirección de email ha sido verificada correctamente.</p>
              <div class="space-y-3">
                <button class="w-full bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700">
                  Ir al Dashboard
                </button>
                <button class="w-full bg-gray-200 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-300">
                  Volver al Inicio
                </button>
              </div>
            </div>

            <!-- Estado: Error -->
            <div v-else-if="currentState === 'error'" class="text-center">
              <ExclamationTriangleIcon class="w-16 h-16 text-red-600 mx-auto mb-4" />
              <h2 class="text-xl font-bold text-gray-900 mb-2">Error de Verificación</h2>
              <p class="text-gray-600 mb-4">Ha ocurrido un problema al verificar tu email.</p>
              
              <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-left">
                <p class="text-sm text-red-700">
                  <span class="font-medium">Posibles causas:</span><br>
                  • El enlace ha expirado (24 horas)<br>
                  • El enlace ya fue utilizado<br>
                  • Error técnico del sistema
                </p>
              </div>
              
              <div class="space-y-3">
                <button class="w-full bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700">
                  Reenviar Email de Verificación
                </button>
                <button class="w-full bg-gray-200 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-300">
                  Contactar Soporte
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Información técnica -->
        <div class="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 class="text-sm font-medium text-blue-800 mb-2">Información Técnica:</h4>
          <ul class="text-sm text-blue-700 list-disc list-inside space-y-1">
            <li>URL real: <code class="bg-blue-100 px-1 rounded">/verificar-email/&#123;token&#125;</code></li>
            <li>Página pública - no requiere autenticación</li>
            <li>Los tokens expiran después de 24 horas</li>
            <li>Integración completa con el backend GraphQL</li>
          </ul>
        </div>

        <!-- Ejemplo de enlace de verificación -->
        <div class="mt-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">Ejemplo de enlace de verificación:</label>
          <div class="bg-gray-100 border border-gray-300 rounded-lg p-3">
            <code class="text-sm text-gray-800 break-all">
              https://sipi.com/verificar-email/a1b2c3d4-e5f6-7890-abcd-ef1234567890
            </code>
          </div>
        </div>
      </div>

      <!-- Botones -->
      <div class="px-6 py-4 border-t border-gray-200 bg-gray-50 flex justify-end">
        <button
          @click="$emit('close')"
          class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
        >
          Cerrar Vista Previa
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { 
  XMarkIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon 
} from '@heroicons/vue/24/outline'

defineEmits(['close'])

const currentState = ref('loading')

// Simular cambio automático de estados para demo
setTimeout(() => {
  currentState.value = 'success'
}, 2000)
</script>