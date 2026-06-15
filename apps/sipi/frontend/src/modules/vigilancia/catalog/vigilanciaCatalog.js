// Catálogo de procesos de vigilancia SIPI-native (fuera de ODM).
//
// Abstrae los "casos de uso": cada TIPO de proceso declara sus parámetros
// afinables. Los VALORES se guardan en ProcesoVigilancia.parametros (JSONB);
// este catálogo define la FORMA del editor (qué campos, de qué tipo) para
// renderizar el formulario dinámico y poder afinar cantidad/calidad de hallazgos.
//
// Tipos de campo de parámetro:
//   texto | textarea | bool | select | numero | lista | keywords
// (lista y keywords se editan con chips; keywords se usa para inclusión/exclusión)

export const SEVERIDADES = ['info', 'aviso', 'alerta']

// Campos comunes — columnas de ProcesoVigilancia (nombres camelCase del GraphQL)
export const CAMPOS_COMUNES = [
  { key: 'nombre', label: 'Nombre', tipo: 'texto', requerido: true },
  { key: 'descripcion', label: 'Descripción', tipo: 'textarea' },
  { key: 'activo', label: 'Activo', tipo: 'bool', default: true },
  {
    key: 'frecuenciaCron', label: 'Frecuencia (cron)', tipo: 'texto',
    placeholder: '0 */6 * * *',
    help: 'Periodicidad de ejecución en formato cron. Vacío = solo manual.',
  },
  {
    key: 'severidadDefecto', label: 'Severidad por defecto', tipo: 'select',
    opciones: SEVERIDADES, default: 'aviso',
    help: 'Severidad de los avisos que emite el proceso si el hallazgo no fija una.',
  },
]

// Tipos de proceso y sus parámetros específicos (los casos de uso afinables)
export const TIPOS_PROCESO = {
  portal_inmobiliario: {
    label: 'Portales inmobiliarios',
    icon: 'home',
    descripcion:
      'Detecta anuncios de venta de inmuebles potencialmente inmatriculados ' +
      '(conventos, palacios episcopales, ermitas, monasterios…).',
    parametros: [
      {
        key: 'portales', label: 'Portales', tipo: 'lista', default: ['idealista'],
        help: 'Portales a rastrear (idealista, fotocasa…).',
      },
      {
        key: 'regiones', label: 'Regiones / provincias', tipo: 'lista',
        help: 'Ámbito territorial. Vacío = todo el Estado.',
      },
      {
        key: 'tipologias', label: 'Tipologías de interés', tipo: 'lista',
        help: 'Tipos de edificio (iglesia, convento, monasterio, ermita, palacio…).',
      },
      {
        key: 'keywords_inclusion', label: 'Palabras clave de inclusión', tipo: 'keywords',
        help: 'Términos que SUMAN religiosidad/inmatriculación: convento, ábside, ' +
          'retablo, palacio episcopal, casa rectoral, espadaña…',
      },
      {
        key: 'keywords_exclusion', label: 'Palabras clave de exclusión', tipo: 'keywords',
        help: 'Términos que DESCARTAN el anuncio: obra nueva, promoción, garaje, ' +
          'plaza de aparcamiento, chalet adosado…',
      },
      {
        key: 'umbral_score', label: 'Umbral de certeza (0–100)', tipo: 'numero',
        min: 0, max: 100, default: 60,
        help: 'Score ≥ umbral → hallazgo "cierto"; por debajo → "dudoso" (revisión humana).',
      },
    ],
  },

  desacralizacion: {
    label: 'Desacralizaciones (CEE)',
    icon: 'church',
    descripcion:
      'Rastrea boletines oficiales diocesanos buscando decretos de reducción a ' +
      'uso profano (c. 1222 §2) y extrae el inmueble afectado.',
    parametros: [
      {
        key: 'diocesis', label: 'Diócesis a vigilar', tipo: 'lista',
        help: 'Boletines a rastrear. Vacío = todas las diócesis configuradas.',
      },
      {
        key: 'keywords_inclusion', label: 'Refuerzos léxicos', tipo: 'keywords',
        help: 'Señales que SUBEN la confianza: canon 1222, supresión de parroquia, ' +
          'desafectación al culto…',
      },
      {
        key: 'keywords_exclusion', label: 'Vetos', tipo: 'keywords',
        help: 'Contextos a DESCARTAR: doctrina, comentario, conferencia, derecho comparado…',
      },
      {
        key: 'umbral_score', label: 'Umbral de confianza (0–100)', tipo: 'numero',
        min: 0, max: 100, default: 70,
      },
    ],
  },

  subvenciones_rehab: {
    label: 'Subvenciones de rehabilitación (BDNS)',
    icon: 'church',
    descripcion:
      'Consulta en OpenDataManager las concesiones BDNS, filtra beneficiarios ' +
      'con NIF R (entidad religiosa) o G (asociación/fundación) y valora la ' +
      'fiabilidad de que financien la rehabilitación de un edificio inmatriculado. ' +
      'Fetcher fijo: ODM (no requiere configurar fuentes).',
    parametros: [
      {
        key: 'recurso_concesiones', label: 'Recurso ODM de concesiones', tipo: 'texto',
        default: 'BDNS - Concesiones de Subvenciones',
        help: 'Nombre EXACTO del recurso publicado en ODM con las concesiones BDNS.',
      },
      {
        key: 'anio', label: 'Año de concesión', tipo: 'numero', min: 2008, max: 2100, default: null,
        help: 'Filtra por año de la concesión. Vacío = todo el dataset.',
      },
      {
        key: 'umbral_score', label: 'Umbral de certeza (0–100)', tipo: 'numero',
        min: 0, max: 100, default: 70,
        help: 'Fiabilidad ≥ umbral → hallazgo "cierto"; por debajo → "dudoso" (revisión humana).',
      },
    ],
  },

  prensa: {
    label: 'Prensa online',
    icon: 'news',
    descripcion:
      'Captura noticias referidas a estos inmuebles (ventas, rehabilitaciones, ' +
      'polémicas de inmatriculación, declaraciones BIC…).',
    parametros: [
      {
        key: 'medios', label: 'Medios / fuentes', tipo: 'lista',
        help: 'Cabeceras, feeds RSS o dominios a vigilar.',
      },
      {
        key: 'keywords_inclusion', label: 'Palabras clave de inclusión', tipo: 'keywords',
      },
      {
        key: 'keywords_exclusion', label: 'Palabras clave de exclusión', tipo: 'keywords',
      },
      {
        key: 'umbral_score', label: 'Umbral (0–100)', tipo: 'numero',
        min: 0, max: 100, default: 50,
      },
    ],
  },
}

export function tiposLista() {
  return Object.entries(TIPOS_PROCESO).map(([key, def]) => ({ key, ...def }))
}

export function parametrosDe(tipo) {
  return TIPOS_PROCESO[tipo]?.parametros ?? []
}

export function tipoLabel(tipo) {
  return TIPOS_PROCESO[tipo]?.label ?? tipo
}

// Valores por defecto de parametros al crear un proceso de un tipo dado
export function parametrosDefault(tipo) {
  const out = {}
  for (const p of parametrosDe(tipo)) {
    if (p.default !== undefined) out[p.key] = p.default
    else if (p.tipo === 'keywords' || p.tipo === 'lista') out[p.key] = []
    else if (p.tipo === 'numero') out[p.key] = null
    else out[p.key] = ''
  }
  return out
}
