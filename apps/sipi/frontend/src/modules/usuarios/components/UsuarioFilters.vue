<template>
  <div class="space-y-4" :class="{ 'opacity-50 pointer-events-none': usuarioSeleccionado }">
    <!-- Tarjetas de Métricas -->
    <div class="grid grid-cols-2 gap-3">
      <div class="bg-white rounded-lg border border-gray-200 p-3 text-center">
        <UsersIcon class="w-6 h-6 text-blue-600 mx-auto mb-1" />
        <div class="text-lg font-bold text-gray-900">{{ usuarios.length }}</div>
        <div class="text-xs text-gray-500">Usuarios</div>
      </div>
      <div class="bg-white rounded-lg border border-gray-200 p-3 text-center">
        <ShieldCheckIcon class="w-6 h-6 text-green-600 mx-auto mb-1" />
        <div class="text-lg font-bold text-gray-900">{{ roles.length }}</div>
        <div class="text-xs text-gray-500">Roles</div>
      </div>
    </div>

    <!-- Filtro de Organización -->
    <div class="bg-white rounded-lg border border-gray-200 p-4">
      <h3 class="font-semibold text-gray-900 text-sm mb-3">Organización</h3>
      <div class="space-y-3">
        <!-- Radio para Todos -->
        <label class="flex items-center">
          <input
            v-model="filtrosLocales.tipoOrganizacion"
            type="radio"
            value=""
            class="w-4 h-4 text-indigo-600 border-gray-300 focus:ring-indigo-500"
            :disabled="usuarioSeleccionado"
            @change="emitirFiltros"
          >
          <span class="ml-2 text-sm text-gray-700">Todos los usuarios</span>
        </label>

        <!-- Radio para Particular -->
        <label class="flex items-center">
          <input
            v-model="filtrosLocales.tipoOrganizacion"
            type="radio"
            value="particular"
            class="w-4 h-4 text-indigo-600 border-gray-300 focus:ring-indigo-500"
            :disabled="usuarioSeleccionado"
            @change="emitirFiltros"
          >
          <span class="ml-2 text-sm text-gray-700">Particular</span>
          <span class="ml-2 text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded-full">
            {{ contarUsuariosPorTipo('particular') }}
          </span>
        </label>

        <!-- Radio para Miembro de organización -->
        <label class="flex items-center">
          <input
            v-model="filtrosLocales.tipoOrganizacion"
            type="radio"
            value="organizacion"
            class="w-4 h-4 text-indigo-600 border-gray-300 focus:ring-indigo-500"
            :disabled="usuarioSeleccionado"
            @change="emitirFiltros"
          >
          <span class="ml-2 text-sm text-gray-700">Miembro de:</span>
        </label>

        <!-- Combo de organizaciones (solo visible cuando se selecciona "Miembro de") -->
        <div v-if="filtrosLocales.tipoOrganizacion === 'organizacion'" class="ml-6 mt-2">
          <select
            v-model="filtrosLocales.organizacionEspecifica"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
            :disabled="usuarioSeleccionado"
            @change="emitirFiltros"
          >
            <option value="">Todas las organizaciones</option>
            <option 
              v-for="org in organizacionesFiltradas" 
              :key="org.id" 
              :value="org.id"
            >
              {{ org.nombre }} ({{ contarUsuariosPorOrganizacion(org.id) }})
            </option>
          </select>
        </div>
      </div>
    </div>

    <!-- Filtro de Estado -->
    <div class="bg-white rounded-lg border border-gray-200 p-4">
      <h3 class="font-semibold text-gray-900 text-sm mb-3">Estado</h3>
      <div class="space-y-2">
        <label class="flex items-center">
          <input
            v-model="filtrosLocales.estado"
            type="radio"
            value=""
            class="w-4 h-4 text-indigo-600 border-gray-300 focus:ring-indigo-500"
            :disabled="usuarioSeleccionado"
            @change="emitirFiltros"
          >
          <span class="ml-2 text-sm text-gray-700">Todos los estados</span>
        </label>
        <label class="flex items-center">
          <input
            v-model="filtrosLocales.estado"
            type="radio"
            value="verificado"
            class="w-4 h-4 text-indigo-600 border-gray-300 focus:ring-indigo-500"
            :disabled="usuarioSeleccionado"
            @change="emitirFiltros"
          >
          <span class="ml-2 text-sm text-gray-700">Email verificado</span>
        </label>
        <label class="flex items-center">
          <input
            v-model="filtrosLocales.estado"
            type="radio"
            value="no-verificado"
            class="w-4 h-4 text-indigo-600 border-gray-300 focus:ring-indigo-500"
            :disabled="usuarioSeleccionado"
            @change="emitirFiltros"
          >
          <span class="ml-2 text-sm text-gray-700">Email no verificado</span>
        </label>
      </div>
    </div>

    <!-- Filtro de Rol -->
    <div class="bg-white rounded-lg border border-gray-200 p-4">
      <h3 class="font-semibold text-gray-900 text-sm mb-3">Rol</h3>
      <select
        v-model="filtrosLocales.rol"
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
        :disabled="usuarioSeleccionado"
        @change="emitirFiltros"
      >
        <option value="">Todos los roles</option>
        <option 
          v-for="rol in roles" 
          :key="rol.id" 
          :value="rol.id"
        >
          {{ rol.nombre }}
        </option>
      </select>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { UsersIcon, ShieldCheckIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  usuarios: {
    type: Array,
    default: () => []
  },
  roles: {
    type: Array,
    default: () => []
  },
  organizaciones: {
    type: Array,
    default: () => []
  },
  filtros: {
    type: Object,
    default: () => ({
      tipoOrganizacion: '',
      organizacionEspecifica: '',
      estado: '',
      rol: ''
    })
  },
  usuarioSeleccionado: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update-filtros', 'reset-filtros'])

// Estado local para los filtros
const filtrosLocales = ref({ ...props.filtros })

// Sincronizar cuando cambien los props
watch(() => props.filtros, (nuevosFiltros) => {
  filtrosLocales.value = { ...nuevosFiltros }
}, { deep: true })

const organizacionesFiltradas = computed(() => {
  return props.organizaciones.filter(org => org.id !== 'particular')
})

const contarUsuariosPorOrganizacion = (orgId) => {
  return props.usuarios.filter(user => user.organizacion === orgId).length
}

const contarUsuariosPorTipo = (tipo) => {
  if (tipo === 'particular') {
    return props.usuarios.filter(user => user.organizacion === 'particular').length
  }
  return 0
}

const emitirFiltros = () => {
  emit('update-filtros', { ...filtrosLocales.value })
}
</script>