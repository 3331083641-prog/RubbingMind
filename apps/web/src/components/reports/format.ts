/** 统一的格式化：时间一律 Asia/Shanghai（UTC+8），空值不拼单位。 */
const TZ = 'Asia/Shanghai';

export function parseIsoTime(value: unknown): number | null {
  if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}T/.test(value)) return null;
  const t = Date.parse(value);
  return Number.isFinite(t) ? t : null;
}

export function formatTime(value: unknown): string {
  const t = parseIsoTime(value);
  if (t == null) return typeof value === 'string' && value ? `${value}（无可解析时间）` : '未记录';
  const parts = new Intl.DateTimeFormat('zh-CN', { timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }).formatToParts(new Date(t));
  const get = (type: string) => parts.find(p => p.type === type)?.value || '';
  return `${get('year')}-${get('month')}-${get('day')} ${get('hour')}:${get('minute')}:${get('second')}（UTC+8）`;
}

export function nowShanghaiIso(): string {
  const t = new Date(Date.now() + 8 * 3600 * 1000).toISOString().replace('Z', '');
  return `${t.slice(0, 19)}+08:00`;
}

/** 数值 + 单位；null/非有限值返回“未评测”且不带单位。 */
export function num(value: number | null | undefined, digits = 3, unit = '', empty = '未评测'): string {
  if (value == null || !Number.isFinite(value)) return empty;
  return `${value.toFixed(digits)}${unit ? ` ${unit}` : ''}`;
}

/** 带符号数值，用于 Δ。 */
export function signed(value: number | null | undefined, digits = 3, unit = '', empty = '未评测'): string {
  if (value == null || !Number.isFinite(value)) return empty;
  const s = value > 0 ? '+' : value < 0 ? '−' : '±';
  return `${s}${Math.abs(value).toFixed(digits)}${unit ? ` ${unit}` : ''}`;
}

export function percent(ratio: number | null | undefined): string {
  if (ratio == null || !Number.isFinite(ratio)) return '无法判定';
  if (ratio > 0 && ratio < 0.0001) return '<0.01%';
  return `${(ratio * 100).toFixed(2)}%`;
}

export function shortSha(sha: string | null | undefined): string {
  return sha ? `${sha.slice(0, 12)}…` : '未记录';
}
