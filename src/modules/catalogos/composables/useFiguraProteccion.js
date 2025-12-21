import { useCatalogoBaseStrawchemy } from './useCatalogoBaseStrawchemy'
import * as queries from '../graphql/figuraProteccionQueries.js'

export function useFiguraProteccion() {
  return useCatalogoBaseStrawchemy('figurasProteccion', queries)
}