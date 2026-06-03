<template>
  <div class="inmueble-tabs-container" v-if="inmueble">
    <!-- Tabs Navigation -->
    <div class="tabs-header">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="tabActiva = tab.id"
        :class="[
          'tab-button',
          { active: tabActiva === tab.id }
        ]"
      >
        <i :class="tab.icono" class="mr-2"></i>
        {{ tab.nombre }}
      </button>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <!-- Básicos -->
      <div v-if="tabActiva === 'basicos'" class="tab-panel">
        <InmuebleFormBasicos :inmueble="inmueble" />
      </div>

      <!-- Inmatriculación -->
      <div v-if="tabActiva === 'inmatriculacion'" class="tab-panel">
        <InmuebleFormInmatriculacion :inmueble="inmueble" />
      </div>

      <!-- Transmisiones -->
      <div v-if="tabActiva === 'transmisiones'" class="tab-panel">
        <InmuebleFormTransmisiones :inmueble="inmueble" />
      </div>

      <!-- Actuaciones -->
      <div v-if="tabActiva === 'actuaciones'" class="tab-panel">
        <InmuebleFormActuaciones :inmueble="inmueble" />
      </div>

      <!-- OSM -->
      <div v-if="tabActiva === 'osm'" class="tab-panel">
        <InmuebleFormOSM :inmueble="inmueble" />
      </div>

      <!-- Wikidata -->
      <div v-if="tabActiva === 'wikidata'" class="tab-panel">
        <InmuebleFormWikidata :inmueble="inmueble" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import InmuebleFormBasicos from '@/modules/inmuebles/components/forms/tabs/InmuebleFormBasicos.vue'
import InmuebleFormInmatriculacion from '@/modules/inmuebles/components/forms/tabs/InmuebleFormInmatriculacion.vue'
import InmuebleFormTransmisiones from '@/modules/inmuebles/components/forms/tabs/InmuebleFormTransmisiones.vue'
import InmuebleFormActuaciones from '@/modules/inmuebles/components/forms/tabs/InmuebleFormActuaciones.vue'
import InmuebleFormOSM from '@/modules/inmuebles/components/forms/tabs/InmuebleFormOSM.vue'
import InmuebleFormWikidata from '@/modules/inmuebles/components/forms/tabs/InmuebleFormWikidata.vue'

const props = defineProps({
  inmueble: {
    type: Object,
    default: null
  }
})

const tabActiva = ref('basicos')

const tabs = [
  { id: 'basicos', nombre: 'Básicos', icono: 'fas fa-info-circle' },
  { id: 'inmatriculacion', nombre: 'Inmatriculación', icono: 'fas fa-file-contract' },
  { id: 'transmisiones', nombre: 'Transmisiones', icono: 'fas fa-exchange-alt' },
  { id: 'actuaciones', nombre: 'Actuaciones', icono: 'fas fa-tasks' },
  { id: 'osm', nombre: 'OpenStreetMap', icono: 'fas fa-map' },
  { id: 'wikidata', nombre: 'Wikidata', icono: 'fas fa-database' }
]
</script>

<style scoped>
.inmueble-tabs-container {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
  overflow: hidden;
}

.tabs-header {
  display: flex;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  overflow-x: auto;
}

.tab-button {
  display: flex;
  align-items: center;
  padding: 1rem 1.5rem;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: 0.875rem;
  font-weight: 500;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.tab-button:hover {
  color: #334155;
  background: #f1f5f9;
}

.tab-button.active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
  background: white;
}

.tab-content {
  padding: 0;
}

.tab-panel {
  min-height: 400px;
}
</style>