// Catálogo de FETCHERS — alineado con OpenDataManager (ODM).
//
// Una fuente/portal no se vigila "en abstracto": hay que informar a la app CÓMO
// obtener sus datos. Eso depende del tipo de fetcher (API REST, scraper HTML,
// buscador por <select>, feed RSS…), y cada tipo necesita sus propios datos.
// Este catálogo declara, por fetcher, los campos de configuración.
//
// Tipos de campo: texto | url | select | bool | kv (pares clave=valor)

export const FETCHERS = {
  api_rest: {
    label: 'API REST',
    descripcion: 'El portal expone una API (JSON/XML). La vía más fiable cuando existe.',
    params: [
      { key: 'url_base', label: 'URL base de la API', tipo: 'url', requerido: true,
        placeholder: 'https://api.idealista.com' },
      { key: 'endpoint', label: 'Endpoint de búsqueda', tipo: 'texto', placeholder: '/3.5/es/search' },
      { key: 'metodo', label: 'Método', tipo: 'select', opciones: ['GET', 'POST'], default: 'POST' },
      { key: 'auth', label: 'Autenticación', tipo: 'select',
        opciones: ['ninguna', 'api_key', 'oauth2'], default: 'oauth2' },
      { key: 'credencial_ref', label: 'Referencia de credencial', tipo: 'texto',
        help: 'Nombre del secreto/credencial a usar (no se guarda la clave aquí).' },
      { key: 'query', label: 'Parámetros de consulta', tipo: 'kv',
        help: 'Pares clave=valor que filtran la búsqueda (operation=sale, propertyType=…).' },
    ],
  },

  html_paginated: {
    label: 'Scraper HTML (paginado)',
    descripcion: 'Buscador web con paginación automática y selectores CSS. Cuando no hay API.',
    params: [
      { key: 'url_busqueda', label: 'URL de búsqueda', tipo: 'url', requerido: true,
        placeholder: 'https://www.idealista.com/venta-viviendas/…' },
      { key: 'selector_item', label: 'Selector del anuncio (fila)', tipo: 'texto', placeholder: 'article.item' },
      { key: 'selector_titulo', label: 'Selector del título', tipo: 'texto' },
      { key: 'selector_precio', label: 'Selector del precio', tipo: 'texto' },
      { key: 'selector_url', label: 'Selector del enlace al detalle', tipo: 'texto' },
      { key: 'selector_siguiente', label: 'Selector «siguiente página»', tipo: 'texto' },
    ],
  },

  html_searchloop: {
    label: 'Scraper HTML (buscador por desplegable)',
    descripcion: 'Formularios que pivotan sobre las opciones de un <select> (provincia, tipo…) e iteran cada una.',
    params: [
      { key: 'url_busqueda', label: 'URL del formulario', tipo: 'url', requerido: true },
      { key: 'selector_select', label: 'Selector del <select> a recorrer', tipo: 'texto', placeholder: 'select#provincia' },
      { key: 'selector_item', label: 'Selector del anuncio (fila)', tipo: 'texto' },
      { key: 'selector_siguiente', label: 'Selector «siguiente página»', tipo: 'texto' },
    ],
  },

  rss_atom: {
    label: 'RSS / Atom',
    descripcion: 'Feed de sindicación (p. ej. una alerta guardada del portal).',
    params: [
      { key: 'feed_url', label: 'URL del feed', tipo: 'url', requerido: true },
    ],
  },
}

export function fetchersLista() {
  return Object.entries(FETCHERS).map(([code, def]) => ({ code, ...def }))
}

export function fetcherDef(code) {
  return FETCHERS[code] || null
}

export function fetcherLabel(code) {
  return FETCHERS[code]?.label ?? code
}

// Fuente vacía de un tipo de fetcher (con defaults de sus params)
export function fuenteNueva(fetcher = 'api_rest') {
  const params = {}
  for (const p of (FETCHERS[fetcher]?.params ?? [])) {
    if (p.default !== undefined) params[p.key] = p.default
    else if (p.tipo === 'kv') params[p.key] = {}
    else if (p.tipo === 'bool') params[p.key] = false
    else params[p.key] = ''
  }
  return { id: crypto.randomUUID(), nombre: '', fetcher, activa: true, params }
}
