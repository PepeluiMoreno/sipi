import { gql } from '@apollo/client/core'

export const LOGIN_MUTATION = gql`
  mutation Login($nombreUsuario: String!, $contrasena: String!) {
    login(nombreUsuario: $nombreUsuario, contrasena: $contrasena) {
      ok token usuarioId nombreUsuario mensaje
    }
  }
`

// Autoservicio: "Mis datos"
export const MIS_DATOS_QUERY = gql`
  query MisDatos {
    me { id nombreUsuario nombre apellidos cargo asociacionId
         emailCorporativo emailPersonal telefono telefonoMovil aceptaNotificaciones }
  }
`
export const ACTUALIZAR_MIS_DATOS_MUTATION = gql`
  mutation ActualizarMisDatos($nombre: String, $apellidos: String, $cargo: String,
                              $emailCorporativo: String, $emailPersonal: String,
                              $telefono: String, $telefonoMovil: String, $aceptaNotificaciones: Boolean) {
    actualizarMisDatos(nombre: $nombre, apellidos: $apellidos, cargo: $cargo,
                       emailCorporativo: $emailCorporativo, emailPersonal: $emailPersonal,
                       telefono: $telefono, telefonoMovil: $telefonoMovil,
                       aceptaNotificaciones: $aceptaNotificaciones) { ok mensaje }
  }
`

export const REGISTER_MUTATION = gql`
  mutation Register($input: RegisterInput!) {
    register(input: $input) {
      success
      message
      user {
        id
        nombre
        apellidos
        email
        nombre_usuario
      }
    }
  }
`

export const LOGOUT_MUTATION = gql`
  mutation Logout {
    logout {
      success
      message
    }
  }
`

export const REFRESH_TOKEN_MUTATION = gql`
  mutation RefreshToken {
    refreshToken {
      success
      token
      message
    }
  }
`

export const GET_CURRENT_USER_QUERY = gql`
  query Me {
    me { id nombreUsuario nombre apellidos isSistema asociacionId roles }
  }
`

export const VERIFY_EMAIL_MUTATION = gql`
  mutation VerifyEmail($token: String!) {
    verifyEmail(token: $token) {
      success
      message
      user {
        id
        email_verificado
      }
    }
  }
`

export const RESEND_VERIFICATION_EMAIL_MUTATION = gql`
  mutation ResendVerificationEmail($email: String!) {
    resendVerificationEmail(email: $email) {
      success
      message
    }
  }
`

export const FORGOT_PASSWORD_MUTATION = gql`
  mutation ForgotPassword($email: String!) {
    forgotPassword(email: $email) {
      success
      message
    }
  }
`

export const RESET_PASSWORD_MUTATION = gql`
  mutation ResetPassword($token: String!, $password: String!) {
    resetPassword(token: $token, password: $password) {
      success
      message
    }
  }
`