/**
 * 跨批次对照（REPORT_DATA_SPEC §1(c)）：只要两个数字来自不同批次，就逐条检查 C1–C4，
 * 命中任一条在比较处显示黄色警告条，并把该比较降为“有限支持”。
 * 两批一律用统一口径重算（同一配对增益定义、同一聚类 CI、同一原图返回判据），不直接拿两批的 summary.csv 互比；
 * 不把两批画在同一根数值轴上，只用表格并列，并标明批次。
 */
import React, { useEffect, useMemo, useState } from 'react';
import type { GlobalModel } from './data/globalModel';
import { aggregate, appliedStatus, baselineMap, BatchInfo, gainWord, hasSplit, isPassthroughStatus, isProcessedStatus, mergeDer, MethodAggregate, ReportApi, Scope, SCOPE_LABELS } from './data/reportData';
import type { BatchDetail, ExperimentRow, Loadable } from './data/types';
import { METRICS, degradationLabel, methodLabel } from './data/labels';
import { GradeBadge } from './GradeBadge';
import { signed } from './format';

interface Side { batch: BatchInfo; detail: BatchDetail; rows: ExperimentRow[]; derSource: string | null }
interface Warning { code: 'C1' | 'C2' | 'C3' | 'C4'; hit: boolean; text: string }

const PSNR = METRICS.find(m => m.key === 'psnr')!;
const artifactKey = (r: ExperimentRow) => r.sourceSha256 || r.sampleId;
const uniq = <T,>(xs: T[]) => Array.from(new Set(xs));
const STRENGTH = (rows: ExperimentRow[]) => uniq(rows.map(r => r.strength).filter((v): v is number => v != null)).sort((a, b) => a - b);

function sampleCrops(side: Side): Map<string, string> {
  const m = new Map<string, string>();
  const cfg = (side.detail.config?.samples as { id: string; crop?: number[] }[] | undefined) || [];
  cfg.forEach(s => { if (s.crop) m.set(s.id, s.crop.join(',')); });
  side.rows.forEach(r => { if (r.crop && !m.has(r.sampleId)) m.set(r.sampleId, r.crop.join(',')); });
  return m;
}
const versionsOf = (rows: ExperimentRow[], method: string) => uniq(rows.filter(r => r.method === method).map(r => r.diagnostics?.version || r.algorithmVersion || '版本未记录'));
const determinable = (rows: ExperimentRow[]) => rows.some(r => { const s = appliedStatus(r).status; return isProcessedStatus(s) || isPassthroughStatus(s); });

export function crossBatchWarnings(a: Side, b: Side, methodA: string, methodB: string): Warning[] {
  const ka = uniq(a.rows.map(artifactKey)), kb = uniq(b.rows.map(artifactKey));
  const inter = ka.filter(k => kb.includes(k)).length, union = uniq([...ka, ...kb]).length;
  const sameSet = inter === ka.length && inter === kb.length;
  const ca = sampleCrops(a), cb = sampleCrops(b);
  const shared = uniq(a.rows.map(r => r.sampleId)).filter(id => cb.has(id) && ca.has(id));
  const cropDiff = shared.filter(id => ca.get(id) !== cb.get(id)).length;
  const tuned = a.batch.kind === 'retest' || b.batch.kind === 'retest';
  const c1: Warning = sameSet && cropDiff === 0
    ? { code: 'C1', hit: tuned, text: tuned ? '同一批文物复测，不是独立验证。' : '两批样本集相同。' }
    : { code: 'C1', hit: true, text: `两批样本集不同（重合 ${inter}/${union} 件${cropDiff ? `；同名样本中 ${cropDiff} 件裁切区域不同` : ''}），差异可能来自样本而非算法。${sameSet && tuned ? '同一批文物复测，不是独立验证。' : ''}` };
  const ta = uniq(a.rows.map(r => r.degradation)).sort().join(','), tb = uniq(b.rows.map(r => r.degradation)).sort().join(',');
  const sa = STRENGTH(a.rows).join(','), sb = STRENGTH(b.rows).join(',');
  const seedA = a.detail.config?.seed, seedB = b.detail.config?.seed;
  const b15 = a.batch.registry.directory === '2026-10-15' || b.batch.registry.directory === '2026-10-15';
  const diffs = [ta !== tb ? '退化类型' : '', sa !== sb ? `强度表（${sa || '未记录'} vs ${sb || '未记录'}）` : '', seedA !== seedB ? `种子（${seedA ?? '未记录'} vs ${seedB ?? '未记录'}）` : '', b15 ? '生成代码与参数（SPEC §10 已核对为不同）' : ''].filter(Boolean);
  const c2: Warning = { code: 'C2', hit: diffs.length > 0, text: diffs.length ? `退化生成方式不同（${diffs.join('、')}），PSNR 绝对值不可直接比较，只比较同批内相对增益。` : '退化类型、强度表与种子一致。' };
  const va = versionsOf(a.rows, methodA), vb = versionsOf(b.rows, methodB);
  const c3: Warning = { code: 'C3', hit: va.join() !== vb.join(), text: va.join() !== vb.join() ? `方法版本不同：A 为 ${va.join(' / ')}，B 为 ${vb.join(' / ')}。` : `方法版本相同（${va.join(' / ')}）。` };
  const rule = (s: Side) => s.batch.registry.directory === '2026-10-15' ? '排除不适用行' : '全部计入';
  const da = determinable(a.rows), db = determinable(b.rows);
  const c4hit = rule(a) !== rule(b) || da !== db;
  const c4: Warning = { code: 'C4', hit: c4hit, text: c4hit ? `汇总口径不同（A ${rule(a)}${da ? '、可区分原图返回' : '、无法判定原图返回'}；B ${rule(b)}${db ? '、可区分原图返回' : '、无法判定原图返回'}）。已按统一口径重算：配对增益 = 输出 − 同 case 退化输入，按文物聚类，口径见表。` : '汇总口径一致（全部计入、按文物聚类）；表中数字已按统一口径重算。' };
  return [c1, c2, c3, c4];
}

const pickMethod = (rows: ExperimentRow[], preferred: string) => {
  const ms = uniq(rows.map(r => r.method));
  if (ms.includes(preferred)) return preferred;
  return ['adaptive_v20', 'adaptive_joint', 'adaptive_v21'].find(m => ms.includes(m)) || '';
};

export const CrossBatchComparison: React.FC<{ model: GlobalModel; batches: BatchInfo[]; compareId: string; onCompare: (id: string) => void }> = ({ model, batches, compareId, onCompare }) => {
  const [other, setOther] = useState<Loadable<Side> | null>(null);
  const target = batches.find(b => b.id === compareId && b.id !== model.batch.id);
  useEffect(() => {
    if (!target) { setOther(null); return; }
    let live = true; setOther({ state: 'loading' });
    Promise.all([ReportApi.batch(target.id), ReportApi.appliedStatus(target.id, target.registry.directory)]).then(([d, der]) => {
      if (!live) return;
      if (d.state !== 'ok') { setOther(d); return; }
      const m = mergeDer(d.data, der);
      setOther({ state: 'ok', data: { batch: target, detail: d.data, rows: m.rows, derSource: m.source } });
    });
    return () => { live = false; };
  }, [target]);

  const result = useMemo(() => {
    if (!other || other.state !== 'ok') return null;
    const A: Side = { batch: model.batch, detail: model.detail, rows: model.rowsAll, derSource: model.der.source };
    const B = other.data;
    const methodA = model.method, methodB = pickMethod(B.rows, methodA);
    const bothSplit = hasSplit(A.rows) && hasSplit(B.rows) && A.batch.kind !== 'retest' && B.batch.kind !== 'retest';
    const split = bothSplit ? model.split : 'none';
    const deg = model.degradation !== 'all' && B.rows.some(r => r.degradation === model.degradation) ? model.degradation : 'all';
    const filt = (rows: ExperimentRow[]) => rows.filter(r => (split === 'none' || r.split === split) && (deg === 'all' || r.degradation === deg));
    const agg = (s: Side, m: string): MethodAggregate | undefined => aggregate(filt(s.rows), baselineMap(s.rows), 'psnr', [m], { split, degradation: deg, sampleFiltered: true, ci: null })[0];
    const ga = agg(A, methodA), gb = methodB ? agg(B, methodB) : undefined;
    const scope: Scope = ga && gb && ga.primaryScope === 'processed' && gb.primaryScope === 'processed' ? 'processed' : 'all';
    return { A, B, methodA, methodB, split, deg, ga, gb, scope, warnings: crossBatchWarnings(A, B, methodA, methodB) };
  }, [other, model]);

  const hits = result?.warnings.filter(w => w.hit) || [];
  return <section aria-label="跨批次对照" className="rounded-xl border border-gold/20 bg-[#0f1418] p-4 space-y-2" data-testid="cross-batch">
    <header className="flex flex-wrap items-center justify-between gap-2">
      <h3 className="font-serif text-gold text-base">跨批次对照（C1–C4 检查）</h3>
      <label className="text-[11px] text-slate-300">与
        <select aria-label="对照批次" value={target?.id || ''} onChange={e => onCompare(e.target.value)} className="mx-1 bg-slate-950 border border-slate-700 rounded p-1 max-w-[18rem]">
          <option value="">不做跨批次对照</option>
          {batches.filter(b => b.id !== model.batch.id).map(b => <option key={b.id} value={b.id}>{b.title}</option>)}
        </select>对照</label>
    </header>
    {!target ? <p className="text-[11px] text-slate-400">选择另一批次后，逐条检查样本集（C1）、退化生成器（C2）、方法版本（C3）、汇总口径（C4），命中任一条即显示警告并降为“有限支持”。</p>
      : !other || other.state === 'loading' ? <p className="text-[11px] text-gold">读取对照批次…</p>
      : other.state !== 'ok' ? <p role="alert" className="text-[11px] text-cinnabar-light">对照批次读取失败：{other.message}</p>
      : result && <>
        <div className="space-y-1" data-testid="cross-batch-warnings">{result.warnings.map(w => <p key={w.code} data-code={w.code} data-hit={w.hit} className={`text-[11px] rounded px-2 py-1 ${w.hit ? 'bg-yellow-500/15 border border-yellow-500/60 text-yellow-200' : 'border border-slate-700 text-slate-400'}`}><b>{w.code}</b> {w.hit ? '⚠ ' : '✓ '}{w.text}</p>)}</div>
        <div className="flex items-center gap-2 text-[11px]"><GradeBadge grade={hits.length ? '有限支持' : '有限支持'} reasons={[...hits.map(h => `${h.code} 命中`), '跨批次比较最高为有限支持']} /><span className="text-slate-400">{hits.length ? `命中 ${hits.map(h => h.code).join('、')}，该比较降为“有限支持”。` : '四项均未命中；跨批次比较仍不高于“有限支持”。'}</span></div>
        <div className="overflow-x-auto"><table className="w-full text-[11px] text-left" data-testid="cross-batch-table">
          <thead className="text-slate-400"><tr>{['批次', '方法', '划分 / 退化', `ΔPSNR（${SCOPE_LABELS[result.scope]}）`, '95% CI', '判定', '文物 / 行', '原图返回', '无法判定'].map(h => <th key={h} className="py-1 pr-3 font-normal">{h}</th>)}</tr></thead>
          <tbody>{[{ s: result.A, m: result.methodA, g: result.ga }, { s: result.B, m: result.methodB, g: result.gb }].map(({ s, m, g }) => { const st = g?.scopes[result.scope]; return <tr key={s.batch.id} className="border-t border-slate-800">
            <td className="pr-3">{s.batch.shortName}</td><td className="pr-3">{m ? methodLabel(m) : '该批无可比方法'}</td><td className="pr-3">{result.split === 'none' ? '不分划分' : result.split} / {degradationLabel(result.deg)}</td>
            <td className="pr-3">{st ? signed(st.value, 2, PSNR.unit) : '无数据'}</td><td className="pr-3">{st?.ci && st.ciReliable ? `${signed(st.ci[0], 2)} ~ ${signed(st.ci[1], 2)}` : st?.ciNote || '无'}</td><td className="pr-3">{st ? gainWord(st) : '—'}</td>
            <td className="pr-3">{st ? `${st.nArtifacts} / ${st.nRecords}` : '—'}</td><td className="pr-3">{g && s.batch.kind !== 'retest' ? `未处理 ${g.passthroughN} 条` : '—'}</td><td>{g?.undeterminedN ?? '—'}</td></tr>; })}</tbody></table></div>
        <p className="text-[10px] text-slate-500">两批的 CI 都是前端临时口径（文物 bootstrap 1000 次，种子 20261019），待替换为 derived/ci_by_artifact。不画在同一根数值轴上。{result.scope === 'all' ? '至少一批无法判定原图返回，两批都用“全部”口径。' : ''}</p>
      </>}
  </section>;
};
