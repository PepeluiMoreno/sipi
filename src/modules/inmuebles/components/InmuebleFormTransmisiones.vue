<template>
  <div class="p-6 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-lg font-semibold text-gray-900">Transmisiones</h3>
        <p class="text-sm text-gray-600 mt-1">Historial de transmisiones patrimoniales</p>
      </div>
      <button
        @click="agregarTransmision"
        class="btn btn-primary btn-sm"
      >
        <PlusIcon class="w-4 h-4 mr-2" />
        Nueva Transmisión
      </button>
    </div>

    <!-- Lista de transmisiones -->
    <div class="space-y-4">
      <div
        v-for="(transmision, index) in transmisiones"
        :key="transmision.id"
        class="border border-gray-200 rounded-lg p-4 bg-white"
      >
        <!-- Header de transmisión -->
        <div class="flex items-center justify-between mb-4">
          <h4 class="text-md font-medium text-gray-900">
            Transmisión #{{ index + 1 }}
          </h4>
          <button
            @click="eliminarTransmision(index)"
            class="btn btn-ghost btn-sm !text-red-600 hover:!bg-red-50"
          >
            <TrashIcon class="w-4 h-4" />
          </button>
        </div>

        <!-- Tipo y Fecha -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Tipo de transmisión</label>
            <select
              v-model="transmision.tipo_transmision_id"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Seleccione tipo</option>
              <option value="compraventa">Compraventa</option>
              <option value="donacion">Donación</option>
              <option value="herencia">Herencia</option>
              <option value="permuta">Permuta</option>
              <option value="dacion_pago">Dación en pago</option>
              <option value="subasta">Subasta</option>
              <option value="otro">Otro</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Fecha de transmisión</label>
            <input
              type="date"
              v-model="transmision.fecha_transmision"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </div>

        <!-- Precio -->
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Precio de venta (€)</label>
          <div class="relative">
            <span class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">€</span>
            <input
              type="number"
              v-model="transmision.precio_venta"
              placeholder="0.00"
              step="0.01"
              class="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </div>

        <!-- Partes intervinientes -->
        <div class="border-t pt-4">
          <h5 class="text-sm font-medium text-gray-900 mb-3">Partes intervinientes</h5>
          
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Transmitente</label>
              <div class="space-y-2">
                <input
                  v-model="transmision.transmitente_id"
                  placeholder="ID del transmitente"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
                <input
                  v-model="transmision.transmitente_nombre"
                  placeholder="Nombre del transmitente"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
                <input
                  v-model="transmision.transmitente_nif"
                  placeholder="NIF/CIF del transmitente"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Adquiriente</label>
              <div class="space-y-2">
                <input
                  v-model="transmision.adquiriente_id"
                  placeholder="ID del adquiriente"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
                <input
                  v-model="transmision.adquiriente_nombre"
                  placeholder="Nombre del adquiriente"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
                <input
                  v-model="transmision.adquiriente_nif"
                  placeholder="NIF/CIF del adquiriente"
                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Documentación -->
        <div class="border-t pt-4">
          <h5 class="text-sm font-medium text-gray-900 mb-3">Documentación</h5>
          
          <div class="space-y-3">
            <label class="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
              <input
                type="checkbox"
                v-model="transmision.tiene_escritura"
                class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <div>
                <span class="text-sm font-medium text-gray-900">Escritura notarial</span>
                <p class="text-xs text-gray-500">Documento notarial de la transmisión</p>
              </div>
            </label>

            <label class="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
              <input
                type="checkbox"
                v-model="transmision.tiene_registro"
                class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
              />
              <div>
                <span class="text-sm font-medium text-gray-900">Inscripción registral</span>
                <p class="text-xs text-gray-500">Inscripción en el Registro de la Propiedad</p>
              </div>
            </label>

            <div v-if="transmision.tiene_escritura" class="ml-6 space-y-2">
              <input
                v-model="transmision.numero_escritura"
                placeholder="Número de escritura"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
              />
              <input
                type="date"
                v-model="transmision.fecha_escritura"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
              />
              <input
                v-model="transmision.notario"
                placeholder="Nombre del notario"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
              />
            </div>
          </div>
        </div>

        <!-- Observaciones -->
        <div class="border-t pt-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Observaciones</label>
          <textarea
            v-model="transmision.observaciones"
            rows="3"
            placeholder="Observaciones adicionales sobre la transmisión..."
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
      </div>
    </div>

    <!-- Estado vacío -->
    <div
      v-if="transmisiones.length === 0"
      class="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg"
    >
      <ArrowPathIcon class="w-12 h-12 text-gray-400 mx-auto mb-4" />
      <h4 class="text-lg font-medium text-gray-900 mb-2">No hay transmisiones</h4>
      <p class="text-gray-500 mb-4">Registre la primera transmisión de este inmueble</p>
      <button
        @click="agregarTransmision"
        class="btn btn-primary"
      >
        <PlusIcon class="w-4 h-4 mr-2" />
        Crear Primera Transmisión
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { PlusIcon, TrashIcon, ArrowPathIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  property: {
    type: Object,
    required: true
  },
  errors: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:property'])

const transmisiones = ref(props.property.transmisiones || [])

watch(transmisiones, (newTransmisiones) => {
  emit('update:property', {
    ...props.property,
    transmisiones: newTransmisiones
  })
}, { deep: true })

const agregarTransmision = () => {
  transmisiones.value.push({
    id: Date.now().toString(),
    tipo_transmision_id: '',
    fecha_transmision: '',
    precio_venta: null,
    transmitente_id: '',
    transmitente_nombre: '',
    transmitente_nif: '',
    adquiriente_id: '',
    adquiriente_nombre: '',
    adquiriente_nif: '',
    tiene_escritura: false,
    tiene_registro: false,
    numero_escritura: '',
    fecha_escritura: '',
    notario: '',
    observaciones: '',
    created_at: new Date().toISOString()
  })
}

const eliminarTransmision = (index) => {
  transmisiones.value.splice(index, 1)
}
</script>