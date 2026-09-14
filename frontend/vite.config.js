import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev-server proxy: the browser calls same-origin "/api/...", Vite forwards
// it to FastAPI. This avoids needing CORS changes on the backend (the
// backend's contract stays untouched, per the Stage 4 requirement).
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
