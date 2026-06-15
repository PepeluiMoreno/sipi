// orgConfig — parámetros generales que el frontend necesita en vivo (p. ej. sesión).
// Se rellena desde las Configuraciones del backend (clave/valor). Defaults seguros.
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useOrgConfigStore = defineStore('orgConfig', () => {
  const sessionInactividad = ref(30)   // minutos; 0 = sin timeout
  const sessionMaximo = ref(480)       // minutos; 0 = sin límite

  // Aplica un listado de configuraciones [{clave, valor}] a los parámetros conocidos.
  const aplicarConfiguraciones = (items = []) => {
    for (const c of items) {
      const v = parseInt(c.valor, 10)
      if (Number.isNaN(v)) continue
      if (c.clave === 'seguridad.timeout_inactividad_min') sessionInactividad.value = v
      else if (c.clave === 'seguridad.timeout_sesion_min') sessionMaximo.value = v
    }
  }

  return { sessionInactividad, sessionMaximo, aplicarConfiguraciones }
})
