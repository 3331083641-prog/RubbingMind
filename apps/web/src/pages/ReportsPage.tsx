/**
 * 算法评测报告页：只负责组装。数据访问集中在 components/reports/data/，状态与 URL 同步。
 * 分层：全局评测（experimentId 驱动，与当前文物无关）/ 本件处理报告（steleId + runId 驱动）。
 */
import React, { useEffect, useMemo, useState } from 'react';
import { SteleItem } from '../types/stele';
import { ReportContextBar } from '../components/reports/ReportContextBar';
import { GlobalEvaluation } from '../components/reports/GlobalEvaluation';
import { FailureCasesPanel } from '../components/reports/FailureCasesPanel';
import { ArtifactRunReport } from '../components/reports/ArtifactRunReport';
import { ReportPrintLayout } from '../components/reports/ReportPrintLayout';
import { useUrlState, runIdForStele, readUrlState } from '../components/reports/useReportUrlState';
import { batchByDirectory, BatchInfo, defaultBatchId, defaultRunId, GlyphEvaluation, orderBatches, ReportApi, RunInfo, RunReport, sortRuns } from '../components/reports/data/reportData';
import type { BatchDetail, Diagnosis, Loadable } from '../components/reports/data/types';
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
}
const loading = { state: 'loading' } as const;

export const ReportsPage: React.FC<Props> = ({ stele, onNavigate }) => {
  useEffect(() => { document.body.classList.add('printing-report'); return () => document.body.classList.remove('printing-report'); }, []);
  const [url, setUrl] = useUrlState();
  const [batches, setBatches] = useState<Loadable<BatchInfo[]>>(loading);
  const [detail, setDetail] = useState<Loadable<BatchDetail>>(loading);
  const [diagnosis, setDiagnosis] = useState<Loadable<Diagnosis>>(loading);
  const [runs, setRuns] = useState<Loadable<RunInfo[]>>(loading);
  const [report, setReport] = useState<Loadable<RunReport> | null>(null);
  const [glyph, setGlyph] = useState<Loadable<GlyphEvaluation>>(loading);
  const [exportedAt, setExportedAt] = useState(nowShanghaiIso());
  // 首次进入：URL 指定 view 就用它；否则从工作台带来了本件 runId → 本件报告，其余 → 全局评测
  const [initialView] = useState<'global' | 'artifact'>(() => { const s = readUrlState(); return s.view === 'artifact' || s.view === 'global' ? s.view : (s.steleId === stele.id && s.runId ? 'artifact' : 'global'); });

  // 批次清单 + 识字评测状态（与文物无关）
  useEffect(() => {
    let live = true;
    ReportApi.batches().then(r => { if (live) setBatches(r.state === 'ok' ? { state: 'ok', data: orderBatches(r.data) } : r); });
    ReportApi.glyphEvaluation().then(r => { if (live) setGlyph(r); });
    return () => { live = false; };
  }, []);

  // experimentId：URL → batch(目录名) → 默认（禁止默认同批复测/历史批次）
  const experimentId = useMemo(() => {
    if (batches.state !== 'ok') return '';
    const list = batches.data;
    if (url.experimentId && list.some(b => b.id === url.experimentId)) return url.experimentId;
    const byDir = url.batch ? batchByDirectory(list, url.batch) : undefined;
    return byDir || defaultBatchId(list);
  }, [batches, url.experimentId, url.batch]);
  const batchInfo = batches.state === 'ok' ? batches.data.find(b => b.id === experimentId) : undefined;

  useEffect(() => {
    if (!experimentId) return;
    let live = true; setDetail(loading); setDiagnosis(loading);
    ReportApi.batch(experimentId).then(r => { if (live) setDetail(r); });
    ReportApi.diagnosis(experimentId).then(r => { if (live) setDiagnosis(r); });
    return () => { live = false; };
  }, [experimentId]);

  // 本件运行：按可解析时间排序，legacy 排后且不作默认
  useEffect(() => {
    let live = true; setRuns(loading); setReport(null);
    ReportApi.runs(stele.id).then(r => { if (live) setRuns(r.state === 'ok' ? { state: 'ok', data: sortRuns(r.data) } : r); });
    return () => { live = false; };
  }, [stele.id]);
  const urlRunId = runIdForStele(url, stele.id);
  const runId = runs.state === 'ok' ? defaultRunId(runs.data, urlRunId) : '';

  useEffect(() => {
    if (!runId) { setReport(null); return; }
    let live = true; setReport(loading);
    ReportApi.report(stele.id, runId).then(r => { if (live) setReport(r); });
    return () => { live = false; };
  }, [stele.id, runId]);

  const view: 'global' | 'artifact' = url.view === 'artifact' || url.view === 'global' ? url.view : initialView;
  // 把当前生效的状态写回 URL（可深链、刷新后由 hook 恢复；跨文物时 runId 被替换，不串号）
  useEffect(() => {
    if (runs.state !== 'ok' || batches.state !== 'ok') return;
    setUrl({ tab: 'reports', steleId: stele.id, runId, experimentId, batch: batchInfo?.registry.directory || '', view });
  }, [runs.state, batches.state, stele.id, runId, experimentId, batchInfo, setUrl, view]);

  const panel: 'overview' | 'failures' = url.panel === 'failures' ? 'failures' : 'overview';
  const model = useGlobalModel(detail.state === 'ok' ? detail.data : null, batchInfo, url);

  const exportJson = () => {
    const at = nowShanghaiIso(); setExportedAt(at);
    const run = report?.state === 'ok' ? report.data.run : null;
    const psnr = model?.panels.find(p => p.metric.key === 'psnr');
    const data = {
      reportId: run ? `RM-${stele.id}-${run.runId}` : `RM-${stele.id}-未选择运行`, exportedAt: at, view, url: window.location.href,
      stele: { id: stele.id, title: stele.title, dynasty: stele.dynasty, originalYear: stele.originalYear || stele.year, rubbingPeriod: stele.rubbingPeriod, collectionInstitution: stele.collectionInstitution || stele.museum, collectionNumber: stele.collectionNumber, sourceUrl: stele.sourceUrl, license: stele.license },
      runId: run?.runId || null, algorithmVersion: run?.algorithmVersion || null, inputImageSha256: run?.inputImageSha256 || null,
      workingImage: run?.workingImage || null, randomSeed: run?.randomSeed ?? null, outputSha256: run?.outputSha256 || null, imageRoles: run?.imageRoles || null,
      adaptiveDiagnostics: run?.adaptiveDiagnostics || null, algorithmParameters: run?.algorithmParameters || null,
      startedAt: run?.startedAt || null, finishedAt: run?.finishedAt || null, processingTimeMs: run?.processing_time_ms ?? null, outputImages: run?.outputImages || null,
      evaluationStatus: run?.evaluationStatus || 'not_run', evaluationMetrics: run?.evaluationMetrics || null, diagnosticMetrics: run?.diagnosticMetrics || null,
      inferenceRecords: report?.state === 'ok' ? report.data.inferenceRecords || [] : [], sourceRecords: report?.state === 'ok' ? report.data.sourceRecords || [] : [],
      experiment: model ? {
        experimentId: model.batch.id, displayName: model.batch.displayName, directory: model.batch.registry.directory, kind: model.batch.kind,
        filters: { split: model.split, degradation: model.degradation, method: model.method, sample: model.sample || null, caseId: model.caseRow ? (model.caseRow.caseId || null) : null },
        conclusion: { method: model.method, deltaPsnr: model.primary?.value ?? null, ci95: model.primary?.ci ?? null, nArtifacts: model.primary?.nArtifacts ?? 0, scope: model.primary?.scope ?? null, grade: model.primaryGrade.grade, gradeReasons: model.primaryGrade.reasons },
        deltaByMethod: model.panels.filter(p => p.metric.delta).map(p => ({ metric: p.metric.key, items: p.items.map(i => ({ method: i.method, value: i.value, ci95: i.ci, nArtifacts: i.nArtifacts, nRecords: i.nRecords, n: i.n, processedN: i.processedN, passthroughN: i.passthroughN, undeterminedN: i.undeterminedN, negativeN: i.negativeN, meanAllIncludingPassthrough: i.meanAll })) })),
        psnrPanelPresent: !!psnr, limitations: model.batch.registry.limitations || [], notes: model.notes,
        method: 'Δ = 输出 − 同 case 退化输入（thinStrokeMae 取 输入 − 输出）；先按文物平均再跨文物平均；CI 为文物 bootstrap 1000 次，种子 20261019；原图返回判据：输出与输入 SHA-256 相同（前端兜底）。',
      } : null,
      glyphEvaluation: glyph.state === 'ok' ? glyph.data : null,
      note: '无配对真值时，诊断变化量不代表修复质量；残字建议须经人工核实。',
    };
    const href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a'); link.href = href; link.download = `${data.reportId}.json`; link.click();
    setTimeout(() => URL.revokeObjectURL(href), 1000);
  };
  const print = () => { setExportedAt(nowShanghaiIso()); setTimeout(() => window.print(), 50); };

  return <div className="min-h-screen bg-[#0A0D12] text-slate-100 px-3 lg:px-6 py-3 space-y-3">
    <div className="report-screen space-y-3">
      <ReportContextBar stele={stele} view={view} panel={panel} runs={runs} runId={runId} batches={batches} experimentId={experimentId} model={model}
        setUrl={setUrl} onExportJson={exportJson} onPrint={print} onNavigate={onNavigate} />
      {view === 'global' ? <section aria-label="全局评测" className="space-y-3">
        <p className="text-[11px] text-slate-400">全局评测：受控退化实验的批次级结果，与当前文物《{stele.title}》无关。</p>
        {batches.state === 'error' || batches.state === 'missing' ? <p role="alert" className="text-cinnabar-light">实验登记不可用：{batches.message}</p>
          : detail.state === 'loading' || batches.state === 'loading' ? <p role="status" className="text-gold">正在读取实验批次…</p>
          : detail.state !== 'ok' ? <p role="alert" className="text-cinnabar-light">实验批次读取失败：{detail.message}</p>
          : model && (panel === 'failures' ? <FailureCasesPanel model={model} diagnosis={diagnosis} setUrl={setUrl} /> : <GlobalEvaluation model={model} glyph={glyph} setUrl={setUrl} />)}
      </section> : <ArtifactRunReport stele={stele} runs={runs} runId={runId} report={report} glyph={glyph} batchDetail={detail.state === 'ok' ? detail.data : null} batchName={batchInfo?.displayName || ''} setUrl={setUrl} onNavigate={onNavigate} />}
    </div>
    <ReportPrintLayout model={model} stele={stele} runId={runId} report={report} glyph={glyph} exportedAt={exportedAt} view={view} />
  </div>;
};
