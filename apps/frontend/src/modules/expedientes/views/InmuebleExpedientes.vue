<template>
  <div class="max-w-3xl mx-auto p-6">
    <router-link :to="`/inmuebles/${inmuebleId}`" class="text-sm text-indigo-600 hover:underline">
      ← Volver al inmueble
    </router-link>

    <div class="mt-4">
      <ExpedienteTimeline
        ref="timeline"
        :inmueble-id="inmuebleId"
        @nuevo="abrirNuevo"
        @editar="abrirEditar"
        @eliminar="confirmarEliminar"
      />
    </div>

    <ExpedienteForm
      v-if="mostrarForm"
      :inmueble-id="inmuebleId"
      :expediente="seleccionado"
      @cerrar="mostrarForm = false"
      @guardado="recargar"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import ExpedienteTimeline from '../components/ExpedienteTimeline.vue'
import ExpedienteForm from '../components/ExpedienteForm.vue'
import { useExpedientes } from '../composables/useExpedientes'

const route = useRoute()
const inmuebleId = route.params.id
const { eliminar } = useExpedientes()

const timeline = ref(null)
const mostrarForm = ref(false)
const seleccionado = ref(null)

function abrirNuevo() { seleccionado.value = null; mostrarForm.value = true }
function abrirEditar(e) { seleccionado.value = e; mostrarForm.value = true }
async function confirmarEliminar(e) {
  if (!confirm(`¿Eliminar el expediente "${e.titulo || e.tipo?.nombre}"?`)) return
  await eliminar(e.id)
  recargar()
}
function recargar() { timeline.value?.cargar() }
</script>
