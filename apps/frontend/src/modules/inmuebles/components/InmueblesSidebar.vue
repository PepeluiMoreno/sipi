<!-- InmueblesSidebar.vue -->
<template>
  <Transition name="slide">
    <aside v-show="isOpen" class="w-80 bg-white border-r border-gray-200 overflow-y-auto flex-shrink-0">
      <div class="p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-base font-semibold text-gray-900">Filtros</h2>
          <button @click="toggleSidebar" class="p-1 hover:bg-gray-100 rounded">
            <ChevronLeftIcon class="w-5 h-5" />
          </button>
        </div>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Buscar</label>
            <input
              v-model="localFilters.search"
              type="text"
              placeholder="Nombre, dirección..."
              class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Estado</label>
            <div class="space-y-2">
              <label v-for="estado in estados" :key="estado.value" class="flex items-center">
                <input
                  v-model="localFilters.estados[estado.value]"
                  type="checkbox"
                  class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span class="ml-2 text-sm text-gray-700">{{ estado.label }}</span>
              </label>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Comunidad Autónoma</label>
            <div class="text-xs text-red-500 mb-1">Debug CCAA: {{ comunidadesAutonomas?.length || 0 }}</div>
            <Listbox v-model="localFilters.comunidadAutonoma">
              <ListboxButton class="relative w-full px-3 py-2 text-sm text-left bg-white border border-gray-300 rounded-lg">
                <span class="block truncate">{{ localFilters.comunidadAutonoma || 'Todas' }}</span>
              </ListboxButton>
              <ListboxOptions class="absolute z-20 mt-1 max-h-60 w-72 overflow-auto bg-white border border-gray-300 rounded-lg shadow-lg">
                <ListboxOption :value="null" v-slot="{ active, selected }">
                  <li :class="['px-3 py-2 text-sm cursor-pointer', active ? 'bg-blue-50' : '']">
                    <span :class="selected ? 'font-semibold' : ''">Todas</span>
                  </li>
                </ListboxOption>
                <ListboxOption
                  v-for="ccaa in comunidadesAutonomas"
                  :key="ccaa"
                  :value="ccaa"
                  v-slot="{ active, selected }"
                >
                  <li :class="['px-3 py-2 text-sm cursor-pointer', active ? 'bg-blue-50' : '']">
                    <span :class="selected ? 'font-semibold' : ''">{{ ccaa }}</span>
                  </li>
                </ListboxOption>
              </ListboxOptions>
            </Listbox>
          </div>

          <div v-if="localFilters.comunidadAutonoma">
            <label class="block text-sm font-medium text-gray-700 mb-2">Provincia</label>
            <div class="text-xs text-red-500 mb-1">
              Debug Prov: {{ provinciasFiltered.length }} | Todas: {{ provincias?.length || 0 }}
            </div>
            <Listbox v-model="localFilters.provincia">
              <ListboxButton class="relative w-full px-3 py-2 text-sm text-left bg-white border border-gray-300 rounded-lg">
                <span class="block truncate">{{ localFilters.provincia || 'Todas' }}</span>
              </ListboxButton>
              <ListboxOptions class="absolute z-20 mt-1 max-h-60 w-72 overflow-auto bg-white border border-gray-300 rounded-lg shadow-lg">
                <ListboxOption :value="null" v-slot="{ active, selected }">
                  <li :class="['px-3 py-2 text-sm cursor-pointer', active ? 'bg-blue-50' : '']">
                    <span :class="selected ? 'font-semibold' : ''">Todas</span>
                  </li>
                </ListboxOption>
                <ListboxOption
                  v-for="prov in provinciasFiltered"
                  :key="prov"
                  :value="prov"
                  v-slot="{ active, selected }"
                >
                  <li :class="['px-3 py-2 text-sm cursor-pointer', active ? 'bg-blue-50' : '']">
                    <span :class="selected ? 'font-semibold' : ''">{{ prov }}</span>
                  </li>
                </ListboxOption>
              </ListboxOptions>
            </Listbox>
          </div>

          <div class="text-xs text-red-500 mb-1">
            Debug: provincia="{{ localFilters.provincia }}" | localidades totales: {{ localidades?.length }}
          </div>


          <div v-if="localFilters.provincia">
            <label class="block text-sm font-medium text-gray-700 mb-2">Localidad</label>
            <div class="text-xs text-red-500 mb-1">
              Debug Loc: {{ localidadesFiltered.length }} | Todas: {{ localidades?.length || 0 }}
            </div>
            <Combobox v-model="localFilters.localidad">
              <ComboboxInput
                @change="queryLocalidad = $event.target.value"
                :displayValue="(l) => l"
                placeholder="Buscar..."
                class="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg"
              />
              <ComboboxOptions class="absolute z-20 mt-1 max-h-60 w-72 overflow-auto bg-white border border-gray-300 rounded-lg shadow-lg">
                <ComboboxOption
                  v-for="loc in localidadesFiltered"
                  :key="loc"
                  :value="loc"
                  v-slot="{ active, selected }"
                >
                  <li :class="['px-3 py-2 text-sm cursor-pointer', active ? 'bg-blue-50' : '']">
                    <span :class="selected ? 'font-semibold' : ''">{{ loc }}</span>
                  </li>
                </ComboboxOption>
              </ComboboxOptions>
            </Combobox>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Tipo</label>
            <Listbox v-model="localFilters.tipoInmueble">
              <ListboxButton class="relative w-full px-3 py-2 text-sm text-left bg-white border border-gray-300 rounded-lg">
                <span class="block truncate">{{ localFilters.tipoInmueble || 'Todos' }}</span>
              </ListboxButton>
              <ListboxOptions class="absolute z-20 mt-1 max-h-60 w-72 overflow-auto bg-white border border-gray-300 rounded-lg shadow-lg">
                <ListboxOption :value="null" v-slot="{ active, selected }">
                  <li :class="['px-3 py-2 text-sm cursor-pointer', active ? 'bg-blue-50' : '']">
                    <span :class="selected ? 'font-semibold' : ''">Todos</span>
                  </li>
                </ListboxOption>
                <ListboxOption
                  v-for="tipo in tiposInmueble"
                  :key="tipo"
                  :value="tipo"
                  v-slot="{ active, selected }"
                >
                  <li :class="['px-3 py-2 text-sm cursor-pointer', active ? 'bg-blue-50' : '']">
                    <span :class="selected ? 'font-semibold' : ''">{{ tipo }}</span>
                  </li>
                </ListboxOption>
              </ListboxOptions>
            </Listbox>
          </div>

          <div class="pt-2 space-y-2">
            <button
              @click="aplicar"
              class="w-full px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              Aplicar
            </button>
            <button
              @click="limpiar"
              class="w-full px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium"
            >
              Limpiar
            </button>
          </div>
        </div>
      </div>
    </aside>
  </Transition>

  <button
    v-show="!isOpen"
    @click="toggleSidebar"
    class="fixed left-0 top-1/2 -translate-y-1/2 z-10 bg-white border border-gray-300 rounded-r-lg p-2 shadow-lg hover:bg-gray-50"
  >
    <ChevronRightIcon class="w-5 h-5" />
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
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/vue/24/outline'

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