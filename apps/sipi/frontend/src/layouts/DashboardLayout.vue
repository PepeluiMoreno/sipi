<!-- src/layouts/DashboardLayout.vue
     Shell a altura de viewport: NADA de scroll de página. El contenido
     (router-view) ocupa exactamente el alto restante y scrollea internamente. -->
<template>
  <div class="h-screen overflow-hidden bg-zinc-100 flex flex-col">
    <DashboardHeader class="shrink-0" />

    <div class="flex flex-1 min-h-0">
      <DashboardSidebar class="shrink-0" />

      <!-- Gutter común a todas las vistas: margen a ambos lados (y arriba/abajo) -->
      <main class="flex-1 min-h-0 overflow-hidden px-6 py-4">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import DashboardHeader from '../modules/core/components/DashboardHeader.vue'
import DashboardSidebar from '../modules/core/components/DashboardSidebar.vue'
</script>
