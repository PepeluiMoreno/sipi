<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Documentación</h1>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div v-for="documento in documentos" :key="documento.id" class="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
        <div class="flex items-start justify-between mb-4">
          <div class="p-2 bg-blue-100 rounded-lg">
            <DocumentTextIcon class="w-6 h-6 text-blue-600" />
          </div>
          <span class="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">{{ documento.estado }}</span>
        </div>
        <h3 class="font-semibold text-gray-900 mb-2">{{ documento.titulo }}</h3>
        <p class="text-sm text-gray-500 mb-4">{{ documento.descripcion }}</p>
        <div class="flex justify-between items-center">
          <span class="text-xs text-gray-400">{{ documento.fecha_subido }}</span>
          <button class="text-indigo-600 hover:text-indigo-900 text-sm font-medium">
            Ver documento
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { DocumentTextIcon } from '@heroicons/vue/24/outline'

const documentos = ref([])

const loadDocumentos = async () => {
  try {
    // TODO: Implementar query Apollo/GraphQL para documentos
    /*
    const { data } = await apolloClient.query({
      query: gql`
        query GetDocumentos {
          documentos {
            id
            titulo
            descripcion
            estado
            fecha_subido
            tipo_documento {
              id
              nombre
            }
          }
        }
      `
    })
    documentos.value = data.documentos
    */
    
    // Mock temporal
    documentos.value = []
  } catch (error) {
    console.error('Error cargando documentos:', error)
  }
}

onMounted(loadDocumentos)
</script>