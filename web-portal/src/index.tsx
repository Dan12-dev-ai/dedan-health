/**
 * DEDAN-Health portal entry point.
 *
 * The application is mounted once; all providers (theme, session state) live
 * inside <App /> so the entry point stays a 3-line bootstrap. PWA offline
 * caching of *data* is handled by offlineStorage (IndexedDB); a Workbox
 * service-worker is intentionally NOT force-registered here because this
 * codebase ships no built SW asset (master spec §42: do not cache PHI
 * unnecessarily, and degrade gracefully when offline).
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
