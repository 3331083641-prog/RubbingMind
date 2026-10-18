import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// The terrain scene streams DEM tiles, which would otherwise evict the default
// 250-entry resource-timing buffer (used by the browser test diagnostics).
if (typeof performance !== 'undefined' && typeof performance.setResourceTimingBufferSize === 'function') {
  performance.setResourceTimingBufferSize(4000);
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
