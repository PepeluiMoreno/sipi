import { gql } from '@apollo/client/core'

export const CONFIGURACIONES = gql`
  query Configuraciones { configuraciones(limit: 500, offset: 0) {
    items { id clave valor tipoDato ambito categoria descripcion editable sistema }
  } }
`

export const ACTUALIZAR_CONFIGURACION = gql`
  mutation ActualizarConfiguracion($data: ConfiguracionUpdateInput!) {
    updateConfiguracion(data: $data) { id clave valor }
  }
`
