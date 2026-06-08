// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import DashboardLayout from '../layouts/DashboardLayout.vue'
import Login from '../modules/auth/views/Login.vue'
import ForgotPassword from '../modules/auth/views/ForgotPassword.vue'
import ResetPassword from '../modules/auth/views/ResetPassword.vue'
import Dashboard from '../modules/core/views/Dashboard.vue'
import NotFound from '../modules/core/views/NotFound.vue'

// Agentes
import AdministracionesView from '../modules/agentes/views/AdministracionesView.vue'
import NotariasView from '../modules/agentes/views/NotariasView.vue'
import RegistrosPropiedadView from '../modules/agentes/views/RegistrosPropiedadView.vue'

// Inmuebles
import InmueblesView from '../modules/inmuebles/views/InmueblesView.vue'
import InmuebleDetalleView from '../modules/inmuebles/views/InmuebleDetalleView.vue'

// Documentos
import Documentos from '../modules/documentos/views/Documentos.vue'

// Configuración
import ConfigCatalogos from '../modules/catalogos/views/ConfigCatalogos.vue'
import ConfigUsuarios from '../modules/usuarios/views/ConfigUsuarios.vue'
import VerificarEmail from '../modules/usuarios/views/VerificarEmail.vue'

// ODM (odmclient)
import OdmRecursosView from '../modules/odmclient/views/OdmRecursosView.vue'

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
    meta: { requiresAuth: false },
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
        path: '/config/usuarios',
        name: 'ConfigUsuarios',
        component: ConfigUsuarios
      },
      // DATOS ABIERTOS (ODM)
      {
        path: '/odm',
        name: 'OdmRecursos',
        component: OdmRecursosView
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

export default router