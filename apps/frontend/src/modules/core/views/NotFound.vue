<template>
  <div class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
      <div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10 text-center">
        <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
          <ExclamationTriangleIcon class="h-6 w-6 text-red-600" />
        </div>
        <h2 class="mt-3 text-3xl font-extrabold text-gray-900">
          404
        </h2>
        <p class="mt-2 text-sm text-gray-600">
          Página no encontrada
        </p>
        <p class="mt-1 text-sm text-gray-500">
          La página que buscas no existe o ha sido movida.
        </p>
        <div class="mt-6">
          <button
            @click="goHome"
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Volver al Dashboard
          </button>
        </div>
        <div class="mt-4">
          <button
            @click="goBack"
            class="text-sm text-indigo-600 hover:text-indigo-500"
          >
            ← Volver atrás
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ExclamationTriangleIcon } from '@heroicons/vue/24/outline'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.back()
}
</script>