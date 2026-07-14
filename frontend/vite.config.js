import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
// Backend Flask server started with `flask run` (see backend/app.py).
const BACKEND_URL = 'http://127.0.0.1:5000'

export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    proxy: {
      // Forwards relative /api calls (see src/services/api.js) to Flask.
      // Without this, requests hit the Vite dev server itself and fail.
      '/api': {
        target: BACKEND_URL,
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('proxyReq', (_proxyReq, req) => {
            console.log(`[api proxy] ${req.method} ${req.url} -> ${BACKEND_URL}${req.url}`)
          })
          proxy.on('error', (err, req) => {
            console.error(`[api proxy] FAILED ${req.method} ${req.url}: ${err.message} (is the Flask backend running on ${BACKEND_URL}?)`)
          })
        },
      },
    },
  },
})
