/**
 * L5 失败案例与不确定性（独立入口 panel=failures）。只用真实数据：
 * - 诊断：SteleService.getExperimentDiagnosis（四个批次都返回 200；未知 ID 才 404）。
 * - 负提升原因：以 NLC（derived/negative_lift_causes）的 measuredCauses 为主，每条附测量值与阈值；
 *   诊断接口里的旧 cause 只放在“旧规则推断”一栏。
 * - 负提升列表全部列出（不抽样、不删除）；原图返回单独一栏“未处理”；无法判定单独计数；运行失败单独列。
 */
import React, { useEffect, useMemo, useState } from 'react';
import type { GlobalModel } from './data/globalModel';
import { caseKeyOf } from './data/globalModel';
import { appliedStatus, baselineMap, isPassthroughStatus, ReportApi, rowDelta } from './data/reportData';
import type { Derived, Diagnosis, Loadable, NlcCase, NlcFile } from './data/types';
import { degradationLabel, methodLabel } from './data/labels';
import { signed } from './format';
import { StatusTag } from './StatusTag';
import type { ReportFilters } from './reportFilters';

interface Props { model: GlobalModel; diagnosis: Loadable<Diagnosis>; setFilters: (p: ReportFilters) => void }

export const FailureCasesPanel: React.FC<Props> = ({ model, diagnosis, setFilters }) => {
  const [nlc, setNlc] = useState<Loadable<Derived<NlcFile>>>({ state: 'loading' });
  useEffect(() => {
    let live = true; setNlc({ state: 'loading' });
    ReportApi.negativeLiftCauses(model.batch.id, model.batch.registry.directory).then(r => { if (live) setNlc(r); });
    return () => { live = false; };
  }, [model.batch.id, model.batch.registry.directory]);
  const nlcByRow = useMemo(() => nlc.state === 'ok' ? new Map<number, NlcCase>(nlc.data.file.cases.map(c => [c.rowIndex, c])) : null, [nlc]);
  const rowIndex = useMemo(() => new Map(model.rowsAll.map((r, i) => [r, i])), [model.rowsAll]);
  const map = useMemo(() => baselineMap(model.rowsAll), [model.rowsAll]);
  const retest = model.batch.kind === 'retest';
  const scoped = model.rows.filter(r => r.method !== 'degraded');
  const negatives = useMemo(() => scoped.map(r => ({ r, d: rowDelta(r, 'psnr', map), s: appliedStatus(r).status }))
    .filter(x => x.d != null && x.d < 0).sort((a, b) => (a.d! - b.d!)), [scoped, map]);
  const passthrough = scoped.filter(r => isPassthroughStatus(appliedStatus(r).status));
  const undetermined = scoped.filter(r => appliedStatus(r).status === 'undetermined');
  const failed = scoped.filter(r => appliedStatus(r).status === 'failed');
  const byMethod = (list: { method: string }[]) => model.methods.map(m => [m, list.filter(x => x.method === m).length] as const).filter(([, n]) => n > 0);
  const open = (caseKey: string, method: string) => setFilters({ panel: 'overview', method, case: caseKey });
  const legacyDiag = diagnosis.state === 'ok' && diagnosis.data.diagnosisVersion === 'heldout-legacy-heuristic';
  const legacyCause = useMemo(() => {
    const m = new Map<string, string>();
    if (diagnosis.state === 'ok') (diagnosis.data.cases || []).forEach(c => { if (c.cause) m.set(`${c.sampleId}|${c.degradation}|${c.method || diagnosis.data.method || ''}`, c.cause); });
    return m;
  }, [diagnosis]);

  return <div className="space-y-4" data-testid="failure-cases">
    <section aria-label="诊断接口" className="rounded-xl border border-cinnabar/30 bg-[#140f0e] p-4 space-y-2">
      <h3 className="font-serif text-cinnabar-light text-base">失败诊断 · {model.batch.title}</h3>
      {diagnosis.state === 'loading' && <p className="text-sm text-slate-400">读取诊断数据…</p>}
      {(diagnosis.state === 'missing' || diagnosis.state === 'error') && <p role="alert" className="text-sm text-slate-300" data-testid="diagnosis-missing">诊断数据不可用：{diagnosis.message}。下方列表由逐条结果计算，不是诊断结论。</p>}
      {diagnosis.state === 'ok' && <div className="space-y-2 text-sm" data-testid="diagnosis-ok" data-version={diagnosis.data.diagnosisVersion || ''}>
        <p>诊断版本 <code className="text-xs">{diagnosis.data.diagnosisVersion || '未标注'}</code>：负提升 <b className="text-cinnabar-light">{diagnosis.data.negativeLiftCount ?? '—'}</b> 条{diagnosis.data.method ? `（方法 ${methodLabel(diagnosis.data.method)}）` : '（全部方法）'}，全部保留。{legacyDiag ? `“输出未改动” ${diagnosis.data.unchangedCount ?? '—'} 条为旧启发式判断，未经像素验证。` : ''}</p>
        {diagnosis.data.byMethod && <div className="overflow-x-auto"><table className="text-[11px] text-left" data-testid="diagnosis-by-method"><thead className="text-slate-400"><tr>{['方法', 'n', '负提升', '输出与输入字节相同', '无法判定字节', '未配对'].map(h => <th key={h} className="pr-3 font-normal">{h}</th>)}</tr></thead>
          <tbody>{Object.entries(diagnosis.data.byMethod).map(([m, v]) => <tr key={m} className="border-t border-slate-800"><td className="pr-3">{methodLabel(m)}</td><td className="pr-3">{v.n}</td><td className="pr-3 text-cinnabar-light">{v.negativeLift}</td><td className="pr-3">{v.byteIdenticalToInput}</td><td className="pr-3">{v.byteIdentityUnknown}</td><td>{v.unmatched}</td></tr>)}</tbody></table></div>}
        {diagnosis.data.causeCounts && <p className="flex flex-wrap gap-2 text-xs"><span className="text-slate-400">旧规则推断：</span>{Object.entries(diagnosis.data.causeCounts).map(([c, n]) => <span key={c} className="rounded border border-slate-600 px-2 py-0.5 text-slate-300">{c} · {n}</span>)}</p>}
        {diagnosis.data.causeBasis && <p className="text-xs text-slate-400">{diagnosis.data.causeBasis}</p>}
        {diagnosis.data.caveat && <p className="text-xs text-slate-400">{diagnosis.data.caveat}</p>}
      </div>}
      <p className="text-[11px] text-slate-400" data-testid="nlc-source">测量原因（E-04）：{nlc.state === 'ok' ? `${nlc.data.file.measuredCriteriaVersion}，来源 ${nlc.data.source}` : nlc.state === 'loading' ? '读取中…' : retest ? '本批没有图像，像素级量不可测；没有 NLC 文件。' : `未接入（${nlc.message}）`}</p>
      {!model.batch.hasImages && <p className="text-[11px] text-slate-400">本批次只保存了数值，没有失败案例图像；不使用其他批次的图代替。</p>}
    </section>

    <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <section aria-label="负提升记录" className="xl:col-span-2 rounded-xl border border-gold/20 bg-[#0f1418] p-4 space-y-2">
        <h3 className="font-serif text-gold text-sm">负提升记录（ΔPSNR &lt; 0，当前筛选下全部 {negatives.length} 条）</h3>
        <p className="text-[11px] text-slate-400">按方法：{byMethod(negatives.map(x => x.r)).map(([m, n]) => `${methodLabel(m)} ${n}`).join(' · ') || '无'}。{model.batch.hasImages ? '点击一行在视觉对照中打开。' : ''}</p>
        {negatives.length === 0 ? <p className="text-sm text-slate-400">当前筛选下没有 ΔPSNR&lt;0 的记录{passthrough.length ? `；另有未处理 ${passthrough.length} 条（原图返回，不算“无负提升”）` : ''}。</p> :
          <div className="max-h-96 overflow-auto"><table className="w-full text-[11px] text-left" data-testid="negative-lift-table"><thead className="text-slate-400 sticky top-0 bg-[#0f1418]"><tr>{['方法', '文物', '退化', '强度', 'ΔPSNR', '状态', '测量原因（值 / 阈值）', '旧规则推断'].map(h => <th key={h} className="py-1 pr-2 font-normal">{h}</th>)}</tr></thead>
            <tbody>{negatives.map(({ r, d, s }) => { const c = nlcByRow?.get(rowIndex.get(r) ?? -1); const ev = c?.measuredEvidence.filter(e => e.triggered) || [];
              const old = c?.ruleInferredCause || legacyCause.get(`${r.sampleId}|${r.degradation}|${r.method}`);
              return <tr key={`${caseKeyOf(r)}-${r.method}`} onClick={() => model.batch.hasImages && open(caseKeyOf(r), r.method)} className={`border-t border-slate-800 align-top ${model.batch.hasImages ? 'cursor-pointer hover:bg-gold/5' : ''}`}>
              <td className="pr-2">{methodLabel(r.method)}</td><td className="pr-2">{r.sampleId}</td><td className="pr-2">{degradationLabel(r.degradation)}</td><td className="pr-2">{r.strength ?? '—'}</td><td className="pr-2 text-cinnabar-light">{signed(d, 3, 'dB')}</td><td className="pr-2"><StatusTag status={s} source={r.statusSource} detail={r.appliedStatusDetail} /></td>
              <td className="pr-2">{c ? (ev.length ? ev.map(e => <span key={e.cause} className="block">{e.cause}（{e.value == null ? '—' : e.value.toFixed(3)} {e.comparator} {e.threshold}）</span>) : '未定位到测量原因（待人工复核）') : nlc.state === 'ok' ? '无对应记录' : '未接入'}</td>
              <td className="pr-2 text-slate-400">{old ? `${old}（规则推断）` : '—'}</td></tr>; })}</tbody></table></div>}
      </section>
      <section aria-label="原图返回与失败" className="rounded-xl border border-slate-700 bg-[#0c1013] p-4 space-y-2 text-[11px]">
        {retest ? <>
          <h3 className="font-serif text-gold text-sm">无法判定 · {undetermined.length} 条</h3>
          <p className="text-slate-400">本批没有图像，isPassthrough = null；不判断是否改动，不显示原图返回率。</p>
        </> : <>
          <h3 className="font-serif text-gold text-sm">原图返回 · 未处理 {passthrough.length} 条</h3>
          <p className="text-slate-400">单独一栏：不算成功，也不算失败。判据：{model.der.source ? `DER ${model.der.criterion}` : '前端兜底（SHA-256 相同）'}。</p>
          <ul className="space-y-0.5">{byMethod(passthrough).map(([m, n]) => <li key={m}>{methodLabel(m)} · 未处理 {n} 条</li>)}</ul>
          {model.degradation === 'blur' && passthrough.length > 0 && <p className="text-gold-light">自适应方法对模糊不做处理：这些行计为“未处理”，禁止计入提升。</p>}
          {undetermined.length > 0 && <p className="text-slate-400">另有无法判定 {undetermined.length} 条，单独计数，不归入任何一类。</p>}
        </>}
        <h3 className="font-serif text-gold text-sm pt-2">运行失败 · {failed.length} 条</h3>
        {failed.length ? <ul className="space-y-0.5">{failed.map(r => <li key={caseKeyOf(r) + r.method}>{methodLabel(r.method)} · {r.sampleId} · {r.error}</li>)}</ul> : <p className="text-slate-400">当前筛选下没有运行失败的记录。</p>}
        <h3 className="font-serif text-gold text-sm pt-2">不确定性</h3>
        <p className="text-slate-400">比较图中的须为按文物聚类 bootstrap 的 95% CI；文物 &lt; 3 标“CI 不可靠”、不画误差线；n_文物 &lt; 10 时结论自动降为“有限支持”。</p>
        <h3 className="font-serif text-gold text-sm pt-2">待人工复核</h3>
        <p className="text-slate-400"><span className="rounded border border-cinnabar/50 px-1 text-cinnabar-light">待人工复核</span> E-09（V22 interior_constant_block）、E-12（两个 glyph schema 不一致）。</p>
      </section>
    </div>
  </div>;
};
