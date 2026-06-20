<!-- ParametrosGenerales.vue — edición de los parámetros del sistema (Configuracion) -->
<template>
  <PageShell title="Parámetros generales" icon="ajustes" :padded="false">
    <template #actions>
      <UiButton variant="primary" icon="check" :loading="guardando" :disabled="!hayCambios" @click="guardar">
        Guardar
      </UiButton>
    </template>

    <div class="h-full min-h-0 overflow-auto p-4">
      <div class="max-w-3xl mx-auto space-y-4">
        <UiPanel v-for="(items, categoria) in porCategoria" :key="categoria" :title="categoria || 'General'" icon="config">
          <div class="space-y-3">
            <div v-for="c in items" :key="c.id" class="grid grid-cols-3 gap-3 items-center">
              <div class="col-span-2 min-w-0">
                <p class="text-sm text-zinc-800">{{ c.descripcion || c.clave }}</p>
                <p class="text-xs text-zinc-400 font-mono truncate">{{ c.clave }}</p>
              </div>
              <div>
                <label v-if="c.tipoDato === 'bool'" class="flex items-center gap-2 text-sm text-zinc-700">
                  <input type="checkbox" :checked="form[c.id] === 'true'" :disabled="!c.editable"
                         @change="form[c.id] = $event.target.checked ? 'true' : 'false'"
                         class="rounded border-zinc-300 text-primary-600 focus:ring-primary-500" />
                  {{ form[c.id] === 'true' ? 'Sí' : 'No' }}
                </label>
                <input v-else v-model="form[c.id]" :disabled="!c.editable"
                       :type="['int','float'].includes(c.tipoDato) ? 'number' : 'text'"
                       class="input" :class="{ 'opacity-60': !c.editable }" />
              </div>
            </div>
          </div>
        </UiPanel>
        <p v-if="!items.length" class="text-center text-zinc-400 py-8">Sin parámetros</p>
      </div>
    </div>
  </PageShell>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useQuery, useMutation } from '@vue/apollo-composable'
import { useOrgConfigStore } from '@/stores/orgConfig'
import { CONFIGURACIONES, ACTUALIZAR_CONFIGURACION } from '../graphql/configQueries'

const orgConfig = useOrgConfigStore()
const { result, refetch } = useQuery(CONFIGURACIONES)
const items = computed(() => result.value?.configuraciones?.items ?? [])

const form = reactive({})
watch(items, (lista) => { for (const c of lista) if (!(c.id in form)) form[c.id] = c.valor ?? '' }, { immediate: true })

const porCategoria = computed(() => {
  const g = {}
  for (const c of items.value) (g[c.categoria || 'general'] ??= []).push(c)
  return g
})

const cambiados = computed(() => items.value.filter(c => (form[c.id] ?? '') !== (c.valor ?? '')))
const hayCambios = computed(() => cambiados.value.length > 0)

const { mutate: actualizar } = useMutation(ACTUALIZAR_CONFIGURACION)
const guardando = ref(false)

async function guardar() {
  guardando.value = true
  try {
    for (const c of cambiados.value) {
      await actualizar({ data: {
        id: c.id, clave: c.clave, valor: String(form[c.id]), tipoDato: c.tipoDato,
        ambito: c.ambito, categoria: c.categoria ?? null, descripcion: c.descripcion ?? null,
        editable: c.editable, sistema: c.sistema,
      } })
    }
    const { data } = await refetch()
    orgConfig.aplicarConfiguraciones(data?.configuraciones?.items ?? [])
  } finally {
    guardando.value = false
  }
}
</script>
