import type { HistoryDataset, Source } from '../types/history';
import { resolveCoreId } from '../data/graphSelection';

const loaders = {
  'tang-duobao': () => import('../../../../data/history/tang-duobao.json'),
  'han-caoquan': () => import('../../../../data/history/han-caoquan.json'),
  'wei-yuanhuai': () => import('../../../../data/history/wei-yuanhuai.json'),
  'wei-jianyi': () => import('../../../../data/history/wei-jianyi.json'),
};
const cache = new Map<string, Promise<HistoryDataset>>();
export function loadHistory(id: string): Promise<HistoryDataset> {
  const canonical = resolveCoreId(id) || id;
  if (cache.has(canonical)) return cache.get(canonical)!;
  const promise = (async () => {
    try {
      const response = await fetch(`/api/steles/${encodeURIComponent(canonical)}/graph`);
      if (!response.ok) throw new Error('图谱接口不可用');
      const data = await response.json();
      if (data.steleId !== canonical) throw new Error('碑刻身份不匹配');
      return data as HistoryDataset;
    } catch (error) {
      const loader = loaders[canonical as keyof typeof loaders];
      if (!loader) throw error;
      const [data, sources] = await Promise.all([loader(), import('../../../../data/history/sources.json')]);
      return { ...data.default, sources: sources.default as Source[], offline: true } as HistoryDataset;
    }
  })();
  cache.set(canonical, promise);
  promise.catch(() => cache.delete(canonical));
  return promise;
}
export async function convertYear(query: string) {
  const response = await fetch('/api/calendar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query }) });
  if (!response.ok) throw new Error('纪年服务暂不可用');
  return response.json() as Promise<{supported: boolean; solar_year: number | null; ganzhi: string | null; zodiac?: string; message: string}>;
}
