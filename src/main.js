// src/main.js
console.log('>>> [DEBUG] Main.js starting')
window.onerror = function (msg, url, line) {
    console.error('>>> [DEBUG] Global Error:', msg, url, line)
}

import './style.css'     // LUEGO tus estilos personalizados

import { createApp } from 'vue'
import { DefaultApolloClient } from '@vue/apollo-composable'
import { ApolloClient, createHttpLink, InMemoryCache, ApolloLink } from '@apollo/client/core'
import { setContext } from '@apollo/client/link/context'

// IMPORTAR EL COMPONENTE PRINCIPAL
import App from './App.vue'
import router from './modules/core/router'
// Importar Pinia
import { createPinia } from 'pinia'

console.log('>>> [DEBUG] Imports done')

// Crear instancia de Pinia
const pinia = createPinia()

// Configurar Apollo Client y Vue Apollo
try {
    const httpLink = createHttpLink({
        uri: import.meta.env.VITE_GRAPHQL_URL || 'http://localhost:8040/graphql',
    })

    const authLink = setContext((_, { headers }) => {
        const token = localStorage.getItem('token')
        return {
            headers: {
                ...headers,
                authorization: token ? `Bearer ${token}` : "",
            }
        }
    })

    // Link para limpiar filtros vacíos automáticamente (solución global)
    const cleanFiltersLink = new ApolloLink((operation, forward) => {
        // Limpiar variables del query
        if (operation.variables) {
            const cleanedVariables = { ...operation.variables }

            // Si existe 'filter' y está vacío, eliminarlo completamente
            if (cleanedVariables.filter &&
                typeof cleanedVariables.filter === 'object' &&
                Object.keys(cleanedVariables.filter).length === 0) {
                delete cleanedVariables.filter
            }

            operation.variables = cleanedVariables
        }

        return forward(operation)
    })

    const apolloClient = new ApolloClient({
        link: cleanFiltersLink.concat(authLink).concat(httpLink),
        cache: new InMemoryCache(),
        defaultOptions: {
            watchQuery: {
                fetchPolicy: 'cache-and-network',
            },
        }
    })

    console.log('>>> [DEBUG] Apollo setup done')

    // Crear la aplicación
    const app = createApp(App)

    // Proveer Apollo client para Composition API
    app.provide(DefaultApolloClient, apolloClient)

    // Usar plugins
    console.log('>>> [DEBUG] Using router')
    app.use(router)
    console.log('>>> [DEBUG] Using pinia')
    app.use(pinia)

    console.log('>>> [DEBUG] Mounting app...')
    // Montar la aplicación
    app.mount('#app')
    console.log('>>> [DEBUG] App mounted!')

} catch (e) {
    console.error('>>> [DEBUG] Error in setup:', e)
}

console.log('🚀 Desarrollo: Mock data cargado')
console.log('📍 Router cargado:', router)
