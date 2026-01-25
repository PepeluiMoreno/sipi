<!-- src/modules/core/layouts/DashboardLayout.vue -->
<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <DashboardHeader />
    
    <div class="flex flex-1">
      <aside class="w-56 bg-indigo-800 text-white flex flex-col">
        <nav class="p-3 space-y-0.5 flex-1 overflow-y-auto">
          <!-- Dashboard -->
          <router-link
            to="/"
            class="flex items-center px-3 py-2 rounded-lg transition-colors group text-sm"
            :class="[
              $route.path === '/'
                ? 'bg-indigo-900 text-white'
                : 'text-indigo-100 hover:bg-indigo-700 hover:text-white'
            ]"
          >
            <HomeIcon class="w-5 h-5 mr-3" />
            <span class="font-medium">Dashboard</span>
          </router-link>

           <!-- Inmuebles -->
           <router-link
             to="/inmueble-index"
             class="flex items-center px-3 py-2 rounded-lg transition-colors group text-sm"
            :class="[
              $route.path.includes('/inmueble')
                ? 'bg-indigo-900 text-white'
                : 'text-indigo-100 hover:bg-indigo-700 hover:text-white'
            ]"
          >
            <BuildingOfficeIcon class="w-5 h-5 mr-3" />
            <span class="font-medium">Inmuebles</span>
          </router-link>

           <!-- Documentos -->
           <router-link
             to="/documentos"
             class="flex items-center px-3 py-2 rounded-lg transition-colors group text-sm"
            :class="[
              $route.path.includes('/documentos')
                ? 'bg-indigo-900 text-white'
                : 'text-indigo-100 hover:bg-indigo-700 hover:text-white'
            ]"
          >
            <DocumentTextIcon class="w-5 h-5 mr-3" />
            <span class="font-medium">Documentos</span>
          </router-link>

          <!-- ACTUACIONES - DESHABILITADO (módulo no implementado) -->
          <!--
          <router-link
            to="/actuaciones"
            class="flex items-center px-4 py-3 rounded-lg transition-colors group"
            :class="[
              $route.path.includes('/actuaciones')
                ? 'bg-indigo-900 text-white'
                : 'text-indigo-100 hover:bg-indigo-700 hover:text-white'
            ]"
          >
            <WrenchScrewdriverIcon class="w-5 h-5 mr-3" />
            <span class="font-medium">Actuaciones</span>
          </router-link>
          -->

          <!-- TRANSMISIONES - DESHABILITADO (módulo no implementado) -->
          <!--
          <router-link
            to="/transmisiones"
            class="flex items-center px-4 py-3 rounded-lg transition-colors group"
            :class="[
              $route.path.includes('/transmisiones')
                ? 'bg-indigo-900 text-white'
                : 'text-indigo-100 hover:bg-indigo-700 hover:text-white'
            ]"
          >
            <ArrowsRightLeftIcon class="w-5 h-5 mr-3" />
            <span class="font-medium">Transmisiones</span>
          </router-link>
          -->

          <!-- MENÚ AGENTES -->
          <div class="pt-2">
             <button
               @click="toggleAgentesMenu"
               class="flex items-center justify-between w-full px-3 py-2 rounded-lg transition-colors group text-sm text-indigo-100 hover:bg-indigo-700 hover:text-white"
            >
              <div class="flex items-center">
                <BuildingLibraryIcon class="w-5 h-5 mr-3" />
                <span class="font-medium">Agentes</span>
              </div>
              <ChevronDownIcon 
                class="w-4 h-4 transition-transform" 
                :class="{ 'rotate-180': isAgentesMenuOpen }" 
              />
            </button>
            
            <div v-if="isAgentesMenuOpen" class="ml-8 space-y-1 mt-1">
               <router-link
                 to="/administraciones"
                 class="flex items-center px-3 py-1.5 rounded-lg transition-colors group text-xs"
                :class="[
                  $route.path.includes('/administraciones')
                    ? 'bg-indigo-900 text-white'
                    : 'text-indigo-100 hover:bg-indigo-700 hover:text-white'
                ]"
              >
                <BuildingOfficeIcon class="w-4 h-4 mr-3" />
                <span class="text-sm">Administraciones</span>
              </router-link>

               <router-link
                 to="/notarias"
                 class="flex items-center px-3 py-1.5 rounded-lg transition-colors group text-xs"
                :class="[
                  $route.path.includes('/notarias')
                    ? 'bg-indigo-900 text-white'
                    : 'text-indigo-100 hover:bg-indigo-700 hover:text-white'
                ]"
              >
                <ScaleIcon class="w-4 h-4 mr-3" />
                <span class="text-sm">Notarías</span>
              </router-link>

               <router-link
                 to="/registros-propiedad"
                 class="flex items-center px-3 py-1.5 rounded-lg transition-colors group text-xs"
                :class="[
                  $route.path.includes('/registros-propiedad')
                    ? 'bg-indigo-900 text-white'
                    : 'text-indigo-100 hover:bg-indigo-700 hover:text-white'
                ]"
              >
                <DocumentDuplicateIcon class="w-4 h-4 mr-3" />
                <span class="text-sm">Registros Propiedad</span>
              </router-link>

               <router-link
                 to="/entidades-religiosas"
                 class="flex items-center px-3 py-1.5 rounded-lg transition-colors group text-xs"
                :class="[
                  $route.path.includes('/entidades-religiosas')
                    ? 'bg-indigo-900 text-white'
                    : 'text-indigo-100 hover:bg-indigo-700 hover:text-white'
                ]"
              >
                <BuildingLibraryIcon class="w-4 h-4 mr-3" />
                <span class="text-sm">Entidades Religiosas</span>
              </router-link>
            </div>
          </div>

          <!-- Configuración -->
          <div class="pt-2">
             <button
               @click="toggleConfigMenu"
               class="flex items-center justify-between w-full px-3 py-2 rounded-lg transition-colors group text-sm text-indigo-100 hover:bg-indigo-700 hover:text-white"
            >
              <div class="flex items-center">
                <Cog6ToothIcon class="w-5 h-5 mr-3" />
                <span class="font-medium">Configuración</span>
              </div>
              <ChevronDownIcon 
                class="w-4 h-4 transition-transform" 
                :class="{ 'rotate-180': isConfigMenuOpen }" 
              />
            </button>
            
            <div v-if="isConfigMenuOpen" class="ml-8 space-y-1 mt-1">
               <router-link
                 to="/config/procesos"
                 class="flex items-center px-3 py-1.5 rounded-lg transition-colors group text-xs"
                :class="[
                  $route.path.includes('/config/procesos')
                    ? 'bg-indigo-900 text-white'
                    : 'text-indigo-100 hover:bg-indigo-700 hover:text-white'
                ]"
              >
                <WrenchScrewdriverIcon class="w-4 h-4 mr-3" />
                <span class="text-sm">Definición de Procesos</span>
              </router-link>

               <router-link
                 to="/config/tipologias"
                 class="flex items-center px-3 py-1.5 rounded-lg transition-colors group text-xs"
                :class="[
                  $route.path.includes('/config/tipologias')
                    ? 'bg-indigo-900 text-white'
                    : 'text-indigo-100 hover:bg-indigo-700 hover:text-white'
                ]"
              >
                <BookOpenIcon class="w-4 h-4 mr-3" />
                <span class="text-sm">Tipologías</span>
              </router-link>

               <router-link
                 to="/config/usuarios"
                 class="flex items-center px-3 py-1.5 rounded-lg transition-colors group text-xs"
                :class="[
                  $route.path.includes('/config/usuarios')
                    ? 'bg-indigo-900 text-white'
                    : 'text-indigo-100 hover:bg-indigo-700 hover:text-white'
                ]"
              >
                <UserGroupIcon class="w-4 h-4 mr-3" />
                <span class="text-sm">Usuarios y Roles</span>
              </router-link>
            </div>
          </div>
        </nav>

         <!-- Footer del Sidebar: Estado del Sistema y Usuario -->
         <div class="p-3 border-t border-indigo-700 bg-indigo-900/50">
           <!-- System Status Component -->
           <SystemStatus />

           <!-- Usuario Conectado -->
           <div v-if="authStore.isAuthenticated && authStore.user">
             <div class="flex items-center space-x-2">
               <UserCircleIcon class="w-6 h-6 text-indigo-300" />
               <div class="flex-1 min-w-0">
                 <p class="text-xs font-medium text-white truncate">{{ authStore.user.nombre || 'Usuario' }}</p>
                 <p class="text-[10px] text-indigo-200 truncate">{{ authStore.user.email || authStore.user.username || '' }}</p>
               </div>
             </div>
           </div>
         </div>
      </aside>

      <main class="flex-1 p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
 import { ref } from 'vue'
 import { useAuthStore } from '../stores/auth'
 import DashboardHeader from '../components/DashboardHeader.vue'
 import SystemStatus from '../components/SystemStatus.vue'
 import {
   HomeIcon,
   BuildingOfficeIcon,
   DocumentTextIcon,
   WrenchScrewdriverIcon,
   BookOpenIcon,
   Cog6ToothIcon,
   ChevronDownIcon,
   UserGroupIcon,
   BuildingLibraryIcon,
   ScaleIcon,
   DocumentDuplicateIcon,
   UserCircleIcon
 } from '@heroicons/vue/24/outline'

 const authStore = useAuthStore()
 const isConfigMenuOpen = ref(false)
 const isAgentesMenuOpen = ref(false)

 const toggleConfigMenu = () => {
   isConfigMenuOpen.value = !isConfigMenuOpen.value
 }

 const toggleAgentesMenu = () => {
   isAgentesMenuOpen.value = !isAgentesMenuOpen.value
 }
</script>