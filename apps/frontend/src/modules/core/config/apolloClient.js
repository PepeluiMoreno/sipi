// src/modules/core/config/apolloClient.js

// ✅ DESCOMENTAR TODO ESTO CUANDO EL BACKEND ESTÉ LISTO:

// import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client/core'
// import { setContext } from '@apollo/client/link/context'

// const httpLink = createHttpLink({
//   uri: import.meta.env.VITE_GRAPHQL_URL || 'http://localhost:4000/graphql',
// })

// const authLink = setContext((_, { headers }) => {
//   const token = localStorage.getItem('auth_token')
//   return {
//     headers: {
//       ...headers,
//       authorization: token ? `Bearer ${token}` : '',
//     }
//   }
// })

// export const apolloClient = new ApolloClient({
//   link: authLink.concat(httpLink),
//   cache: new InMemoryCache(),
//   defaultOptions: {
//     query: {
//       fetchPolicy: 'network-only',
//     },
//   },
// })

// ✅ Y EN TU main.js, DESCOMENTAR ESTO:
// import { createApp } from 'vue'
// import { apolloClient } from './modules/core/config/apolloClient'
// import { createApolloProvider } from '@vue/apollo-composable'

// const app = createApp(App)
// app.use(createApolloProvider({ defaultClient: apolloClient }))
// app.mount('#app')