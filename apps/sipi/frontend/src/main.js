// src/main.js

import './style.css'

import { createApp } from 'vue'
import { createApolloProvider } from '@vue/apollo-option'
import { DefaultApolloClient } from '@vue/apollo-composable'
import { ApolloClient, createHttpLink, InMemoryCache } from '@apollo/client/core'
import { setContext } from '@apollo/client/link/context'

import App from './App.vue'
import router from './router'  // ✅ CORREGIDO
import { createPinia } from 'pinia'
import { registerUi } from './modules/core/components/ui'
import { getToken } from './modules/auth/token'

const pinia = createPinia()

const httpLink = createHttpLink({
  // Mismo origen por defecto (/graphql lo reenvía el dev server a la API).
  // Override con VITE_API_URL si se necesita un endpoint absoluto.
  uri: import.meta.env.VITE_API_URL || '/graphql/',
})

const authLink = setContext((_, { headers }) => {
  const token = getToken()
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

const app = createApp(App)

app.use(router)
app.use(pinia)
app.use(apolloProvider)
// `@vue/apollo-composable` (useQuery/useMutation) usa otra clave de inyección que
// `@vue/apollo-option`; hay que proveer el cliente también aquí o falla con
// "Apollo client with id default not found".
app.provide(DefaultApolloClient, apolloClient)
registerUi(app)   // widgets base del sistema de diseño (UiButton, UiPanel, PageShell…)

app.mount('#app')