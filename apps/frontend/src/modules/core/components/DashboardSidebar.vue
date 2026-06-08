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
            to="/config/usuarios"
            class="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors"
            :class="{ 'bg-gray-800': $route.path === '/config/usuarios' }"
          >
            <UsersIcon class="w-5 h-5" />
            <span>Usuarios</span>
          </router-link>
        </div>

        <!-- Datos abiertos -->
        <div class="mt-6">
          <p class="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
            Datos abiertos
          </p>
          <router-link
            to="/odm"
            class="flex items-center space-x-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors"
            :class="{ 'bg-gray-800': $route.path.startsWith('/odm') }"
          >
            <CircleStackIcon class="w-5 h-5" />
            <span>Recursos ODM</span>
          </router-link>
        </div>
      </div>
    </nav>
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
  UsersIcon,
  CircleStackIcon
} from '@heroicons/vue/24/outline'
</script>