<!-- DashboardSidebar.vue -->
<template>
  <aside class="w-64 bg-gray-900 text-white flex flex-col">
    <div class="p-4 border-b border-gray-800">
      <h1 class="text-xl font-bold">SIPI</h1>
      <p class="text-xs text-gray-400">Sistema de Información</p>
    </div>

    <nav class="flex-1 overflow-y-auto p-4">
      <div class="space-y-1">
        <!-- Dashboard -->
        <router-link
          to="/"
          class="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors"
          :class="{ 'bg-gray-800': $route.path === '/' }"
        >
          <HomeIcon class="w-5 h-5" />
          <span>Dashboard</span>
        </router-link>

        <!-- Inmuebles -->
        <router-link
          to="/inmuebles"
          class="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors"
          :class="{ 'bg-gray-800': $route.path.startsWith('/inmuebles') }"
        >
          <BuildingLibraryIcon class="w-5 h-5" />
          <span>Inmuebles</span>
        </router-link>

        <!-- Agentes -->
        <div class="mt-6">
          <p class="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Agentes
          </p>
          <router-link
            to="/administraciones"
            class="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors"
            :class="{ 'bg-gray-800': $route.path === '/administraciones' }"
          >
            <BuildingOfficeIcon class="w-5 h-5" />
            <span>Administraciones</span>
          </router-link>
          <router-link
            to="/notarias"
            class="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors"
            :class="{ 'bg-gray-800': $route.path === '/notarias' }"
          >
            <ScaleIcon class="w-5 h-5" />
            <span>Notarías</span>
          </router-link>
          <router-link
            to="/registros-propiedad"
            class="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors"
            :class="{ 'bg-gray-800': $route.path === '/registros-propiedad' }"
          >
            <DocumentTextIcon class="w-5 h-5" />
            <span>Registros Propiedad</span>
          </router-link>
          <router-link
            to="/entidades-religiosas"
            class="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors"
            :class="{ 'bg-gray-800': $route.path === '/entidades-religiosas' }"
          >
            <BuildingLibraryIcon class="w-5 h-5" />
            <span>Entidades religiosas</span>
          </router-link>
        </div>

        <!-- Documentos -->
        <div class="mt-6">
          <p class="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Documentación
          </p>
          <router-link
            to="/documentos"
            class="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors"
            :class="{ 'bg-gray-800': $route.path === '/documentos' }"
          >
            <FolderIcon class="w-5 h-5" />
            <span>Documentos</span>
          </router-link>
        </div>

        <!-- Configuración -->
        <div class="mt-6">
          <p class="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Configuración
          </p>
          <router-link
            to="/config/catalogos"
            class="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors"
            :class="{ 'bg-gray-800': $route.path === '/config/catalogos' }"
          >
            <ListBulletIcon class="w-5 h-5" />
            <span>Catálogos</span>
          </router-link>
          <router-link
            to="/acceso"
            class="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors"
            :class="{ 'bg-gray-800': $route.path === '/acceso' }"
          >
            <ShieldCheckIcon class="w-5 h-5" />
            <span>Control de acceso</span>
          </router-link>
          <router-link
            to="/acceso/roles"
            class="flex items-center space-x-3 pl-11 pr-3 py-1.5 rounded-lg text-sm text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
            :class="{ 'bg-gray-800 text-white': $route.path === '/acceso/roles' }"
          >
            <span>Roles y permisos</span>
          </router-link>
          <router-link
            to="/config/parametros"
            class="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors"
            :class="{ 'bg-gray-800': $route.path === '/config/parametros' }"
          >
            <Cog6ToothIcon class="w-5 h-5" />
            <span>Parámetros generales</span>
          </router-link>
          <router-link
            to="/papelera"
            class="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors"
            :class="{ 'bg-gray-800': $route.path === '/papelera' }"
          >
            <TrashIcon class="w-5 h-5" />
            <span>Papelera</span>
          </router-link>
        </div>
      </div>
    </nav>

    <!-- Usuario actual + tiempo de conexión + cerrar sesión -->
    <div class="shrink-0 border-t border-gray-800 p-3">
      <div class="flex items-center gap-2.5">
        <router-link to="/mis-datos" title="Mis datos"
                     class="flex items-center gap-2.5 flex-1 min-w-0 rounded p-1 -m-1 hover:bg-gray-800">
          <AvatarImg :nombre="user?.nombre || user?.nombreUsuario" :apellido="user?.apellidos" size="sm" />
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium truncate">{{ user?.nombre || user?.nombreUsuario || 'Usuario' }}</p>
            <p class="text-xs text-gray-400 truncate">
              <span v-if="user?.isSistema">Sistema · </span>Conectado: {{ sessionTime }}
            </p>
          </div>
        </router-link>
        <button @click="logout" title="Cerrar sesión"
                class="p-1.5 rounded hover:bg-gray-800 text-gray-400 hover:text-white shrink-0">
          <ArrowRightOnRectangleIcon class="w-5 h-5" />
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import {
  HomeIcon,
  BuildingLibraryIcon,
  BuildingOfficeIcon,
  ScaleIcon,
  DocumentTextIcon,
  FolderIcon,
  ListBulletIcon,
  ShieldCheckIcon,
  ArrowRightOnRectangleIcon,
  Cog6ToothIcon,
  TrashIcon
} from '@heroicons/vue/24/outline'
import { useAuth } from '../../auth/composables/useAuth'
import { useSessionGuard } from '@/composables/useSessionGuard'
import AvatarImg from './AvatarImg.vue'

const { user, logout } = useAuth()
const { sessionTime } = useSessionGuard()  // arranca la vigilancia y expone el contador
</script>