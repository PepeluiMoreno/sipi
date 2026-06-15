<!-- ProcesosVigilancia.vue — alta/edición y afinado de los procesos de vigilancia. -->
<template>
  <PageShell title="Procesos de vigilancia" icon="vigilancia" :padded="false">
    <template #actions>
      <UiButton v-if="sel" variant="primary" icon="check" :loading="guardando"
                :disabled="!hayCambios || !form.nombre" @click="guardar">
        Guardar
      </UiButton>
    </template>

    <div class="flex h-full min-h-0">
      <!-- Maestro: lista de procesos por tipo -->
      <aside class="w-72 shrink-0 border-r border-zinc-200 flex flex-col min-h-0">
        <div class="p-3 border-b border-zinc-200 flex gap-2">
          <select v-model="nuevoTipo" class="input text-sm flex-1">
            <option v-for="t in tipos" :key="t.key" :value="t.key">{{ t.label }}</option>
          </select>
          <UiButton size="sm" icon="plus" @click="nuevo">Nuevo</UiButton>
        </div>
        <div class="flex-1 overflow-auto min-h-0">
          <template v-for="t in tipos" :key="t.key">
            <div v-if="porTipo[t.key]?.length"
                 class="px-3 pt-3 pb-1 text-[11px] font-medium text-zinc-400 uppercase tracking-wide">
              {{ t.label }}
            </div>
            <button v-for="p in porTipo[t.key]" :key="p.id || p._draft"
                    class="w-full text-left px-3 py-2 flex items-center gap-2 text-sm hover:bg-zinc-50"
                    :class="esActual(p) ? 'bg-primary-50 text-primary-700' : 'text-zinc-700'"
                    @click="seleccionar(p)">
              <span class="w-2 h-2 rounded-full shrink-0"
                    :class="p.activo ? 'bg-emerald-500' : 'bg-zinc-300'"></span>
              <span class="truncate">{{ p.nombre || '(sin nombre)' }}</span>
            </button>
          </template>
          <UiEmptyState v-if="!items.length && !sel" icon="vigilancia"
                        title="Sin procesos" subtitle="Crea el primero con «Nuevo»." class="mt-8" />
        </div>
      </aside>

      <!-- Detalle: formulario -->
      <section class="flex-1 overflow-auto min-h-0 p-4">
        <div v-if="!sel" class="text-center text-zinc-400 py-16">
          Selecciona un proceso o crea uno nuevo para afinar sus parámetros.
        </div>

        <div v-else class="max-w-3xl mx-auto space-y-4">
          <UiPanel title="General" icon="config">
            <div class="space-y-3">
              <div class="flex items-center gap-2 text-xs text-zinc-500">
                <span class="rounded bg-zinc-100 px-2 py-0.5">{{ tipoLabel(form.tipo) }}</span>
                <span v-if="form.id" class="font-mono text-zinc-400">{{ form.id.slice(0, 8) }}</span>
              </div>
              <div v-for="c in comunes" :key="c.key">
                <label class="block text-sm text-zinc-700 mb-1">
                  {{ c.label }}<span v-if="c.requerido" class="text-red-500">*</span>
                </label>
                <label v-if="c.tipo === 'bool'" class="flex items-center gap-2 text-sm text-zinc-700">
                  <input type="checkbox" v-model="form[c.key]"
                         class="rounded border-zinc-300 text-primary-600 focus:ring-primary-500" />
                  {{ form[c.key] ? 'Sí' : 'No' }}
                </label>
                <select v-else-if="c.tipo === 'select'" v-model="form[c.key]" class="input">
                  <option v-for="o in c.opciones" :key="o" :value="o">{{ o }}</option>
                </select>
                <textarea v-else-if="c.tipo === 'textarea'" v-model="form[c.key]" rows="2" class="input"></textarea>
                <input v-else v-model="form[c.key]" :placeholder="c.placeholder || ''" class="input" />
                <p v-if="c.help" class="mt-1 text-xs text-zinc-400">{{ c.help }}</p>
              </div>
            </div>
          </UiPanel>

          <UiPanel :title="`Parámetros · ${tipoLabel(form.tipo)}`" icon="ajustes">
            <p v-if="descripcionTipo" class="text-xs text-zinc-400 mb-3">{{ descripcionTipo }}</p>
            <div class="space-y-3">
              <div v-for="p in parametros" :key="p.key">
                <label class="block text-sm text-zinc-700 mb-1">{{ p.label }}</label>

                <KeywordInput v-if="p.tipo === 'keywords' || p.tipo === 'lista'"
                              v-model="form.parametros[p.key]" :help="p.help"
                              :placeholder="p.tipo === 'keywords' ? 'término + Enter…' : 'añadir + Enter…'" />

                <template v-else>
                  <input v-if="p.tipo === 'numero'" type="number" v-model.number="form.parametros[p.key]"
                         :min="p.min" :max="p.max" class="input w-32" />
                  <input v-else v-model="form.parametros[p.key]" class="input" />
                  <p v-if="p.help" class="mt-1 text-xs text-zinc-400">{{ p.help }}</p>
                </template>
              </div>
            </div>
          </UiPanel>
        </div>
      </section>
    </div>
  </PageShell>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useQuery, useMutation } from '@vue/apollo-composable'
import {
  CAMPOS_COMUNES, tiposLista, parametrosDe, parametrosDefault, tipoLabel, TIPOS_PROCESO,
} from '../catalog/vigilanciaCatalog'
import { PROCESOS_VIGILANCIA, CREAR_PROCESO, ACTUALIZAR_PROCESO } from '../graphql/vigilanciaQueries'
import KeywordInput from '../components/KeywordInput.vue'

const comunes = CAMPOS_COMUNES
const tipos = tiposLista()

const { result, refetch } = useQuery(PROCESOS_VIGILANCIA)
const items = computed(() => result.value?.procesosVigilancia?.items ?? [])

const porTipo = computed(() => {
  const g = {}
  for (const p of items.value) (g[p.tipo] ??= []).push(p)
  return g
})

const sel = ref(null)          // proceso seleccionado (existente o draft)
const nuevoTipo = ref('portal_inmobiliario')
const form = reactive({ id: null, nombre: '', tipo: '', descripcion: '', activo: true,
  frecuenciaCron: '', severidadDefecto: 'aviso', parametros: {} })
let original = ''

const parametros = computed(() => parametrosDe(form.tipo))
const descripcionTipo = computed(() => TIPOS_PROCESO[form.tipo]?.descripcion ?? '')

function snapshot() { return JSON.stringify(form) }
const hayCambios = computed(() => snapshot() !== original)

function cargar(p) {
  form.id = p.id ?? null
  form.nombre = p.nombre ?? ''
  form.tipo = p.tipo
  form.descripcion = p.descripcion ?? ''
  form.activo = p.activo ?? true
  form.frecuenciaCron = p.frecuenciaCron ?? ''
  form.severidadDefecto = p.severidadDefecto ?? 'aviso'
  // Mezcla defaults del catálogo con lo guardado (asegura todas las claves)
  form.parametros = { ...parametrosDefault(p.tipo), ...(p.parametros || {}) }
  original = snapshot()
}

function seleccionar(p) { sel.value = p; cargar(p) }

function nuevo() {
  const draft = { _draft: Date.now(), tipo: nuevoTipo.value, nombre: '', activo: true,
    severidadDefecto: 'aviso', parametros: parametrosDefault(nuevoTipo.value) }
  sel.value = draft
  cargar(draft)
}

function esActual(p) {
  return sel.value && ((p.id && p.id === form.id) || (!p.id && p === sel.value))
}

const { mutate: crear } = useMutation(CREAR_PROCESO)
const { mutate: actualizar } = useMutation(ACTUALIZAR_PROCESO)
const guardando = ref(false)

function datos() {
  return {
    nombre: form.nombre,
    tipo: form.tipo,
    descripcion: form.descripcion || null,
    activo: form.activo,
    frecuenciaCron: form.frecuenciaCron || null,
    severidadDefecto: form.severidadDefecto,
    parametros: form.parametros,
  }
}

async function guardar() {
  guardando.value = true
  try {
    if (form.id) {
      await actualizar({ data: { id: form.id, ...datos() } })
    } else {
      const { data } = await crear({ data: datos() })
      form.id = data?.createProcesoVigilancia?.id ?? null
    }
    const { data } = await refetch()
    const lista = data?.procesosVigilancia?.items ?? []
    const actual = lista.find(p => p.id === form.id)
    if (actual) seleccionar(actual)
    else original = snapshot()
  } finally {
    guardando.value = false
  }
}
</script>
