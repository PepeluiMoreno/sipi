<!-- ProcesosVigilancia.vue — alta/edición y afinado de los procesos de vigilancia. -->
<template>
  <PageShell title="Procesos de vigilancia" icon="vigilancia" :padded="false">
    <template #actions>
      <UiButton v-if="sel" variant="primary" icon="check" :loading="guardando"
                :disabled="!hayCambios || !form.nombre" @click="guardar">Guardar</UiButton>
    </template>

    <div class="flex h-full min-h-0">
      <!-- Maestro -->
      <aside class="w-60 shrink-0 border-r border-zinc-200 flex flex-col min-h-0 bg-zinc-50/40">
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
                    class="w-full text-left px-3 py-2 flex items-center gap-2 text-sm hover:bg-white"
                    :class="esActual(p) ? 'bg-white text-primary-700 font-medium' : 'text-zinc-700'"
                    @click="seleccionar(p)">
              <span class="w-2 h-2 rounded-full shrink-0" :class="p.activo ? 'bg-emerald-500' : 'bg-zinc-300'"></span>
              <span class="truncate">{{ p.nombre || '(sin nombre)' }}</span>
            </button>
          </template>
          <UiEmptyState v-if="!items.length && !sel" icon="vigilancia"
                        title="Sin procesos" subtitle="Crea el primero con «Nuevo»." class="mt-8" />
        </div>
      </aside>

      <!-- Detalle (ancho, multi-columna) -->
      <section class="flex-1 overflow-auto min-h-0">
        <div v-if="!sel" class="h-full flex items-center justify-center text-zinc-400">
          Selecciona un proceso o crea uno nuevo para afinar sus parámetros.
        </div>

        <div v-else class="p-5 space-y-4">
          <!-- Cabecera: nombre + tipo + activo -->
          <div class="flex flex-wrap items-center gap-3">
            <input v-model="form.nombre" placeholder="Nombre del proceso"
                   class="input text-lg font-semibold flex-1 min-w-[16rem]" />
            <span class="rounded bg-zinc-100 text-zinc-600 text-xs px-2 py-1">{{ tipoLabel(form.tipo) }}</span>
            <button type="button" class="flex items-center gap-2 text-sm text-zinc-600 select-none"
                    @click="form.activo = !form.activo">
              <span class="relative inline-flex h-6 w-11 items-center rounded-full transition"
                    :class="form.activo ? 'bg-emerald-500' : 'bg-zinc-300'">
                <span class="inline-block h-5 w-5 rounded-full bg-white shadow transition"
                      :class="form.activo ? 'translate-x-5' : 'translate-x-0.5'"></span>
              </span>
              {{ form.activo ? 'Activo' : 'Pausado' }}
            </button>
          </div>
          <p v-if="descripcionTipo" class="text-sm text-zinc-500 -mt-1">{{ descripcionTipo }}</p>

          <div class="grid grid-cols-1 2xl:grid-cols-2 gap-4 items-start">
            <!-- Programación -->
            <UiPanel title="Programación" icon="config">
              <div class="space-y-3">
                <div>
                  <label class="block text-sm text-zinc-700 mb-1">Cada cuánto se ejecuta</label>
                  <select v-model="preset" class="input">
                    <option v-for="p in PRESETS" :key="p.id" :value="p.id">{{ p.label }}</option>
                  </select>
                </div>
                <div v-if="preset === 'custom'">
                  <label class="block text-sm text-zinc-700 mb-1">Expresión cron</label>
                  <input v-model="cronCustom" placeholder="0 */6 * * *" class="input font-mono" />
                  <p class="mt-1 text-xs text-zinc-400">Formato cron estándar (min hora día mes díaSemana).</p>
                </div>
                <div>
                  <label class="block text-sm text-zinc-700 mb-1">Severidad por defecto de los avisos</label>
                  <select v-model="form.severidadDefecto" class="input w-40">
                    <option v-for="s in SEVERIDADES" :key="s" :value="s">{{ s }}</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm text-zinc-700 mb-1">Descripción</label>
                  <textarea v-model="form.descripcion" rows="2" class="input"
                            placeholder="Para qué sirve este proceso…"></textarea>
                </div>
              </div>
            </UiPanel>

            <!-- Criterios de detección (comunes a todos los tipos) -->
            <UiPanel title="Criterios de detección" icon="ajustes">
              <div class="space-y-3">
                <div>
                  <label class="block text-sm text-zinc-700 mb-1">Palabras clave de inclusión</label>
                  <KeywordInput v-model="P.keywords_inclusion" placeholder="término + Enter…"
                                help="Términos que SUMAN interés (convento, ermita, palacio episcopal, ábside…)." />
                </div>
                <div>
                  <label class="block text-sm text-zinc-700 mb-1">Palabras clave de exclusión</label>
                  <KeywordInput v-model="P.keywords_exclusion" placeholder="término + Enter…"
                                help="Términos que DESCARTAN (obra nueva, promoción, garaje…)." />
                </div>
                <div v-if="form.tipo === 'portal_inmobiliario'">
                  <label class="block text-sm text-zinc-700 mb-1">Tipologías de interés</label>
                  <KeywordInput v-model="P.tipologias" placeholder="convento, ermita…" />
                </div>
                <div v-if="form.tipo === 'desacralizacion'">
                  <label class="block text-sm text-zinc-700 mb-1">Diócesis a vigilar</label>
                  <KeywordInput v-model="P.diocesis" placeholder="Tui-Vigo, Santiago…"
                                help="Vacío = todas las diócesis configuradas." />
                </div>
                <div v-if="form.tipo === 'prensa'">
                  <label class="block text-sm text-zinc-700 mb-1">Medios / fuentes</label>
                  <KeywordInput v-model="P.medios" placeholder="cabecera o feed…" />
                </div>
                <div>
                  <label class="block text-sm text-zinc-700 mb-1">
                    Umbral de certeza: <span class="font-mono text-primary-700">{{ P.umbral_score ?? 60 }}</span>
                  </label>
                  <input type="range" min="0" max="100" step="5" v-model.number="P.umbral_score" class="w-full" />
                  <p class="text-xs text-zinc-400">Score ≥ umbral → hallazgo «cierto»; por debajo → «dudoso» (revisión humana).</p>
                </div>
              </div>
            </UiPanel>
          </div>

          <!-- Fuentes (solo portales): cada una con su fetcher -->
          <UiPanel v-if="form.tipo === 'portal_inmobiliario'" title="Fuentes y cómo obtenerlas" icon="config">
            <template #actions>
              <UiButton size="sm" icon="plus" variant="ghost" @click="añadirFuente">Añadir fuente</UiButton>
            </template>
            <p class="text-xs text-zinc-400 mb-3">
              Cada portal/fuente declara su <b>fetcher</b> (API REST, scraper HTML, RSS…); los datos a
              rellenar dependen de ese tipo. Así la app sabe exactamente cómo obtener los anuncios.
            </p>
            <div class="space-y-3">
              <FuenteEditor v-for="(fu, i) in (P.fuentes || [])" :key="fu.id"
                            :model-value="fu" @update:model-value="v => actualizarFuente(i, v)"
                            @remove="quitarFuente(i)" />
              <p v-if="!(P.fuentes || []).length" class="text-sm text-zinc-400 text-center py-6 border border-dashed rounded-lg">
                Sin fuentes. Añade al menos una para que el proceso tenga de dónde leer.
              </p>
            </div>
          </UiPanel>
        </div>
      </section>
    </div>
  </PageShell>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useQuery, useMutation } from '@vue/apollo-composable'
import { tiposLista, tipoLabel, TIPOS_PROCESO, SEVERIDADES } from '../catalog/vigilanciaCatalog'
import { PRESETS, presetDesdeCron, cronDesdePreset } from '../catalog/frecuencias'
import { fuenteNueva } from '../catalog/fetcherCatalog'
import { PROCESOS_VIGILANCIA, CREAR_PROCESO, ACTUALIZAR_PROCESO } from '../graphql/vigilanciaQueries'
import KeywordInput from '../components/KeywordInput.vue'
import FuenteEditor from '../components/FuenteEditor.vue'

const tipos = tiposLista()

const { result, refetch } = useQuery(PROCESOS_VIGILANCIA)
const items = computed(() => result.value?.procesosVigilancia?.items ?? [])
const porTipo = computed(() => {
  const g = {}
  for (const p of items.value) (g[p.tipo] ??= []).push(p)
  return g
})

const sel = ref(null)
const nuevoTipo = ref('portal_inmobiliario')
const form = reactive({ id: null, nombre: '', tipo: '', descripcion: '', activo: true,
  severidadDefecto: 'aviso', parametros: {} })
const P = reactive({})            // alias reactivo de form.parametros
const preset = ref('manual')
const cronCustom = ref('')
let original = ''

const descripcionTipo = computed(() => TIPOS_PROCESO[form.tipo]?.descripcion ?? '')

function defaultsParametros(tipo) {
  const base = { keywords_inclusion: [], keywords_exclusion: [], umbral_score: 60 }
  if (tipo === 'portal_inmobiliario') return { ...base, tipologias: [], fuentes: [] }
  if (tipo === 'desacralizacion') return { ...base, umbral_score: 70, diocesis: [] }
  if (tipo === 'prensa') return { ...base, umbral_score: 50, medios: [] }
  return base
}

function snapshot() {
  return JSON.stringify({ ...form, parametros: P, frec: cronDesdePreset(preset.value, cronCustom.value) })
}
const hayCambios = computed(() => snapshot() !== original)

function cargar(p) {
  form.id = p.id ?? null
  form.nombre = p.nombre ?? ''
  form.tipo = p.tipo
  form.descripcion = p.descripcion ?? ''
  form.activo = p.activo ?? true
  form.severidadDefecto = p.severidadDefecto ?? 'aviso'
  const merged = { ...defaultsParametros(p.tipo), ...(p.parametros || {}) }
  Object.keys(P).forEach(k => delete P[k])
  Object.assign(P, merged)
  preset.value = presetDesdeCron(p.frecuenciaCron)
  cronCustom.value = preset.value === 'custom' ? (p.frecuenciaCron || '') : ''
  original = snapshot()
}

function seleccionar(p) { sel.value = p; cargar(p) }

function nuevo() {
  const draft = { _draft: Date.now(), tipo: nuevoTipo.value, nombre: '', activo: true,
    severidadDefecto: 'aviso', parametros: defaultsParametros(nuevoTipo.value), frecuenciaCron: '' }
  sel.value = draft
  cargar(draft)
}

function esActual(p) {
  return sel.value && ((p.id && p.id === form.id) || (!p.id && p === sel.value))
}

// --- fuentes ---
function añadirFuente() { (P.fuentes ??= []).push(fuenteNueva('api_rest')) }
function actualizarFuente(i, v) { P.fuentes[i] = v }
function quitarFuente(i) { P.fuentes.splice(i, 1) }

const { mutate: crear } = useMutation(CREAR_PROCESO)
const { mutate: actualizar } = useMutation(ACTUALIZAR_PROCESO)
const guardando = ref(false)

function datos() {
  return {
    nombre: form.nombre,
    tipo: form.tipo,
    descripcion: form.descripcion || null,
    activo: form.activo,
    frecuenciaCron: cronDesdePreset(preset.value, cronCustom.value) || null,
    severidadDefecto: form.severidadDefecto,
    parametros: JSON.parse(JSON.stringify(P)),
  }
}

async function guardar() {
  guardando.value = true
  try {
    if (form.id) await actualizar({ data: { id: form.id, ...datos() } })
    else {
      const { data } = await crear({ data: datos() })
      form.id = data?.createProcesoVigilancia?.id ?? null
    }
    const { data } = await refetch()
    const actual = (data?.procesosVigilancia?.items ?? []).find(p => p.id === form.id)
    if (actual) seleccionar(actual)
    else original = snapshot()
  } finally {
    guardando.value = false
  }
}
</script>
