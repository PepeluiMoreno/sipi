import { useTipologiaBase } from './useTipologiaBase'

/**
 * Factory para usar el composable base con cualquier nombre de tipología
 * @param {String} nombre - Nombre del modelo (ej: 'estadosConservacion')
 */
export function useTipologiaGenerico(nombre) {
  return useTipologiaBase(nombre)
}