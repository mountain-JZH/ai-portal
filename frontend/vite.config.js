import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig({
  // Do not let Vite's public directory bypass the authenticated standalone tool.
  server: { proxy: { '/tools/qstart': { target: 'http://127.0.0.1:8000' } } },
  preview: { proxy: { '/tools/qstart': { target: 'http://127.0.0.1:8000' } } },
  plugins: [
    vue(),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
})
