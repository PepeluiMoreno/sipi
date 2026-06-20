<!-- InmueblesSidebar.vue — filtros, austero y a altura completa -->
<template>
  <aside v-if="isOpen" class="w-72 shrink-0 bg-white border-r border-zinc-200 flex flex-col min-h-0">
    <div class="shrink-0 h-12 px-4 flex items-center justify-between border-b border-zinc-200">
      <h2 class="text-sm font-semibold text-zinc-800 flex items-center gap-2">
        <UiIcon name="filtro" size="sm" class="text-zinc-400" /> Filtros
      </h2>
      <button @click="toggleSidebar" class="btn-ghost btn-icon" title="Ocultar filtros">
        <UiIcon name="chevron-left" size="sm" />
      </button>
    </div>

    <div class="flex-1 min-h-0 overflow-auto p-4">
      <div class="field">
        <label class="label">Buscar</label>
        <input v-model="localFilters.search" type="text" placeholder="Nombre, dirección…" class="input" />
      </div>

      <div class="field">
        <label class="label">Estado</label>
        <div class="space-y-1.5">
          <label v-for="estado in estados" :key="estado.value" class="flex items-center gap-2 text-sm text-zinc-700">
            <input v-model="localFilters.estados[estado.value]" type="checkbox"
                   class="rounded border-zinc-300 text-primary-600 focus:ring-primary-500" />
            <span>{{ estado.label }}</span>
          </label>
        </div>
      </div>

      <div class="field">
        <label class="label">Comunidad Autónoma</label>
        <Listbox v-model="localFilters.comunidadAutonoma">
          <ListboxButton class="select text-left">{{ localFilters.comunidadAutonoma || 'Todas' }}</ListboxButton>
          <ListboxOptions class="absolute z-20 mt-1 max-h-60 w-64 overflow-auto card py-1">
            <ListboxOption :value="null" v-slot="{ active, selected }">
              <li :class="['px-3 py-1.5 text-sm cursor-pointer', active ? 'bg-zinc-100' : '', selected && 'font-semibold']">Todas</li>
            </ListboxOption>
            <ListboxOption v-for="ccaa in comunidadesAutonomas" :key="ccaa" :value="ccaa" v-slot="{ active, selected }">
              <li :class="['px-3 py-1.5 text-sm cursor-pointer', active ? 'bg-zinc-100' : '', selected && 'font-semibold']">{{ ccaa }}</li>
            </ListboxOption>
          </ListboxOptions>
        </Listbox>
      </div>

      <div v-if="localFilters.comunidadAutonoma" class="field">
        <label class="label">Provincia</label>
        <Listbox v-model="localFilters.provincia">
          <ListboxButton class="select text-left">{{ localFilters.provincia || 'Todas' }}</ListboxButton>
          <ListboxOptions class="absolute z-20 mt-1 max-h-60 w-64 overflow-auto card py-1">
            <ListboxOption :value="null" v-slot="{ active, selected }">
              <li :class="['px-3 py-1.5 text-sm cursor-pointer', active ? 'bg-zinc-100' : '', selected && 'font-semibold']">Todas</li>
            </ListboxOption>
            <ListboxOption v-for="prov in provinciasFiltered" :key="prov" :value="prov" v-slot="{ active, selected }">
              <li :class="['px-3 py-1.5 text-sm cursor-pointer', active ? 'bg-zinc-100' : '', selected && 'font-semibold']">{{ prov }}</li>
            </ListboxOption>
          </ListboxOptions>
        </Listbox>
      </div>

      <div v-if="localFilters.provincia" class="field">
        <label class="label">Localidad</label>
        <Combobox v-model="localFilters.localidad">
          <ComboboxInput @change="queryLocalidad = $event.target.value" :displayValue="(l) => l"
                         placeholder="Buscar…" class="input" />
          <ComboboxOptions class="absolute z-20 mt-1 max-h-60 w-64 overflow-auto card py-1">
            <ComboboxOption v-for="loc in localidadesFiltered" :key="loc" :value="loc" v-slot="{ active, selected }">
              <li :class="['px-3 py-1.5 text-sm cursor-pointer', active ? 'bg-zinc-100' : '', selected && 'font-semibold']">{{ loc }}</li>
            </ComboboxOption>
          </ComboboxOptions>
        </Combobox>
      </div>

      <div class="field">
        <label class="label">Tipo</label>
        <Listbox v-model="localFilters.tipoInmueble">
          <ListboxButton class="select text-left">{{ localFilters.tipoInmueble || 'Todos' }}</ListboxButton>
          <ListboxOptions class="absolute z-20 mt-1 max-h-60 w-64 overflow-auto card py-1">
            <ListboxOption :value="null" v-slot="{ active, selected }">
              <li :class="['px-3 py-1.5 text-sm cursor-pointer', active ? 'bg-zinc-100' : '', selected && 'font-semibold']">Todos</li>
            </ListboxOption>
            <ListboxOption v-for="tipo in tiposInmueble" :key="tipo" :value="tipo" v-slot="{ active, selected }">
              <li :class="['px-3 py-1.5 text-sm cursor-pointer', active ? 'bg-zinc-100' : '', selected && 'font-semibold']">{{ tipo }}</li>
            </ListboxOption>
          </ListboxOptions>
        </Listbox>
      </div>
    </div>

    <div class="shrink-0 p-3 border-t border-zinc-200 flex gap-2">
      <UiButton variant="primary" icon="filtro" class="flex-1" @click="aplicar">Aplicar</UiButton>
      <UiButton variant="secondary" @click="limpiar">Limpiar</UiButton>
    </div>
  </aside>

  <button v-else @click="toggleSidebar" title="Mostrar filtros"
          class="self-center -ml-px bg-white border border-zinc-200 rounded-r p-2 text-zinc-500 hover:bg-zinc-50">
    <UiIcon name="chevron-right" size="sm" />
  </button>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import {
  Combobox,
  ComboboxInput,
  ComboboxOptions,
  ComboboxOption,
  Listbox,
  ListboxButton,
  ListboxOptions,
  ListboxOption
} from '@headlessui/vue'

const props = defineProps({
  filters: Object,
  estados: Array,
  tiposInmueble: Array,
  comunidadesAutonomas: Array,
  provincias: Array,
  localidades: Array
})

const emit = defineEmits(['update:filters', 'apply', 'clear'])

const isOpen = ref(true)
const localFilters = ref({ ...props.filters })
const queryLocalidad = ref('')

const provinciasFiltered = computed(() => {
  if (!localFilters.value.comunidadAutonoma) return []
  return props.provincias
    .filter(p => p.comunidad === localFilters.value.comunidadAutonoma)
    .map(p => p.nombre)
})

const localidadesFiltered = computed(() => {
  if (!localFilters.value.provincia) return []
  const localidades = props.localidades
    .filter(l => l.provincia === localFilters.value.provincia)
    .map(l => l.nombre)
  
  if (!queryLocalidad.value) return localidades
  return localidades.filter(l =>
    l.toLowerCase().includes(queryLocalidad.value.toLowerCase())
  )
})

watch(() => localFilters.value.comunidadAutonoma, () => {
  localFilters.value.provincia = null
  localFilters.value.localidad = null
})

watch(() => localFilters.value.provincia, () => {
  localFilters.value.localidad = null
})

const toggleSidebar = () => {
  isOpen.value = !isOpen.value
}

const aplicar = () => {
  emit('update:filters', localFilters.value)
  emit('apply')
}

const limpiar = () => {
  localFilters.value = {
    search: '',
    estados: {},
    comunidadAutonoma: null,
    provincia: null,
    localidad: null,
    tipoInmueble: null
  }
  emit('clear')
}
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(-100%);
}
</style>