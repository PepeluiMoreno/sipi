import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    // Acceso tras Traefik como sipi.optiplex-790 (dev)
    allowedHosts: ['sipi.optiplex-790', '.optiplex-790', 'localhost'],
    // HMR a través del proxy TLS de Traefik (websecure → 443)
    hmr: { clientPort: 443, protocol: 'wss' },
    // GraphQL en el mismo origen: el dev server lo reenvía a la API (red interna).
    // Así el navegador llama a /graphql (sin CORS) y funciona tras Traefik.
    proxy: {
      '/graphql': {
        target: process.env.VITE_API_TARGET || 'http://api:8040',
        changeOrigin: true,
        ws: true,
      },
    },
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  }
})