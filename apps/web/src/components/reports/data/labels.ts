/** 方法、退化、指标的中文名与固定顺序（P2-6）。未登记的 ID 原样显示。 */
export const METHOD_ORDER = ['degraded', 'gaussian_lowpass', 'butterworth_lowpass', 'notch', 'fast_nlm', 'morphology', 'nlm_clahe', 'joint', 'adaptive_joint', 'adaptive_v20', 'adaptive_v21'];
export const METHOD_LABELS: Record<string, string> = {
  degraded: '退化输入（基线）',
  gaussian_lowpass: '高斯低通',
  butterworth_lowpass: '巴特沃斯低通',
  notch: '陷波',
  fast_nlm: '快速 NLM',
  morphology: '形态学',
  nlm_clahe: 'NLM+CLAHE',
  joint: '固定联合',
  adaptive_joint: '自适应联合 v2.0',
  adaptive_v20: '自适应 v2.0',
  adaptive_v21: '自适应 v2.1',
};
export const DEGRADATION_ORDER = ['gaussian', 'salt_pepper', 'periodic', 'blur', 'occlusion'];
export const DEGRADATION_LABELS: Record<string, string> = { all: '全部退化', gaussian: '高斯噪声', salt_pepper: '椒盐噪声', periodic: '周期噪声', blur: '模糊', occlusion: '遮挡' };
export const SPLIT_LABELS: Record<string, string> = { development: '开发组 development', test: '测试组 test', none: '未划分' };

export const methodLabel = (m: string) => METHOD_LABELS[m] || m;
export const degradationLabel = (d: string) => DEGRADATION_LABELS[d] || d;
export const sortMethods = (ms: string[]) => [...ms].sort((a, b) => {
  const ia = METHOD_ORDER.indexOf(a), ib = METHOD_ORDER.indexOf(b);
  return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib) || a.localeCompare(b);
});
export const sortDegradations = (ds: string[]) => [...ds].sort((a, b) => {
  const ia = DEGRADATION_ORDER.indexOf(a), ib = DEGRADATION_ORDER.indexOf(b);
  return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
});

export type MetricKey = 'psnr' | 'ssim' | 'edgeF1' | 'thinStrokeMae' | 'processingMs';
export interface MetricDef { key: MetricKey; title: string; unit: string; digits: number; direction: 'higher' | 'lower'; delta: boolean; note?: string }
/** Δ 指标：相对同一 case 的退化输入。thinStrokeMae 按 SPEC §0.3 取 in − out，越大越好。耗时不做 Δ，越低越好。 */
export const METRICS: MetricDef[] = [
  { key: 'psnr', title: 'ΔPSNR', unit: 'dB', digits: 2, direction: 'higher', delta: true },
  { key: 'ssim', title: 'ΔSSIM', unit: '', digits: 3, direction: 'higher', delta: true },
  { key: 'edgeF1', title: 'Δ边缘 F1', unit: '', digits: 3, direction: 'higher', delta: true },
  { key: 'thinStrokeMae', title: '细笔画误差改善（输入−输出）', unit: '灰度', digits: 2, direction: 'higher', delta: true },
  { key: 'processingMs', title: '单次耗时', unit: 'ms', digits: 1, direction: 'lower', delta: false, note: '绝对值，不是 Δ' },
];
export const directionText = (d: 'higher' | 'lower') => d === 'higher' ? '↑ 越高越好' : '↓ 越低越好';

export const APPLIED_LABELS: Record<string, string> = {
  baseline: '输入基线',
  processed: '实际处理',
  passthrough: '原图返回（未处理）',
  passthrough_not_applicable: '原图返回（判定不适用）',
  processed_not_applicable_label: '标为不适用但有改动（E-05）',
  failed: '失败',
  undetermined: '无法判定',
};

/** SPEC §1(b) E-05：rounding / other 细分文案（兼容 DER 长值 not-applicable-but-modified-*）。 */
export function appliedStatusLabel(status: string, detail?: string | null): string {
  if (status === 'processed_not_applicable_label') {
    const d = detail || '';
    if (d === 'rounding' || d === 'not-applicable-but-modified-rounding' || d.includes('rounding')) {
      return '不适用分支的 1 级截断（E-05），非算法处理';
    }
    if (d === 'other' || d === 'not-applicable-but-modified-other' || d.includes('other')) {
      return '标为不适用但有改动，原因未定，待人工复核';
    }
    return APPLIED_LABELS.processed_not_applicable_label;
  }
  return APPLIED_LABELS[status] || status;
}
