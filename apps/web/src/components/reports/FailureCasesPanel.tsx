/**
 * L5 失败案例与不确定性（独立入口 panel=failures）。只用真实数据：
 * - 诊断接口 /diagnosis：有就显示；404 就照实说明“该批次暂无失败案例诊断数据”。
 * - 负提升：由逐条结果按 ΔPSNR<0 全部列出（不抽样、不删除），可点开对应三联图。
 * - 原图返回单独一栏，不算成功也不算失败；运行失败单独列。
 */
import React, { useMemo } from 'react';
import type { GlobalModel } from './data/globalModel';
import { caseKeyOf } from './data/globalModel';
import { appliedStatus, baselineMap, isPassthroughStatus, rowDelta } from './data/reportData';
import type { Diagnosis, Loadable } from './data/types';
import { APPLIED_LABELS, degradationLabel, methodLabel } from './data/labels';
import { signed } from './format';
import type { UrlState } from './useReportUrlState';

interface Props { model: GlobalModel; diagnosis: Loadable<Diagnosis>; setUrl: (p: UrlState) => void }

export const FailureCasesPanel: React.FC<Props> = ({ model, diagnosis, setUrl }) => {
  const map = useMemo(() => baselineMap(model.detail.rows), [model.detail.rows]);
  const scoped = model.rows.filter(r => r.method !== 'degraded');
  const negatives = useMemo(() => scoped.map(r => ({ r, d: rowDelta(r, 'psnr', map), s: appliedStatus(r).status }))
    .filter(x => x.d != null && x.d < 0).sort((a, b) => (a.d! - b.d!)), [scoped, map]);
  const passthrough = scoped.filter(r => isPassthroughStatus(appliedStatus(r).status));
  const failed = scoped.filter(r => appliedStatus(r).status === 'failed');
  const byMethod = (list: { r: { method: string } }[]) => model.methods.map(m => [m, list.filter(x => x.r.method === m).length] as const).filter(([, n]) => n > 0);
  const open = (caseKey: string, method: string) => setUrl({ panel: 'overview', method, case: caseKey });

  return <div className="space-y-4" data-testid="failure-cases">
    <section aria-label="诊断接口" className="rounded-xl border border-cinnabar/30 bg-[#140f0e] p-4 space-y-2">
      <h3 className="font-serif text-cinnabar-light text-base">失败诊断 · {model.batch.displayName}</h3>
      {diagnosis.state === 'loading' && <p className="text-sm text-slate-400">读取诊断数据…</p>}
      {diagnosis.state === 'missing' && <p className="text-sm text-slate-300" data-testid="diagnosis-missing">该批次暂无失败案例诊断数据（诊断接口返回 404）。下方的负提升与原图返回列表由逐条结果计算，不是诊断结论。</p>}
      {diagnosis.state === 'error' && <p role="alert" className="text-sm text-cinnabar-light">诊断数据读取失败：{diagnosis.message}</p>}
      {diagnosis.state === 'ok' && <div className="space-y-2 text-sm">
        <p>方法 {methodLabel(diagnosis.data.method || '')}：负提升 <b className="text-cinnabar-light">{diagnosis.data.negativeLiftCount ?? '—'}</b> 条，输出未改动 {diagnosis.data.unchangedCount ?? '—'} 条（诊断接口原值，均保留）。</p>
        {diagnosis.data.causeCounts && <p className="flex flex-wrap gap-2 text-xs">{Object.entries(diagnosis.data.causeCounts).map(([c, n]) => <span key={c} className="rounded border border-cinnabar/40 px-2 py-0.5">{c} · {n}</span>)}</p>}
        {diagnosis.data.caveat && <p className="text-xs text-slate-400">{diagnosis.data.caveat}</p>}
        {diagnosis.data.cases && <div className="max-h-56 overflow-auto"><table className="w-full text-[11px] text-left"><thead className="text-slate-400 sticky top-0 bg-[#140f0e]"><tr>{['文物', '退化', 'ΔPSNR', '未改动', '保真门控', '原因'].map(h => <th key={h} className="py-1 pr-2 font-normal">{h}</th>)}</tr></thead>
          <tbody>{diagnosis.data.cases.map((c, i) => <tr key={i} className="border-t border-slate-800"><td className="pr-2">{c.sampleId}</td><td className="pr-2">{degradationLabel(c.degradation)}</td><td className={`pr-2 ${c.negativeLift ? 'text-cinnabar-light' : ''}`}>{signed(c.psnrDeltaFromInput, 3, 'dB')}</td><td className="pr-2">{c.unchangedFromInput ? '是' : '否'}</td><td className="pr-2">{c.fidelityAccepted == null ? '—' : c.fidelityAccepted ? '通过' : '拒绝'}</td><td>{c.cause || '—'}</td></tr>)}</tbody></table></div>}
      </div>}
      {!model.batch.hasImages && <p className="text-[11px] text-slate-400">本批次只保存了数值，没有失败案例图像；不使用其他批次的图代替。</p>}
    </section>

    <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <section aria-label="负提升记录" className="xl:col-span-2 rounded-xl border border-gold/20 bg-[#0f1418] p-4 space-y-2">
        <h3 className="font-serif text-gold text-sm">负提升记录（ΔPSNR &lt; 0，当前筛选下全部 {negatives.length} 条）</h3>
        <p className="text-[11px] text-slate-400">按方法：{byMethod(negatives).map(([m, n]) => `${methodLabel(m)} ${n}`).join(' · ') || '无'}。{model.batch.hasImages ? '点击一行在视觉对照中打开。' : ''}</p>
        {negatives.length === 0 ? <p className="text-sm text-slate-400">当前筛选下没有 ΔPSNR&lt;0 的记录。</p> :
          <div className="max-h-80 overflow-auto"><table className="w-full text-[11px] text-left" data-testid="negative-lift-table"><thead className="text-slate-400 sticky top-0 bg-[#0f1418]"><tr>{['方法', '文物', '退化', '强度', 'ΔPSNR', '状态'].map(h => <th key={h} className="py-1 pr-2 font-normal">{h}</th>)}</tr></thead>
            <tbody>{negatives.map(({ r, d, s }) => <tr key={`${caseKeyOf(r)}-${r.method}`} onClick={() => model.batch.hasImages && open(caseKeyOf(r), r.method)} className={`border-t border-slate-800 ${model.batch.hasImages ? 'cursor-pointer hover:bg-gold/5' : ''}`}>
              <td className="pr-2">{methodLabel(r.method)}</td><td className="pr-2">{r.sampleId}</td><td className="pr-2">{degradationLabel(r.degradation)}</td><td className="pr-2">{r.strength ?? '—'}</td><td className="pr-2 text-cinnabar-light">{signed(d, 3, 'dB')}</td><td>{APPLIED_LABELS[s]}</td></tr>)}</tbody></table></div>}
      </section>
      <section aria-label="原图返回与失败" className="rounded-xl border border-slate-700 bg-[#0c1013] p-4 space-y-2 text-[11px]">
        <h3 className="font-serif text-gold text-sm">原图返回（未处理）· {passthrough.length} 条</h3>
        <p className="text-slate-400">不算成功，也不算失败；Δ 恒为 0。判据：{model.batch.hasImages ? '输出与输入 SHA-256 相同' : '本批无图像与 SHA，无法判定（undetermined）'}。</p>
        <ul className="space-y-0.5">{byMethod(passthrough.map(r => ({ r }))).map(([m, n]) => <li key={m}>{methodLabel(m)} · {n}</li>)}</ul>
        <h3 className="font-serif text-gold text-sm pt-2">运行失败 · {failed.length} 条</h3>
        {failed.length ? <ul className="space-y-0.5">{failed.map(r => <li key={caseKeyOf(r) + r.method}>{methodLabel(r.method)} · {r.sampleId} · {r.error}</li>)}</ul> : <p className="text-slate-400">当前筛选下没有运行失败的记录。</p>}
        <h3 className="font-serif text-gold text-sm pt-2">不确定性</h3>
        <p className="text-slate-400">比较图中的须为按文物 bootstrap 的 95% CI；n_文物 &lt; 10 时结论自动降为“有限支持”。</p>
      </section>
    </div>
  </div>;
};
