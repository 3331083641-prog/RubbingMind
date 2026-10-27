// Shared, linkable page state (ARCHITECTURE_DECISIONS R1-6, R2-8).
// Canonical query parameters: tab, steleId, runId, experimentId. `batch` (results directory name) is
// accepted only as a readable input alias: it is resolved to experimentId and removed from the URL.
// Rules (Green 2026-10-19, red-team gate on 7c0e258):
//  * opening a URL without parameters never rewrites it; the URL is written only after a user change;
//  * invalid tab / runId values are removed from the URL with a visible notice, never replaced silently;
//  * experimentId wins over batch; an unknown experimentId stays an explicit empty state (no fallback).
export interface UrlState {
  tab?: string;
  steleId?: string;
  runId?: string;
  experimentId?: string;
  /** input-only alias; never written back */
  batch?: string;
}

export interface UrlIssue { key: keyof UrlState; value: string; message: string }

export const URL_STATE_KEYS = ['tab', 'steleId', 'runId', 'experimentId', 'batch'] as const;
export const CANONICAL_KEYS = ['tab', 'steleId', 'runId', 'experimentId'] as const;
export const KNOWN_TABS = new Set(['home', 'museum', 'workbench', 'graph', 'reports']);
/** Run ids are UTC `YYYYMMDDTHHMMSS_<8 hex>` (museum_processing.read_run). */
export const RUN_ID_PATTERN = /^[0-9]{8}T[0-9]{6}_[0-9a-f]{8}$/;

function currentSearch(): string { return typeof window === 'undefined' ? '' : window.location.search; }

/** Raw values present in the URL (trimmed, empty dropped). */
export function readRawUrlState(search: string = currentSearch()): UrlState {
  const params = new URLSearchParams(search);
  const state: UrlState = {};
  for (const key of URL_STATE_KEYS) {
    const value = params.get(key)?.trim();
    if (value) state[key] = value;
  }
  return state;
}

/** Validated state plus the issues that must be shown and cleared from the URL. */
export function parseUrlState(search: string = currentSearch()): { state: UrlState; issues: UrlIssue[]; raw: UrlState } {
  const raw = readRawUrlState(search);
  const state: UrlState = { ...raw };
  const issues: UrlIssue[] = [];
  if (state.tab && !KNOWN_TABS.has(state.tab)) {
    issues.push({ key: 'tab', value: state.tab, message: `链接中的页面参数 tab=${state.tab} 无效，已从地址中移除` });
    delete state.tab;
  }
  if (state.runId && !RUN_ID_PATTERN.test(state.runId)) {
    issues.push({ key: 'runId', value: state.runId, message: `链接中的运行编号 ${state.runId} 格式无效，已从地址中移除，未替换为其他运行` });
    delete state.runId;
  }
  return { state, issues, raw };
}

/** Back-compat helper used by older callers: validated state only. */
export function readUrlState(search: string = currentSearch()): UrlState {
  return parseUrlState(search).state;
}

export interface ExperimentRef { id: string; batch?: string | null; directory?: string; defaultForReport?: boolean }
export type ExperimentResolution =
  | { status: 'none'; experimentId: null }
  | { status: 'ok'; experimentId: string; via: 'experimentId' | 'batch'; notice?: string }
  | { status: 'unknown'; experimentId: string | null; requested: { experimentId?: string; batch?: string }; notice: string };

const batchOf = (item: ExperimentRef) => item.batch ?? item.directory ?? null;

/** experimentId is authoritative; batch is only an alias resolved through the backend mapping. */
export function resolveExperiment(list: ExperimentRef[], requested: { experimentId?: string; batch?: string }): ExperimentResolution {
  const { experimentId, batch } = requested;
  if (!experimentId && !batch) return { status: 'none', experimentId: null };
  if (experimentId) {
    const hit = list.find(item => item.id === experimentId);
    if (!hit) return { status: 'unknown', experimentId, requested, notice: `没有实验批次 ${experimentId}；不会回落到其他批次` };
    const conflict = batch && batchOf(hit) !== batch;
    return { status: 'ok', experimentId, via: 'experimentId', notice: conflict ? `batch=${batch} 与 experimentId=${experimentId} 不一致，已以 experimentId 为准` : undefined };
  }
  const byBatch = list.find(item => batchOf(item) === batch);
  if (!byBatch) return { status: 'unknown', experimentId: null, requested, notice: `没有目录为 ${batch} 的实验批次；不会回落到其他批次` };
  return { status: 'ok', experimentId: byBatch.id, via: 'batch' };
}

/** The one batch the backend marks defaultForReport (ExperimentBatchMeta.defaultForReport), else null. */
export function defaultExperimentId(list: ExperimentRef[]): string | null {
  return list.find(item => item.defaultForReport === true)?.id ?? null;
}

/** Only canonical keys are written; `batch` is always removed. */
export function buildUrlSearch(state: UrlState, currentSearchText = ''): string {
  const params = new URLSearchParams(currentSearchText);
  params.delete('batch');
  for (const key of CANONICAL_KEYS) {
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
