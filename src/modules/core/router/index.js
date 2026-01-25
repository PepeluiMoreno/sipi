// src/modules/core/router/index.js

import { createRouter, createWebHistory } from 'vue-router'
import DashboardLayout from '../layouts/DashboardLayout.vue'
import Login from '../../auth/views/Login.vue'
import ForgotPassword from '../../auth/views/ForgotPassword.vue'
import ResetPassword from '../../auth/views/ResetPassword.vue'
import Dashboard from '../views/Dashboard.vue'
import NotFound from '../views/NotFound.vue'

// Importar vistas de Agentes
import AdministracionesView from '../../agentes/views/AdministracionesView.vue'
import NotariasView from '../../agentes/views/NotariasView.vue'
import RegistrosPropiedadView from '../../agentes/views/RegistrosPropiedadView.vue'
import EntidadesReligiosasView from '../../agentes/views/EntidadesReligiosasView.vue'

// Importar vistas de Documentos
import Documentos from '../../documentos/views/Documentos.vue'

// Importar vistas de Configuración
import ConfigProcesos from '../../procesos/views/ConfigProcesos.vue'
import ConfigTipologias from '../../tipologias/views/ConfigTipologias.vue'
import ConfigUsuarios from '../../usuarios/views/ConfigUsuarios.vue'

// Importar vistas de Auth
import VerificarEmail from '../../usuarios/views/VerificarEmail.vue'

// Importar vistas de Inmueble
import InmuebleIndex from '../../inmuebles/views/InmuebleIndex.vue'

// DESCOMENTAR CUANDO ESTÉN IMPLEMENTADOS:
// import Transmisiones from '../../transmisiones/views/Transmisiones.vue'

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
    meta: { requiresAuth: false }, // TEMPORALMENTE DESHABILITADO
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
        path: '/inmueble-index',
        name: 'InmuebleIndex',
        component: InmuebleIndex
      },
      // DOCUMENTOS
      {
        path: '/documentos',
        name: 'Documentos',
        component: Documentos
      },
      // ACTUACIONES - DESHABILITADO TEMPORALMENTE
      /*
      {
        path: '/actuaciones',
        name: 'Actuaciones',
        component: { template: '<div><h1>Actuaciones - En construcción</h1></div>' }
      },
      */
      // TRANSMISIONES - DESHABILITADO TEMPORALMENTE
      /*
      {
        path: '/transmisiones',
        name: 'Transmisiones',
        component: Transmisiones
      },
      */
      // CONFIGURACIÓN
      {
        path: '/config/procesos',
        name: 'ConfigProcesos',
        component: ConfigProcesos
      },
      {
        path: '/config/tipologias',
        name: 'ConfigTipologias',
        component: ConfigTipologias
      },
      {
        path: '/config/usuarios',
        name: 'ConfigUsuarios',
        component: ConfigUsuarios
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

// GUARD DE AUTENTICACIÓN - DESHABILITADO TEMPORALMENTE
// Descomentar cuando se implemente el registro de usuarios
/*
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (!to.meta.requiresAuth && token && to.path !== '/') {
    next('/')
  } else {
    next()
  }
})
*/

export default router