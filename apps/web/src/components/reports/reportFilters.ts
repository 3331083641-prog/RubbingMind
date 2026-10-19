/**
 * 报告页内部筛选的 URL 参数（view / panel / split / deg / method / sample / case / cmp）。
 * 共享参数 tab / steleId / runId / experimentId / batch 不在这里：它们由 App 通过 props 下发，
 * 由 state/urlState.ts 写回 URL（agent/arch-backend R1-6）。两边都只改自己的键，其余参数原样保留。
 */
import { useCallback, useEffect, useState } from 'react';
import { URL_STATE_KEYS } from '../../state/urlState';

export const FILTER_KEYS = ['view', 'panel', 'split', 'deg', 'method', 'sample', 'case', 'cmp'] as const;
export type FilterKey = typeof FILTER_KEYS[number];
export type ReportFilters = Partial<Record<FilterKey, string>>;
const EVENT = 'rm-report-filters';

export function readFilters(search: string = typeof window === 'undefined' ? '' : window.location.search): ReportFilters {
  const params = new URLSearchParams(search); const out: ReportFilters = {};
  FILTER_KEYS.forEach(k => { const v = params.get(k)?.trim(); if (v) out[k] = v; });
  return out;
}

/** replaceState 合并写入；值为空的键删除。共享键（URL_STATE_KEYS）在类型上不可写，避免与 App 重复写。 */
export function writeFilters(patch: ReportFilters) {
  if (typeof window === 'undefined' || !window.history?.replaceState) return;
  const url = new URL(window.location.href);
  (Object.keys(patch) as FilterKey[]).forEach(k => {
    if ((URL_STATE_KEYS as readonly string[]).includes(k)) return;
    const v = patch[k]; if (v) url.searchParams.set(k, v); else url.searchParams.delete(k);
  });
  const next = `${url.pathname}${url.search}${url.hash}`;
  if (next === `${window.location.pathname}${window.location.search}${window.location.hash}`) return;
  window.history.replaceState(window.history.state, '', next);
  window.dispatchEvent(new Event(EVENT));
}

export function useReportFilters(): [ReportFilters, (patch: ReportFilters) => void] {
  const [state, setState] = useState<ReportFilters>(() => readFilters());
  useEffect(() => {
    const sync = () => setState(readFilters());
    window.addEventListener('popstate', sync); window.addEventListener(EVENT, sync);
    return () => { window.removeEventListener('popstate', sync); window.removeEventListener(EVENT, sync); };
  }, []);
  const update = useCallback((patch: ReportFilters) => writeFilters(patch), []);
  return [state, update];
}
