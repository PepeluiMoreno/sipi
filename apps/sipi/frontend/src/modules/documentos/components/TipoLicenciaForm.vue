<template>
  <div class="space-y-6">
    <!-- Información básica -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700">Código *</label>
        <input v-model="form.codigo" type="text" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2" required>
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">Familia</label>
        <input v-model="form.familia" type="text" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2">
      </div>
    </div>

    <!-- URLs -->
    <div class="grid grid-cols-1 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700">URL Licencia</label>
        <input v-model="form.url_licencia" type="url" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2">
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700">URL Legal</label>
        <input v-model="form.url_legal" type="url" class="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2">
      </div>
    </div>

    <!-- Permisos -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <label class="flex items-center">
        <input v-model="form.requiere_atribucion" type="checkbox" class="rounded">
        <span class="ml-2 text-sm text-gray-700">Requiere atribución</span>
      </label>
      <label class="flex items-center">
        <input v-model="form.permite_uso_comercial" type="checkbox" class="rounded">
        <span class="ml-2 text-sm text-gray-700">Uso comercial</span>
      </label>
      <label class="flex items-center">
        <input v-model="form.permite_derivadas" type="checkbox" class="rounded">
        <span class="ml-2 text-sm text-gray-700">Permite derivadas</span>
      </label>
      <label class="flex items-center">
        <input v-model="form.requiere_compartir_igual" type="checkbox" class="rounded">
        <span class="ml-2 text-sm text-gray-700">Compartir igual</span>
      </label>
    </div>

    <!-- Características -->
    <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
      <label class="flex items-center">
        <input v-model="form.es_libre" type="checkbox" class="rounded">
        <span class="ml-2 text-sm text-gray-700">Es libre</span>
      </label>
      <label class="flex items-center">
        <input v-model="form.es_open_source" type="checkbox" class="rounded">
        <span class="ml-2 text-sm text-gray-700">Open source</span>
      </label>
      <label class="flex items-center">
        <input v-model="form.es_copyleft" type="checkbox" class="rounded">
        <span class="ml-2 text-sm text-gray-700">Copyleft</span>
      </label>
    </div>
  </div>
</template>

<script setup>
defineProps({
  form: Object
})
</script>