<template>
  <div class="min-h-screen bg-gray-50 p-6" :class="{ 'overflow-hidden': usuarioSeleccionado }">
    <!-- Overlay cuando el panel de detalles está abierto -->
    <div
      v-if="usuarioSeleccionado"
      class="fixed inset-0 bg-black bg-opacity-50 z-30 transition-opacity duration-300"
      @click="usuarioSeleccionado = null"
    />

    <!-- Header Principal -->
    <div class="mb-6 relative z-10">
      <div class="flex justify-between items-start">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Gestión de Usuarios</h1>
          <p class="text-gray-600 mt-1">Administre usuarios, roles y permisos del sistema</p>
        </div>
        <div class="flex space-x-3">
          <button
            @click="mostrarModalUsuario = true"
            class="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors flex items-center text-sm font-medium"
            :disabled="usuarioSeleccionado"
            :class="{ 'opacity-50 cursor-not-allowed': usuarioSeleccionado }"
          >
            <PlusIcon class="w-4 h-4 mr-2" />
            Nuevo Usuario
          </button>
          <button
            @click="mostrarModalRol = true"
            class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center text-sm font-medium"
            :disabled="usuarioSeleccionado"
            :class="{ 'opacity-50 cursor-not-allowed': usuarioSeleccionado }"
          >
            <PlusIcon class="w-4 h-4 mr-2" />
            Nuevo Rol
          </button>
        </div>
      </div>
    </div>

    <!-- Panel de Control -->
    <div class="grid grid-cols-1 xl:grid-cols-4 gap-6 relative z-10">
      <!-- Filtros -->
      <UsuarioFilters
        :usuarios="usuarios"
        :roles="roles"
        :organizaciones="organizaciones"
        :filtros="filtros"
        :usuario-seleccionado="usuarioSeleccionado"
        @update-filtros="actualizarFiltros"
        @reset-filtros="resetearFiltros"
        class="xl:col-span-1"
      />

      <!-- Contenido Principal -->
      <div class="xl:col-span-3" :class="{ 'opacity-50 pointer-events-none': usuarioSeleccionado }">
        <!-- Barra de Herramientas -->
        <UsuarioToolbar
          :total-resultados="usuariosFiltrados.length"
          :busqueda="filtros.busqueda"
          :usuario-seleccionado="usuarioSeleccionado"
          @update-busqueda="actualizarBusqueda"
          @reset-filtros="resetearFiltros"
          @nuevo-usuario="mostrarModalUsuario = true"
          class="mb-4"
        />

        <!-- Grid de Usuarios -->
        <UsuarioGrid
          :usuarios="usuariosFiltrados"
          :usuario-seleccionado="usuarioSeleccionado"
          :organizaciones="organizaciones"
          @seleccionar-usuario="seleccionarUsuario"
          @editar-usuario="editarUsuario"
          @eliminar-usuario="eliminarUsuario"
        />
      </div>
    </div>

    <!-- Panel de Detalles -->
    <UsuarioDetailPanel
      v-if="usuarioSeleccionado"
      :usuario="usuarioSeleccionado"
      :organizaciones="organizaciones"
      :roles-disponibles="roles"
      @cerrar="usuarioSeleccionado = null"
      @editar-usuario="editarUsuario"
      @eliminar-usuario="eliminarUsuario"
      @quitar-rol="quitarRol"
      @roles-actualizados="onRolesActualizados"
    />

    <!-- Modales -->
    <UsuarioFormModal
      v-if="mostrarModalUsuario"
      :user="usuarioEditando"
      :is-editing="!!usuarioEditando"
      @save="guardarUsuario"
      @close="cerrarModalUsuario"
    />

    <RoleFormModal
      v-if="mostrarModalRol"
      :role="rolEditando"
      :is-editing="!!rolEditando"
      @save="guardarRol"
      @close="cerrarModalRol"
    />

    <DeleteConfirmationModal
      v-if="mostrarModalEliminar"
      :item="itemAEliminar"
      item-type="user"
      @confirm="confirmarEliminacion"
      @cancel="cancelarEliminacion"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { PlusIcon } from '@heroicons/vue/24/outline'

// Components
import UsuarioFilters from '../components/UsuarioFilters.vue'
import UsuarioGrid from '../components/UsuarioGrid.vue'
import UsuarioDetailPanel from '../components/UsuarioDetailPanel.vue'
import UsuarioToolbar from '../components/UsuarioToolbar.vue'
import UsuarioFormModal from '../components/UsuarioFormModal.vue'
import RoleFormModal from '../components/RoleFormModal.vue'
import DeleteConfirmationModal from '../components/DeleteConfirmationModal.vue'

// Mocks
import { mockUsers, mockRoles, mockOrganizaciones } from '../mocks/usuariosMocks'

// Estado
const usuarios = ref([])
const roles = ref([])
const organizaciones = ref([])
const usuarioSeleccionado = ref(null)
const usuarioEditando = ref(null)
const rolEditando = ref(null)
const itemAEliminar = ref(null)

// Filtros unificados
const filtros = ref({
  busqueda: '',
  tipoOrganizacion: '',
  organizacionEspecifica: '',
  estado: '',
  rol: ''
})

// Modales
const mostrarModalUsuario = ref(false)
const mostrarModalRol = ref(false)
const mostrarModalEliminar = ref(false)

// Computed
const usuariosFiltrados = computed(() => {
  return usuarios.value.filter(usuario => aplicarFiltros(usuario, filtros.value))
})

// Métodos de filtrado
const aplicarFiltros = (usuario, filtros) => {
  // Filtro de búsqueda
  if (filtros.busqueda) {
    const termino = filtros.busqueda.toLowerCase()
    const textoBusqueda = `${usuario.nombre} ${usuario.apellidos} ${usuario.email} ${usuario.localidad}`.toLowerCase()
    if (!textoBusqueda.includes(termino)) return false
  }

  // Filtro de organización
  if (filtros.tipoOrganizacion === 'particular') {
    if (usuario.organizacion !== 'particular') return false
  } else if (filtros.tipoOrganizacion === 'organizacion') {
    if (!filtros.organizacionEspecifica) return false
    if (usuario.organizacion !== filtros.organizacionEspecifica) return false
  }

  // Filtro de estado
  if (filtros.estado === 'verificado' && !usuario.email_verificado) return false
  if (filtros.estado === 'no-verificado' && usuario.email_verificado) return false

  // Filtro de rol
  if (filtros.rol) {
    const tieneRol = usuario.roles.some(rol => rol.id === filtros.rol)
    if (!tieneRol) return false
  }

  return true
}

// Event handlers
const actualizarFiltros = (nuevosFiltros) => {
  filtros.value = { ...filtros.value, ...nuevosFiltros }
}

const actualizarBusqueda = (busqueda) => {
  filtros.value.busqueda = busqueda
}

const resetearFiltros = () => {
  filtros.value = {
    busqueda: '',
    tipoOrganizacion: '',
    organizacionEspecifica: '',
    estado: '',
    rol: ''
  }
}

const seleccionarUsuario = (usuario) => {
  usuarioSeleccionado.value = usuario
}

const editarUsuario = (usuario) => {
  usuarioEditando.value = usuario
  mostrarModalUsuario.value = true
  usuarioSeleccionado.value = null
}

const eliminarUsuario = (usuario) => {
  itemAEliminar.value = usuario
  mostrarModalEliminar.value = true
}

const quitarRol = (usuario, rol) => {
  // Actualizar usuario quitando el rol
  const usuarioIndex = usuarios.value.findIndex(u => u.id === usuario.id)
  if (usuarioIndex !== -1) {
    const usuarioActualizado = {
      ...usuarios.value[usuarioIndex],
      roles: usuarios.value[usuarioIndex].roles.filter(r => r.id !== rol.id)
    }
    usuarios.value[usuarioIndex] = usuarioActualizado
    
    // Actualizar usuario seleccionado si es el mismo
    if (usuarioSeleccionado.value?.id === usuario.id) {
      usuarioSeleccionado.value = usuarioActualizado
    }
  }
}

const onRolesActualizados = (usuarioActualizado) => {
  const index = usuarios.value.findIndex(u => u.id === usuarioActualizado.id)
  if (index !== -1) {
    usuarios.value[index] = usuarioActualizado
  }
  
  // Actualizar usuario seleccionado si es el mismo
  if (usuarioSeleccionado.value?.id === usuarioActualizado.id) {
    usuarioSeleccionado.value = usuarioActualizado
  }
}

const guardarUsuario = (userData) => {
  if (usuarioEditando.value) {
    // Actualizar usuario existente
    const index = usuarios.value.findIndex(u => u.id === usuarioEditando.value.id)
    if (index !== -1) {
      const usuarioActualizado = {
        ...usuarios.value[index],
        ...userData,
        updated_at: new Date().toISOString()
      }
      usuarios.value[index] = usuarioActualizado
      
      // Actualizar usuario seleccionado si es el mismo
      if (usuarioSeleccionado.value?.id === usuarioActualizado.id) {
        usuarioSeleccionado.value = usuarioActualizado
      }
    }
  } else {
    // Crear nuevo usuario
    const nuevoUsuario = {
      ...userData,
      id: Date.now().toString(),
      email_verificado: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    usuarios.value.unshift(nuevoUsuario)
  }
  cerrarModalUsuario()
}

const guardarRol = (rolData) => {
  if (rolEditando.value) {
    // Actualizar rol existente
    const index = roles.value.findIndex(r => r.id === rolEditando.value.id)
    if (index !== -1) {
      roles.value[index] = {
        ...roles.value[index],
        ...rolData,
        updated_at: new Date().toISOString()
      }
    }
  } else {
    // Crear nuevo rol
    const nuevoRol = {
      ...rolData,
      id: Date.now().toString(),
      usuarios_count: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    roles.value.unshift(nuevoRol)
  }
  cerrarModalRol()
}

const confirmarEliminacion = () => {
  usuarios.value = usuarios.value.filter(u => u.id !== itemAEliminar.value.id)
  if (usuarioSeleccionado.value?.id === itemAEliminar.value.id) {
    usuarioSeleccionado.value = null
  }
  mostrarModalEliminar.value = false
  itemAEliminar.value = null
}

const cancelarEliminacion = () => {
  mostrarModalEliminar.value = false
  itemAEliminar.value = null
}

const cerrarModalUsuario = () => {
  mostrarModalUsuario.value = false
  usuarioEditando.value = null
}

const cerrarModalRol = () => {
  mostrarModalRol.value = false
  rolEditando.value = null
}

// Inicialización
onMounted(() => {
  usuarios.value = mockUsers
  roles.value = mockRoles
  organizaciones.value = mockOrganizaciones
})
</script>