/**
 * 逐条实验记录（原“算法实验与消融分析”，接回报告页并吸收其功能）。
 * - 不再自己拉批次：由报告页的 experimentId 驱动（修 E-07：不再默认 items.at(-1)，也不把无 split 的行混进 test）。
 * - 每行带 7 值状态标签（REPORT_DATA_SPEC §1(b)）；空值/失败保留，不改为 0 分。
 * - 方法汇总：n / 实际处理 / 原图返回 / 无法判定 + 三口径均值（绝对值，非 Δ）。
 */
import React, { useMemo, useState } from 'react';
import type { GlobalModel } from './reports/data/globalModel';
import { caseKeyOf } from './reports/data/globalModel';
import { appliedStatus, baselineMap, isPassthroughStatus, isProcessedStatus, rowDelta } from './reports/data/reportData';
import type { AppliedStatus } from './reports/data/types';
import { APPLIED_LABELS, degradationLabel, methodLabel } from './reports/data/labels';
import { signed } from './reports/format';
import { StatusTag } from './reports/StatusTag';

type MetricKey = 'psnr' | 'ssim' | 'edgeF1' | 'processingMs';
const METRIC_LABEL: Record<MetricKey, string> = { psnr: 'PSNR (dB)', ssim: 'SSIM', edgeF1: '边缘 F1', processingMs: '耗时 (ms)' };
const fmt = (n: number | null | undefined, d = 3) => n == null || !Number.isFinite(n) ? '未评测' : n.toFixed(d);
const avg = (xs: number[]) => xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null;
const STATUSES: AppliedStatus[] = ['processed', 'passthrough', 'passthrough_not_applicable', 'processed_not_applicable_label', 'failed', 'undetermined', 'baseline'];
const PAGE = 60;

export const ExperimentExplorer: React.FC<{ model: GlobalModel; onOpenCase?: (caseKey: string, method: string) => void }> = ({ model, onOpenCase }) => {
  const [metric, setMetric] = useState<MetricKey>('psnr');
  const [status, setStatus] = useState<AppliedStatus | ''>('');
  const [limit, setLimit] = useState(PAGE);
  const map = useMemo(() => baselineMap(model.rowsAll), [model.rowsAll]);
  const rows = useMemo(() => model.rows.filter(r => r.method === model.method || r.method === 'degraded').map(r => ({ r, s: appliedStatus(r).status })), [model.rows, model.method]);
  const shown = rows.filter(x => !status || x.s === status);
  const counts = STATUSES.map(s => [s, rows.filter(x => x.s === s).length] as const).filter(([, n]) => n > 0);
  const groups = useMemo(() => model.methods.map(m => {
    const own = model.rows.filter(r => r.method === m).map(r => ({ r, s: appliedStatus(r).status }));
    const val = (xs: typeof own) => avg(xs.map(x => x.r[metric]).filter((n): n is number => n != null && Number.isFinite(n)));
    return { method: m, n: own.length, processed: own.filter(x => isProcessedStatus(x.s)).length, passthrough: own.filter(x => isPassthroughStatus(x.s)).length, undetermined: own.filter(x => x.s === 'undetermined').length,
      all: val(own), meanProcessed: val(own.filter(x => isProcessedStatus(x.s))), meanPassthrough: val(own.filter(x => isPassthroughStatus(x.s))) };
  }), [model.rows, model.methods, metric]);
  const retest = model.batch.kind === 'retest';
  return <section aria-label="逐条实验记录" className="rounded-xl border border-gold/20 bg-[#0f1418] p-4 space-y-3" data-testid="experiment-explorer">
    <header className="flex flex-wrap items-baseline justify-between gap-2">
      <h3 className="font-serif text-gold text-base">逐条实验记录与方法汇总 · {model.batch.title}</h3>
      <p className="text-[11px] text-slate-400">仅对应受控退化实验，不代表 28 件历史拓本的无参考修复质量或识字准确率。</p>
    </header>
    <div className="flex flex-wrap items-center gap-3 text-[11px]">
      <label>汇总指标（绝对值）<select aria-label="对比指标" value={metric} onChange={e => setMetric(e.target.value as MetricKey)} className="ml-1 bg-slate-950 border border-slate-700 rounded p-1">{(Object.keys(METRIC_LABEL) as MetricKey[]).map(k => <option key={k} value={k}>{METRIC_LABEL[k]}</option>)}</select></label>
      <span className="text-slate-500">筛选同上方上下文栏（划分 / 退化 / 文物）。</span>
    </div>
    <div className="overflow-x-auto"><table data-testid="experiment-table" className="w-full text-[11px] text-left">
      <thead className="text-slate-400"><tr>{['方法', 'n', ...(retest ? ['无法判定'] : ['实际处理', '原图返回', '无法判定']), `${METRIC_LABEL[metric]} · 全部`, ...(retest ? [] : ['实际处理', '原图返回'])].map((v, i) => <th key={`${i}-${v}`} className="py-1 pr-3 font-normal">{v}</th>)}</tr></thead>
      <tbody>{groups.map(g => <tr key={g.method} className={`border-t border-slate-800 ${g.method === model.method ? 'bg-gold/5' : ''}`}>
        <td className="pr-3 py-0.5">{methodLabel(g.method)}</td><td className="pr-3">{g.n}</td>
        {retest ? <td className="pr-3">{g.undetermined}</td> : <><td className="pr-3">{g.processed}</td><td className="pr-3">{g.passthrough ? `未处理 ${g.passthrough}` : 0}</td><td className="pr-3">{g.undetermined}</td></>}
        <td className="pr-3">{fmt(g.all, metric === 'processingMs' ? 1 : 3)}</td>
        {!retest && <><td className="pr-3">{fmt(g.meanProcessed, metric === 'processingMs' ? 1 : 3)}</td><td className="pr-3">{g.passthrough ? fmt(g.meanPassthrough, metric === 'processingMs' ? 1 : 3) : '—'}</td></>}
      </tr>)}</tbody></table></div>
    <div className="flex flex-wrap items-center gap-1 text-[11px]" role="group" aria-label="按状态筛选">
      <span className="text-slate-400 mr-1">{methodLabel(model.method)} 与输入基线的逐条记录（{rows.length} 行）：</span>
      <button type="button" aria-pressed={!status} onClick={() => setStatus('')} className={`px-1.5 rounded border ${!status ? 'border-gold text-gold' : 'border-slate-700 text-slate-400'}`}>全部</button>
      {counts.map(([s, n]) => <button key={s} type="button" aria-pressed={status === s} onClick={() => setStatus(s)} className={`px-1.5 rounded border ${status === s ? 'border-gold text-gold' : 'border-slate-700 text-slate-400'}`}>{APPLIED_LABELS[s]} {n}</button>)}
    </div>
    <div className="max-h-72 overflow-auto"><table className="w-full text-[11px] text-left" data-testid="record-table">
      <thead className="text-slate-400 sticky top-0 bg-[#0f1418]"><tr>{['状态', '方法', '文物', '划分', '退化', '强度', 'PSNR', 'ΔPSNR', 'SSIM', '边缘 F1', '改动像素', 'seed'].map(h => <th key={h} className="py-1 pr-2 font-normal">{h}</th>)}</tr></thead>
      <tbody>{shown.slice(0, limit).map(({ r, s }, i) => { const d = r.method === 'degraded' ? null : rowDelta(r, 'psnr', map); return <tr key={`${caseKeyOf(r)}-${r.method}-${i}`} onClick={() => model.batch.hasImages && r.method !== 'degraded' && onOpenCase?.(caseKeyOf(r), r.method)} className={`border-t border-slate-800 ${model.batch.hasImages && r.method !== 'degraded' ? 'cursor-pointer hover:bg-gold/5' : ''}`}>
        <td className="pr-2"><StatusTag status={s} source={r.statusSource} /></td><td className="pr-2">{methodLabel(r.method)}</td><td className="pr-2">{r.sampleId}</td><td className="pr-2">{r.split || '未划分'}</td><td className="pr-2">{degradationLabel(r.degradation)}</td><td className="pr-2">{r.strength ?? '—'}</td>
        <td className="pr-2">{fmt(r.psnr, 2)}</td><td className={`pr-2 ${d != null && d < 0 ? 'text-cinnabar-light' : ''}`}>{isPassthroughStatus(s) ? '未处理' : signed(d, 2)}</td><td className="pr-2">{fmt(r.ssim)}</td><td className="pr-2">{fmt(r.edgeF1)}</td>
        <td className="pr-2">{r.changedPixelRatio != null ? `${(r.changedPixelRatio * 100).toFixed(2)}%` : '无法判定'}</td><td>{r.seed ?? '—'}</td></tr>; })}</tbody></table></div>
    {shown.length > limit && <button type="button" className="text-[11px] text-gold underline" onClick={() => setLimit(l => l + PAGE)}>再显示 {Math.min(PAGE, shown.length - limit)} 行（共 {shown.length} 行）</button>}
    <p className="text-[11px] text-slate-500">空值 / 失败保留，不改为 0 分。原图返回行的 ΔPSNR 写“未处理”，不写“0”。状态角标“兜底”表示该批次 DER 未接入、由前端按 SHA-256 判定。</p>
  </section>;
};
