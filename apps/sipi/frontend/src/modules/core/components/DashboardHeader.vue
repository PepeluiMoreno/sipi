<!-- src/modules/core/components/DashboardHeader.vue -->
<template>
  <header class="bg-white border-b border-gray-200 px-6 py-3 h-16">
    <div class="flex justify-between items-center h-full">
      <!-- Nombre de la aplicación sin logo -->
      <div class="flex items-center">
        <h1 class="text-xl font-bold text-gray-900">SIPI (versión beta) - Sistema de Información del Patrimonio Inmatriculado</h1>
      </div>

      <!-- Fecha, hora y usuario -->
      <div class="flex items-center space-x-6">
        <!-- Fecha y hora -->
        <div class="flex items-center space-x-4">
          <div class="text-sm text-gray-600">
            {{ currentDate }}
          </div>
          <div class="text-md font-semibold text-gray-900">
            {{ currentTime }}
          </div>
        </div>

        <!-- Notificaciones y perfil -->
        <div class="flex items-center space-x-3">
          <!-- Campana de notificaciones -->
          <button 
            @click="toggleNotifications"
            class="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <BellIcon class="w-5 h-5" />
            <span v-if="unreadNotifications > 0" 
                  class="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center text-[10px]">
              {{ unreadNotifications }}
            </span>
          </button>

          <!-- Menú de usuario -->
          <div class="relative">
            <button 
              @click="toggleUserMenu"
              class="flex items-center space-x-2 p-1 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div class="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center">
                <span class="text-sm font-medium text-indigo-600">
                  {{ userInitial }}
                </span>
              </div>
              <ChevronDownIcon class="w-4 h-4 text-gray-400" />
            </button>

            <!-- Dropdown menu -->
            <div v-if="showUserMenu" 
                 class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
              <div class="px-4 py-2 border-b border-gray-100">
                <p class="text-sm font-medium text-gray-900">{{ user.nombre || 'Usuario' }}</p>
                <p class="text-xs text-gray-500 truncate">{{ user.email || 'usuario@sistema.com' }}</p>
              </div>
              <button 
                @click="logout"
                class="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
              >
                <ArrowRightOnRectangleIcon class="w-4 h-4 mr-3" />
                Cerrar Sesión
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useAuthStore } from '../../../stores/auth'
import { 
  BellIcon, 
  ChevronDownIcon, 
  ArrowRightOnRectangleIcon 
} from '@heroicons/vue/24/outline'

const authStore = useAuthStore()
const showUserMenu = ref(false)
const currentTime = ref('')
const currentDate = ref('')
const unreadNotifications = ref(3) // Mock data

const user = computed(() => authStore.user || {
  nombre: 'Administrador',
  email: 'admin@sistema.com'
})

const userInitial = computed(() => {
  const name = user.value.nombre || user.value.email || 'U'
  return name.charAt(0).toUpperCase()
})

const updateDateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('es-ES', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
  currentDate.value = now.toLocaleDateString('es-ES', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
}

const toggleNotifications = () => {
  // TODO: Implementar panel de notificaciones
  console.log('Abrir notificaciones')
}

const logout = () => {
  authStore.logout()
  // Redirigir al login
  window.location.href = '/login'
}

let timeInterval

onMounted(() => {
  updateDateTime()
  timeInterval = setInterval(updateDateTime, 60000) // Actualizar cada minuto
})

onUnmounted(() => {
  clearInterval(timeInterval)
})
</script>