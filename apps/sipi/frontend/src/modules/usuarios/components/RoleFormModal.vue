<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">
          {{ isEditing ? 'Editar Rol' : 'Crear Nuevo Rol' }}
        </h2>
      </div>

      <!-- Formulario -->
      <form @submit.prevent="saveRole" class="p-6 space-y-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Nombre del rol *
          </label>
          <input
            v-model="formData.nombre"
            type="text"
            required
            maxlength="50"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Ej: Administrador, Editor, Consultor..."
          >
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            Descripción
          </label>
          <textarea
            v-model="formData.descripcion"
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Describe las funciones y permisos de este rol..."
          ></textarea>
        </div>

        <!-- Botones -->
        <div class="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          <button
            type="button"
            @click="$emit('close')"
            class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Cancelar
          </button>
          <button
            type="submit"
            class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            {{ isEditing ? 'Actualizar' : 'Crear' }} Rol
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, defineProps, defineEmits } from 'vue'

const props = defineProps({
  role: Object,
  isEditing: Boolean
})

const emit = defineEmits(['save', 'close'])

const formData = ref({
  nombre: '',
  descripcion: ''
})

// Cargar datos del rol si estamos editando
watch(() => props.role, (role) => {
  if (role && props.isEditing) {
    formData.value = {
      nombre: role.nombre || '',
      descripcion: role.descripcion || ''
    }
  }
}, { immediate: true })

const saveRole = () => {
  if (!formData.value.nombre.trim()) {
    alert('El nombre del rol es obligatorio')
    return
  }

  emit('save', formData.value)
}
</script>