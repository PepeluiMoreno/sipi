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
  query Usuarios { usuarios(limit: 500, offset: 0) {
    items { id nombreUsuario nombre apellidos nombreCompleto identificacion
            emailCorporativo emailPersonal telefono telefonoMovil
            emailVerificado isSistema asociacionId cargo aceptaNotificaciones }
  } }
`

export const USUARIO_ROLES = gql`
  query UsuarioRoles { usuarioRoles(limit: 2000, offset: 0) {
    items { id usuarioId rolId }
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

// ===== Funcionalidades (= permisos) y su asignación a roles =====
export const FUNCIONALIDADES = gql`
  query Funcionalidades { funcionalidades(limit: 500, offset: 0) {
    items { id codigo nombre modulo orden }
  } }
`
export const FUNCIONALIDAD_TRANSACCIONES = gql`
  query FuncionalidadTransacciones { funcionalidadTransacciones(limit: 2000, offset: 0) {
    items { id funcionalidadId transaccionId }
  } }
`
export const ROL_FUNCIONALIDADES = gql`
  query RolFuncionalidades { rolFuncionalidades(limit: 2000, offset: 0) {
    items { id rolId funcionalidadId }
  } }
`
export const CREAR_ROL_FUNCIONALIDAD = gql`
  mutation CrearRolFuncionalidad($data: RolFuncionalidadCreateInput!) {
    createRolFuncionalidad(data: $data) { id rolId funcionalidadId }
  }
`
export const BORRAR_ROL_FUNCIONALIDAD = gql`
  mutation BorrarRolFuncionalidad($id: ID!) { deleteRolFuncionalidad(id: $id) }
`

export const CREAR_USUARIO_ROL = gql`
  mutation CrearUsuarioRol($data: UsuarioRolCreateInput!) {
    createUsuarioRol(data: $data) { id usuarioId rolId }
  }
`

export const BORRAR_USUARIO_ROL = gql`
  mutation BorrarUsuarioRol($id: ID!) { deleteUsuarioRol(id: $id) }
`

// ===== Asociaciones (organizaciones con acceso) =====
export const ASOCIACIONES = gql`
  query Asociaciones { asociaciones(limit: 500, offset: 0) {
    items { id nombre siglas cif descripcion activa emailCorporativo telefono sitioWeb }
  } }
`
export const CREAR_ASOCIACION = gql`
  mutation CrearAsociacion($data: AsociacionCreateInput!) { createAsociacion(data: $data) { id } }
`
export const ACTUALIZAR_ASOCIACION = gql`
  mutation ActualizarAsociacion($data: AsociacionUpdateInput!) { updateAsociacion(data: $data) { id } }
`
export const BORRAR_ASOCIACION = gql`
  mutation BorrarAsociacion($id: ID!) { deleteAsociacion(id: $id) }
`

// ===== Usuarios: registro con credenciales (el usuario ES el miembro) =====
export const REGISTRAR_USUARIO = gql`
  mutation RegistrarUsuario($nombreUsuario: String!, $contrasena: String!, $nombre: String!,
                            $asociacionId: String, $apellidos: String, $identificacion: String,
                            $emailCorporativo: String, $emailPersonal: String, $telefono: String,
                            $telefonoMovil: String, $cargo: String, $aceptaNotificaciones: Boolean, $isSistema: Boolean) {
    registrarUsuario(nombreUsuario: $nombreUsuario, contrasena: $contrasena, nombre: $nombre,
                     asociacionId: $asociacionId, apellidos: $apellidos, identificacion: $identificacion,
                     emailCorporativo: $emailCorporativo, emailPersonal: $emailPersonal, telefono: $telefono,
                     telefonoMovil: $telefonoMovil, cargo: $cargo, aceptaNotificaciones: $aceptaNotificaciones,
                     isSistema: $isSistema) {
      ok id mensaje
    }
  }
`
export const ESTABLECER_CONTRASENA = gql`
  mutation EstablecerContrasena($usuarioId: ID!, $contrasena: String!) {
    establecerContrasena(usuarioId: $usuarioId, contrasena: $contrasena) { ok id mensaje }
  }
`
export const ACTUALIZAR_USUARIO = gql`
  mutation ActualizarUsuario($data: UsuarioUpdateInput!) { updateUsuario(data: $data) { id } }
`
export const BORRAR_USUARIO = gql`
  mutation BorrarUsuario($id: ID!) { deleteUsuario(id: $id) }
`
