<template>
  <div class="space-y-6">
    <!-- Información básica -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700">Código *</label>
        <input v-model="form.codigo" type="text" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2" required>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Categoría</label>
        <input v-model="form.categoria" type="text" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2">
      </div>
    </div>

    <!-- Configuración técnica -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700">API Endpoint</label>
        <input v-model="form.api_endpoint" type="url" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2">
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Frecuencia Sync (días)</label>
        <input v-model="form.frecuencia_sync_dias" type="number" min="1" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2">
      </div>
    </div>

    <!-- Configuración visual -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700">Icono</label>
        <input v-model="form.icono" type="text" placeholder="heroicon name" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2">
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Color</label>
        <div class="flex items-center space-x-2">
          <input v-model="form.color_hex" type="color" class="w-10 h-10 rounded border">
          <input v-model="form.color_hex" type="text" placeholder="#000000" class="flex-1 border border-gray-300 rounded-md px-3 py-2">
        </div>
      </div>
    </div>

    <!-- Opciones -->
    <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
      <label class="flex items-center">
        <input v-model="form.es_externa" type="checkbox" class="rounded">
        <span class="ml-2 text-sm text-gray-700">Es externa</span>
      </label>
      <label class="flex items-center">
        <input v-model="form.soporta_sincronizacion" type="checkbox" class="rounded">
        <span class="ml-2 text-sm text-gray-700">Sincronización</span>
      </label>
      <label class="flex items-center">
        <input v-model="form.activa" type="checkbox" class="rounded">
        <span class="ml-2 text-sm text-gray-700">Activa</span>
      </label>
    </div>
  </div>
</template>

<script setup>
defineProps({
  form: Object
})
</script>