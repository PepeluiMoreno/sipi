<!-- KeywordInput.vue — editor de listas de términos por chips (keywords, regiones…). -->
<template>
  <div>
    <div class="flex flex-wrap gap-1.5 rounded border border-zinc-300 bg-white p-2 min-h-[2.5rem]"
         :class="{ 'opacity-60': disabled }" @click="focus">
      <span v-for="(item, i) in modelValue" :key="item + i"
            class="inline-flex items-center gap-1 rounded bg-primary-50 text-primary-700 text-xs px-2 py-0.5">
        {{ item }}
        <button v-if="!disabled" type="button" class="text-primary-400 hover:text-primary-700"
                @click.stop="quitar(i)" aria-label="Quitar">×</button>
      </span>
      <input ref="inp" v-model="texto" :disabled="disabled"
             :placeholder="modelValue.length ? '' : (placeholder || 'Añadir y Enter…')"
             class="flex-1 min-w-[8rem] border-0 p-0 text-sm focus:ring-0 focus:outline-none"
             @keydown.enter.prevent="añadir"
             @keydown.,.prevent="añadir"
             @keydown.backspace="borrarUltimo"
             @blur="añadir" />
    </div>
    <p v-if="help" class="mt-1 text-xs text-zinc-400">{{ help }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  placeholder: { type: String, default: '' },
  help: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const inp = ref(null)
const texto = ref('')

function focus() { inp.value?.focus() }

function añadir() {
  const v = texto.value.trim()
  texto.value = ''
  if (!v) return
  // permite pegar varios separados por coma
  const nuevos = v.split(',').map(s => s.trim()).filter(Boolean)
  const set = new Set(props.modelValue)
  let cambiado = false
  for (const n of nuevos) if (!set.has(n)) { set.add(n); cambiado = true }
  if (cambiado) emit('update:modelValue', [...set])
}

function quitar(i) {
  const out = props.modelValue.slice()
  out.splice(i, 1)
  emit('update:modelValue', out)
}

function borrarUltimo(e) {
  if (texto.value === '' && props.modelValue.length) {
    e.preventDefault()
    quitar(props.modelValue.length - 1)
  }
}
</script>
