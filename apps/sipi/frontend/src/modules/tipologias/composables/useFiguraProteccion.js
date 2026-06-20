import { useTipologiaBaseStrawchemy } from './useTipologiaBaseStrawchemy'
import * as queries from '../graphql/figuraProteccionQueries.js'

export function useFiguraProteccion() {
  return useTipologiaBaseStrawchemy('figurasProteccion', queries)
}