// Shared, linkable page state (ARCHITECTURE_DECISIONS R1-6).
// Query parameter names are fixed by Green: steleId, runId, experimentId, batch
// (plus `tab` for the page). Absent parameters mean "current default behaviour".
export interface UrlState {
  tab?: string;
  steleId?: string;
  runId?: string;
  experimentId?: string;
  batch?: string;
}

export const URL_STATE_KEYS = ['tab', 'steleId', 'runId', 'experimentId', 'batch'] as const;
const KNOWN_TABS = new Set(['home', 'museum', 'workbench', 'graph', 'reports']);

export function readUrlState(search: string = typeof window === 'undefined' ? '' : window.location.search): UrlState {
  const params = new URLSearchParams(search);
  const state: UrlState = {};
  for (const key of URL_STATE_KEYS) {
    const value = params.get(key)?.trim();
    if (value) state[key] = value;
  }
  if (state.tab && !KNOWN_TABS.has(state.tab)) delete state.tab;
  return state;
}

export function buildUrlSearch(state: UrlState, currentSearch = ''): string {
  const params = new URLSearchParams(currentSearch);
  for (const key of URL_STATE_KEYS) {
    const value = state[key];
    if (value) params.set(key, value); else params.delete(key);
  }
  const text = params.toString();
  return text ? `?${text}` : '';
}

/** replaceState only: no new history entries, hash (legacy #/tab links) preserved. */
export function writeUrlState(state: UrlState): void {
  if (typeof window === 'undefined' || !window.history?.replaceState) return;
  const { pathname, search, hash } = window.location;
  const next = buildUrlSearch(state, search);
  if (next !== search) window.history.replaceState(window.history.state, '', `${pathname}${next}${hash}`);
}
