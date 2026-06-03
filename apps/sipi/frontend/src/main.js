// src/main.js

import './style.css'

import { createApp } from 'vue'
import { createApolloProvider } from '@vue/apollo-option'
import { ApolloClient, createHttpLink, InMemoryCache } from '@apollo/client/core'
import { setContext } from '@apollo/client/link/context'

import App from './App.vue'
import router from './router'  // ✅ CORREGIDO
import { createPinia } from 'pinia'

const pinia = createPinia()

const httpLink = createHttpLink({
  uri: 'http://localhost:4000/graphql',
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

const app = createApp(App)

app.use(router)
app.use(pinia)
app.use(apolloProvider)

app.mount('#app')

console.log('🚀 Desarrollo: Mock data cargado')
console.log('📍 Router cargado:', router)
console.log('📍 Apollo Client cargado:', apolloClient)