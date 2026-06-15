// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import DashboardLayout from '../layouts/DashboardLayout.vue'
import Login from '../modules/auth/views/Login.vue'
import MisDatos from '../modules/auth/views/MisDatos.vue'
import ForgotPassword from '../modules/auth/views/ForgotPassword.vue'
import ResetPassword from '../modules/auth/views/ResetPassword.vue'
import Dashboard from '../modules/core/views/Dashboard.vue'
import NotFound from '../modules/core/views/NotFound.vue'
import Papelera from '../modules/core/views/Papelera.vue'

// Agentes
import AdministracionesView from '../modules/agentes/views/AdministracionesView.vue'
import NotariasView from '../modules/agentes/views/NotariasView.vue'
import RegistrosPropiedadView from '../modules/agentes/views/RegistrosPropiedadView.vue'
import EntidadesReligiosasView from '../modules/agentes/views/EntidadesReligiosasView.vue'

// Inmuebles
import InmueblesView from '../modules/inmuebles/views/InmueblesView.vue'
import InmuebleDetalleView from '../modules/inmuebles/views/InmuebleDetalleView.vue'

// Documentos
import Documentos from '../modules/documentos/views/Documentos.vue'

// Configuración
import ConfigCatalogos from '../modules/catalogos/views/ConfigCatalogos.vue'
import VerificarEmail from '../modules/usuarios/views/VerificarEmail.vue'
// Control de acceso (estilo SIPI)
import ControlAcceso from '../modules/acceso/views/ControlAcceso.vue'
import RolesPermisos from '../modules/acceso/views/RolesPermisos.vue'
import ParametrosGenerales from '../modules/configuracion/views/ParametrosGenerales.vue'
import { getToken } from '../modules/auth/token'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: ForgotPassword,
    meta: { requiresAuth: false }
  },
  {
    path: '/reset-password/:token',
    name: 'ResetPassword',
    component: ResetPassword,
    meta: { requiresAuth: false }
  },
  {
    path: '/verificar-email/:token',
    name: 'VerificarEmail',
    component: VerificarEmail,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: DashboardLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: Dashboard
      },
      // AGENTES
      {
        path: '/administraciones',
        name: 'Administraciones',
        component: AdministracionesView
      },
      {
        path: '/notarias',
        name: 'Notarias',
        component: NotariasView
      },
      {
        path: '/registros-propiedad',
        name: 'RegistrosPropiedad',
        component: RegistrosPropiedadView
      },
      {
        path: '/entidades-religiosas',
        name: 'EntidadesReligiosas',
        component: EntidadesReligiosasView
      },
      // INMUEBLES
      {
        path: '/inmuebles',
        name: 'Inmuebles',
        component: InmueblesView
      },
      {
        path: '/inmuebles/:id',
        name: 'InmuebleDetalle',
        component: InmuebleDetalleView
      },
      // DOCUMENTOS
      {
        path: '/documentos',
        name: 'Documentos',
        component: Documentos
      },
      // CONFIGURACIÓN
      {
        path: '/config/catalogos',
        name: 'ConfigCatalogos',
        component: ConfigCatalogos
      },
      {
        path: '/mis-datos',
        name: 'MisDatos',
        component: MisDatos
      },
      {
        path: '/acceso',
        name: 'ControlAcceso',
        component: ControlAcceso
      },
      {
        path: '/acceso/roles',
        name: 'RolesPermisos',
        component: RolesPermisos
      },
      {
        path: '/config/parametros',
        name: 'ParametrosGenerales',
        component: ParametrosGenerales
      },
      {
        path: '/papelera',
        name: 'Papelera',
        component: Papelera
      },
      // 404
      {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: NotFound
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Guard: las rutas con requiresAuth exigen token. Sin él → /login.
router.beforeEach((to) => {
  const requiere = to.matched.some((r) => r.meta.requiresAuth)
  const autenticado = !!getToken()
  if (requiere && !autenticado) {
    return { name: 'Login', query: to.fullPath !== '/' ? { redirect: to.fullPath } : undefined }
  }
  if (to.name === 'Login' && autenticado) {
    return { path: '/' }
  }
})

export default router