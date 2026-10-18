import React, { useEffect, useState } from 'react';

type Summary = {
  method: string;
  degradation: string;
  n: number;
  failed: number;
  psnrMean: number | null;
  ssimMean: number | null;
  edgeF1Mean: number | null;
  thinStrokeMaeMean: number | null;
  processingMsMean: number;
  negativeLiftCount: number;
};
type Batch = {
  experimentId?: string;
  pairedReference?: string;
  samplingRule?: string;
  notThePreviousBatch?: string;
  summary: Summary[];
  registry?: { limitations?: string[]; metricsOnly?: boolean; sampleCount?: number; rowCount?: number };
};

const METHODS = ['degraded', 'gaussian_lowpass', 'butterworth_lowpass', 'notch', 'fast_nlm', 'adaptive_v20', 'adaptive_v21'];
const DEGRADATIONS = ['all', 'gaussian', 'salt_pepper', 'periodic', 'blur', 'occlusion'];
const LABELS: Record<string, string> = { all: '全部', gaussian: '高斯噪声', salt_pepper: '椒盐噪声', periodic: '周期噪声', blur: '模糊', occlusion: '遮挡' };
const fmt = (value: number | null | undefined, digits = 3) => value == null ? '未评测' : value.toFixed(digits);

export const HeldoutComparison: React.FC = () => {
  const [data, setData] = useState<Batch | null>(null);
  const [error, setError] = useState('');
  const [degradation, setDegradation] = useState('all');
  const [metric, setMetric] = useState<'psnrMean' | 'ssimMean' | 'edgeF1Mean' | 'thinStrokeMaeMean' | 'processingMsMean'>('psnrMean');
  const [diagnosis, setDiagnosis] = useState<{ caveat?: string; negativeLiftCount?: number; causeCounts?: Record<string, number>; notRetuned?: string } | null>(null);
  useEffect(() => {
    let live = true;
    fetch('/api/experiments/heldout-v20-v21-2026-10-18/diagnosis').then(response => response.ok ? response.json() : null).then(value => { if (live) setDiagnosis(value); }).catch(() => undefined);
    fetch('/api/experiments/heldout-v20-v21-2026-10-18').then(async response => {
      if (!response.ok) throw new Error('留出实验不可用');
      return response.json();
    }).then(value => { if (live) setData(value); }).catch(reason => { if (live) setError(String(reason)); });
    return () => { live = false; };
  }, []);
  const rows = data?.summary.filter(row => row.degradation === degradation && METHODS.includes(row.method)) || [];
  const ordered = METHODS.map(method => rows.find(row => row.method === method)).filter((row): row is Summary => !!row);
  const max = Math.max(1, ...ordered.map(row => Math.abs(row[metric] || 0)));
  const overall = (method: string) => data?.summary.find(row => row.method === method && row.degradation === 'all');
  const occlusion = (method: string) => data?.summary.find(row => row.method === method && row.degradation === 'occlusion');
  const v20 = overall('adaptive_v20');
  const v21 = overall('adaptive_v21');
  return <section aria-label="v2.0与v2.1留出对比" className="glass-panel rounded-xl border border-gold/20 p-4 md:p-6 space-y-3 print:hidden">
    <h2 className="text-lg text-gold font-serif">v2.0 / v2.1 自适应修复对比</h2>
    <p className="text-xs text-slate-300">本次是受控退化实验，配对对象是退化前的阅读图局部，不是历史原碑完全复原准确率。</p>
    {error && <p role="alert" className="text-cinnabar-light">{error}</p>}
    {data && <>
      <p className="text-xs text-slate-400">{data.samplingRule} {data.notThePreviousBatch} {data.registry?.metricsOnly ? '本批次已保留真实数值，部分图像对比不可用。' : ''}</p>
      <p className="text-sm">样本 {data.registry?.sampleCount ?? '—'} 件 · 记录 {data.registry?.rowCount ?? data.summary.length} 条。v2.0 负提升 {v20?.negativeLiftCount}/{v20?.n}，v2.1 负提升 {v21?.negativeLiftCount}/{v21?.n}。遮挡场景 v2.0 {occlusion('adaptive_v20')?.negativeLiftCount}/{occlusion('adaptive_v20')?.n}，v2.1 {occlusion('adaptive_v21')?.negativeLiftCount}/{occlusion('adaptive_v21')?.n}。</p>
      {diagnosis && <p className="text-xs">{diagnosis.caveat} 负提升 {diagnosis.negativeLiftCount} 条仍保留。{Object.entries(diagnosis.causeCounts || {}).map(([cause, count]) => `${cause} ${count}`).join('；')}。{diagnosis.notRetuned}</p>}
      <div className="flex flex-wrap gap-2 text-xs">{DEGRADATIONS.map(item => <button key={item} aria-pressed={degradation === item} onClick={() => setDegradation(item)} className={degradation === item ? 'text-slate-950 bg-gold px-2 py-1 rounded' : 'border border-slate-700 px-2 py-1 rounded'}>{LABELS[item]}</button>)}</div>
      <label className="text-xs">对比指标<select aria-label="留出实验指标" value={metric} onChange={event => setMetric(event.target.value as typeof metric)} className="ml-2 bg-slate-950 p-1">{[['psnrMean', 'PSNR'], ['ssimMean', 'SSIM'], ['edgeF1Mean', '边缘F1'], ['thinStrokeMaeMean', '细笔画误差'], ['processingMsMean', '耗时']].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <table className="w-full text-xs text-left"><thead><tr>{['方法', 'n', '失败', 'PSNR', 'SSIM', '边缘F1', '细笔画误差', '耗时', '负提升'].map(item => <th key={item} className="p-2">{item}</th>)}</tr></thead>
        <tbody>{ordered.map(row => <tr key={row.method} className="border-t border-slate-700"><td className="p-2">{row.method}</td><td>{row.n}</td><td>{row.failed}</td><td>{fmt(row.psnrMean, 2)}</td><td>{fmt(row.ssimMean)}</td><td>{fmt(row.edgeF1Mean)}</td><td>{fmt(row.thinStrokeMaeMean, 2)}</td><td>{fmt(row.processingMsMean, 1)}</td><td>{row.negativeLiftCount}/{row.n}</td></tr>)}</tbody></table>
      <div className="space-y-1">{ordered.map(row => <div key={row.method} className="grid grid-cols-[9rem_1fr_4rem] gap-2 text-xs items-center"><span>{row.method}</span><div className="h-2 bg-gold/70" style={{ width: `${Math.max(0, (row[metric] || 0) / max * 100)}%` }} /><span>{fmt(row[metric], metric === 'processingMsMean' || metric === 'psnrMean' ? 2 : 3)}</span></div>)}</div>
      <div className="flex flex-wrap gap-3 text-xs text-gold">{['results.json', 'results.csv', 'summary.csv'].map(kind => <a key={kind} href={`/api/experiments/heldout-v20-v21-2026-10-18/export/${kind}`} download>导出 {kind}</a>)}</div>
    </>}
  </section>;
};
