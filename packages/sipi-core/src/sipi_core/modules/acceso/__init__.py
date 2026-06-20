# dominio: acceso — RBAC por perfiles/roles (estilo SIGA)
#
# El permiso es por TRANSACCIÓN (acción atómica). Los roles agrupan transacciones;
# los usuarios tienen roles; una matriz de permisos (rol→transacciones) resuelve la
# autorización en runtime. Las funcionalidades agrupan transacciones para la UI.
#
# Identidad (Usuario, Rol) vive en modules.usuarios; aquí va la capa de permisos.
