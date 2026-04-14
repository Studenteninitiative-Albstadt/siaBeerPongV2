import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    allowedHosts: ['butzke.it'],
    host: true,
    port: 5173,
    proxy: {
      '/tournaments': { target: 'http://backend:8000', changeOrigin: true },
      '/auth':        { target: 'http://backend:8000', changeOrigin: true },
      '/health':      { target: 'http://backend:8000', changeOrigin: true },
      '/ws': {
        target: 'ws://backend:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
