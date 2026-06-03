import { gql } from '@apollo/client/core'

export const ROLES = gql`
  query Roles { roles(limit: 200, offset: 0) {
    items { id codigo nombre descripcion tipo nivel esTerritorial sistema activo }
  } }
`

export const TRANSACCIONES = gql`
  query Transacciones { transacciones(limit: 500, offset: 0) {
    items { id codigo nombre descripcion modulo tipo activa }
  } }
`

export const ROL_TRANSACCIONES = gql`
  query RolTransacciones { rolTransacciones(limit: 2000, offset: 0) {
    items { id rolId transaccionId }
  } }
`

export const USUARIOS = gql`
  query Usuarios { usuarios(limit: 200, offset: 0) {
    items { id nombreUsuario nombreCompleto emailCorporativo emailVerificado isSistema }
  } }
`

export const CREAR_ROL_TRANSACCION = gql`
  mutation CrearRolTransaccion($data: RolTransaccionCreateInput!) {
    createRolTransaccion(data: $data) { id rolId transaccionId }
  }
`

export const BORRAR_ROL_TRANSACCION = gql`
  mutation BorrarRolTransaccion($id: ID!) { deleteRolTransaccion(id: $id) }
`
