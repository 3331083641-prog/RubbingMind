import CORE_DATA from './coreSamples.json';
import { SteleItem } from '../types/stele';
export const CORE_SAMPLES = CORE_DATA as unknown as SteleItem[];
export function resolveSelected(steles: SteleItem[], id: string): SteleItem {
  const record = [...steles, ...CORE_SAMPLES].find(s => s.id === id);
  if (!record) throw new Error(`未找到文物 ${id}，不能切换到其他样本`);
  return record;
}
