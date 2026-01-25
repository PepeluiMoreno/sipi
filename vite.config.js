import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ mode }) => {
  // Cargar .env desde sipi-core (directorio padre)
  const env = loadEnv(mode, path.resolve(__dirname, '../sipi-core'), '')

  return {
    plugins: [vue()],
    server: {
      host: '0.0.0.0',
      port: 5173
    },
    // Exponer variables VITE_* al frontend
    define: {
      'import.meta.env.VITE_API_URL': JSON.stringify(env.VITE_API_URL),
      'import.meta.env.VITE_GRAPHQL_URL': JSON.stringify(env.VITE_GRAPHQL_URL),
    }
  }
})