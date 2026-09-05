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
    // Allows the Cloudflare Tunnel's *.trycloudflare.com host through -
    // Vite blocks unrecognized Host headers by default (DNS-rebinding
    // protection). Fine for a temporary demo tunnel.
    allowedHosts: true,
  },
})
