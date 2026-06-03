<template>
  <div>
    <!-- Grid de Usuarios -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="usuario in usuarios"
        :key="usuario.id"
        class="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-all duration-200 cursor-pointer"
        @click="$emit('seleccionar-usuario', usuario)"
        :class="{ 
          'ring-2 ring-indigo-500 border-indigo-300': usuarioSeleccionado?.id === usuario.id,
          'cursor-default': usuarioSeleccionado
        }"
      >
        <!-- Header de la Tarjeta -->
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center space-x-3">
            <div class="relative">
              <div class="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center overflow-hidden">
                <img 
                  v-if="usuario.avatar" 
                  :src="usuario.avatar" 
                  alt="Avatar"
                  class="w-10 h-10 rounded-full object-cover"
                >
                <UserIcon v-else class="w-5 h-5 text-indigo-600" />
              </div>
              <div 
                v-if="usuario.email_verificado"
                class="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white flex items-center justify-center"
                title="Email verificado"
              >
                <CheckIcon class="w-2 h-2 text-white" />
              </div>
            </div>
            <div>
              <h3 class="font-semibold text-gray-900 text-sm leading-tight">
                {{ usuario.nombre }} {{ usuario.apellidos }}
              </h3>
              <p class="text-xs text-gray-500 truncate max-w-[150px]">{{ usuario.email }}</p>
            </div>
          </div>
          <div class="flex space-x-1">
            <button
              @click.stop="$emit('editar-usuario', usuario)"
              class="p-1 text-gray-400 hover:text-indigo-600 transition-colors"
              title="Editar usuario"
              :disabled="usuarioSeleccionado"
            >
              <PencilIcon class="w-4 h-4" />
            </button>
            <button
              @click.stop="$emit('eliminar-usuario', usuario)"
              class="p-1 text-gray-400 hover:text-red-600 transition-colors"
              title="Eliminar usuario"
              :disabled="usuarioSeleccionado"
            >
              <TrashIcon class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Información del Usuario -->
        <div class="space-y-2">
          <div class="flex items-center justify-between text-xs">
            <span class="text-gray-500">Organización</span>
            <span class="font-medium text-gray-900">
              {{ obtenerNombreOrganizacion(usuario.organizacion) }}
            </span>
          </div>
          <div class="flex items-center justify-between text-xs">
            <span class="text-gray-500">Localidad</span>
            <span class="font-medium text-gray-900">{{ usuario.localidad || 'No especificada' }}</span>
          </div>
          <div class="flex items-center justify-between text-xs">
            <span class="text-gray-500">Teléfono</span>
            <span class="font-medium text-gray-900">{{ usuario.telefono || 'No especificado' }}</span>
          </div>
        </div>

        <!-- Roles y Fecha -->
        <div class="mt-3 pt-3 border-t border-gray-100">
          <div class="flex flex-wrap gap-1 mb-2">
            <span
              v-for="rol in usuario.roles"
              :key="rol.id"
              class="inline-flex items-center px-2 py-1 rounded text-xs font-medium"
              :class="getRoleBadgeClass(rol.nombre)"
            >
              {{ rol.nombre }}
            </span>
          </div>
          <div class="flex justify-between items-center text-xs text-gray-400">
            <span>Creado: {{ formatFechaCorta(usuario.created_at) }}</span>
            <span v-if="usuario.ultimo_acceso">Último acceso</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Estado Vacío -->
    <div v-if="usuarios.length === 0" class="text-center py-12">
      <UsersIcon class="w-16 h-16 text-gray-300 mx-auto mb-4" />
      <h3 class="text-lg font-medium text-gray-900 mb-2">No se encontraron usuarios</h3>
      <p class="text-gray-500 mb-4">Intenta ajustar los filtros de búsqueda</p>
    </div>
  </div>
</template>

<script setup>
import { 
  UserIcon, 
  CheckIcon, 
  PencilIcon, 
  TrashIcon, 
  UsersIcon 
} from '@heroicons/vue/24/outline'

const props = defineProps({
  usuarios: {
    type: Array,
    default: () => []
  },
  usuarioSeleccionado: {
    type: Object,
    default: null
  },
  organizaciones: {
    type: Array,
    default: () => []
  }
})

defineEmits(['seleccionar-usuario', 'editar-usuario', 'eliminar-usuario'])

const obtenerNombreOrganizacion = (orgId) => {
  if (orgId === 'particular') return 'Particular'
  const org = props.organizaciones.find(o => o.id === orgId)
  return org ? org.nombre : 'Organización desconocida'
}

const getRoleBadgeClass = (roleName) => {
  const classes = {
    'Administrador': 'bg-red-100 text-red-800',
    'Configurador': 'bg-blue-100 text-blue-800',
    'Grabador': 'bg-green-100 text-green-800',
    'Lector': 'bg-gray-100 text-gray-800'
  }
  return classes[roleName] || 'bg-gray-100 text-gray-800'
}

const formatFechaCorta = (fecha) => {
  return new Date(fecha).toLocaleDateString('es-ES')
}
</script>