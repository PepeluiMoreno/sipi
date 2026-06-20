<!-- CheckboxDropdown: desplegable multi-selección con checkboxes (filtros estándar).
     v-model = array de valores seleccionados. Reutilizable en toda la app. -->
<template>
  <Popover class="relative" v-slot="{ open }">
    <PopoverButton
      class="inline-flex items-center justify-between gap-2 min-w-[11rem] px-3 py-1.5 text-sm border border-gray-300 rounded-lg bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
    >
      <span class="truncate" :class="modelValue.length ? 'text-gray-900' : 'text-gray-500'">{{ botonTexto }}</span>
      <ChevronDownIcon class="w-4 h-4 text-gray-400 shrink-0 transition-transform" :class="open && 'rotate-180'" />
    </PopoverButton>

    <transition
      enter-active-class="transition ease-out duration-100"
      enter-from-class="opacity-0 translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition ease-in duration-75"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 translate-y-1"
    >
      <PopoverPanel class="absolute z-30 mt-1 w-64 max-h-72 overflow-auto rounded-lg border border-gray-200 bg-white shadow-lg p-1">
        <div v-if="!options.length" class="px-2 py-2 text-sm text-gray-400">Sin opciones</div>
        <!-- Cualquiera = seleccionar todas -->
        <label v-if="options.length"
               class="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-50 cursor-pointer text-sm border-b border-gray-100 mb-1">
          <input type="checkbox" class="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                 :checked="todas" @change="toggleTodas" />
          <span class="text-gray-500">Cualquiera</span>
        </label>
        <label
          v-for="opt in options"
          :key="opt[valueKey]"
          class="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-50 cursor-pointer text-sm"
        >
          <input
            type="checkbox"
            class="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
            :checked="modelValue.includes(opt[valueKey])"
            @change="toggle(opt[valueKey])"
          />
          <span class="truncate text-gray-700">{{ opt[labelKey] }}</span>
        </label>
        <div v-if="modelValue.length" class="border-t border-gray-100 mt-1 pt-1">
          <button type="button" @click="limpiar"
                  class="w-full text-left px-2 py-1 text-xs text-gray-500 hover:text-gray-800">
            Limpiar selección
          </button>
        </div>
      </PopoverPanel>
    </transition>
  </Popover>
</template>

<script setup>
import { computed } from 'vue'
import { Popover, PopoverButton, PopoverPanel } from '@headlessui/vue'
import { ChevronDownIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'Todos' },
  valueKey: { type: String, default: 'id' },
  labelKey: { type: String, default: 'nombre' },
  // staticLabel: el botón muestra siempre el placeholder (los seleccionados se listan fuera)
  staticLabel: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'change'])

const botonTexto = computed(() => {
  if (props.staticLabel) return props.placeholder
  if (!props.modelValue.length) return props.placeholder
  if (props.modelValue.length === 1) {
    const o = props.options.find((o) => o[props.valueKey] === props.modelValue[0])
    return o ? o[props.labelKey] : `${props.modelValue.length} seleccionado`
  }
  return `${props.modelValue.length} seleccionados`
})

// "Cualquiera": marcada cuando están todas seleccionadas; alterna todas / ninguna.
const todas = computed(() => props.options.length > 0 && props.modelValue.length === props.options.length)
const toggleTodas = () => {
  const arr = todas.value ? [] : props.options.map((o) => o[props.valueKey])
  emit('update:modelValue', arr)
  emit('change', arr)
}

const toggle = (val) => {
  const set = new Set(props.modelValue)
  set.has(val) ? set.delete(val) : set.add(val)
  const arr = [...set]
  emit('update:modelValue', arr)
  emit('change', arr)
}
const limpiar = () => {
  emit('update:modelValue', [])
  emit('change', [])
}
</script>
