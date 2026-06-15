<!-- InmuebleFormDatosGenerales.vue — ficha compacta; "Ver en el mapa" abre un panel a la izquierda que empuja la ficha -->
<template>
  <div class="flex gap-4 items-stretch">
    <!-- ===== Panel de mapa (izquierda), conmutable ===== -->
    <transition
      enter-active-class="transition-all duration-200 ease-out" enter-from-class="opacity-0 -translate-x-2"
      leave-active-class="transition-all duration-150 ease-in" leave-to-class="opacity-0 -translate-x-2">
      <div v-if="mostrarMapa" class="w-[28rem] shrink-0 flex flex-col card !p-0 overflow-hidden">
        <div class="shrink-0 flex items-center justify-between px-3 py-2 border-b border-zinc-200">
          <span class="text-sm font-medium text-zinc-700">Ubicación</span>
          <div class="flex items-center gap-3">
            <span class="text-xs text-zinc-400 font-mono">{{ modelValue.latitud }}, {{ modelValue.longitud }}</span>
            <button type="button" @click="mostrarMapa = false" class="text-zinc-400 hover:text-zinc-700">
              <UiIcon name="cerrar" class="w-4 h-4" />
            </button>
          </div>
        </div>
        <div class="flex-1 min-h-0">
          <InmuebleMapa :inmuebles="[modelValue]" />
        </div>
      </div>
    </transition>

    <!-- ===== Ficha (derecha): ancho y columnas constantes; el mapa solo la desplaza ===== -->
    <div class="w-full max-w-4xl mx-auto">
      <div class="card p-4">
        <div class="grid grid-cols-3 gap-x-4 gap-y-3">
          <!-- Identificación -->
          <p class="ui-section">Identificación</p>

          <div class="col-span-2">
            <label class="label">Denominación principal *</label>
            <input :value="modelValue.denominacion_principal"
                   @input="updateField('denominacion_principal', $event.target.value)"
                   type="text" class="input" :class="{ '!border-red-500': errores.denominacion_principal }" />
            <p v-if="errores.denominacion_principal" class="mt-1 text-xs text-red-600">{{ errores.denominacion_principal }}</p>
          </div>

          <div>
            <label class="label">Tipo de inmueble *</label>
            <Listbox :modelValue="modelValue.tipo_inmueble" @update:modelValue="updateField('tipo_inmueble', $event)">
              <div class="relative">
                <ListboxButton class="select text-left truncate">{{ modelValue.tipo_inmueble || 'Seleccionar…' }}</ListboxButton>
                <ListboxOptions class="absolute z-10 mt-1 max-h-60 w-full overflow-auto card py-1">
                  <ListboxOption v-for="tipo in catalogos.tiposInmueble" :key="tipo" :value="tipo" v-slot="{ active, selected }">
                    <li :class="optClass(active, selected)">{{ tipo }}</li>
                  </ListboxOption>
                </ListboxOptions>
              </div>
            </Listbox>
          </div>

          <div>
            <label class="label">Referencia catastral</label>
            <input :value="modelValue.referencia_catastral"
                   @input="updateField('referencia_catastral', $event.target.value)"
                   type="text" maxlength="20" placeholder="14 / 20 dígitos" class="input font-mono" />
          </div>

          <div>
            <label class="label">Código BIC</label>
            <input :value="modelValue.codigo_bien_interes_cultural"
                   @input="updateField('codigo_bien_interes_cultural', $event.target.value)" type="text" class="input" />
          </div>

          <div>
            <label class="label">Estado</label>
            <Listbox :modelValue="modelValue.estado" @update:modelValue="updateField('estado', $event)">
              <div class="relative">
                <ListboxButton class="select text-left truncate">{{ getEstadoLabel(modelValue.estado) || 'Seleccionar…' }}</ListboxButton>
                <ListboxOptions class="absolute z-10 mt-1 max-h-60 w-full overflow-auto card py-1">
                  <ListboxOption v-for="estado in catalogos.estados" :key="estado.value" :value="estado.value" v-slot="{ active, selected }">
                    <li :class="optClass(active, selected)">{{ estado.label }}</li>
                  </ListboxOption>
                </ListboxOptions>
              </div>
            </Listbox>
          </div>

          <div>
            <label class="label">Estado de conservación</label>
            <Listbox :modelValue="modelValue.estado_conservacion" @update:modelValue="updateField('estado_conservacion', $event)">
              <div class="relative">
                <ListboxButton class="select text-left truncate">{{ getConservacionLabel(modelValue.estado_conservacion) || 'Seleccionar…' }}</ListboxButton>
                <ListboxOptions class="absolute z-10 mt-1 max-h-60 w-full overflow-auto card py-1">
                  <ListboxOption v-for="c in catalogos.estadosConservacion" :key="c.value" :value="c.value" v-slot="{ active, selected }">
                    <li :class="optClass(active, selected)">{{ c.label }}</li>
                  </ListboxOption>
                </ListboxOptions>
              </div>
            </Listbox>
          </div>

          <!-- Ubicación -->
          <p class="ui-section">Ubicación</p>

          <div class="col-span-2">
            <label class="label">Dirección</label>
            <input :value="modelValue.direccion" @input="updateField('direccion', $event.target.value)" type="text" class="input" />
          </div>
          <div>
            <label class="label">Código postal</label>
            <input :value="modelValue.codigo_postal" @input="updateField('codigo_postal', $event.target.value)"
                   type="text" maxlength="5" class="input" />
          </div>
          <div>
            <label class="label">Comunidad Autónoma</label>
            <Listbox :modelValue="modelValue.comunidad_autonoma" @update:modelValue="updateField('comunidad_autonoma', $event)">
              <div class="relative">
                <ListboxButton class="select text-left truncate">{{ modelValue.comunidad_autonoma || 'Seleccionar…' }}</ListboxButton>
                <ListboxOptions class="absolute z-10 mt-1 max-h-60 w-full overflow-auto card py-1">
                  <ListboxOption v-for="ccaa in catalogos.comunidadesAutonomas" :key="ccaa" :value="ccaa" v-slot="{ active, selected }">
                    <li :class="optClass(active, selected)">{{ ccaa }}</li>
                  </ListboxOption>
                </ListboxOptions>
              </div>
            </Listbox>
          </div>

          <div v-if="modelValue.comunidad_autonoma">
            <label class="label">Provincia</label>
            <Listbox :modelValue="modelValue.provincia" @update:modelValue="updateField('provincia', $event)">
              <div class="relative">
                <ListboxButton class="select text-left truncate">{{ modelValue.provincia || 'Seleccionar…' }}</ListboxButton>
                <ListboxOptions class="absolute z-10 mt-1 max-h-60 w-full overflow-auto card py-1">
                  <ListboxOption v-for="prov in provinciasFiltered" :key="prov" :value="prov" v-slot="{ active, selected }">
                    <li :class="optClass(active, selected)">{{ prov }}</li>
                  </ListboxOption>
                </ListboxOptions>
              </div>
            </Listbox>
          </div>

          <div v-if="modelValue.provincia">
            <label class="label">Localidad</label>
            <Combobox :modelValue="modelValue.localidad" @update:modelValue="updateField('localidad', $event)">
              <div class="relative">
                <ComboboxInput @change="queryLocalidad = $event.target.value" :displayValue="(l) => l" placeholder="Buscar…" class="input" />
                <ComboboxOptions class="absolute z-10 mt-1 max-h-60 w-full overflow-auto card py-1">
                  <ComboboxOption v-for="loc in localidadesFiltered" :key="loc" :value="loc" v-slot="{ active, selected }">
                    <li :class="optClass(active, selected)">{{ loc }}</li>
                  </ComboboxOption>
                </ComboboxOptions>
              </div>
            </Combobox>
          </div>

          <!-- Coordenadas: el botón alterna entre geolocalizar y ver/ocultar el mapa -->
          <div class="col-span-2">
            <label class="label">Coordenadas</label>
            <div class="flex items-center gap-2">
              <input :value="modelValue.latitud" @input="updateField('latitud', parseFloat($event.target.value))"
                     type="number" step="0.000001" placeholder="Latitud" class="input w-28" />
              <input :value="modelValue.longitud" @input="updateField('longitud', parseFloat($event.target.value))"
                     type="number" step="0.000001" placeholder="Longitud" class="input w-28" />
              <UiButton v-if="tieneCoords" variant="secondary" :icon="mostrarMapa ? 'cerrar' : 'mapa'"
                        class="whitespace-nowrap ml-auto" @click="mostrarMapa = !mostrarMapa">
                {{ mostrarMapa ? 'Ocultar mapa' : 'Ver en el mapa' }}
              </UiButton>
              <UiButton v-else variant="secondary" icon="map-pin" :loading="geolocalizando"
                        class="whitespace-nowrap ml-auto" @click="intentarGeolocalizacion">
                Intentar geolocalización
              </UiButton>
            </div>
          </div>

          <!-- Características -->
          <p class="ui-section">Características</p>
          <div>
            <label class="label">Fecha construcción</label>
            <input :value="modelValue.fecha_construccion" @input="updateField('fecha_construccion', $event.target.value)" type="date" class="input" />
          </div>
          <div>
            <label class="label">Superficie construida (m²)</label>
            <input :value="modelValue.superficie_construida" @input="updateField('superficie_construida', parseFloat($event.target.value))"
                   type="number" step="0.01" class="input" />
          </div>
          <div>
            <label class="label">Superficie parcela (m²)</label>
            <input :value="modelValue.superficie_parcela" @input="updateField('superficie_parcela', parseFloat($event.target.value))"
                   type="number" step="0.01" class="input" />
          </div>

          <!-- Descripción -->
          <p class="ui-section">Descripción</p>
          <div class="col-span-full">
            <textarea :value="modelValue.descripcion" @input="updateField('descripcion', $event.target.value)"
                      rows="2" class="input resize-y" />
          </div>
        </div>
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

const emit = defineEmits(['update:modelValue', 'geolocalizar'])

const queryLocalidad = ref('')
const geolocalizando = ref(false)
const mostrarMapa = ref(false)

const tieneCoords = computed(() => !!(props.modelValue.latitud && props.modelValue.longitud))

// Si dejan de existir coordenadas, ocultar el panel del mapa.
watch(tieneCoords, (v) => { if (!v) mostrarMapa.value = false })

/**
 * Lanza un intento de geolocalización (cascada del backend: fusión OSM → geocoder
 * con validación point-in-polygon). NO inventa coordenadas: si el servicio no
 * acierta con confianza, el inmueble queda "pendiente de geolocalizar".
 * Emite el contexto de dirección para que la vista invoque el servicio.
 */
const intentarGeolocalizacion = () => {
  emit('geolocalizar', {
    direccion: props.modelValue.direccion,
    codigo_postal: props.modelValue.codigo_postal,
    localidad: props.modelValue.localidad,
    provincia: props.modelValue.provincia,
    comunidad_autonoma: props.modelValue.comunidad_autonoma,
    denominacion: props.modelValue.denominacion_principal,
  })
}

// Clase austera para las opciones de Listbox/Combobox (DRY).
const optClass = (active, selected) => [
  'px-3 py-1.5 text-sm cursor-pointer',
  active ? 'bg-zinc-100' : '',
  selected ? 'font-semibold text-primary-700' : 'text-zinc-700',
]

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
