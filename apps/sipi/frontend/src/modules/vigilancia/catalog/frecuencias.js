// Frecuencia de ejecución ↔ cron (5 campos: min hora díaMes mes díaSemana).
// El usuario piensa en "cada N [unidad]" y, según la unidad, día de la semana /
// día del mes / hora. Aquí va la conversión en ambos sentidos (DRY: la usan el
// constructor FrecuenciaCron y la card para humanizar).

export const DIAS_SEMANA = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
export const UNIDADES = [
  { id: 'manual', label: '— (manual, no se ejecuta solo)' },
  { id: 'minuto', label: 'minuto(s)' },
  { id: 'hora', label: 'hora(s)' },
  { id: 'dia', label: 'día(s)' },
  { id: 'semana', label: 'semana(s)' },
  { id: 'mes', label: 'mes(es)' },
]

const dosDig = (x) => String(x).padStart(2, '0')

// partes → cron
export function partsToCron(p) {
  const n = Math.max(1, parseInt(p.n, 10) || 1)
  const m = Math.min(59, Math.max(0, parseInt(p.minuto, 10) || 0))
  const h = Math.min(23, Math.max(0, parseInt(p.hora, 10) || 0))
  switch (p.unidad) {
    case 'minuto': return `*/${n} * * * *`
    case 'hora': return `${m} */${n} * * *`
    case 'dia': return n === 1 ? `${m} ${h} * * *` : `${m} ${h} */${n} * *`
    case 'semana': return `${m} ${h} * * ${p.diaSemana ?? 1}`
    case 'mes': return `${m} ${h} ${Math.min(28, Math.max(1, parseInt(p.diaMes, 10) || 1))} * *`
    default: return ''   // manual
  }
}

// cron → partes (best-effort; null si no encaja en el constructor → modo avanzado)
export function cronToParts(cron) {
  const c = (cron || '').trim()
  if (!c) return { unidad: 'manual', n: 1, hora: 9, minuto: 0, diaSemana: 1, diaMes: 1 }
  const f = c.split(/\s+/)
  if (f.length !== 5) return null
  const [m, h, dom, mon, dow] = f
  if (mon !== '*') return null
  const num = (x) => (/^\d+$/.test(x) ? parseInt(x, 10) : null)
  const cadaN = (x) => { const mm = /^\*\/(\d+)$/.exec(x); return mm ? parseInt(mm[1], 10) : null }
  const base = { hora: 9, minuto: 0, diaSemana: 1, diaMes: 1, n: 1 }

  // cada N minutos
  if (cadaN(m) && h === '*' && dom === '*' && dow === '*')
    return { ...base, unidad: 'minuto', n: cadaN(m) }
  // cada N horas
  if (num(m) != null && cadaN(h) && dom === '*' && dow === '*')
    return { ...base, unidad: 'hora', n: cadaN(h), minuto: num(m) }
  // semanal (día de la semana fijado)
  if (num(m) != null && num(h) != null && dom === '*' && num(dow) != null)
    return { ...base, unidad: 'semana', diaSemana: num(dow), hora: num(h), minuto: num(m) }
  // mensual (día del mes fijado)
  if (num(m) != null && num(h) != null && num(dom) != null && dow === '*')
    return { ...base, unidad: 'mes', diaMes: num(dom), hora: num(h), minuto: num(m) }
  // diario / cada N días
  if (num(m) != null && num(h) != null && dow === '*' && (dom === '*' || cadaN(dom)))
    return { ...base, unidad: 'dia', n: cadaN(dom) || 1, hora: num(h), minuto: num(m) }
  return null
}

// cron → texto legible (para listados/cards)
export function humanizar(cron) {
  const c = (cron || '').trim()
  if (!c) return 'Manual'
  const p = cronToParts(c)
  if (!p) return `Cron: ${c}`
  const hhmm = `${p.hora}:${dosDig(p.minuto)}`
  switch (p.unidad) {
    case 'manual': return 'Manual'
    case 'minuto': return p.n === 1 ? 'Cada minuto' : `Cada ${p.n} minutos`
    case 'hora': return p.n === 1 ? 'Cada hora' : `Cada ${p.n} horas`
    case 'dia': return p.n === 1 ? `Cada día a las ${hhmm}` : `Cada ${p.n} días a las ${hhmm}`
    case 'semana': return `Cada semana, ${DIAS_SEMANA[p.diaSemana] || '—'} a las ${hhmm}`
    case 'mes': return `Cada mes, el día ${p.diaMes} a las ${hhmm}`
    default: return `Cron: ${c}`
  }
}

export function resumen(parts) {
  return humanizar(partsToCron(parts))
}
