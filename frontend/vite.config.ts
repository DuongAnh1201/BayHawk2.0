import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => {
  const rootEnv = loadEnv(mode, '..', '')

  return {
    plugins: [react(), tailwindcss()],
    envDir: '..',
    define: {
      'import.meta.env.VITE_OPENWEATHERMAP_API_KEY': JSON.stringify(rootEnv.OPENWEATHERMAP_API_KEY ?? ''),
      'import.meta.env.VITE_NASA_FIRMS_MAP_KEY': JSON.stringify(rootEnv.NASA_FIRMS_MAP_KEY ?? ''),
    },
  }
})
