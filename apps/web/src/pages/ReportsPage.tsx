/**
 * 算法评测报告页：只负责组装。数据访问集中在 components/reports/data/。
 * 共享选择（steleId / runId / experimentId / batch）来自 App props（R1-6），变更通过 onRunChange / onExperimentChange 交回 App，
 * 由 state/urlState.ts 写回 URL；报告页内部筛选用 components/reports/reportFilters.ts。
 */
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { SteleItem } from '../types/stele';
import { ReportContextBar } from '../components/reports/ReportContextBar';
import { GlobalEvaluation } from '../components/reports/GlobalEvaluation';
import { FailureCasesPanel } from '../components/reports/FailureCasesPanel';
import { ArtifactRunReport } from '../components/reports/ArtifactRunReport';
import { ReportPrintLayout } from '../components/reports/ReportPrintLayout';
import { useReportFilters, readFilters } from '../components/reports/reportFilters';
import { BatchInfo, CiLookup, evaluationSummaryText, GlyphEvaluation, mergeDer, orderBatches, ReportApi, resolveBatch, RunInfo, RunReport, RunSelection, sortRuns } from '../components/reports/data/reportData';
import type { BatchDetail, DerFile, Derived, Diagnosis, Loadable, CiFile } from '../components/reports/data/types';
import { useGlobalModel } from '../components/reports/data/globalModel';
import { nowShanghaiIso } from '../components/reports/format';

interface Props {
  stele: SteleItem;
  onNavigate: (tab: string) => void;
  runId?: string | null;
  onRunChange?: (runId: string | null) => void;
  experimentId?: string | null;
  batch?: string | null;
  onExperimentChange?: (experimentId: string | null, batch?: string | null) => void;
  /** App-level resolution of the URL experimentId (R2-8): 'unknown' must render an empty state, not a fallback. */
  experimentStatus?: 'none' | 'resolving' | 'ok' | 'unknown' | 'unavailable';
}
const loading = { state: 'loading' } as const;
type Keyed<T> = { id: string; value: Loadable<T> };

export const ReportsPage: React.FC<Props> = ({ stele, onNavigate, runId: sharedRunId, onRunChange, experimentId: sharedExperimentId, batch: sharedBatch, onExperimentChange }) => {
  useEffect(() => { document.body.classList.add('printing-report'); return () => document.body.classList.remove('printing-report'); }, []);
  const [filters, setFilters] = useReportFilters();
  const [batches, setBatches] = useState<Loadable<BatchInfo[]>>(loading);
  // 按 experimentId 存放，切换批次时不会把上一批的行与新批次的 ID 混用
  const [detail, setDetail] = useState<Keyed<BatchDetail> | null>(null);
  const [der, setDer] = useState<Keyed<Derived<DerFile>> | null>(null);
  const [ciFile, setCiFile] = useState<Keyed<Derived<CiFile>> | null>(null);
  const [diagnosis, setDiagnosis] = useState<Keyed<Diagnosis> | null>(null);
  const [runs, setRuns] = useState<Loadable<RunInfo[]>>(loading);
  const [selection, setSelection] = useState<Loadable<{ runSelection: RunSelection | null; runId: string }>>(loading);
  const [report, setReport] = useState<Loadable<RunReport> | null>(null);
  const [glyph, setGlyph] = useState<Loadable<GlyphEvaluation>>(loading);
  const [exportedAt, setExportedAt] = useState(nowShanghaiIso());
  const [initialView] = useState<'global' | 'artifact'>(() => { const f = readFilters(); return f.view === 'artifact' || f.view === 'global' ? f.view : sharedRunId ? 'artifact' : 'global'; });

  useEffect(() => {
    let live = true;
    ReportApi.batches().then(r => { if (live) setBatches(r.state === 'ok' ? { state: 'ok', data: orderBatches(r.data) } : r); });
    ReportApi.glyphEvaluation().then(r => { if (live) setGlyph(r); });
    return () => { live = false; };
  }, []);

  // experimentId 权威；batch 只是别名；未知 ID 显示真实空状态，不回落；默认只认 defaultForReport
  const resolution = useMemo(() => batches.state === 'ok' ? resolveBatch(batches.data, sharedExperimentId, sharedBatch) : null, [batches, sharedExperimentId, sharedBatch]);
  const experimentId = resolution?.state === 'ok' ? resolution.id : '';
  const batchInfo = batches.state === 'ok' ? batches.data.find(b => b.id === experimentId) : undefined;
  useEffect(() => {
    if (resolution?.state !== 'ok' || !batchInfo) return;
    const dir = batchInfo.registry.directory || null;
    if (sharedExperimentId !== resolution.id || (sharedBatch || null) !== dir) onExperimentChange?.(resolution.id, dir);
  }, [resolution, batchInfo, sharedExperimentId, sharedBatch, onExperimentChange]);

  useEffect(() => {
    if (!experimentId) return;
    let live = true; const dir = batchInfo?.registry.directory;
    setDetail({ id: experimentId, value: loading }); setDer({ id: experimentId, value: loading }); setCiFile({ id: experimentId, value: loading }); setDiagnosis({ id: experimentId, value: loading });
    ReportApi.batch(experimentId).then(r => { if (live) setDetail({ id: experimentId, value: r }); });
    ReportApi.appliedStatus(experimentId, dir).then(r => { if (live) setDer({ id: experimentId, value: r }); });
    ReportApi.ciByArtifact(experimentId, dir).then(r => { if (live) setCiFile({ id: experimentId, value: r }); });
    ReportApi.diagnosis(experimentId).then(r => { if (live) setDiagnosis({ id: experimentId, value: r }); });
    return () => { live = false; };
  }, [experimentId, batchInfo]);

  // 本件运行：列表仅供选择器；默认运行必须走 getReportSelection（R1-1），禁止 items[0]（否则 han-caoquan 会落到 legacy）。
  useEffect(() => {
    let live = true; setRuns(loading);
    ReportApi.runs(stele.id).then(r => { if (live) setRuns(r.state === 'ok' ? { state: 'ok', data: sortRuns(r.data) } : r); });
    return () => { live = false; };
  }, [stele.id]);
  const requestedRunId = sharedRunId || '';
  const defaultRule = useRef(new Map<string, RunSelection>());
  const runBelongs = runs.state === 'ok' && (!requestedRunId || runs.data.some(x => x.run.runId === requestedRunId));
  useEffect(() => {
    if (runs.state !== 'ok') return;
    if (!runBelongs) { setSelection({ state: 'missing', status: 404, message: `URL 中的 runId ${requestedRunId} 不在《${stele.title}》的运行记录中` }); return; }
    let live = true; setSelection(loading);
    ReportApi.selection(stele.id, requestedRunId || undefined).then(r => {
      if (!live) return;
      if (r.state !== 'ok') { setSelection(r); return; }
      let rs = r.data.runSelection; const id = rs?.runId || r.data.run?.runId || '';
      // 默认运行写回 URL 后会以 explicit 再取一次；同一文物、同一 runId 时保留后端最初给出的默认规则，便于说明“为什么是这条”
      const key = `${stele.id}|${id}`;
      if (rs && rs.rule !== 'explicit') defaultRule.current.set(key, rs); else if (rs && defaultRule.current.has(key)) rs = defaultRule.current.get(key)!;
      setSelection({ state: 'ok', data: { runSelection: rs, runId: id } });
    });
    return () => { live = false; };
  }, [runs.state, runBelongs, stele.id, stele.title, requestedRunId]);
  const runId = selection.state === 'ok' ? selection.data.runId : '';
  // 把后端选定的默认运行交回 App，使 URL 可深链（App 用 replaceState 写 runId）
  useEffect(() => { if (runId && runId !== sharedRunId) onRunChange?.(runId); }, [runId, sharedRunId, onRunChange]);

  const view: 'global' | 'artifact' = filters.view === 'artifact' || filters.view === 'global' ? filters.view : initialView;
  useEffect(() => {
    if (!runId || view !== 'artifact') { if (!runId) setReport(null); return; }
    let live = true; setReport(loading);
    ReportApi.report(stele.id, runId).then(r => { if (live) setReport(r); });
    return () => { live = false; };
  }, [stele.id, runId, view]);

  useEffect(() => { if (filters.view !== view) setFilters({ view }); }, [filters.view, view, setFilters]);
  const panel: 'overview' | 'failures' = filters.panel === 'failures' ? 'failures' : 'overview';

  const detailNow = detail && detail.id === experimentId ? detail.value : loading;
  const derNow = der && der.id === experimentId ? der.value : loading;
  const ciNow = ciFile && ciFile.id === experimentId ? ciFile.value : loading;
  const diagnosisNow: Loadable<Diagnosis> = diagnosis && diagnosis.id === experimentId ? diagnosis.value : loading;
  const merged = useMemo(() => detailNow.state === 'ok' && derNow.state !== 'loading' ? mergeDer(detailNow.data, derNow) : null, [detailNow, derNow]);
  const ciLookup: CiLookup | null = useMemo(() => ciNow.state === 'ok' ? { file: ciNow.data.file, source: ciNow.data.source } : null, [ciNow]);
  const model = useGlobalModel(detailNow.state === 'ok' ? detailNow.data : null, batchInfo, merged, ciNow.state === 'loading' ? null : ciLookup, filters);

  const selectRun = (id: string) => { onRunChange?.(id || null); setFilters({ view: 'artifact' }); };
  const selectBatch = (b: BatchInfo) => { onExperimentChange?.(b.id, b.registry.directory || null); setFilters({ case: '', sample: '', split: '', deg: '', cmp: '' }); };

  const exportJson = () => {
    const at = nowShanghaiIso(); setExportedAt(at);
    const run = report?.state === 'ok' ? report.data.run : null;
    const tag = model ? `${model.batch.shortName}` : '未选批次';
    const data = {
      reportId: run ? `RM-${stele.id}-${run.runId}` : `RM-${stele.id}-未选择运行`, exportedAt: at, view, url: window.location.href,
      stele: { id: stele.id, title: stele.title, dynasty: stele.dynasty, originalYear: stele.originalYear || stele.year, rubbingPeriod: stele.rubbingPeriod, collectionInstitution: stele.collectionInstitution || stele.museum, collectionNumber: stele.collectionNumber, sourceUrl: stele.sourceUrl, license: stele.license },
      runId: run?.runId || null, runSelection: selection.state === 'ok' ? selection.data.runSelection : null, algorithmVersion: run?.algorithmVersion || null, inputImageSha256: run?.inputImageSha256 || null,
      workingImage: run?.workingImage || null, randomSeed: run?.randomSeed ?? null, outputSha256: run?.outputSha256 || null, imageRoles: run?.imageRoles || null,
      changeStatus: run ? { isPassthrough: run.isPassthrough ?? null, changedPixelCount: run.changedPixelCount ?? null, changedPixelRatio: run.changedPixelRatio ?? null, maxAbsDiff: run.maxAbsDiff ?? null, passthroughCriterion: run.passthroughCriterion ?? null, passthroughSource: (run as { passthroughSource?: string | null }).passthroughSource ?? null, grayChangedPixelCount: (run as { grayChangedPixelCount?: number | null }).grayChangedPixelCount ?? null, grayChangedPixelRatio: (run as { grayChangedPixelRatio?: number | null }).grayChangedPixelRatio ?? null, grayMaxAbsDiff: (run as { grayMaxAbsDiff?: number | null }).grayMaxAbsDiff ?? null, grayPassthroughCriterion: (run as { grayPassthroughCriterion?: string | null }).grayPassthroughCriterion ?? null, effectiveParameters: run.effectiveParameters ?? null } : null,
      evaluationSummary: evaluationSummaryText(run),
      adaptiveDiagnostics: run?.adaptiveDiagnostics || null, algorithmParameters: run?.algorithmParameters || null,
      startedAt: run?.startedAt || null, finishedAt: run?.finishedAt || null, processingTimeMs: run?.processing_time_ms ?? null, outputImages: run?.outputImages || null,
      evaluationStatus: run?.evaluationStatus || 'not_run', evaluationMetrics: run?.evaluationMetrics || null, diagnosticMetrics: run?.diagnosticMetrics || null,
      inferenceRecords: report?.state === 'ok' ? report.data.inferenceRecords || [] : [], sourceRecords: report?.state === 'ok' ? report.data.sourceRecords || [] : [],
      experiment: model ? {
        experimentId: model.batch.id, name: model.batch.shortName, directory: model.batch.registry.directory, kind: model.batch.kind,
        filters: { split: model.split, degradation: model.degradation, method: model.method, sample: model.sample || null, caseId: model.caseRow ? caseIdOf(model.caseRow) : null, caseSelection: model.caseKind },
        appliedStatusSource: model.der.source || '前端兜底（SHA-256 比较）', ciSource: model.ci?.source || '前端临时口径',
        conclusion: model.primary ? { method: model.method, primaryScope: model.primary.primaryScope, scopes: model.primary.scopes, n: model.primary.n, processedN: model.primary.processedN, passthroughN: model.primary.passthroughN, undeterminedN: model.primary.undeterminedN, grade: model.primaryGrade.grade, gradeReasons: model.primaryGrade.reasons } : null,
        deltaByMethod: model.panels.filter(p => p.metric.delta).map(p => ({ metric: p.metric.key, items: p.items.map(i => ({ method: i.method, primaryScope: i.primaryScope, all: strip(i.scopes.all), processed: strip(i.scopes.processed), passthrough: strip(i.scopes.passthrough), n: i.n, processedN: i.processedN, passthroughN: i.passthroughN, undeterminedN: i.undeterminedN, negativeProcessedN: i.negativeProcessedN })) })),
        representativeRule: model.representative.rule, limitations: model.batch.registry.limitations || [], notes: model.notes,
      } : null,
      glyphEvaluation: glyph.state === 'ok' ? glyph.data : null,
      note: '无配对真值时，诊断变化量不代表修复质量；残字建议须经人工核实。',
    };
    const href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a'); link.href = href; link.download = `${data.reportId}-${tag}.json`.replace(/[\\/:*?"<>|\s]+/g, '_'); link.click();
    setTimeout(() => URL.revokeObjectURL(href), 1000);
  };
  const print = () => { setExportedAt(nowShanghaiIso()); setTimeout(() => window.print(), 50); };

  const batchState = batches.state !== 'ok' ? batches : resolution?.state === 'unknown' ? null : resolution?.state === 'no-default' ? null : detailNow;
  return <div className="min-h-screen bg-[#0A0D12] text-slate-100 px-3 lg:px-6 py-3 space-y-3">
    <div className="report-screen space-y-3">
      <ReportContextBar stele={stele} view={view} panel={panel} runs={runs} runId={runId} selection={selection} batches={batches} experimentId={experimentId} model={model}
        setFilters={setFilters} onSelectRun={selectRun} onSelectBatch={selectBatch} onExportJson={exportJson} onPrint={print} onNavigate={onNavigate} />
      {view === 'global' ? <section aria-label="全局评测" className="space-y-3">
        <p className="text-[11px] text-slate-400">全局评测：受控退化实验的批次级结果，与当前文物《{stele.title}》无关。</p>
        {resolution?.state === 'unknown' ? <div role="alert" data-testid="unknown-experiment" className="rounded-xl border border-cinnabar/50 bg-[#140f0e] p-5 text-sm text-slate-200">没有登记 {resolution.param === 'experimentId' ? '实验 ID' : '批次别名'} <code>{resolution.requested}</code> 的实验批次。不会改用其他批次；请在上方“实验批次”中选择。</div>
          : resolution?.state === 'no-default' ? <div role="status" className="rounded-xl border border-slate-600 p-5 text-sm text-slate-300">后端没有标记默认报告批次（defaultForReport），请在上方“实验批次”中选择。</div>
          : batchState && batchState.state !== 'ok' ? (batchState.state === 'loading' ? <p role="status" className="text-gold">正在读取实验批次…</p> : <p role="alert" className="text-cinnabar-light">实验数据读取失败：{batchState.message}</p>)
          : !model ? <p role="status" className="text-gold">正在读取派生状态…</p>
          : panel === 'failures' ? <FailureCasesPanel model={model} diagnosis={diagnosisNow} setFilters={setFilters} />
          : <GlobalEvaluation model={model} batches={batches.state === 'ok' ? batches.data : []} glyph={glyph} filters={filters} setFilters={setFilters} onSelectBatch={selectBatch} />}
      </section> : <ArtifactRunReport stele={stele} runs={runs} runId={runId} selection={selection} report={report} glyph={glyph} batchDetail={detailNow.state === 'ok' ? detailNow.data : null} batchName={batchInfo?.title || ''} onNavigate={onNavigate} />}
    </div>
    <ReportPrintLayout model={model} stele={stele} runId={runId} report={report} glyph={glyph} exportedAt={exportedAt} view={view} />
  </div>;
};

const caseIdOf = (r: { caseId?: string; sampleId: string; degradation: string; strength?: number }) => r.caseId || `${r.sampleId}|${r.degradation}|${r.strength ?? ''}`;
const strip = (s: { value: number | null; ci: [number, number] | null; ciReliable: boolean; sign: unknown; nArtifacts: number; nRecords: number; ciSource: string; ciNote: string | null }) => ({ value: s.value, ci95: s.ci, ciReliable: s.ciReliable, sign: s.sign, nArtifacts: s.nArtifacts, nRecords: s.nRecords, ciSource: s.ciSource, ciNote: s.ciNote });
