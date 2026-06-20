<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Configuración del Sistema</h1>
    
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Tipologías -->
      <router-link 
        to="/config/tipologias"
        class="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow cursor-pointer"
      >
        <div class="flex items-center space-x-4">
          <div class="p-3 bg-indigo-100 rounded-lg">
            <Cog6ToothIcon class="w-8 h-8 text-indigo-600" />
          </div>
          <div>
            <h3 class="font-semibold text-gray-900">Tipologías del Sistema</h3>
            <p class="text-sm text-gray-500">Gestionar estados, tipos, roles...</p>
          </div>
        </div>
      </router-link>

      <!-- Usuarios (deshabilitado) -->
      <div class="bg-white rounded-lg shadow p-6 opacity-50 cursor-not-allowed">
        <div class="flex items-center space-x-4">
          <div class="p-3 bg-gray-100 rounded-lg">
            <UsersIcon class="w-8 h-8 text-gray-600" />
          </div>
          <div>
            <h3 class="font-semibold text-gray-900">Gestión de Usuarios</h3>
            <p class="text-sm text-gray-500">Usuarios y permisos (próximamente)</p>
          </div>
        </div>
      </div>

      <!-- Backup (deshabilitado) -->
      <div class="bg-white rounded-lg shadow p-6 opacity-50 cursor-not-allowed">
        <div class="flex items-center space-x-4">
          <div class="p-3 bg-gray-100 rounded-lg">
            <CloudArrowUpIcon class="w-8 h-8 text-gray-600" />
          </div>
          <div>
            <h3 class="font-semibold text-gray-900">Backup y Exportación</h3>
            <p class="text-sm text-gray-500">Exportar/importar datos (próximamente)</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Vista anidada para /config/tipologias -->
    <router-view class="mt-8" />
  </div>
</template>

<script setup>
import { Cog6ToothIcon, UsersIcon, CloudArrowUpIcon } from '@heroicons/vue/24/outline'
</script>