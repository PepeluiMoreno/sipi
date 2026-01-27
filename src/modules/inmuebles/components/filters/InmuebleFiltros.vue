<template>
  <div class="filtros-container">
    <!-- Búsqueda textual -->
    <div class="filtro-group">
      <label class="filtro-label">Buscar inmuebles</label>
      <input 
        type="text" 
        class="filtro-input"
        placeholder="Nombre o dirección..."
        :value="filters.search"
        @input="handleFilterChange('search', $event.target.value)"
      />
    </div>

    <!-- Filtros geográficos usando API real -->
    <div class="filtro-group">
      <label class="filtro-label">Provincia</label>
      <select
        class="filtro-select"
        :value="filters.provinciaId"
        @change="handleProvinciaChange($event.target.value)"
        :disabled="loadingProvincias"
      >
        <option value="">{{ loadingProvincias ? 'Cargando...' : 'Todas las provincias' }}</option>
        <option v-for="provincia in todasLasProvincias" :key="provincia.id" :value="provincia.id">
          {{ provincia.nombre }}
        </option>
      </select>
    </div>

    <div class="filtro-group">
      <label class="filtro-label">Municipio</label>
      <select
        class="filtro-select"
        :value="filters.municipioId"
        @change="handleFilterChange('municipioId', $event.target.value)"
        :disabled="!filters.provinciaId || loadingMunicipios"
      >
        <option value="">{{ loadingMunicipios ? 'Cargando...' : (filters.provinciaId ? 'Todos los municipios' : 'Seleccione provincia primero') }}</option>
        <option v-for="municipio in todasLasLocalidades" :key="municipio.id" :value="municipio.id">
          {{ municipio.nombre }}
        </option>
      </select>
    </div>

    <!-- Filtro por estados -->
    <div class="filtro-group">
      <label class="filtro-label">Estados</label>
      <div class="estados-list">
        <div v-for="estado in estadosDisponibles" :key="estado.key" class="estado-item">
          <input
            type="checkbox"
            :id="`estado-${estado.key}`"
            :checked="filters.estados[estado.key] || false"
            @change="handleEstadoChange(estado.key, $event.target.checked)"
            class="estado-checkbox"
          />
          <label :for="`estado-${estado.key}`" class="estado-label">
            {{ estado.label }}
          </label>
        </div>
      </div>
    </div>

    <!-- Botones de acción -->
    <div class="filtro-actions">
      <button 
        @click="handleAplicarFiltros" 
        class="btn-aplicar"
        :disabled="loading"
      >
        <span v-if="loading">Aplicando...</span>
        <span v-else>Aplicar Filtros</span>
      </button>
      
      <button 
        @click="handleLimpiarFiltros" 
        class="btn-limpiar"
        :disabled="loading"
      >
        Limpiar Filtros
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, defineProps, defineEmits, onMounted } from 'vue'
import { useGeografiaStore } from '../../../core/stores/geografia'

const props = defineProps({
  filters: {
    type: Object,
    required: true,
    default: () => ({
      search: '',
      provinciaId: null,
      municipioId: null,
      estados: {}
    })
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['filters-change', 'apply-filters'])

// Estados de tratamiento disponibles
const estadosDisponibles = [
  { key: 'no_investigado', label: 'No investigado' },
  { key: 'inmatriculado', label: 'Inmatriculado' },
  { key: 'vendido', label: 'Vendido' },
  { key: 'en_venta', label: 'En venta' },
  { key: 'bic', label: 'BIC' }
]

// Usar store de geografía (datos cacheados en memoria)
const geografiaStore = useGeografiaStore()

// Computed para las listas (sin llamadas al servidor)
const loadingProvincias = computed(() => geografiaStore.loading)
const loadingMunicipios = computed(() => geografiaStore.loading)
const todasLasProvincias = computed(() => geografiaStore.provincias)
const todasLasLocalidades = computed(() => {
  if (!props.filters.provinciaId) return []
  return geografiaStore.getMunicipiosDeProvincia(props.filters.provinciaId)
})

// Cargar datos del store al montar (solo una vez en toda la app)
onMounted(async () => {
  await geografiaStore.cargarDatos()
})

const handleFilterChange = (key, value) => {
  const nuevosFiltros = {
    ...props.filters,
    [key]: value || null
  }
  emit('filters-change', nuevosFiltros)
}

// Manejar cambio de provincia (limpia municipio seleccionado)
const handleProvinciaChange = (provinciaId) => {
  const nuevosFiltros = {
    ...props.filters,
    provinciaId: provinciaId || null,
    municipioId: null // Limpiar municipio al cambiar provincia
  }
  emit('filters-change', nuevosFiltros)
}

const handleEstadoChange = (estadoKey, checked) => {
  const nuevosEstados = {
    ...props.filters.estados,
    [estadoKey]: checked
  }
  const nuevosFiltros = {
    ...props.filters,
    estados: nuevosEstados
  }
  emit('filters-change', nuevosFiltros)
}

const handleAplicarFiltros = () => {
  emit('apply-filters')
}

const handleLimpiarFiltros = () => {
  const filtrosLimpiados = {
    search: '',
    provinciaId: null,
    municipioId: null,
    estados: {}
  }
  emit('filters-change', filtrosLimpiados)
}
</script>

<style scoped>
.filtros-container {
  padding: 1.5rem;
  background: white;
  border-right: 1px solid #e5e7eb;
  height: 100%;
  overflow-y: auto;
}

.filtro-group {
  margin-bottom: 1.5rem;
}

.filtro-label {
  display: block;
  font-weight: 600;
  font-size: 0.875rem;
  color: #374151;
  margin-bottom: 0.5rem;
}

.filtro-input,
.filtro-select {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  transition: border-color 0.15s ease;
}

.filtro-input:focus,
.filtro-select:focus {
  outline: none;
  border-color: #3b82f6;
  ring: 2px solid #3b82f6;
}

.estados-list {
  space-y: 0.5rem;
}

.estado-item {
  display: flex;
  align-items: center;
  padding: 0.5rem 0;
}

.estado-checkbox {
  width: 1rem;
  height: 1rem;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
  margin-right: 0.5rem;
}

.estado-label {
  font-size: 0.875rem;
  color: #374151;
  cursor: pointer;
}

.filtro-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 2rem;
}

.btn-aplicar {
  width: 100%;
  padding: 0.75rem 1rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.btn-aplicar:hover:not(:disabled) {
  background: #2563eb;
}

.btn-aplicar:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-limpiar {
  width: 100%;
  padding: 0.75rem 1rem;
  background: #6b7280;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.btn-limpiar:hover:not(:disabled) {
  background: #4b5563;
}
</style>