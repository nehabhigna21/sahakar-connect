import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // WSL2's inotify doesn't see changes on /mnt/c (Windows-mounted) paths,
  // so HMR silently stops working without polling.
  server: {
    watch: {
      usePolling: true,
      interval: 300,
    },
  },
})
