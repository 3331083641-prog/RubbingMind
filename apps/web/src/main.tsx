import React from 'react';
import ReactDOM from 'react-dom/client';
import 'katex/dist/katex.min.css';
import App from './App';
import { ExperienceProvider } from './context/ExperienceContext';
import './index.css';
import './styles/theme.css';

// The terrain scene streams DEM tiles, which would otherwise evict the default
// 250-entry resource-timing buffer (used by the browser test diagnostics).
if (typeof performance !== 'undefined' && typeof performance.setResourceTimingBufferSize === 'function') {
  performance.setResourceTimingBufferSize(4000);
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ExperienceProvider>
      <App />
    </ExperienceProvider>
  </React.StrictMode>
);
