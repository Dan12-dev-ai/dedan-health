/**
 * DEDAN-Health — Vite configuration.
 *
 * Vite replaces react-scripts so we avoid CRA5's transitive ajv-keywords/ajv
 * resolution conflict (master spec: build must be deterministic). The app
 * entry is the root `index.html` mounting `#root`; React + JSX come from the
 * `@vitejs/plugin-react` SWC/Babel transformation (respects tsconfig.jsx).
 */
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    strictPort: true,
    host: true, // bind 0.0.0.0 so it's reachable on the network
    open: false,
  },
  preview: {
    port: 3000,
    host: true,
  },
  build: {
    target: 'es2020',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          // MUI is heavy — give it its own chunk for stable caching.
          mui: ['@mui/material', '@mui/icons-material', '@emotion/react', '@emotion/styled'],
          router: ['react-router-dom'],
        },
      },
    },
  },
});
