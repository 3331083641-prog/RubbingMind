/**
 * 全局评测层（与当前文物无关，由 experimentId 驱动）。
 * L1 研究总览（分级结论）· L2 视觉对照（代表案例 + 三联 + 差分 + ROI）· L3 ECharts 横向比较（三口径）
 * · 逐条记录（7 值状态）· 跨批次对照（C1–C4）· 同批复测 v2.1 · L6 可复现性。
 */
import React, { useState } from 'react';
import type { GlobalModel } from './data/globalModel';
import { caseKeyOf } from './data/globalModel';
import { appliedStatus, BatchInfo, BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED, gainWord, GAIN_SIGN_TEXT, GlyphEvaluation, isPassthroughStatus, MethodAggregate, ReportApi, ScopeStat, SCOPE_LABELS, glyphEvaluationText } from './data/reportData';
import type { ExperimentRow, Loadable } from './data/types';
import { APPLIED_LABELS, degradationLabel, methodLabel, SPLIT_LABELS } from './data/labels';
import { signed, shortSha } from './format';
import { GradeBadge } from './GradeBadge';
import { StatusTag } from './StatusTag';
import { SyncedTriptych, TriptychPane } from './SyncedTriptych';
import { MethodComparisonChart } from './MethodComparisonChart';
import { ExperimentExplorer } from '../ExperimentExplorer';
import { HeldoutComparison, RetestTeaser } from '../HeldoutComparison';
import { CrossBatchComparison } from './CrossBatchComparison';
import type { ReportFilters } from './reportFilters';

export const REFERENCE_NOTE = '参考图 = 馆藏可读 JPG 的 256×256 裁切，经受控退化后再处理；它不是碑石真值，结论只对受控退化成立。';

interface Props { model: GlobalModel; batches: BatchInfo[]; glyph: Loadable<GlyphEvaluation>; filters: ReportFilters; setFilters: (p: ReportFilters) => void; onSelectBatch?: (b: BatchInfo) => void }

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

const ciText = (s: ScopeStat, digits = 2) => s.value == null ? '无数据' : s.ci && s.ciReliable ? `95% CI ${signed(s.ci[0], digits)} ~ ${signed(s.ci[1], digits)}` : s.ciNote || (s.ci ? `CI 不可靠（文物数 ${s.nArtifacts}）` : '无 CI');
const ciSourceText = (s: ScopeStat) => s.ciSource === 'ci_by_artifact' ? 'CI 来源：derived/ci_by_artifact.json' : `临时口径：前端计算，待替换为 derived/ci_by_artifact（文物 bootstrap ${BOOTSTRAP_RESAMPLES} 次，种子 ${BOOTSTRAP_SEED}）`;

/** 三口径并列：主显示“实际处理”；旁注全部 / MeanPassthrough；E-05 单独计数（SPEC §1(b)，不进 MeanProcessed）。 */
export const ScopeTriple: React.FC<{ it: MethodAggregate; unit?: string; retest?: boolean }> = ({ it, unit = 'dB', retest }) => {
  const main = it.scopes[it.primaryScope];
  const pt = it.scopes.passthrough;
  return <div className="space-y-1" data-testid="scope-triple">
    <p className="font-serif text-2xl" style={{ color: main.value == null ? '#94a3b8' : main.sign === 'negative' ? '#EE5C42' : main.sign === 'positive' && main.ciReliable ? '#85D3C3' : '#F5D46E' }}>
      {main.value == null ? (it.passthroughN > 0 && it.processedN === 0 ? `未处理 ${it.passthroughN} 条` : '无数据') : signed(main.value, 2, unit)}
      {main.value != null && <><span className="text-sm text-slate-300 ml-2">{ciText(main)}</span>
      <span className="text-xs ml-2 rounded border border-slate-600 px-1 py-0.5 text-slate-300">{gainWord(main)}</span></>}
    </p>
    <p className="text-[11px] text-slate-300">主口径 <b>{SCOPE_LABELS[it.primaryScope]}</b>：文物 {main.nArtifacts} 件 · {main.nRecords} 行（n = {it.n}）{main.sign ? ` · ${GAIN_SIGN_TEXT[main.sign]}` : ''}</p>
    <ul className="text-[11px] text-slate-400 grid grid-cols-1 sm:grid-cols-3 gap-x-3">
      <li>全部：{it.scopes.all.value == null ? '无数据' : signed(it.scopes.all.value, 2, unit)}（{it.scopes.all.nRecords} 行{!retest && it.processedN === 0 && it.passthroughN > 0 ? '，均为原图返回，不是“提升 0”' : ''}）</li>
      {retest ? <li className="sm:col-span-2">无法判定 {it.undeterminedN} 条（本批没有图像，不区分实际处理与原图返回）</li> : <>
        <li>实际处理：{it.scopes.processed.value == null ? '无数据' : signed(it.scopes.processed.value, 2, unit)}（{it.processedN} 条{it.negativeProcessedN ? `，其中负提升 ${it.negativeProcessedN}` : ''}；不含 E-05）</li>
        <li>原图返回：{pt.value == null ? '无均值' : signed(pt.value, 2, unit)}（未处理 {it.passthroughN} 条；MeanPassthrough）{it.undeterminedN ? ` · 无法判定 ${it.undeterminedN} 条（单独计数）` : ''}{it.naChangedN ? ` · E-05 标为不适用但有改动 ${it.naChangedN} 条（不计入实际处理/原图返回）` : ''}</li>
      </>}
    </ul>
    <p className="text-[10px] text-slate-500">{ciSourceText(main)}</p>
  </div>;
};

const CASE_BUTTONS: { kind: 'median' | 'worst' | 'passthrough'; label: string; param: string }[] = [
  { kind: 'median', label: '中位案例（默认）', param: '' },
  { kind: 'worst', label: '最差一条（负提升）', param: '@worst' },
  { kind: 'passthrough', label: '原图返回样例', param: '@passthrough' },
];

export const GlobalEvaluation: React.FC<Props> = ({ model, batches, glyph, filters, setFilters, onSelectBatch }) => {
  const { batch, primary, primaryGrade, caseRow } = model;
  const retest = batch.kind === 'retest';
  const psnrPanel = model.panels.find(p => p.metric.key === 'psnr');
  const items = psnrPanel?.items || [];
  const neg = items.filter(i => { const s = i.scopes[i.primaryScope]; return s.sign === 'negative' && s.ciReliable; });
  const pos = items.filter(i => { const s = i.scopes[i.primaryScope]; return s.sign === 'positive' && s.ciReliable; });
  const panes = triptychPanes(model, caseRow);
  const [showAbs, setShowAbs] = useState(false);
  const filterText = `${SPLIT_LABELS[model.split]} · ${degradationLabel(model.degradation)}${model.sample ? ` · 仅 ${model.sample}` : ''}`;
  const caseStatus = caseRow ? appliedStatus(caseRow).status : null;
  return <div className="space-y-4" data-testid="global-evaluation">
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
      {/* L1 研究总览 */}
      <section aria-label="研究总览" className="xl:col-span-5 rounded-xl border border-gold/20 bg-[#0f1418] p-4 space-y-3">
        <header className="flex flex-wrap items-baseline justify-between gap-2">
          <h3 className="font-serif text-gold text-base" data-testid="batch-title">研究总览 · {batch.title}</h3>
          <span className="text-[11px] text-slate-400">{filterText}</span>
        </header>
        <article className="rounded-lg border border-slate-700/80 bg-black/20 p-3 space-y-1.5" data-testid="conclusion-primary">
          <div className="flex items-center justify-between gap-2"><p className="text-xs text-slate-400">结论 1 · {methodLabel(model.method)} 相对退化输入的配对 ΔPSNR</p><GradeBadge grade={primaryGrade.grade} reasons={primaryGrade.reasons} /></div>
          {primary ? <ScopeTriple it={primary} retest={retest} /> : <p className="text-sm text-slate-400">当前筛选没有该方法的记录。</p>}
          <p className="text-[11px] text-slate-500">分级依据：{primaryGrade.reasons.join('；')}。“提升”只在配对增益 CI 下界 &gt; 0 且文物数 ≥ 3 时使用。</p>
        </article>
        <article className="rounded-lg border border-slate-700/80 bg-black/20 p-3 space-y-1" data-testid="conclusion-negative">
          <div className="flex items-center justify-between gap-2"><p className="text-xs text-slate-400">结论 2 · 各方法相对输入的配对增益（主口径）</p><GradeBadge grade={items.length ? '有限支持' : '未评测'} reasons={['受控退化；逐方法见图中 CI']} /></div>
          {items.length ? <p className="text-sm">CI 下界 &gt; 0（可写“提升”）：<span className="text-celadon-light">{pos.length ? pos.map(i => methodLabel(i.method)).join('、') : '无'}</span>；CI 上界 &lt; 0（下降）：<span className="text-cinnabar-light font-bold">{neg.length ? neg.map(i => methodLabel(i.method)).join('、') : '无'}</span>；其余为 CI 跨 0、不可靠或无数据。</p> : <p className="text-sm">当前筛选没有可比记录。</p>}
          <p className="text-[11px] text-slate-500">负提升全部保留；不跨批次求均值。跨批次比较见下方“跨批次对照”，并逐条检查 C1–C4。</p>
        </article>
        <article className="rounded-lg border border-slate-700/80 bg-black/20 p-3 space-y-1" data-testid="conclusion-unevaluated">
          <div className="flex items-center justify-between gap-2"><p className="text-xs text-slate-400">结论 3 · 未评测项</p><GradeBadge grade="未评测" /></div>
          <p className="text-sm">真实拓本修复质量：未评测（无配对参考，不报告 PSNR/SSIM）。</p>
          <p className="text-sm" data-testid="glyph-topk-line">古碑识字 Top-1 / Top-3：{glyph.state === 'ok' ? glyphEvaluationText(glyph.data, 'with-topk') : glyph.state === 'loading' ? '读取中…' : `状态不可用（${glyph.state === 'missing' || glyph.state === 'error' ? glyph.message : ''}）`}</p>
        </article>
        <p className="text-[11px] text-gold-light/90 border-l-2 border-gold/60 pl-2">{REFERENCE_NOTE}</p>
        {retest && <p className="text-[11px] text-cinnabar-light border-l-2 border-cinnabar pl-2">同一批文物复测，不是独立验证：本批 14 件文物与 v2-text 相同，且参与过 v2.1 的误差分析；结论最高为“有限支持”。本批没有图像，全部行“无法判定”，不显示有效处理率、原图返回率，也不显示 dev/test 划分。</p>}
        {batch.kind === 'historical' && <p className="text-[11px] text-cinnabar-light border-l-2 border-cinnabar pl-2">{batch.registry.historicalWarning || batch.registry.statusReasons?.join('；')}</p>}
        {!model.splitAvailable && !retest && <p className="text-[11px] text-slate-300 border-l-2 border-slate-500 pl-2">本批未划分 dev/test：记录不带 split 字段，不能当作测试集解读，也不混进 test（E-07）。</p>}
        {model.splitAvailable && model.split === 'test' && <p className="text-[11px] text-slate-400">当前为测试组；阈值与参数不得依测试组结果调整。</p>}
        {model.notes.length > 0 && <ul className="text-[11px] text-slate-300 list-disc pl-4 space-y-0.5">{model.notes.map(n => <li key={n}>{n}</li>)}</ul>}
      </section>

      {/* L2 视觉对照 */}
      <section aria-label="修复效果视觉对照" className="xl:col-span-7 rounded-xl border border-gold/20 bg-[#0f1418] p-4 space-y-2">
        <header className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="font-serif text-gold text-base">视觉对照</h3>
          {panes && model.caseRows.length > 0 && <div className="flex flex-wrap items-center gap-1 text-[11px]" role="group" aria-label="代表案例">
            {CASE_BUTTONS.map(b => { const has = !!model.representative[b.kind]; const on = model.caseKind === b.kind; return <button key={b.kind} type="button" disabled={!has} aria-pressed={on} data-testid={`case-${b.kind}`} onClick={() => setFilters({ case: b.param })} className={`px-1.5 py-0.5 rounded border ${on ? 'bg-gold text-slate-950 border-gold' : has ? 'border-slate-600 text-slate-300' : 'border-slate-800 text-slate-600 cursor-not-allowed'}`} title={has ? '' : '当前筛选下没有这类记录'}>{b.label}</button>; })}
            <label className="text-slate-300 ml-1">逐条
              <select aria-label="单次实验记录" value={caseRow && model.caseKind === 'explicit' ? caseKeyOf(caseRow) : ''} onChange={e => setFilters({ case: e.target.value })} className="ml-1 bg-slate-950 border border-slate-700 rounded p-1 max-w-[15rem]">
                <option value="">（按规则选择）</option>
                {model.caseRows.map(r => <option key={caseKeyOf(r)} value={caseKeyOf(r)}>{r.sampleId} · {degradationLabel(r.degradation)} {r.strength ?? ''} · {APPLIED_LABELS[appliedStatus(r).status]}</option>)}
              </select></label>
          </div>}
        </header>
        {panes == null
          ? <div className="rounded-md border border-dashed border-slate-600 p-6 text-sm text-slate-300" data-testid="no-images">本批次只保存了数值，没有保存对比图像；不使用其他批次的图代替，也不从本批选取对照案例。可在“失败案例与不确定性”中查看逐条数值。</div>
          : !caseRow ? <div className="rounded-md border border-dashed border-slate-600 p-6 text-sm text-slate-300" data-testid="no-case">当前筛选下 {methodLabel(model.method)} 没有{model.caseKind === 'worst' || filters.case === '@worst' ? '负提升的实际处理' : model.caseKind === 'passthrough' || filters.case === '@passthrough' ? '原图返回的' : ''}记录。</div>
          : <SyncedTriptych testId="experiment-triptych" panes={panes} diffPair={['in', 'out']} height={248} knownPassthrough={caseStatus != null && isPassthroughStatus(caseStatus) && caseRow.statusSource === 'DER'}
              meta={<>实验 <code>{batch.id}</code> · 方法 {methodLabel(caseRow.method)}（{caseRow.algorithmVersion || '版本未记录'}）· case <code>{caseKeyOf(caseRow)}</code> · seed {caseRow.seed ?? '未记录'} · 状态 <StatusTag status={caseStatus!} source={caseRow.statusSource} detail={caseRow.appliedStatusDetail} /></>} />}
        {panes != null && <p className="text-[11px] text-slate-400" data-testid="case-rule">{model.caseKind === 'explicit' ? '当前为手动选择的记录。' : `当前为“${CASE_BUTTONS.find(b => b.kind === model.caseKind)?.label || '—'}”。`}{model.representative.rule}（本筛选实际处理 {model.representative.processedN} 条）</p>}
        {caseRow && <p className="text-[11px] text-slate-400">本条：PSNR {caseRow.psnr?.toFixed(2) ?? '未评测'}（输入 {model.caseBaseline?.psnr?.toFixed(2) ?? caseRow.inputPsnr?.toFixed(2) ?? '—'}）· SSIM {caseRow.ssim?.toFixed(3) ?? '未评测'} · 边缘 F1 {caseRow.edgeF1?.toFixed(3) ?? '未评测'} · DER 改动 {caseRow.changedPixelRatio != null ? `${(caseRow.changedPixelRatio * 100).toFixed(2)}% 像素，最大差 ${caseRow.maxAbsDiff ?? '—'}` : '无法判定'} · 输出 SHA {shortSha(caseRow.outputSha256)}</p>}
      </section>
    </div>

    {/* L3 横向比较 */}
    <section aria-label="算法横向比较" className="rounded-xl border border-gold/20 bg-[#0f1418] p-4 space-y-2">
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="font-serif text-gold text-base">算法横向比较 · 相对退化输入的配对增益</h3>
        <p className="text-[11px] text-slate-400">每个量纲单独一轴，轴含 0 与全部负值；柱 = 主口径（{retest ? '全部（本批无法判定原图返回）' : '实际处理'}）文物均值，须 = 按文物聚类 95% CI（文物 &lt; 3 或空组不画），点 = 每件文物。提示框并列“实际处理 / 全部 / 原图返回”三口径。点击柱选方法，点击点看该文物。</p>
      </header>
      <MethodComparisonChart testId="method-comparison-chart" panels={model.panels} methods={model.methods} selectedMethod={model.method}
        onSelectMethod={m => setFilters({ method: m, case: '' })} onSelectSample={(s, m) => setFilters({ method: m, sample: s, case: '' })} height={Math.max(250, 44 + model.methods.length * 26)} />
      <p className="text-[11px] text-slate-500">原图返回判据：{model.der.source ? `DER ${model.der.criterion}（${model.der.source}）` : '前端兜底：输出与输入 SHA-256 相同（DER 未接入）'}；“无法判定”的行单独计数，不归入任何一类。CI：{model.ci ? `${model.ci.source}（未按单件文物筛选时以文件为准；细笔画误差与耗时无文件，用前端临时口径）` : '临时口径，前端计算，待替换为 derived/ci_by_artifact'}。仅同批内比较。</p>
      <button type="button" onClick={() => setShowAbs(v => !v)} className="text-[11px] text-gold underline print:hidden">{showAbs ? '收起' : '展开'}与历史 summary 对照的数值（MeanAll 口径）</button>
      {showAbs && <AbsoluteTable model={model} />}
    </section>

    <ExperimentExplorer model={model} onOpenCase={(key, method) => setFilters({ method, case: key })} />
    <CrossBatchComparison model={model} batches={batches} compareId={filters.cmp || ''} onCompare={id => setFilters({ cmp: id })} />
    {retest ? <HeldoutComparison model={model} /> : <RetestTeaser batches={batches} onSelect={onSelectBatch} />}
    <Reproducibility model={model} />
  </div>;
};

const AbsoluteTable: React.FC<{ model: GlobalModel }> = ({ model }) => {
  const rows = (model.detail.summary || []).filter(s => (model.split === 'none' || s.split === model.split) && (!('degradation' in s) || s.degradation === model.degradation));
  if (!rows.length) return <p className="text-[11px] text-slate-400">本批次 summary 没有与当前筛选对应的分组。</p>;
  return <div className="overflow-x-auto"><table className="text-[11px] text-left" data-testid="summary-reference-table"><caption className="text-left text-slate-400 mb-1">后端 summary 原值（MeanAll 口径，含原图返回；只作对照，不作主数字）</caption>
    <thead><tr className="text-slate-400">{['划分', '退化', '方法', 'n', 'PSNR 均值', 'PSNR CI95', 'SSIM 均值'].map(h => <th key={h} className="pr-3 py-1 font-normal">{h}</th>)}</tr></thead>
    <tbody>{rows.map((s, i) => <tr key={i} className="border-t border-slate-800"><td className="pr-3">{String(s.split ?? '未划分')}</td><td className="pr-3">{String(s.degradation ?? '全部')}</td><td className="pr-3">{methodLabel(String(s.method))}</td><td className="pr-3">{String(s.n ?? '—')}</td><td className="pr-3">{typeof s.psnrMean === 'number' ? s.psnrMean.toFixed(3) : '未评测'}</td><td className="pr-3">{Array.isArray(s.psnrCI95) ? (s.psnrCI95 as number[]).map(v => v.toFixed(2)).join(' ~ ') : '无'}</td><td>{typeof s.ssimMean === 'number' ? s.ssimMean.toFixed(3) : '未评测'}</td></tr>)}</tbody></table></div>;
};

const KNOWN_ISSUES = [
  'E-05：历史批次中 notch 的不适用分支仍有轻微像素改动（已在新代码修复），由 DER 标为“标为不适用但有改动”。',
  'E-06：不同批次 summary 的汇总口径不同（是否计入不适用行），跨批比较一律按统一口径重算。',
  'E-07：旧页面默认选最后一个批次、把无 split 的行混进 test；本页默认批次只认后端 defaultForReport，无 split 显示“本批未划分”。',
  'E-08 / E-10：馆藏运行的实际生效参数（effectiveParameters）尚未记录时显示“未记录实际生效参数”。',
];

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
      <div><dt className="text-slate-500">原图返回判据版本</dt><dd>{model.der.criterion ? <code>{model.der.criterion}</code> : '前端兜底 byteIdentical（DER 未接入）'}</dd></div>
      <div><dt className="text-slate-500">派生状态来源</dt><dd>{model.der.source ? <code className="break-all">{model.der.source}</code> : (model.der.problem || '未接入')}</dd></div>
      <div className="md:col-span-2"><dt className="text-slate-500">CI 来源</dt><dd>{model.ci ? <code className="break-all">{model.ci.source}</code> : '临时口径：前端计算，待替换为 derived/ci_by_artifact'}</dd></div>
      <div className="md:col-span-2"><dt className="text-slate-500">源码 SHA-256</dt><dd className="break-all">{env.codeSha256 ? Object.entries(env.codeSha256).map(([f, h]) => <span key={f} className="mr-3"><code>{f}</code> {String(h).slice(0, 12)}…</span>) : '未记录'}</dd></div>
    </dl>
    <p className="flex flex-wrap gap-3">{['results.json', 'results.csv', 'summary.csv'].map(k => <a key={k} className="text-gold underline" href={ReportApi.exportUrl(reg.id, k)} download>导出 {k}</a>)}<span className="text-slate-500">applied_status.csv/json 下载：待后端提供接口（REPORT_DATA_SPEC §7）</span></p>
    <details><summary className="cursor-pointer text-slate-400">已知限制（E-05 / E-06 / E-07 / E-08 / E-10）</summary><ul className="list-disc pl-4 mt-1 space-y-0.5">{KNOWN_ISSUES.map(t => <li key={t}>{t}</li>)}</ul></details>
    {limitations.length > 0 && <details><summary className="cursor-pointer text-slate-400">本批次限制说明（{limitations.length} 条）与来源（{d.sources?.length ?? 0} 件）</summary>
      <ul className="list-disc pl-4 mt-1 space-y-0.5">{limitations.map(t => <li key={t}>{t}</li>)}</ul>
      <ul className="mt-1 space-y-0.5">{(d.sources || []).map(s => <li key={s.id}><a className="text-gold underline" href={s.sourceUrl} target="_blank" rel="noreferrer">{s.id}</a> · {s.license || '许可未记录'} · 源图 SHA {shortSha(s.sourceSha256)}</li>)}</ul>
    </details>}
  </section>;
};
