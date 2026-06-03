<!-- InmuebleFormDatosGenerales.vue -->
<template>
  <div class="bg-white rounded-lg border border-gray-200 p-6">
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Columna izquierda -->
      <div class="space-y-6">
        <!-- Denominación principal -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Denominación principal *
          </label>
          <input
            :value="modelValue.denominacion_principal"
            @input="updateField('denominacion_principal', $event.target.value)"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            :class="{ 'border-red-500': errores.denominacion_principal }"
          />
          <p v-if="errores.denominacion_principal" class="mt-1 text-sm text-red-600">
            {{ errores.denominacion_principal }}
          </p>
        </div>

        <!-- Tipo inmueble -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Tipo de inmueble *
          </label>
          <Listbox :modelValue="modelValue.tipo_inmueble" @update:modelValue="updateField('tipo_inmueble', $event)">
            <div class="relative">
              <ListboxButton class="relative w-full px-3 py-2 text-left bg-white border border-gray-300 rounded-lg">
                <span class="block truncate">{{ modelValue.tipo_inmueble || 'Seleccionar...' }}</span>
              </ListboxButton>
              <ListboxOptions class="absolute z-10 mt-1 max-h-60 w-full overflow-auto bg-white border border-gray-300 rounded-lg shadow-lg">
                <ListboxOption
                  v-for="tipo in catalogos.tiposInmueble"
                  :key="tipo"
                  :value="tipo"
                  v-slot="{ active, selected }"
                >
                  <li :class="['px-3 py-2 cursor-pointer', active ? 'bg-blue-50' : '']">
                    <span :class="[selected ? 'font-semibold' : '']">{{ tipo }}</span>
                  </li>
                </ListboxOption>
              </ListboxOptions>
            </div>
          </Listbox>
        </div>

        <!-- Estado -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Estado</label>
          <Listbox :modelValue="modelValue.estado" @update:modelValue="updateField('estado', $event)">
            <div class="relative">
              <ListboxButton class="relative w-full px-3 py-2 text-left bg-white border border-gray-300 rounded-lg">
                <span class="block truncate">{{ getEstadoLabel(modelValue.estado) || 'Seleccionar...' }}</span>
              </ListboxButton>
              <ListboxOptions class="absolute z-10 mt-1 max-h-60 w-full overflow-auto bg-white border border-gray-300 rounded-lg shadow-lg">
                <ListboxOption
                  v-for="estado in catalogos.estados"
                  :key="estado.value"
                  :value="estado.value"
                  v-slot="{ active, selected }"
                >
                  <li :class="['px-3 py-2 cursor-pointer', active ? 'bg-blue-50' : '']">
                    <span :class="[selected ? 'font-semibold' : '']">{{ estado.label }}</span>
                  </li>
                </ListboxOption>
              </ListboxOptions>
            </div>
          </Listbox>
        </div>
                <!-- Estado Conservación -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Estado de conservación</label>
          <Listbox :modelValue="modelValue.estado_conservacion" @update:modelValue="updateField('estado_conservacion', $event)">
            <div class="relative">
              <ListboxButton class="relative w-full px-3 py-2 text-left bg-white border border-gray-300 rounded-lg">
                <span class="block truncate">{{ getConservacionLabel(modelValue.estado_conservacion) || 'Seleccionar...' }}</span>
              </ListboxButton>
              <ListboxOptions class="absolute z-10 mt-1 max-h-60 w-full overflow-auto bg-white border border-gray-300 rounded-lg shadow-lg">
                <ListboxOption
                  v-for="conservacion in catalogos.estadosConservacion"
                  :key="conservacion.value"
                  :value="conservacion.value"
                  v-slot="{ active, selected }"
                >
                  <li :class="['px-3 py-2 cursor-pointer', active ? 'bg-blue-50' : '']">
                    <span :class="[selected ? 'font-semibold' : '']">{{ conservacion.label }}</span>
                  </li>
                </ListboxOption>
              </ListboxOptions>
            </div>
          </Listbox>
        </div> 




        <!-- Dirección -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Dirección</label>
          <input
            :value="modelValue.direccion"
            @input="updateField('direccion', $event.target.value)"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- Código postal -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Código postal</label>
          <input
            :value="modelValue.codigo_postal"
            @input="updateField('codigo_postal', $event.target.value)"
            type="text"
            maxlength="5"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- Comunidad Autónoma -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Comunidad Autónoma</label>
          <Listbox :modelValue="modelValue.comunidad_autonoma" @update:modelValue="updateField('comunidad_autonoma', $event)">
            <div class="relative">
              <ListboxButton class="relative w-full px-3 py-2 text-left bg-white border border-gray-300 rounded-lg">
                <span class="block truncate">{{ modelValue.comunidad_autonoma || 'Seleccionar...' }}</span>
              </ListboxButton>
              <ListboxOptions class="absolute z-10 mt-1 max-h-60 w-full overflow-auto bg-white border border-gray-300 rounded-lg shadow-lg">
                <ListboxOption
                  v-for="ccaa in catalogos.comunidadesAutonomas"
                  :key="ccaa"
                  :value="ccaa"
                  v-slot="{ active, selected }"
                >
                  <li :class="['px-3 py-2 cursor-pointer', active ? 'bg-blue-50' : '']">
                    <span :class="[selected ? 'font-semibold' : '']">{{ ccaa }}</span>
                  </li>
                </ListboxOption>
              </ListboxOptions>
            </div>
          </Listbox>
        </div>

        <!-- Provincia -->
        <div v-if="modelValue.comunidad_autonoma">
          <label class="block text-sm font-medium text-gray-700 mb-2">Provincia</label>
          <Listbox :modelValue="modelValue.provincia" @update:modelValue="updateField('provincia', $event)">
            <div class="relative">
              <ListboxButton class="relative w-full px-3 py-2 text-left bg-white border border-gray-300 rounded-lg">
                <span class="block truncate">{{ modelValue.provincia || 'Seleccionar...' }}</span>
              </ListboxButton>
              <ListboxOptions class="absolute z-10 mt-1 max-h-60 w-full overflow-auto bg-white border border-gray-300 rounded-lg shadow-lg">
                <ListboxOption
                  v-for="prov in provinciasFiltered"
                  :key="prov"
                  :value="prov"
                  v-slot="{ active, selected }"
                >
                  <li :class="['px-3 py-2 cursor-pointer', active ? 'bg-blue-50' : '']">
                    <span :class="[selected ? 'font-semibold' : '']">{{ prov }}</span>
                  </li>
                </ListboxOption>
              </ListboxOptions>
            </div>
          </Listbox>
        </div>

        <!-- Localidad -->
        <div v-if="modelValue.provincia">
          <label class="block text-sm font-medium text-gray-700 mb-2">Localidad</label>
          <Combobox :modelValue="modelValue.localidad" @update:modelValue="updateField('localidad', $event)">
            <ComboboxInput
              @change="queryLocalidad = $event.target.value"
              :displayValue="(l) => l"
              placeholder="Buscar..."
              class="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
            <ComboboxOptions class="absolute z-10 mt-1 max-h-60 overflow-auto bg-white border border-gray-300 rounded-lg shadow-lg">
              <ComboboxOption
                v-for="localidad in localidadesFiltered"
                :key="localidad"
                :value="localidad"
                v-slot="{ active, selected }"
              >
                <li :class="['px-3 py-2 cursor-pointer', active ? 'bg-blue-50' : '']">
                  <span :class="[selected ? 'font-semibold' : '']">{{ localidad }}</span>
                </li>
              </ComboboxOption>
            </ComboboxOptions>
          </Combobox>
        </div>

        <!-- Coordenadas -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Latitud</label>
            <input
              :value="modelValue.latitud"
              @input="updateField('latitud', parseFloat($event.target.value))"
              type="number"
              step="0.000001"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Longitud</label>
            <input
              :value="modelValue.longitud"
              @input="updateField('longitud', parseFloat($event.target.value))"
              type="number"
              step="0.000001"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <!-- Columna derecha -->
      <div class="space-y-6">
        <!-- Fecha construcción -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Fecha construcción</label>
          <input
            :value="modelValue.fecha_construccion"
            @input="updateField('fecha_construccion', $event.target.value)"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- Superficie construida -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Superficie construida (m²)</label>
          <input
            :value="modelValue.superficie_construida"
            @input="updateField('superficie_construida', parseFloat($event.target.value))"
            type="number"
            step="0.01"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- Superficie parcela -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Superficie parcela (m²)</label>
          <input
            :value="modelValue.superficie_parcela"
            @input="updateField('superficie_parcela', parseFloat($event.target.value))"
            type="number"
            step="0.01"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- Código BIC -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Código BIC</label>
          <input
            :value="modelValue.codigo_bien_interes_cultural"
            @input="updateField('codigo_bien_interes_cultural', $event.target.value)"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- Inmatriculación -->
        <div class="border-t pt-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Inmatriculación</h3>
          
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Fecha inmatriculación</label>
              <input
                :value="modelValue.fecha_inmatriculacion"
                @input="updateField('fecha_inmatriculacion', $event.target.value)"
                type="date"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Registro de la propiedad</label>
              <Listbox :modelValue="modelValue.registro_propiedad" @update:modelValue="updateField('registro_propiedad', $event)">
                <div class="relative">
                  <ListboxButton class="relative w-full px-3 py-2 text-left bg-white border border-gray-300 rounded-lg">
                    <span class="block truncate">{{ modelValue.registro_propiedad || 'Seleccionar...' }}</span>
                  </ListboxButton>
                  <ListboxOptions class="absolute z-10 mt-1 max-h-60 w-full overflow-auto bg-white border border-gray-300 rounded-lg shadow-lg">
                    <ListboxOption
                      v-for="registro in catalogos.registrosPropiedad"
                      :key="registro"
                      :value="registro"
                      v-slot="{ active, selected }"
                    >
                      <li :class="['px-3 py-2 cursor-pointer', active ? 'bg-blue-50' : '']">
                        <span :class="[selected ? 'font-semibold' : '']">{{ registro }}</span>
                      </li>
                    </ListboxOption>
                  </ListboxOptions>
                </div>
              </Listbox>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Número de finca</label>
              <input
                :value="modelValue.numero_finca"
                @input="updateField('numero_finca', $event.target.value)"
                type="text"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        <!-- Descripción -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Descripción</label>
          <textarea
            :value="modelValue.descripcion"
            @input="updateField('descripcion', $event.target.value)"
            rows="4"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
    </div>

    <!-- Mapa -->
    <div v-if="modelValue.latitud && modelValue.longitud" class="mt-6 border-t pt-6">
      <h3 class="text-lg font-medium text-gray-900 mb-4">Ubicación</h3>
      <div class="h-96 rounded-lg overflow-hidden border border-gray-300">
        <InmuebleMapa :inmuebles="[modelValue]" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Listbox, ListboxButton, ListboxOptions, ListboxOption, Combobox, ComboboxInput, ComboboxOptions, ComboboxOption } from '@headlessui/vue'
import InmuebleMapa from './InmuebleMapa.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  },
  catalogos: {
    type: Object,
    required: true
  },
  errores: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

const queryLocalidad = ref('')

const updateField = (field, value) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [field]: value
  })
}

const getEstadoLabel = (value) => {
  const estado = props.catalogos.estados?.find(e => e.value === value)
  return estado?.label || value
}

const getConservacionLabel = (value) => {
  const conservacion = props.catalogos.estadosConservacion?.find(e => e.value === value)
  return conservacion?.label || value
}


const provinciasFiltered = computed(() => {
  if (!props.modelValue.comunidad_autonoma) return []
  return (props.catalogos.provincias || [])
    .filter(p => p.comunidad === props.modelValue.comunidad_autonoma)
    .map(p => p.nombre)
})

const localidadesFiltered = computed(() => {
  if (!props.modelValue.provincia) return []
  const localidades = (props.catalogos.localidades || [])
    .filter(l => l.provincia === props.modelValue.provincia)
    .map(l => l.nombre)
  
  if (!queryLocalidad.value) return localidades
  return localidades.filter(l =>
    l.toLowerCase().includes(queryLocalidad.value.toLowerCase())
  )
})

// Limpiar provincia/localidad cuando cambia comunidad
watch(() => props.modelValue.comunidad_autonoma, () => {
  if (props.modelValue.provincia) {
    updateField('provincia', null)
    updateField('localidad', null)
  }
})

// Limpiar localidad cuando cambia provincia
watch(() => props.modelValue.provincia, () => {
  if (props.modelValue.localidad) {
    updateField('localidad', null)
  }
})
</script>