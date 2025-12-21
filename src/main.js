// src/main.js
console.log('>>> [DEBUG] Main.js starting')
window.onerror = function (msg, url, line) {
    console.error('>>> [DEBUG] Global Error:', msg, url, line)
}

import './style.css'     // LUEGO tus estilos personalizados

import { createApp } from 'vue'
import { createApolloProvider } from '@vue/apollo-option'
import { ApolloClient, createHttpLink, InMemoryCache } from '@apollo/client/core'
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
        uri: 'http://localhost:4000/graphql', // Tu endpoint GraphQL
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

    const apolloClient = new ApolloClient({
        link: authLink.concat(httpLink),
        cache: new InMemoryCache(),
        defaultOptions: {
            watchQuery: {
                fetchPolicy: 'cache-and-network',
            },
        }
    })

    const apolloProvider = createApolloProvider({
        defaultClient: apolloClient,
    })

    console.log('>>> [DEBUG] Apollo setup done')

    // Crear la aplicación
    const app = createApp(App)

    // Usar plugins
    console.log('>>> [DEBUG] Using router')
    app.use(router)
    console.log('>>> [DEBUG] Using pinia')
    app.use(pinia)
    console.log('>>> [DEBUG] Using apollo')
    app.use(apolloProvider)

    console.log('>>> [DEBUG] Mounting app...')
    // Montar la aplicación
    app.mount('#app')
    console.log('>>> [DEBUG] App mounted!')

} catch (e) {
    console.error('>>> [DEBUG] Error in setup:', e)
}

console.log('🚀 Desarrollo: Mock data cargado')
console.log('📍 Router cargado:', router)
