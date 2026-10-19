/**
 * 全局评测层（与当前文物无关，由 experimentId 驱动）。
 * L1 研究总览（分级结论，≤3 条）· L2 视觉对照（三联 + 差分 + ROI）· L3 ECharts 横向比较 · L6 可复现性。
 */
import React, { useState } from 'react';
import type { GlobalModel } from './data/globalModel';
import { caseKeyOf } from './data/globalModel';
import { appliedStatus, BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED, GlyphEvaluation, isPassthroughStatus, ReportApi } from './data/reportData';
import type { ExperimentRow, Loadable } from './data/types';
import { APPLIED_LABELS, degradationLabel, methodLabel, SPLIT_LABELS } from './data/labels';
import { signed, shortSha } from './format';
import { GradeBadge } from './GradeBadge';
import { SyncedTriptych, TriptychPane } from './SyncedTriptych';
import { MethodComparisonChart } from './MethodComparisonChart';
import type { UrlState } from './useReportUrlState';

export const REFERENCE_NOTE = '参考图 = 馆藏可读 JPG 的 256×256 裁切，经受控退化后再处理；它不是碑石真值，结论只对受控退化成立。';

interface Props { model: GlobalModel; glyph: Loadable<GlyphEvaluation>; setUrl: (p: UrlState) => void }

export function triptychPanes(model: GlobalModel, row: ExperimentRow | undefined): TriptychPane[] | null {
  const id = model.batch.id;
  if (!model.batch.hasImages) return null;
  if (!row) return [];
  const base = model.caseBaseline;
  const st = appliedStatus(row);
  const outLabel = st.status === 'processed' ? `本方法输出 · ${methodLabel(row.method)}` : `${APPLIED_LABELS[st.status]} · ${methodLabel(row.method)}`;
  const inputFile = row.input || base?.output || null;
  const inputSha = row.input ? row.inputSha256 : base?.outputSha256;
  return [
    { key: 'ref', label: '受控参考（退化前裁切）', src: row.reference ? ReportApi.assetUrl(id, row.reference) : null, sha: row.referenceSha256, tone: 'ref', emptyReason: '本批次未保存参考图' },
    { key: 'in', label: `退化输入 · ${degradationLabel(row.degradation)}${row.strength != null ? ` ${row.strength}` : ''}`, src: inputFile ? ReportApi.assetUrl(id, inputFile) : null, sha: inputSha, tone: 'input', emptyReason: '本批次未保存退化输入图' },
    { key: 'out', label: outLabel, src: row.output && !row.error ? ReportApi.assetUrl(id, row.output) : null, sha: row.outputSha256, tone: isPassthroughStatus(st.status) ? 'passthrough' : st.status === 'processed' ? 'output' : 'warn', caption: st.criterion, emptyReason: row.error ? `运行失败：${row.error}` : '本行没有输出图' },
  ];
}

export const GlobalEvaluation: React.FC<Props> = ({ model, glyph, setUrl }) => {
  const { batch, primary, primaryGrade, caseRow } = model;
  const psnrPanel = model.panels.find(p => p.metric.key === 'psnr');
  const negMethods = (psnrPanel?.items || []).filter(i => i.value != null && i.value < 0);
  const withValue = (psnrPanel?.items || []).filter(i => i.value != null);
  const panes = triptychPanes(model, caseRow);
  const [showAbs, setShowAbs] = useState(false);
  const scopeText = primary?.scope === 'processed' ? `实际处理 ${primary.processedN}/${primary.n} 条；另有 ${primary.passthroughN} 条原图返回（Δ≡0，未计入主数字）` : primary ? `全部 ${primary.n} 条（本批无法判定原图返回）` : '';
  const filterText = `${SPLIT_LABELS[model.split]} · ${degradationLabel(model.degradation)}${model.sample ? ` · 仅 ${model.sample}` : ''}`;
  return <div className="space-y-4" data-testid="global-evaluation">
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
      {/* L1 研究总览 */}
      <section aria-label="研究总览" className="xl:col-span-5 rounded-xl border border-gold/20 bg-[#0f1418] p-4 space-y-3">
        <header className="flex flex-wrap items-baseline justify-between gap-2">
          <h3 className="font-serif text-gold text-base">研究总览 · {batch.displayName}</h3>
          <span className="text-[11px] text-slate-400">{filterText}</span>
        </header>
        <article className="rounded-lg border border-slate-700/80 bg-black/20 p-3 space-y-1.5" data-testid="conclusion-primary">
          <div className="flex items-center justify-between gap-2"><p className="text-xs text-slate-400">结论 1 · {methodLabel(model.method)} 相对退化输入的 ΔPSNR</p><GradeBadge grade={primaryGrade.grade} reasons={primaryGrade.reasons} /></div>
          <p className="font-serif text-2xl" style={{ color: primary?.value == null ? '#94a3b8' : primary.value < 0 ? '#EE5C42' : '#85D3C3' }}>
            {signed(primary?.value, 2, 'dB')}
            <span className="text-sm text-slate-300 ml-2">95% CI {primary?.ci ? `${signed(primary.ci[0], 2)} ~ ${signed(primary.ci[1], 2)}` : '无'}</span>
          </p>
          <p className="text-[11px] text-slate-400">n_文物 {primary?.nArtifacts ?? 0} · {scopeText}{primary && primary.negativeN ? ` · 负提升 ${primary.negativeN} 条` : ''}</p>
          <p className="text-[11px] text-slate-500">分级依据：{primaryGrade.reasons.join('；')}。</p>
        </article>
        <article className="rounded-lg border border-slate-700/80 bg-black/20 p-3 space-y-1" data-testid="conclusion-negative">
          <div className="flex items-center justify-between gap-2"><p className="text-xs text-slate-400">结论 2 · 相对输入 ΔPSNR 为负的方法</p><GradeBadge grade={withValue.length ? '有限支持' : '未评测'} reasons={['受控退化；逐方法见图中 CI']} /></div>
          <p className="text-sm">{withValue.length ? <><span className={negMethods.length ? 'text-cinnabar-light font-bold' : 'text-celadon-light'}>{negMethods.length}/{withValue.length}</span> 种方法的聚类均值低于输入{negMethods.length ? '：' : '。'}{negMethods.map(i => `${methodLabel(i.method)}（${signed(i.value, 2, 'dB')}）`).join('、')}</> : '当前筛选没有可比记录。'}</p>
          <p className="text-[11px] text-slate-500">负提升全部保留；不跨批次求均值，不把批次间差异解读为进步。</p>
        </article>
        <article className="rounded-lg border border-slate-700/80 bg-black/20 p-3 space-y-1" data-testid="conclusion-unevaluated">
          <div className="flex items-center justify-between gap-2"><p className="text-xs text-slate-400">结论 3 · 未评测项</p><GradeBadge grade="未评测" /></div>
          <p className="text-sm">真实拓本修复质量：未评测（无配对参考，不报告 PSNR/SSIM）。</p>
          <p className="text-sm">古碑识字 Top-1 / Top-3：{glyph.state === 'ok' ? (glyph.data.status === 'not_evaluated' ? `未评测（已核验标注 ${glyph.data.verifiedLabels} 条）` : `${glyph.data.top1 ?? '—'} / ${glyph.data.top3 ?? '—'}（已核验标注 ${glyph.data.verifiedLabels} 条）`) : glyph.state === 'loading' ? '读取中…' : `状态不可用（${glyph.state === 'missing' || glyph.state === 'error' ? glyph.message : ''}）`}</p>
        </article>
        <p className="text-[11px] text-gold-light/90 border-l-2 border-gold/60 pl-2">{REFERENCE_NOTE}</p>
        {batch.kind === 'retest' && <p className="text-[11px] text-cinnabar-light border-l-2 border-cinnabar pl-2">同批文物复测，不是独立验证：据 REPORT_DATA_SPEC §1(a)，本批 14 件文物与 v2-text 相同，且参与过 v2.1 的误差分析；结论最高为“有限支持”。</p>}
        {batch.kind === 'historical' && <p className="text-[11px] text-cinnabar-light border-l-2 border-cinnabar pl-2">{batch.registry.historicalWarning}</p>}
        {!model.splitAvailable && <p className="text-[11px] text-slate-300 border-l-2 border-slate-500 pl-2">本批未划分 dev/test：记录不带 split 字段，不能当作测试集解读。</p>}
        {model.splitAvailable && model.split === 'test' && <p className="text-[11px] text-slate-400">当前为测试组；阈值与参数不得依测试组结果调整。</p>}
        {model.notes.length > 0 && <ul className="text-[11px] text-slate-300 list-disc pl-4 space-y-0.5">{model.notes.map(n => <li key={n}>{n}</li>)}</ul>}
      </section>

      {/* L2 视觉对照 */}
      <section aria-label="修复效果视觉对照" className="xl:col-span-7 rounded-xl border border-gold/20 bg-[#0f1418] p-4 space-y-2">
        <header className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="font-serif text-gold text-base">视觉对照</h3>
          {panes && model.caseRows.length > 0 && <label className="text-[11px] text-slate-300">实验记录
            <select aria-label="单次实验记录" value={caseRow ? caseKeyOf(caseRow) : ''} onChange={e => setUrl({ case: e.target.value })} className="ml-1 bg-slate-950 border border-slate-700 rounded p-1 max-w-[18rem]">
              {model.caseRows.map(r => <option key={caseKeyOf(r)} value={caseKeyOf(r)}>{r.sampleId} · {degradationLabel(r.degradation)} {r.strength ?? ''} · {APPLIED_LABELS[appliedStatus(r).status]}</option>)}
            </select></label>}
        </header>
        {panes == null
          ? <div className="rounded-md border border-dashed border-slate-600 p-6 text-sm text-slate-300" data-testid="no-images">本批次只保存了数值，没有保存对比图像（registry.metricsOnly）；不使用其他批次的图代替。可在“失败案例与不确定性”中查看逐条数值。</div>
          : !caseRow ? <div className="rounded-md border border-dashed border-slate-600 p-6 text-sm text-slate-300">当前筛选下 {methodLabel(model.method)} 没有记录。</div>
          : <SyncedTriptych testId="experiment-triptych" panes={panes} diffPair={['in', 'out']} height={248}
              meta={<>实验 <code>{batch.id}</code> · 方法 {methodLabel(caseRow.method)}（{caseRow.algorithmVersion || '版本未记录'}）· case <code>{caseKeyOf(caseRow)}</code> · seed {caseRow.seed ?? '未记录'}</>} />}
        {caseRow && <p className="text-[11px] text-slate-400">未指定 case 时默认显示按文物/退化排序的第一条实际处理记录。本条：PSNR {caseRow.psnr?.toFixed(2) ?? '未评测'}（输入 {model.caseBaseline?.psnr?.toFixed(2) ?? caseRow.inputPsnr?.toFixed(2) ?? '—'}）· SSIM {caseRow.ssim?.toFixed(3) ?? '未评测'} · 边缘 F1 {caseRow.edgeF1?.toFixed(3) ?? '未评测'} · 输出 SHA {shortSha(caseRow.outputSha256)} · 源图 SHA {shortSha(caseRow.sourceSha256)}</p>}
      </section>
    </div>

    {/* L3 横向比较 */}
    <section aria-label="算法横向比较" className="rounded-xl border border-gold/20 bg-[#0f1418] p-4 space-y-2">
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="font-serif text-gold text-base">算法横向比较 · 相对退化输入的变化量</h3>
        <p className="text-[11px] text-slate-400">每个量纲单独一轴，轴含 0 与全部负值；柱 = 按文物聚类均值，须 = 文物 bootstrap 95% CI（{BOOTSTRAP_RESAMPLES} 次，种子 {BOOTSTRAP_SEED}，前端按 SPEC §0.3 计算），点 = 每件文物。点击柱选方法，点击点看该文物。</p>
      </header>
      <MethodComparisonChart testId="method-comparison-chart" panels={model.panels} methods={model.methods} selectedMethod={model.method}
        onSelectMethod={m => setUrl({ method: m, case: '' })} onSelectSample={(s, m) => setUrl({ method: m, sample: s, case: '' })} height={Math.max(250, 44 + model.methods.length * 26)} />
      <p className="text-[11px] text-slate-500">主数字口径：有可判定的原图返回时只计实际处理记录（REPORT_DATA_SPEC §1(b)），提示框里附含原图返回的全部记录均值作对照；判定依据为输出与输入文件 SHA-256 是否相同（DER 像素判据接入后替换）。仅同批内比较，不跨批次。</p>
      <button type="button" onClick={() => setShowAbs(v => !v)} className="text-[11px] text-gold underline print:hidden">{showAbs ? '收起' : '展开'}与历史 summary 对照的数值</button>
      {showAbs && <AbsoluteTable model={model} />}
    </section>

    <Reproducibility model={model} />
  </div>;
};

const AbsoluteTable: React.FC<{ model: GlobalModel }> = ({ model }) => {
  const rows = (model.detail.summary || []).filter(s => (model.split === 'none' || s.split === model.split) && (!('degradation' in s) || s.degradation === model.degradation));
  if (!rows.length) return <p className="text-[11px] text-slate-400">本批次 summary 没有与当前筛选对应的分组。</p>;
  return <div className="overflow-x-auto"><table className="text-[11px] text-left" data-testid="summary-reference-table"><caption className="text-left text-slate-400 mb-1">后端 summary 原值（MeanAll 口径，含原图返回；只作对照）</caption>
    <thead><tr className="text-slate-400">{['划分', '退化', '方法', 'n', 'PSNR 均值', 'PSNR CI95', 'SSIM 均值'].map(h => <th key={h} className="pr-3 py-1 font-normal">{h}</th>)}</tr></thead>
    <tbody>{rows.map((s, i) => <tr key={i} className="border-t border-slate-800"><td className="pr-3">{String(s.split ?? '未划分')}</td><td className="pr-3">{String(s.degradation ?? '全部')}</td><td className="pr-3">{methodLabel(String(s.method))}</td><td className="pr-3">{String(s.n ?? '—')}</td><td className="pr-3">{typeof s.psnrMean === 'number' ? s.psnrMean.toFixed(3) : '未评测'}</td><td className="pr-3">{Array.isArray(s.psnrCI95) ? (s.psnrCI95 as number[]).map(v => v.toFixed(2)).join(' ~ ') : '无'}</td><td>{typeof s.ssimMean === 'number' ? s.ssimMean.toFixed(3) : '未评测'}</td></tr>)}</tbody></table></div>;
};

export const Reproducibility: React.FC<{ model: GlobalModel }> = ({ model }) => {
  const d = model.detail; const reg = model.batch.registry; const env = d.environment || {};
  const limitations = Array.from(new Set([...(reg.limitations || []), ...((d.config?.limitations as string[] | undefined) || [])]));
  return <section aria-label="科学结论与可复现性" className="rounded-xl border border-slate-700 bg-[#0c1013] p-4 text-[11px] text-slate-300 space-y-2">
    <h3 className="font-serif text-gold text-sm">可复现性与限制</h3>
    <dl className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-x-6 gap-y-1">
      <div><dt className="text-slate-500">实验 ID</dt><dd><code>{reg.id}</code></dd></div>
      <div><dt className="text-slate-500">结果目录（路径）</dt><dd><code>experiments/results/{reg.directory}</code></dd></div>
      <div><dt className="text-slate-500">样本 / 记录</dt><dd>{reg.sampleCount ?? '—'} 件 / {reg.rowCount ?? d.rows.length} 条</dd></div>
      <div><dt className="text-slate-500">随机种子</dt><dd>{String(d.config?.seed ?? d.rows[0]?.seed ?? '配置未记录')}</dd></div>
      <div><dt className="text-slate-500">代码提交</dt><dd><code>{String(env.gitSha || d.candidateCommit || '未记录')}</code>{d.baselineCommit ? <> · 基线 <code>{d.baselineCommit}</code></> : null}</dd></div>
      <div><dt className="text-slate-500">环境</dt><dd>{['python', 'numpy', 'opencv', 'scikitImage'].filter(k => env[k]).map(k => `${k} ${String(env[k])}`).join(' · ') || '未记录'}</dd></div>
      <div className="md:col-span-2"><dt className="text-slate-500">源码 SHA-256</dt><dd className="break-all">{env.codeSha256 ? Object.entries(env.codeSha256).map(([f, h]) => <span key={f} className="mr-3"><code>{f}</code> {String(h).slice(0, 12)}…</span>) : '未记录'}</dd></div>
    </dl>
    <p className="flex flex-wrap gap-3">{['results.json', 'results.csv', 'summary.csv'].map(k => <a key={k} className="text-gold underline" href={ReportApi.exportUrl(reg.id, k)} download>导出 {k}</a>)}<span className="text-slate-500">DER applied_status 导出：待后端接入（REPORT_DATA_SPEC §7）</span></p>
    {limitations.length > 0 && <details><summary className="cursor-pointer text-slate-400">本批次限制说明（{limitations.length} 条）与来源（{d.sources?.length ?? 0} 件）</summary>
      <ul className="list-disc pl-4 mt-1 space-y-0.5">{limitations.map(t => <li key={t}>{t}</li>)}</ul>
      <ul className="mt-1 space-y-0.5">{(d.sources || []).map(s => <li key={s.id}><a className="text-gold underline" href={s.sourceUrl} target="_blank" rel="noreferrer">{s.id}</a> · {s.license || '许可未记录'} · 源图 SHA {shortSha(s.sourceSha256)}</li>)}</ul>
    </details>}
  </section>;
};
