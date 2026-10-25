/**
 * 同批复测 v2.1（原“v2.0 与 v2.1 留出对比”，接回报告页）。评测科学家 2026-10-19 裁定：
 * - 页面主标题与标签写“同批复测 v2.1（非留出）”；tooltip、图例、导出文件名、PDF 图题只写“同批复测 v2.1”。
 * - 不能当默认批次；本批没有图像、全部“无法判定”：不显示有效处理率、原图返回率，也不显示 dev/test 划分。
 * - 只写“同批复测下的差异”，等级 ≤ 有限支持。
 * 实验 ID 与目录名是历史标识，只在等宽“路径”里原样出现。
 */
import React, { useMemo, useState } from 'react';
import type { GlobalModel } from './reports/data/globalModel';
import { baselineMap, BatchInfo, RETEST_SHORT, RETEST_TITLE, ReportApi, rowDelta } from './reports/data/reportData';
import { DEGRADATION_LABELS, methodLabel } from './reports/data/labels';
import { GradeBadge } from './reports/GradeBadge';
import { signed } from './reports/format';

const METHODS = ['degraded', 'gaussian_lowpass', 'butterworth_lowpass', 'notch', 'fast_nlm', 'adaptive_v20', 'adaptive_v21'];
const DEGS = ['all', 'gaussian', 'salt_pepper', 'periodic', 'blur', 'occlusion'];
const COPY_ONLY = new Set(['skip_notch', 'identity', 'preserve_missing', 'fallback_identity']);
const avg = (xs: number[]) => xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null;
const fmt = (n: number | null | undefined, d = 3) => n == null ? '未评测' : n.toFixed(d);

export const HeldoutComparison: React.FC<{ model: GlobalModel }> = ({ model }) => {
  const [deg, setDeg] = useState('all');
  const map = useMemo(() => baselineMap(model.rowsAll), [model.rowsAll]);
  const table = useMemo(() => METHODS.filter(m => model.rowsAll.some(r => r.method === m)).map(m => {
    const own = model.rowsAll.filter(r => r.method === m && (deg === 'all' || r.degradation === deg));
    const deltas = own.map(r => rowDelta(r, 'psnr', map)).filter((d): d is number => d != null);
    return { method: m, n: own.length, psnr: avg(own.map(r => r.psnr).filter((v): v is number => v != null)), ssim: avg(own.map(r => r.ssim).filter((v): v is number => v != null)), edge: avg(own.map(r => r.edgeF1).filter((v): v is number => v != null)), thin: avg(own.map(r => r.thinStrokeMae).filter((v): v is number => v != null)),
      delta: m === 'degraded' ? null : avg(deltas), negative: m === 'degraded' ? null : deltas.filter(d => d < 0).length,
      zeroIndicator: m === 'degraded' ? null : own.filter(r => r.psnrDeltaFromInput === 0).length,
      copyOnly: m === 'degraded' ? null : own.filter(r => Array.isArray(r.diagnosticsOperators) && r.diagnosticsOperators.length > 0 && r.diagnosticsOperators.every(o => COPY_ONLY.has(o))).length };
  }), [model.rowsAll, deg, map]);
  const v20 = table.find(t => t.method === 'adaptive_v20'), v21 = table.find(t => t.method === 'adaptive_v21');
  return <section aria-label={RETEST_SHORT} className="rounded-xl border border-gold/20 bg-[#0f1418] p-4 space-y-3" data-testid="retest-comparison">
    <header className="flex flex-wrap items-center justify-between gap-2">
      <h3 className="font-serif text-gold text-base">{RETEST_TITLE} · v2.0 / v2.1 同批复测下的差异</h3>
      <GradeBadge grade="有限支持" reasons={['样本参与过 v2.1 的误差分析（同批复测）', '本批没有图像，无法判定是否改动']} />
    </header>
    <p className="text-[11px] text-cinnabar-light">同一批文物复测，不是独立验证：14 件文物与 v2-text 相同，v2.1 的改动针对 v2-text 的误差分析。只能写“同批复测下的差异”，不能写“泛化到新文物”。</p>
    <div className="flex flex-wrap gap-1 text-[11px]">{DEGS.map(d => <button key={d} type="button" aria-pressed={deg === d} onClick={() => setDeg(d)} className={`px-1.5 py-0.5 rounded border ${deg === d ? 'bg-gold text-slate-950 border-gold' : 'border-slate-700 text-slate-400'}`}>{d === 'all' ? '全部退化' : DEGRADATION_LABELS[d] || d}</button>)}</div>
    <p className="text-sm">ΔPSNR 负提升（全部行，相对同 case 退化输入）：v2.0 <b className="text-cinnabar-light">{v20?.negative ?? '—'}/{v20?.n ?? '—'}</b>，v2.1 <b className="text-cinnabar-light">{v21?.negative ?? '—'}/{v21?.n ?? '—'}</b>。</p>
    <div className="overflow-x-auto"><table className="w-full text-[11px] text-left" data-testid="retest-table">
      <thead className="text-slate-400"><tr>{['方法', 'n', 'PSNR', 'SSIM', '边缘 F1', '细笔画误差', 'ΔPSNR（全部）', '负提升', '指示量：ΔPSNR=0', '指示量：仅复制算子'].map(h => <th key={h} className="py-1 pr-2 font-normal">{h}</th>)}</tr></thead>
      <tbody>{table.map(t => <tr key={t.method} className="border-t border-slate-800"><td className="pr-2">{methodLabel(t.method)}</td><td className="pr-2">{t.n}</td><td className="pr-2">{fmt(t.psnr, 2)}</td><td className="pr-2">{fmt(t.ssim)}</td><td className="pr-2">{fmt(t.edge)}</td><td className="pr-2">{fmt(t.thin, 2)}</td>
        <td className={`pr-2 ${t.delta != null && t.delta < 0 ? 'text-cinnabar-light' : ''}`}>{t.method === 'degraded' ? '输入基线' : signed(t.delta, 3, 'dB')}</td><td className="pr-2">{t.negative == null ? '—' : t.n > 0 && t.zeroIndicator === t.n ? '不适用（ΔPSNR 全为 0，未经像素验证）' : `${t.negative}/${t.n}`}</td><td className="pr-2">{t.zeroIndicator ?? '—'}</td><td>{t.copyOnly ?? '—'}</td></tr>)}</tbody></table></div>
    <p className="text-[11px] text-slate-400">本批全部行“无法判定”是否改动（没有图像，isPassthrough = null），不显示有效处理率或原图返回率。两列指示量均<b>未经像素验证</b>，彼此并不一致，不能当判据。主数字为“全部”口径的行均值，不分 dev/test。</p>
    <p className="flex flex-wrap gap-3 text-[11px]">{['results.json', 'results.csv', 'summary.csv'].map(k => <a key={k} className="text-gold underline" href={ReportApi.exportUrl(model.batch.id, k)} download={`${RETEST_SHORT}-${k}`}>导出 {k}</a>)}<span className="text-slate-500">数据来源路径：<code>experiments/results/{model.batch.registry.directory}</code></span></p>
  </section>;
};

/** 非复测批次页上的入口卡片：确保同批复测在页面上可见，但不作为默认批次。 */
export const RetestTeaser: React.FC<{ batches: BatchInfo[]; onSelect?: (b: BatchInfo) => void }> = ({ batches, onSelect }) => {
  const b = batches.find(x => x.kind === 'retest');
  if (!b) return null;
  return <section aria-label={`${RETEST_SHORT}入口`} className="rounded-xl border border-slate-700 bg-[#0c1013] p-3 text-[11px] text-slate-300 flex flex-wrap items-center justify-between gap-2" data-testid="retest-teaser">
    <p><b className="text-gold">{RETEST_TITLE}</b>：v2.0 与 v2.1 在同一批 14 件文物上的复测（{b.registry.rowCount ?? '—'} 行，只有数值、没有图像）。不是独立验证，不作默认批次。</p>
    {onSelect && <button type="button" className="px-2 py-1 rounded border border-gold/50 text-gold" onClick={() => onSelect(b)}>查看{RETEST_SHORT}</button>}
  </section>;
};
