<!-- ProcesoVigilanciaForm — formulario INLINE en drawer (no modal). Skeleton estándar:
     card + header (título + pestañas + cerrar) + cuerpo + footer (Cancelar/Guardar). -->
<template>
  <div class="card flex flex-col min-h-0 h-full">
    <!-- Cabecera: título + pestañas + cerrar -->
    <div class="shrink-0 px-4 pt-3 border-b border-zinc-200">
      <div class="flex items-center justify-between">
        <h2 class="text-sm font-semibold text-zinc-800">
          {{ form.id ? 'Editar' : 'Nuevo' }} proceso · {{ tipoLabel(form.tipo) }}
        </h2>
        <button @click="$emit('cancelar')" class="btn-ghost btn-icon" title="Cerrar">
          <UiIcon name="atras" size="sm" />
        </button>
      </div>
      <nav class="flex gap-4 mt-2 -mb-px text-sm">
        <button v-for="t in tabs" :key="t.id" @click="tab = t.id"
                class="pb-2 border-b-2 transition-colors"
                :class="tab === t.id ? 'border-indigo-600 text-indigo-700 font-medium' : 'border-transparent text-zinc-500 hover:text-zinc-700'">
          {{ t.label }}
        </button>
      </nav>
    </div>

    <!-- Cuerpo -->
    <div class="flex-1 min-h-0 overflow-auto p-4">
      <!-- ===== CONFIG ===== -->
      <div v-show="tab === 'config'" class="space-y-4">
        <div class="flex items-center gap-3">
          <input v-model="form.nombre" placeholder="Nombre del proceso"
                 class="input font-semibold flex-1" />
          <button type="button" class="flex items-center gap-2 text-sm text-zinc-600 select-none shrink-0"
                  @click="form.activo = !form.activo">
            <span class="relative inline-flex h-6 w-11 items-center rounded-full transition"
                  :class="form.activo ? 'bg-emerald-500' : 'bg-zinc-300'">
              <span class="inline-block h-5 w-5 rounded-full bg-white shadow transition"
                    :class="form.activo ? 'translate-x-5' : 'translate-x-0.5'"></span>
            </span>
            {{ form.activo ? 'Activo' : 'Pausado' }}
          </button>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 items-start">
          <UiPanel title="Programación" icon="config">
            <div class="space-y-3">
              <div>
                <label class="label">Frecuencia</label>
                <FrecuenciaCron v-model="frecuenciaCron" />
              </div>
              <div>
                <label class="label">Severidad por defecto</label>
                <select v-model="form.severidadDefecto" class="select w-40">
                  <option v-for="s in SEVERIDADES" :key="s" :value="s">{{ s }}</option>
                </select>
              </div>
              <div>
                <label class="label">Descripción</label>
                <textarea v-model="form.descripcion" rows="2" class="input"></textarea>
              </div>
            </div>
          </UiPanel>

          <UiPanel title="Criterios de detección" icon="ajustes">
            <div class="space-y-3">
              <div>
                <label class="label">Palabras clave de inclusión</label>
                <KeywordInput v-model="P.keywords_inclusion" placeholder="término + Enter…"
                              help="Suman interés (convento, ermita, palacio episcopal, ábside…)." />
              </div>
              <div>
                <label class="label">Palabras clave de exclusión</label>
                <KeywordInput v-model="P.keywords_exclusion" placeholder="término + Enter…"
                              help="Descartan (obra nueva, promoción, garaje…)." />
              </div>
              <div v-if="form.tipo === 'portal_inmobiliario'">
                <label class="label">Tipologías de interés</label>
                <KeywordInput v-model="P.tipologias" placeholder="convento, ermita…" />
              </div>
              <div v-if="form.tipo === 'desacralizacion'">
                <label class="label">Diócesis a vigilar</label>
                <KeywordInput v-model="P.diocesis" placeholder="Tui-Vigo, Santiago…" />
              </div>
              <div v-if="form.tipo === 'prensa'">
                <label class="label">Medios / fuentes</label>
                <KeywordInput v-model="P.medios" placeholder="cabecera o feed…" />
              </div>
              <div>
                <label class="label">Umbral de certeza: <span class="font-mono text-indigo-700">{{ P.umbral_score ?? 60 }}</span></label>
                <input type="range" min="0" max="100" step="5" v-model.number="P.umbral_score" class="w-full" />
              </div>
            </div>
          </UiPanel>
        </div>

        <UiPanel v-if="form.tipo === 'portal_inmobiliario'" title="Fuentes y cómo obtenerlas" icon="config">
          <template #actions>
            <UiButton size="sm" icon="plus" variant="ghost" @click="añadirFuente">Añadir fuente</UiButton>
          </template>
          <p class="text-xs text-zinc-400 mb-3">
            Cada fuente declara su <b>fetcher</b> (API REST, scraper HTML, RSS…); los datos a rellenar
            dependen de ese tipo.
          </p>
          <div class="space-y-3">
            <FuenteEditor v-for="(fu, i) in (P.fuentes || [])" :key="fu.id"
                          :model-value="fu" @update:model-value="v => P.fuentes[i] = v" @remove="P.fuentes.splice(i, 1)" />
            <p v-if="!(P.fuentes || []).length" class="text-sm text-zinc-400 text-center py-6 border border-dashed rounded-lg">
              Sin fuentes. Añade al menos una.
            </p>
          </div>
        </UiPanel>
      </div>

      <!-- ===== HALLAZGOS ===== -->
      <div v-show="tab === 'hallazgos'" class="space-y-3">
        <div class="flex items-center justify-between">
          <p class="text-sm text-zinc-500">Últimos hallazgos obtenidos por este proceso.</p>
          <UiButton size="sm" icon="search" :loading="probando" :disabled="!form.id" @click="probar">
            Probar ahora
          </UiButton>
        </div>
        <p v-if="!form.id" class="text-xs text-amber-600">Guarda el proceso antes de probarlo.</p>
        <p v-if="probarMsg" class="text-sm rounded bg-zinc-50 border border-zinc-200 px-3 py-2">{{ probarMsg }}</p>

        <div v-if="muestras.length" class="border border-zinc-200 rounded-lg divide-y">
          <div v-for="(m, i) in muestras" :key="i" class="p-2 text-sm flex items-center justify-between gap-3">
            <a :href="m.url" target="_blank" class="truncate text-indigo-700 hover:underline">{{ m.titulo || m.url }}</a>
            <span v-if="m.precio" class="text-zinc-500 shrink-0">{{ m.precio }}</span>
          </div>
        </div>

        <div v-if="hallazgos.length" class="space-y-2">
          <div v-for="h in hallazgos" :key="h.id" class="border border-zinc-200 rounded-lg p-3">
            <div class="flex items-center justify-between gap-2">
              <span class="font-medium text-zinc-800 truncate">{{ h.titulo || h.tipoEvento }}</span>
              <span class="text-xs px-2 py-0.5 rounded-full"
                    :class="h.certeza === 'cierto' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'">
                {{ h.certeza || h.estado }}
              </span>
            </div>
            <p class="text-xs text-zinc-500">{{ h.fuente }} · {{ (h.fechaDeteccion || '').slice(0, 10) }}</p>
          </div>
        </div>
        <p v-else-if="!muestras.length" class="text-sm text-zinc-400 text-center py-8 border border-dashed rounded-lg">
          Aún no hay hallazgos. Usa «Probar ahora» para validar las fuentes.
        </p>
      </div>
    </div>

    <!-- Footer: botones SIEMPRE aquí -->
    <div class="shrink-0 p-3 border-t border-zinc-200 flex justify-end gap-2">
      <UiButton variant="secondary" @click="$emit('cancelar')">Cancelar</UiButton>
      <UiButton variant="primary" icon="check" :loading="loading" :disabled="!form.nombre" @click="handleSubmit">
        Guardar
      </UiButton>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useApolloClient } from '@vue/apollo-composable'
import { tipoLabel, SEVERIDADES } from '../catalog/vigilanciaCatalog'
import { fuenteNueva } from '../catalog/fetcherCatalog'
import { HALLAZGOS_PROCESO, PROBAR_PROCESO } from '../graphql/vigilanciaQueries'
import KeywordInput from './KeywordInput.vue'
import FuenteEditor from './FuenteEditor.vue'
import FrecuenciaCron from './FrecuenciaCron.vue'

const props = defineProps({ proceso: { type: Object, default: null }, loading: Boolean })
const emit = defineEmits(['cancelar', 'save'])

const tabs = [{ id: 'config', label: 'Configuración' }, { id: 'hallazgos', label: 'Hallazgos' }]
const tab = ref('config')

const form = reactive({ id: null, nombre: '', tipo: 'portal_inmobiliario', descripcion: '',
  activo: true, severidadDefecto: 'aviso' })
const P = reactive({})
const frecuenciaCron = ref('')

function defaultsParametros(tipo) {
  const base = { keywords_inclusion: [], keywords_exclusion: [], umbral_score: 60 }
  if (tipo === 'portal_inmobiliario') return { ...base, tipologias: [], fuentes: [] }
  if (tipo === 'desacralizacion') return { ...base, umbral_score: 70, diocesis: [] }
  if (tipo === 'prensa') return { ...base, umbral_score: 50, medios: [] }
  return base
}

function cargarDesde(p) {
  tab.value = 'config'
  muestras.value = []; probarMsg.value = ''; hallazgos.value = []
  const src = p || { tipo: 'portal_inmobiliario' }
  form.id = src.id ?? null
  form.nombre = src.nombre ?? ''
  form.tipo = src.tipo ?? 'portal_inmobiliario'
  form.descripcion = src.descripcion ?? ''
  form.activo = src.activo ?? true
  form.severidadDefecto = src.severidadDefecto ?? 'aviso'
  const merged = { ...defaultsParametros(form.tipo), ...(src.parametros || {}) }
  Object.keys(P).forEach(k => delete P[k])
  Object.assign(P, merged)
  frecuenciaCron.value = src.frecuenciaCron || ''
  if (form.id) cargarHallazgos()
}

function añadirFuente() { (P.fuentes ??= []).push(fuenteNueva('api_rest')) }

function handleSubmit() {
  emit('save', {
    id: form.id,
    nombre: form.nombre,
    tipo: form.tipo,
    descripcion: form.descripcion || null,
    activo: form.activo,
    frecuenciaCron: frecuenciaCron.value || null,
    severidadDefecto: form.severidadDefecto,
    parametros: JSON.parse(JSON.stringify(P)),
  })
}

// --- Hallazgos / Probar ---
const { resolveClient } = useApolloClient()
const hallazgos = ref([])
const muestras = ref([])
const probando = ref(false)
const probarMsg = ref('')

async function cargarHallazgos() {
  try {
    const filters = [{ field: 'proceso_id', operator: 'EQ', value: String(form.id) }]
    const { data } = await resolveClient().query({
      query: HALLAZGOS_PROCESO, variables: { filters, limit: 25 }, fetchPolicy: 'network-only',
    })
    hallazgos.value = data?.hallazgos?.items ?? []
  } catch (e) { hallazgos.value = [] }
}

async function probar() {
  if (!form.id) return
  probando.value = true; probarMsg.value = ''; muestras.value = []
  try {
    const { data } = await resolveClient().mutate({
      mutation: PROBAR_PROCESO, variables: { procesoId: form.id, fuenteId: null },
    })
    const r = data?.probarProcesoVigilancia
    probarMsg.value = r?.mensaje || (r?.ok ? 'Prueba completada.' : 'Sin resultado.')
    muestras.value = r?.muestras ?? []
  } catch (e) {
    probarMsg.value = 'No se pudo ejecutar la prueba (¿motor de fetch disponible?): ' + (e?.message || e)
  } finally {
    probando.value = false
  }
}

// Al final: todos los refs ya están inicializados antes del watch immediate.
watch(() => props.proceso, (p) => cargarDesde(p), { immediate: true })
</script>
