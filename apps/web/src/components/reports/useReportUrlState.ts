/**
 * 报告页 / 工作台共用的 URL 查询参数状态（不依赖路由库，不改 App.tsx）。
 * 约定参数：steleId / runId / experimentId / batch（Green 决定），以及报告页内部筛选
 * view / panel / split / deg / method / sample / case。
 * 由于 App.tsx 目前不读 URL，刷新后页签与当前文物仍由 App 决定：本 hook 只在 steleId 与当前文物一致时才采信 runId，
 * 防止跨文物串结果。App 层读取 tab/steleId 的改动已写成需求交架构后端。
 */
import { useCallback, useEffect, useState } from 'react';

export const URL_KEYS = ['tab', 'steleId', 'runId', 'experimentId', 'batch', 'view', 'panel', 'split', 'deg', 'method', 'sample', 'case'] as const;
export type UrlKey = typeof URL_KEYS[number];
export type UrlState = Partial<Record<UrlKey, string>>;

export function readUrlState(): UrlState {
  if (typeof window === 'undefined') return {};
  const params = new URLSearchParams(window.location.search);
  const out: UrlState = {};
  URL_KEYS.forEach(k => { const v = params.get(k); if (v) out[k] = v; });
  return out;
}

/** 合并写入：值为 '' / undefined 的键被删除；其他未知参数（例如 steleQA）原样保留。 */
export function writeUrlState(patch: UrlState, mode: 'replace' | 'push' = 'replace') {
  if (typeof window === 'undefined') return;
  const url = new URL(window.location.href);
  (Object.keys(patch) as UrlKey[]).forEach(k => { const v = patch[k]; if (v) url.searchParams.set(k, v); else url.searchParams.delete(k); });
  const next = `${url.pathname}${url.search}${url.hash}`;
  if (next === `${window.location.pathname}${window.location.search}${window.location.hash}`) return;
  if (mode === 'push') window.history.pushState(null, '', next); else window.history.replaceState(null, '', next);
  window.dispatchEvent(new Event('rm-url-state'));
}

export function useUrlState(): [UrlState, (patch: UrlState, mode?: 'replace' | 'push') => void] {
  const [state, setState] = useState<UrlState>(readUrlState);
  useEffect(() => {
    const sync = () => setState(readUrlState());
    window.addEventListener('popstate', sync);
    window.addEventListener('rm-url-state', sync);
    return () => { window.removeEventListener('popstate', sync); window.removeEventListener('rm-url-state', sync); };
  }, []);
  const update = useCallback((patch: UrlState, mode: 'replace' | 'push' = 'replace') => writeUrlState(patch, mode), []);
  return [state, update];
}

/** 只有 URL 的 steleId 与当前文物一致时才返回 URL 中的 runId。 */
export function runIdForStele(state: UrlState, steleId: string): string {
  return state.steleId === steleId && state.runId ? state.runId : '';
}
