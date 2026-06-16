<!-- FuenteEditor.vue — configura una fuente/portal: fetcher + sus parámetros. -->
<template>
  <div class="rounded-lg border border-zinc-200 bg-white">
    <!-- Cabecera: nombre · fetcher · activa · eliminar -->
    <div class="flex flex-wrap items-center gap-2 p-3 border-b border-zinc-100 bg-zinc-50/60">
      <input v-model="f.nombre" placeholder="Nombre de la fuente (Idealista…)"
             class="input flex-1 min-w-[10rem] font-medium" @input="emit" />
      <select v-model="f.fetcher" class="input w-auto text-sm" @change="cambiarFetcher">
        <option v-for="ft in fetchers" :key="ft.code" :value="ft.code">{{ ft.label }}</option>
      </select>
      <button type="button" class="flex items-center gap-1.5 text-sm text-zinc-600 select-none"
              @click="f.activa = !f.activa; emit()">
        <span class="relative inline-flex h-5 w-9 items-center rounded-full transition"
              :class="f.activa ? 'bg-emerald-500' : 'bg-zinc-300'">
          <span class="inline-block h-4 w-4 rounded-full bg-white transition"
                :class="f.activa ? 'translate-x-4' : 'translate-x-0.5'"></span>
        </span>
        {{ f.activa ? 'Activa' : 'Pausada' }}
      </button>
      <button v-if="removable" type="button" class="text-zinc-400 hover:text-red-600 px-1" title="Eliminar fuente"
              @click="$emit('remove')">✕</button>
    </div>

    <p class="px-3 pt-2 text-xs text-zinc-400">{{ def?.descripcion }}</p>

    <!-- Parámetros del fetcher (rejilla ancha) -->
    <div class="p-3 grid grid-cols-1 md:grid-cols-2 gap-3">
      <div v-for="p in def?.params || []" :key="p.key"
           :class="(p.tipo === 'kv' || p.tipo === 'url') ? 'md:col-span-2' : ''">
        <label class="block text-xs font-medium text-zinc-600 mb-1">
          {{ p.label }}<span v-if="p.requerido" class="text-red-500">*</span>
        </label>

        <select v-if="p.tipo === 'select'" v-model="f.params[p.key]" class="input" @change="emit">
          <option v-for="o in p.opciones" :key="o" :value="o">{{ o }}</option>
        </select>

        <input v-else-if="p.tipo === 'bool'" type="checkbox" v-model="f.params[p.key]" @change="emit"
               class="rounded border-zinc-300 text-primary-600 focus:ring-primary-500" />

        <!-- pares clave=valor: una línea «clave=valor» -->
        <textarea v-else-if="p.tipo === 'kv'" rows="3" class="input font-mono text-sm"
                  :value="kvTexto(p.key)" @input="kvParse(p.key, $event.target.value)"
                  placeholder="operation=sale&#10;propertyType=homes"></textarea>

        <input v-else v-model="f.params[p.key]" :placeholder="p.placeholder || ''"
               :type="p.tipo === 'url' ? 'url' : 'text'" class="input" @input="emit" />

        <p v-if="p.help" class="mt-1 text-xs text-zinc-400">{{ p.help }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed, watch } from 'vue'
import { fetchersLista, fetcherDef, fuenteNueva } from '../catalog/fetcherCatalog'

const props = defineProps({
  modelValue: { type: Object, required: true },
  removable: { type: Boolean, default: true },
})
const emitFn = defineEmits(['update:modelValue', 'remove'])

const fetchers = fetchersLista()
const f = reactive({ ...props.modelValue })
watch(() => props.modelValue, (v) => { if (v && v.id !== f.id) Object.assign(f, v) })

const def = computed(() => fetcherDef(f.fetcher))

function emit() { emitFn('update:modelValue', JSON.parse(JSON.stringify(f))) }

function cambiarFetcher() {
  const fresh = fuenteNueva(f.fetcher)
  f.params = fresh.params
  emit()
}

// --- kv como texto «clave=valor» por línea ---
function kvTexto(key) {
  const obj = f.params[key] || {}
  return Object.entries(obj).map(([k, v]) => `${k}=${v}`).join('\n')
}
function kvParse(key, texto) {
  const obj = {}
  for (const linea of texto.split('\n')) {
    const i = linea.indexOf('=')
    if (i > 0) obj[linea.slice(0, i).trim()] = linea.slice(i + 1).trim()
  }
  f.params[key] = obj
  emit()
}
</script>
