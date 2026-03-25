import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: ['money-maker.shop'],
    hmr: {
      protocol: 'wss',
      host: 'money-maker.shop',
      clientPort: 443,
      path: '/__vite_hmr',
    },
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})
