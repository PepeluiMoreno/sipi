<!-- src/layouts/DashboardLayout.vue -->
<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <DashboardHeader />
    
    <div class="flex flex-1">
      <DashboardSidebar />
      
      <main class="flex-1 p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import DashboardHeader from '../modules/core/components/DashboardHeader.vue'  // ✅ CORREGIDO
import DashboardSidebar from '../modules/core/components/DashboardSidebar.vue'  // ✅ CORREGIDO
</script>