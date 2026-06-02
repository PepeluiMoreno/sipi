import { useAgenteBase } from './useAgenteBase'

/**
 * Composable para Entidades Religiosas
 * Usa el composable base que se conecta automáticamente con el esquema GraphQL autogenerado
 */
export function useEntidadReligiosa() {
  return useAgenteBase('entidadesReligiosas', {
    nombreSingular: 'entidadReligiosa',
    nombrePlural: 'entidadesReligiosas',
    conTitulares: true,
    conContacto: true,
    conDireccion: true
  })
}
