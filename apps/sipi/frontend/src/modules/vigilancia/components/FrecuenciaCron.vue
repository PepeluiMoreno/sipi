<!-- FrecuenciaCron.vue — constructor de frecuencia humano (v-model: expresión cron). -->
<template>
  <div class="space-y-2">
    <div v-if="!avanzado" class="space-y-2">
      <div class="flex items-center gap-2 flex-wrap">
        <span class="text-sm text-zinc-600">Cada</span>
        <input v-if="!intervaloFijo" type="number" min="1" v-model.number="p.n" class="input w-16" />
        <select v-model="p.unidad" class="select w-auto">
          <option v-for="u in UNIDADES" :key="u.id" :value="u.id">{{ u.label }}</option>
        </select>
      </div>

      <!-- según unidad: día de la semana -->
      <div v-if="p.unidad === 'semana'" class="flex items-center gap-2 flex-wrap">
        <span class="text-sm text-zinc-600">el</span>
        <select v-model.number="p.diaSemana" class="select w-auto">
          <option v-for="(d, i) in DIAS_SEMANA" :key="i" :value="i">{{ d }}</option>
        </select>
      </div>
      <!-- día del mes -->
      <div v-if="p.unidad === 'mes'" class="flex items-center gap-2 flex-wrap">
        <span class="text-sm text-zinc-600">el día</span>
        <input type="number" min="1" max="28" v-model.number="p.diaMes" class="input w-16" />
        <span class="text-xs text-zinc-400">(1–28)</span>
      </div>
      <!-- hora del día (para día/semana/mes) -->
      <div v-if="['dia', 'semana', 'mes'].includes(p.unidad)" class="flex items-center gap-2">
        <span class="text-sm text-zinc-600">a las</span>
        <input type="number" min="0" max="23" v-model.number="p.hora" class="input w-16" />
        <span class="text-zinc-400">:</span>
        <input type="number" min="0" max="59" v-model.number="p.minuto" class="input w-16" />
      </div>
    </div>

    <!-- modo avanzado: cron crudo -->
    <input v-else v-model="cronManual" class="input font-mono text-sm"
           placeholder="min hora díaMes mes díaSemana" @input="emit('update:modelValue', cronManual.trim())" />

    <p class="text-xs text-zinc-400 flex items-center gap-2">
      <span>{{ resumen(p) }}</span>
      <template v-if="p.unidad !== 'manual'">
        · <code class="font-mono">{{ cronActual }}</code>
      </template>
      <button type="button" class="underline hover:text-zinc-600" @click="toggleAvanzado">
        {{ avanzado ? 'usar asistente' : 'editar cron' }}
      </button>
    </p>
  </div>
</template>

<script setup>
import { reactive, ref, computed, watch } from 'vue'
import { UNIDADES, DIAS_SEMANA, partsToCron, cronToParts, resumen } from '../catalog/frecuencias'

const props = defineProps({ modelValue: { type: String, default: '' } })
const emit = defineEmits(['update:modelValue'])

const DEF = { unidad: 'manual', n: 1, hora: 9, minuto: 0, diaSemana: 1, diaMes: 1 }
const parsed = cronToParts(props.modelValue)
const avanzado = ref(parsed === null)
const cronManual = ref(props.modelValue || '')
const p = reactive(parsed || { ...DEF })

const intervaloFijo = computed(() => p.unidad === 'manual')
const cronActual = computed(() => partsToCron(p))

// builder → emite cron
watch(p, () => { if (!avanzado.value) emit('update:modelValue', cronActual.value) }, { deep: true })

// el padre cambió el valor (p. ej. cargar otro proceso): re-sincroniza sin bucle
watch(() => props.modelValue, (v) => {
  if (avanzado.value) { cronManual.value = v || ''; return }
  if ((v || '') === cronActual.value) return         // eco de nuestro propio emit
  const np = cronToParts(v)
  if (np === null) { avanzado.value = true; cronManual.value = v || '' }
  else Object.assign(p, np)
})

function toggleAvanzado() {
  if (avanzado.value) {
    const np = cronToParts(cronManual.value)
    if (np) { Object.assign(p, np); avanzado.value = false }
    else avanzado.value = false   // si no parsea, vuelve al asistente con lo que haya
  } else {
    cronManual.value = cronActual.value
    avanzado.value = true
  }
}
</script>
