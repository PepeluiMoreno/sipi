<template>
  <div class="fixed inset-y-0 right-0 w-96 bg-white shadow-xl z-40 transform transition-transform duration-300 ease-in-out"
       :class="panelAbierto ? 'translate-x-0' : 'translate-x-full'">
    
    <!-- Header del Panel -->
    <div class="flex items-center justify-between p-6 border-b border-gray-200">
      <div>
        <h2 class="text-lg font-semibold text-gray-900">Detalles del Usuario</h2>
        <p class="text-sm text-gray-500 mt-1">Información completa y roles</p>
      </div>
      <button
        @click="$emit('cerrar')"
        class="p-2 text-gray-400 hover:text-gray-600 transition-colors"
      >
        <XMarkIcon class="w-5 h-5" />
      </button>
    </div>

    <!-- Contenido del Panel -->
    <div class="p-6 space-y-6 overflow-y-auto max-h-[calc(100vh-80px)]">
      
      <!-- Información Básica -->
      <div>
        <h3 class="text-sm font-medium text-gray-900 mb-3">Información Básica</h3>
        <div class="space-y-3">
          <div class="flex justify-between">
            <span class="text-sm text-gray-500">Nombre completo</span>
            <span class="text-sm font-medium text-gray-900">{{ usuario.nombre }} {{ usuario.apellidos }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-sm text-gray-500">Email</span>
            <span class="text-sm font-medium text-gray-900">{{ usuario.email }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-sm text-gray-500">Teléfono</span>
            <span class="text-sm font-medium text-gray-900">{{ usuario.telefono || 'No especificado' }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-sm text-gray-500">Localidad</span>
            <span class="text-sm font-medium text-gray-900">{{ usuario.localidad || 'No especificada' }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-sm text-gray-500">Organización</span>
            <span class="text-sm font-medium text-gray-900">{{ obtenerNombreOrganizacion(usuario.organizacion) }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-sm text-gray-500">Estado</span>
            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                  :class="usuario.email_verificado ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'">
              {{ usuario.email_verificado ? 'Verificado' : 'No verificado' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Roles del Usuario -->
      <div>
        <h3 class="text-sm font-medium text-gray-900 mb-3">Roles Asignados</h3>
        
        <!-- Lista de Roles (solo lectura) -->
        <div class="space-y-2">
          <div
            v-for="rol in usuario.roles"
            :key="rol.id"
            class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
          >
            <div class="flex items-center space-x-3">
              <div class="w-2 h-2 rounded-full bg-indigo-500"></div>
              <div>
                <span class="text-sm font-medium text-gray-900">{{ rol.nombre }}</span>
                <p class="text-xs text-gray-500 mt-1">{{ rol.descripcion }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Mensaje cuando no hay roles -->
        <div v-if="usuario.roles.length === 0" class="text-center py-4">
          <ShieldExclamationIcon class="w-8 h-8 text-gray-300 mx-auto mb-2" />
          <p class="text-sm text-gray-500">El usuario no tiene roles asignados</p>
        </div>
      </div>

      <!-- Fechas -->
      <div>
        <h3 class="text-sm font-medium text-gray-900 mb-3">Registro de Actividad</h3>
        <div class="space-y-2">
          <div class="flex justify-between text-sm">
            <span class="text-gray-500">Fecha de creación</span>
            <span class="font-medium text-gray-900">{{ formatFecha(usuario.created_at) }}</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-gray-500">Última actualización</span>
            <span class="font-medium text-gray-900">{{ formatFecha(usuario.updated_at) }}</span>
          </div>
          <div v-if="usuario.ultimo_acceso" class="flex justify-between text-sm">
            <span class="text-gray-500">Último acceso</span>
            <span class="font-medium text-gray-900">{{ formatFecha(usuario.ultimo_acceso) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer del Panel -->
    <div class="absolute bottom-0 left-0 right-0 p-6 bg-white border-t border-gray-200">
      <div class="flex space-x-3">
        <button
          @click="$emit('editar-usuario', usuario)"
          class="flex-1 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium"
        >
          Editar Usuario
        </button>
        <button
          @click="$emit('eliminar-usuario', usuario)"
          class="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
        >
          Eliminar Usuario
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { 
  XMarkIcon,
  ShieldExclamationIcon
} from '@heroicons/vue/24/outline'
import { ref, watch } from 'vue'

const props = defineProps({
  usuario: {
    type: Object,
    required: true
  },
  organizaciones: {
    type: Array,
    default: () => []
  },
  rolesDisponibles: {
    type: Array,
    default: () => []
  }
})

defineEmits(['cerrar', 'editar-usuario', 'eliminar-usuario'])

const panelAbierto = ref(false)

watch(() => props.usuario, (newVal) => {
  if (newVal) {
    panelAbierto.value = true
  }
}, { immediate: true })

const obtenerNombreOrganizacion = (orgId) => {
  if (orgId === 'particular') return 'Particular'
  const org = props.organizaciones.find(o => o.id === orgId)
  return org ? org.nombre : 'Organización desconocida'
}

const formatFecha = (fecha) => {
  if (!fecha) return 'Nunca'
  return new Date(fecha).toLocaleDateString('es-ES', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>