import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  resolve: {
    dedupe: ['react', 'react-dom'],
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    allowedHosts: ['money-maker.shop'],
    hmr: {
      path: '/__vite_hmr',
      ...(process.env.VITE_HMR_HOST ? {
        protocol: 'wss',
        host: process.env.VITE_HMR_HOST,
        clientPort: 443,
      } : {}),
    },
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})
