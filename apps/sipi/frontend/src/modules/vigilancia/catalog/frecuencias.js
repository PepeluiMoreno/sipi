// Frecuencias humanizadas para los procesos de vigilancia.
// El usuario elige una opción legible; por debajo se guarda un cron en
// ProcesoVigilancia.frecuenciaCron (vacío = solo manual).

export const PRESETS = [
  { id: 'manual', label: 'Manual (no se ejecuta solo)', cron: '' },
  { id: 'horaria', label: 'Cada hora', cron: '0 * * * *' },
  { id: 'cada6', label: 'Cada 6 horas', cron: '0 */6 * * *' },
  { id: 'cada12', label: 'Cada 12 horas', cron: '0 */12 * * *' },
  { id: 'diaria', label: 'Una vez al día (de madrugada)', cron: '0 3 * * *' },
  { id: 'semanal', label: 'Una vez por semana (lunes)', cron: '0 3 * * 1' },
  { id: 'mensual', label: 'Una vez al mes (día 1)', cron: '0 3 1 * *' },
  { id: 'custom', label: 'Personalizada (cron avanzado)…', cron: null },
]

export function presetDesdeCron(cron) {
  const c = (cron || '').trim()
  const p = PRESETS.find(x => x.cron === c)
  if (p) return p.id
  return c ? 'custom' : 'manual'
}

export function cronDesdePreset(presetId, cronCustom = '') {
  const p = PRESETS.find(x => x.id === presetId)
  if (!p) return ''
  if (p.id === 'custom') return (cronCustom || '').trim()
  return p.cron
}

// Texto legible de una frecuencia (para listados).
export function humanizar(cron) {
  const c = (cron || '').trim()
  if (!c) return 'Manual'
  const p = PRESETS.find(x => x.cron === c && x.id !== 'custom')
  return p ? p.label : `Cron: ${c}`
}
