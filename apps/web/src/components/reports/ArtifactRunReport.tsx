/**
 * 本件处理报告（steleId + runId 驱动）· 金石文化与算法处理鉴定档案界面。
 * 遵循 SPEC §8 文案与科研真实性规范：
 * - isPassthrough=true → “本次未改动原图”；passthroughSource=computed-on-read → 注明“读取时校验”；
 * - 保持所有 data-testid、数据契约与异常状态完整无损。
 */
import React, { useCallback, useState } from 'react';
import type { SteleItem } from '../../types/stele';
import { roleText } from '../../types/stele';
import type { GlyphEvaluation, RunInfo, RunReport, RunSelection } from './data/reportData';
import { evaluationSummaryText, glyphEvaluationText, runAdaptive, runAlgorithmOutputModeView, runOutcome } from './data/reportData';
import { formatGlyphBBox, mappedSourceBBox } from './data/glyphInference';
import type { BatchDetail, Loadable } from './data/types';
import { formatTime, shortSha } from './format';
import { DiffStats, SyncedTriptych } from './SyncedTriptych';
import { writeFilters } from './reportFilters';

interface Props {
  stele: SteleItem;
  runs: Loadable<RunInfo[]>;
  runId: string;
  selection: Loadable<{ runSelection: RunSelection | null; runId: string }>;
  report: Loadable<RunReport> | null;
  glyph: Loadable<GlyphEvaluation>;
  batchDetail: BatchDetail | null;
  batchName: string;
  onNavigate: (tab: string) => void;
}

const FEATURE_LABELS: Record<string, string> = {
  noiseSigmaMAD: '噪声 σ（MAD）',
  impulseFraction: '脉冲噪声比例',
  highFrequencyEnergyFraction: '高频能量占比',
  localContrastRMS: '局部对比度 RMS',
  laplacianVariance: '拉普拉斯方差',
  thinStrokeRisk: '细笔画风险',
  dynamicRange: '动态范围',
};

const INTERMEDIATE: [string, string][] = [
  ['frequency_spectrum', '频域谱'],
  ['binary_skeleton', '前景骨架'],
  ['contour', '边缘轮廓'],
  ['character_skeleton', '字形骨架'],
  ['cinnabar_rubbing', '朱砂视图'],
];

export const ArtifactRunReport: React.FC<Props> = ({
  stele,
  runs,
  runId,
  selection,
  report,
  glyph,
  batchDetail,
  batchName,
  onNavigate,
}) => {
  const info = runs.state === 'ok' ? runs.data.find(x => x.run.runId === runId) : undefined;
  const run = report?.state === 'ok' && report.data.run?.runId === runId ? report.data.run : null;
  const [pixel, setPixel] = useState<DiffStats | null>(null);
  const onDiff = useCallback((s: DiffStats | null) => setPixel(s), []);
  const outcome = run ? runOutcome(run) : null;
  const confirmedSame = pixel?.sameSize && pixel.changed === 0;
  const passthrough = outcome?.mode === 'passthrough';
  const conflict = !!(pixel?.sameSize && outcome && outcome.mode !== 'undetermined' && (pixel.changed === 0) !== passthrough);
  const eff = run?.effectiveParameters as (Record<string, unknown> & { ignoredRequestParameters?: string[] }) | null | undefined;
  const effMissing = !eff && (run as { effectiveParametersUnavailableReason?: string | null } | null)?.effectiveParametersUnavailableReason;
  const adaptive = run ? runAdaptive(run) : null;
  const algoMode = run ? runAlgorithmOutputModeView(run) : null;
  const features = (adaptive?.features || {}) as Record<string, unknown>;
  const gate = (adaptive?.fidelityGate || null) as Record<string, unknown> | null;
  const inBatch = batchDetail ? batchDetail.rows.filter(r => r.sampleId === stele.id) : [];
  const reportId = run ? `RM-${stele.id}-${run.runId}` : `RM-${stele.id}-未选择运行`;

  const [copiedId, setCopiedId] = useState(false);
  const copyReportId = () => {
    navigator.clipboard?.writeText(reportId).then(() => {
      setCopiedId(true);
      setTimeout(() => setCopiedId(false), 2000);
    });
  };

  return (
    <article
      className="artifact-report-container scroll-mt-36"
      data-testid="artifact-report"
      aria-label="本件处理报告"
    >
      {/* 头部：档案编号与文物身份 */}
      <header className="artifact-header">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-xs font-medium px-2 py-0.5 rounded bg-[#c8a86b]/15 text-[#dfc187] border border-[#c8a86b]/30">
              单件文物处理档案
            </span>
            <span className="text-xs text-slate-400">
              {stele.dynasty} · 原刻 {stele.originalYear || stele.year}
            </span>
          </div>
          <h3 className="mt-2 text-2xl font-serif font-bold text-[#f7f5ef]">
            本件处理报告 ·《{stele.title}》
          </h3>
          <p className="artifact-header-meta">
            馆藏：{stele.collectionInstitution || stele.museum} · 拓本年代：{stele.rubbingPeriod || '未核定'} · 编号：{stele.collectionNumber || '未提供'} · 书体：{stele.script_type || '未核定'}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1.5 self-start">
          <div className="flex items-center gap-2">
            <span className="artifact-header-id font-mono">
              编号：{reportId}
            </span>
            <button
              onClick={copyReportId}
              type="button"
              className="text-xs px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
              title="复制报告编号"
            >
              {copiedId ? '已复制' : '复制'}
            </button>
          </div>
          <span className="text-[11px] text-[#8c9d90]">文物标识代码：{stele.id}</span>
        </div>
      </header>

      {/* 异常与载入状态提示 */}
      {runs.state === 'error' && (
        <div role="alert" className="p-4 rounded-lg bg-[#c83c23]/15 border border-[#c83c23]/40 text-[#f5a898] text-sm mb-4">
          后端服务不可用，无法读取运行记录（{runs.message}）。这不等于“本件尚未执行”。
        </div>
      )}
      {runs.state === 'missing' && (
        <div role="alert" className="p-4 rounded-lg bg-[#c83c23]/15 border border-[#c83c23]/40 text-[#f5a898] text-sm mb-4">
          {runs.message}
        </div>
      )}
      {runs.state === 'ok' && runs.data.length === 0 && (
        <div className="p-6 rounded-lg bg-slate-900/60 border border-slate-800 text-center my-6 space-y-3">
          <p className="text-base text-slate-300">《{stele.title}》尚未执行图像修复处理。</p>
          <p className="text-xs text-slate-500">本件尚无真实算法输出，亦无配对真值评测。可前往工作台执行频空域联合去噪。</p>
          <button
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-[#dfc187] text-[#0f1613] font-medium text-sm hover:bg-[#ecd39f] transition-colors"
            onClick={() => onNavigate('workbench')}
          >
            前往工作台执行处理 →
          </button>
        </div>
      )}
      {selection.state === 'missing' && (
        <div role="alert" className="p-4 rounded-lg bg-[#c83c23]/15 border border-[#c83c23]/40 text-[#f5a898] text-sm mb-4" data-testid="run-not-found">
          {selection.message}。不会改用其他运行；请在上方“本件运行”中重新选择。
        </div>
      )}
      {selection.state === 'error' && (
        <div role="alert" className="p-4 rounded-lg bg-[#c83c23]/15 border border-[#c83c23]/40 text-[#f5a898] text-sm mb-4">
          {selection.message}
        </div>
      )}
      {runs.state === 'ok' && runs.data.length > 0 && !runId && selection.state === 'ok' && (
        <div className="p-4 rounded-lg bg-[#c8a86b]/10 border border-[#c8a86b]/30 text-[#dfc187] text-sm mb-4">
          {runs.data.every(x => x.legacy)
            ? '本件仅有历史旧版未验证（legacy）运行，不作为默认推荐；请在上方“本件运行”下拉框中选择查看。'
            : '请在上方工具栏“本件运行”中选择一条运行记录。'}
        </div>
      )}
      {runId && report?.state === 'loading' && (
        <div className="py-12 text-center text-slate-400 text-sm">
          正在读取本件算法运行报告…
        </div>
      )}
      {runId && report && (report.state === 'error' || report.state === 'missing') && (
        <div
          role="alert"
          className="p-4 rounded-lg bg-[#c83c23]/15 border border-[#c83c23]/40 text-[#f5a898] text-sm mb-4"
          data-testid="artifact-report-status"
          data-http={report.state === 'missing' ? String(report.status) : 'error'}
          data-status={
            /stele_retired/.test(report.message)
              ? 'stele_retired'
              : /run_not_found/.test(report.message)
              ? 'run_not_found'
              : /stele_not_found/.test(report.message)
              ? 'stele_not_found'
              : /backend_unavailable/.test(report.message)
              ? 'backend_unavailable'
              : 'error'
          }
        >
          运行报告读取失败：{report.message}
        </div>
      )}

      {/* 真实运行结果呈现 */}
      {run && outcome && (
        <>
          {/* Act 1: 核心判定与执行成效卡片 */}
          <div
            className={`artifact-verdict-card ${
              passthrough
                ? 'is-passthrough'
                : outcome.mode === 'undetermined'
                ? 'is-undetermined'
                : 'is-processed'
            }`}
            data-testid="run-outcome"
            data-outcome={outcome.mode}
            data-source={(run as { passthroughSource?: string | null }).passthroughSource || ''}
          >
            <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
              <h4 className="artifact-verdict-title">
                {outcome.title}
                {outcome.mode === 'passthrough' && (run as { passthroughSource?: string | null }).passthroughSource === 'computed-on-read' && (
                  <span
                    className="text-xs rounded border border-[#dfc187]/60 text-[#dfc187] bg-[#c8a86b]/10 px-2 py-0.5 font-normal tracking-wide"
                    data-testid="computed-on-read"
                  >
                    读取时校验
                  </span>
                )}
                {info?.legacy && (
                  <span className="text-xs rounded bg-[#c83c23] text-white px-2 py-0.5 font-normal">
                    旧版未验证（legacy）
                  </span>
                )}
              </h4>
              <span className="text-xs text-slate-400">
                算法版本：<code className="text-[#dfc187]">{run.algorithmVersion}</code>
              </span>
            </div>

            <p className="text-sm text-[#e6ece7] leading-relaxed mb-2">
              {outcome.detail}
              {outcome.changeText ? ` ${outcome.changeText}。` : ''}
            </p>

            <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-[#98a89c] pt-2 border-t border-white/5">
              <span data-testid="gray-change">
                {outcome.grayText || '灰度域改动：后端尚未返回 grayChangedPixelCount（真实空状态，不推断）。'}
              </span>
              <span>
                判定基准：{outcome.criterion}
                {run.comparedImages ? `；比较对象 ${(run.comparedImages as string[]).join(' / ')}` : ''}
                {outcome.source ? `；来源：${outcome.source}` : ''}
              </span>
              {pixel?.sameSize && (
                <span className="text-slate-300">
                  浏览器像素校验：
                  {confirmedSame
                    ? `0 像素不同（${pixel.width}×${pixel.height}）`
                    : `改动 ${(pixel.ratio * 100).toFixed(2)}% 像素，最大差 ${pixel.max}`}
                </span>
              )}
            </div>

            {effMissing && (
              <p className="text-xs text-[#f08573] mt-2" data-testid="eff-params-unavailable">
                实际生效参数不可用：{effMissing}。系统严禁伪造参数。
              </p>
            )}
            {conflict && (
              <div role="alert" className="text-xs text-[#f08573] bg-[#c83c23]/10 p-2 rounded mt-2 border border-[#c83c23]/30">
                注意：后端判定与浏览器逐像素比较结果不一致，请研究人员人工复核。
              </div>
            )}

            <p className="text-xs text-[#b8c8bc] mt-2 pt-2 border-t border-white/5" data-testid="evaluation-summary">
              评测说明：{evaluationSummaryText(run)}
            </p>
          </div>

          {/* Act 2: 核心处理前后图像对照（置于前部，大尺寸展示） */}
          <section className="artifact-triptych-frame">
            <div className="flex justify-between items-center mb-2 px-1">
              <div>
                <h4 className="font-serif text-base font-semibold text-[#f0ede6]">
                  真实拓本处理前后对比
                </h4>
                <p className="text-xs text-[#8c9c90]">
                  真实碑拓无合成配对真值，仅并排或滑杆对照输入原图与算法输出；不计算伪造的 PSNR/SSIM。
                </p>
              </div>
              <div className="text-xs text-[#c8a86b]">
                支持同步平移、缩放与局部差异观测
              </div>
            </div>
            <SyncedTriptych
              testId="run-triptych"
              height={360}
              onDiffStats={onDiff}
              diffPair={['original', 'restored']}
              knownPassthrough={passthrough}
              panes={[
                {
                  key: 'original',
                  label: '工作输入原图（original.png）',
                  src: run.outputImages?.original || null,
                  sha: run.outputSha256?.original,
                  tone: 'input',
                  emptyReason: '该运行未留存工作输入原图',
                },
                {
                  key: 'restored',
                  label: passthrough
                    ? '本次未改动原图（restored.png 逐像素相同）'
                    : outcome.mode === 'undetermined'
                    ? '算法输出（restored.png，未能判定是否改动）'
                    : '算法已改动像素（restored.png）',
                  src: run.outputImages?.restored || run.restored_image || null,
                  sha: run.outputSha256?.restored,
                  tone: passthrough ? 'passthrough' : 'output',
                  emptyReason: '该运行未留存算法输出图',
                },
              ]}
              meta={<>真实拓本比对 · 拓片字符结构与石花斑驳保留核验</>}
            />
          </section>

          {/* Act 3: 运行过程指标与决策链 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
            {/* 决策链与保真门控 */}
            <section className="artifact-section-card">
              <h4>自适应决策链与保真门控</h4>
              {algoMode && (
                <div
                  className={`rounded-lg border p-3 mb-3 text-xs ${
                    algoMode.provided && algoMode.mode === 'processed'
                      ? 'border-[#2eb88a]/40 bg-[#2eb88a]/10 text-[#d8f2e7]'
                      : algoMode.provided
                      ? 'border-[#c83c23]/40 bg-[#c83c23]/10 text-[#fcdad5]'
                      : 'border-slate-700 bg-slate-900/40 text-slate-300'
                  }`}
                  data-testid="algorithm-output-mode"
                  data-mode={algoMode.code || ''}
                  data-provided={algoMode.provided ? 'true' : 'false'}
                >
                  <p className="font-semibold text-sm">
                    {algoMode.title}
                    {algoMode.code ? <span className="ml-2 font-mono text-xs opacity-80">[{algoMode.code}]</span> : null}
                  </p>
                  <p className="mt-1 text-slate-300">{algoMode.detail}</p>
                  {adaptive?.selectedOutput != null && adaptive.selectedOutput !== '' && (
                    <p className="mt-1 font-mono text-[11px] text-[#dfc187]">
                      算法层输出标记：{String(adaptive.selectedOutput)}
                    </p>
                  )}
                </div>
              )}

              {adaptive?.decisions?.length ? (
                <div className="space-y-1.5 text-xs text-slate-300 mb-3">
                  <p className="text-[#8c9d90] font-medium mb-1">执行算子步骤：</p>
                  <ol className="list-decimal pl-5 space-y-1">
                    {adaptive.decisions.map((d, i) => (
                      <li key={i}>
                        <code className="text-[#dfc187] bg-black/40 px-1 py-0.5 rounded">{d.operator}</code>
                        {d.reason ? <span className="ml-2 text-slate-300">：{d.reason}</span> : ''}
                      </li>
                    ))}
                  </ol>
                </div>
              ) : (
                <p className="text-xs text-slate-400 mb-3">
                  该运行未记录自适应动态决策（采用固定算子路径或历史运行）。
                </p>
              )}

              {gate ? (
                <div className="p-2.5 rounded bg-black/30 border border-white/5 text-xs text-slate-300">
                  <span className="font-medium text-[#dfc187]">保真门控结果：</span>
                  <span className={`ml-1 font-semibold ${gate.accepted === true ? 'text-[#2eb88a]' : gate.accepted === false ? 'text-[#e05d44]' : 'text-slate-400'}`}>
                    {gate.accepted === true ? '通过' : gate.accepted === false ? '拒绝' : '—'}
                  </span>
                  {' · '}强边缘保留 {typeof gate.strongEdgeRetention === 'number' ? gate.strongEdgeRetention.toFixed(3) : '—'}
                  {' · '}平均改动 {typeof gate.meanAbsoluteChange === 'number' ? gate.meanAbsoluteChange.toFixed(3) : '—'}
                  <p className="text-[11px] text-slate-500 mt-1">
                    {String(gate.basis || '')}（基于启发式金石保真规则，非统计检验）
                  </p>
                </div>
              ) : (
                <p className="text-xs text-slate-500">本运行未记录保真门控指标。</p>
              )}
            </section>

            {/* 运行参数与耗时概览 */}
            <section className="artifact-section-card">
              <h4>运行元数据与无参考诊断</h4>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs mb-3">
                <div>
                  <dt className="text-[#8c9d90]">耗时：</dt>
                  <dd className="font-mono text-sm font-semibold text-[#f0ede6]">
                    {run.processing_time_ms != null ? `${run.processing_time_ms} ms` : '未记录'}
                  </dd>
                </div>
                <div>
                  <dt className="text-[#8c9d90]">随机种子：</dt>
                  <dd className="font-mono text-sm font-semibold text-[#f0ede6]">
                    {run.randomSeed ?? '未记录'}
                  </dd>
                </div>
                <div>
                  <dt className="text-[#8c9d90]">执行时间：</dt>
                  <dd className="text-slate-300">{formatTime(run.startedAt)}</dd>
                </div>
                <div>
                  <dt className="text-[#8c9d90]">结束时间：</dt>
                  <dd className="text-slate-300">{formatTime(run.finishedAt)}</dd>
                </div>
              </dl>

              {Object.keys(features).length > 0 ? (
                <div>
                  <p className="text-xs font-medium text-[#dfc187] mb-1.5">无参考诊断特征（非修复准确率）：</p>
                  <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
                    {Object.entries(FEATURE_LABELS)
                      .filter(([k]) => typeof features[k] === 'number')
                      .map(([k, l]) => (
                        <div key={k} className="flex justify-between border-b border-white/5 py-0.5">
                          <dt className="text-[#8c9d90]">{l}</dt>
                          <dd className="font-mono text-slate-200">{(features[k] as number).toFixed(4)}</dd>
                        </div>
                      ))}
                  </dl>
                </div>
              ) : (
                <p className="text-xs text-slate-500">未记录无参考诊断特征。</p>
              )}
            </section>
          </div>

          {/* 中间产物展台 */}
          {INTERMEDIATE.some(([k]) => run.outputImages?.[k]) && (
            <section className="artifact-section-card mb-4">
              <h4>本次运行的真实中间处理产物</h4>
              <div className="artifact-intermediate-strip">
                {INTERMEDIATE.map(([k, l]) =>
                  run.outputImages?.[k] ? (
                    <figure key={k}>
                      <img
                        src={run.outputImages[k]}
                        alt={l}
                        loading="lazy"
                        onError={e => {
                          e.currentTarget.hidden = true;
                          e.currentTarget.parentElement!.dataset.imageError = '图像不可用';
                        }}
                      />
                      <figcaption title={`${l} · SHA ${run.outputSha256?.[k]}`}>
                        {l}
                        <br />
                        <span className="font-mono text-[9px] opacity-75">
                          {shortSha(run.outputSha256?.[k])}
                        </span>
                      </figcaption>
                    </figure>
                  ) : null
                )}
              </div>
            </section>
          )}

          {/* Act 4: 考据证据、参数与完整核查详情（默认折叠抽屉） */}
          <div className="space-y-3 pt-2">
            {/* 详细参数核验 */}
            <details className="studio-details">
              <summary>查看详细算法参数与请求配置</summary>
              <div className="p-3 bg-black/40 rounded border border-white/5 text-xs space-y-2 mt-2">
                <div>
                  <p className="font-semibold text-[#dfc187]">实际生效参数（Effective Parameters）：</p>
                  {eff ? (
                    <p className="font-mono text-xs break-all text-slate-300 mt-1" data-testid="effective-parameters">
                      {Object.entries(eff)
                        .filter(([k]) => k !== 'ignoredRequestParameters')
                        .map(([k, v]) => `${k}=${typeof v === 'object' ? JSON.stringify(v) : String(v)}`)
                        .join(' · ')}
                    </p>
                  ) : (
                    <p className="text-slate-500 mt-1" data-testid="effective-parameters">
                      未记录实际生效参数（effectiveParameters 为空）。
                    </p>
                  )}
                </div>
                <div className="pt-2 border-t border-white/5">
                  <p className="font-semibold text-[#dfc187]">请求参数列表：</p>
                  <p className="font-mono text-xs break-all text-slate-300 mt-1">
                    {Object.entries(run.algorithmParameters || {})
                      .filter(([k]) => k !== 'stele_id')
                      .map(([k, v]) => {
                        const ignored = eff?.ignoredRequestParameters?.includes(k);
                        return (
                          <span key={k} className={ignored ? 'opacity-50 line-through' : ''}>
                            {k}={String(v ?? '—')}{ignored ? '（自适应未采纳）' : ''} ·{' '}
                          </span>
                        );
                      })}
                  </p>
                </div>
              </div>
            </details>

            {/* 残字推演与人工确认 */}
            <details className="studio-details">
              <summary>残字推演候选与人工确认记录（{report?.state === 'ok' && report.data.inferenceRecords ? report.data.inferenceRecords.length : 0} 条）</summary>
              <div className="p-3 bg-black/40 rounded border border-white/5 text-xs mt-2">
                {report?.state === 'ok' && report.data.inferenceRecords?.length ? (
                  <ul className="divide-y divide-white/5">
                    {report.data.inferenceRecords.map((item, i) => (
                      <li key={item.inferenceId || i} className="py-2 first:pt-0 last:pb-0">
                        <div className="flex justify-between items-baseline mb-1">
                          <span className="font-medium text-[#f0ede6]">
                            推演记录 #{item.inferenceId} · 来源：{item.source} · 状态：{item.status}
                          </span>
                          <span className="text-xs text-[#dfc187]">
                            人工采纳：{item.adoptedGlyph || '暂无'}
                          </span>
                        </div>
                        <p className="text-slate-300 mb-1">
                          推荐候选（仅供学术参考，非确凿释读）：
                          {item.candidates.map(c => `${c.glyph}（依据：${c.scoreBasis}）`).join('、') || '无置信候选'}
                        </p>
                        <p className="font-mono text-[11px] text-[#8c9d90]" data-testid="glyph-inference-r1">
                          bbox {formatGlyphBBox(item.bbox)} · mappedSourceBBox {formatGlyphBBox(mappedSourceBBox(item))}
                          {item.roi?.mappedInsideSource == null ? '' : ` · 映射在源图内=${item.roi.mappedInsideSource ? '是' : '否'}`}
                          {' · '}输入 SHA {shortSha(item.inputImageSha256)} · 裁切 SHA {shortSha(item.cropSha256)}
                        </p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-slate-400">本运行未关联合成残字推演记录；无人工确认释读结果。</p>
                )}
              </div>
            </details>

            {/* 图像 SHA 与工作图溯源 */}
            <details className="studio-details">
              <summary>图像密码学哈希与缩放尺度留痕</summary>
              <div className="p-3 bg-black/40 rounded border border-white/5 text-xs font-mono space-y-1.5 mt-2">
                <p className="text-slate-300">
                  <span className="text-[#8c9d90]">输入 SHA-256：</span>
                  <span className="break-all">{run.inputImageSha256 || '未记录'}</span>
                </p>
                <p className="text-slate-300">
                  <span className="text-[#8c9d90]">工作图尺度：</span>
                  {run.workingImage
                    ? `源 ${run.workingImage.sourceShape?.join('×')} → 工作图 ${run.workingImage.workingShape?.join('×')}（缩放比例 ${run.workingImage.scale}，插值方式 ${run.workingImage.interpolation}）`
                    : '未记录'}
                </p>
              </div>
            </details>

            {/* 馆藏考据与历史溯源 */}
            <details className="studio-details">
              <summary>馆藏出处、撰文书丹与影像授权</summary>
              <div className="p-3 bg-black/40 rounded border border-white/5 text-xs text-slate-300 space-y-1.5 mt-2">
                <p>
                  撰文：{roleText(stele.inscriptionAuthor, stele.authorVerification)}；
                  书丹：{roleText(stele.calligrapher, stele.calligrapherVerification)}；
                  碑主/墓主：{roleText(stele.steleSubject, stele.steleSubjectVerification)}。
                </p>
                <p>
                  拓本影像品相：{stele.imageCondition || '待人工复核'}（{stele.imageConditionReviewStatus || '自动初筛，待人工复核'}）；
                  影像许可：{stele.license || '需核查'}。
                </p>
                {stele.sourceUrl && (
                  <p>
                    官方出处：<a href={stele.sourceUrl} target="_blank" rel="noreferrer" className="underline text-[#dfc187] break-all">{stele.sourceUrl}</a>
                  </p>
                )}
              </div>
            </details>

            {/* 古碑识字能力说明 */}
            <div className="p-3 rounded bg-black/20 border border-white/5 text-xs text-slate-400">
              <p className="text-[#dfc187] font-medium mb-1">古碑文字识读状态：</p>
              <p data-testid="artifact-glyph-evaluation">
                {glyph.state === 'ok'
                  ? glyphEvaluationText(glyph.data, 'short')
                  : glyph.state === 'loading'
                  ? '读取中…'
                  : `识字评测状态不可用（${glyph.message}）。`}
              </p>
              <p className="text-[11px] text-slate-500 mt-1">
                图像去噪增强与文字释读属于不同处理层级；在缺乏配对真值的情形下，不得将图像指标等同于文字识别率。
              </p>
            </div>

            {/* 本件与全局实验关联 */}
            <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded bg-black/20 border border-white/5 text-xs">
              <span className="text-slate-300">
                {batchDetail ? (
                  inBatch.length ? (
                    <>
                      当前批次「{batchName}」中收录本件 {inBatch.length} 条测试样本（分组：
                      {Array.from(new Set(inBatch.map(r => r.split || '未划分'))).join('、')}）。
                    </>
                  ) : (
                    <>
                      当前批次「{batchName}」中未收录 sampleId = <code>{stele.id}</code> 的样本。
                    </>
                  )
                ) : (
                  '实验批次数据未载入。'
                )}
              </span>
              {batchDetail && inBatch.length > 0 && (
                <button
                  type="button"
                  className="px-3 py-1 rounded bg-[#c8a86b]/15 text-[#dfc187] border border-[#c8a86b]/30 hover:bg-[#c8a86b]/25 transition-colors"
                  onClick={() => writeFilters({ view: 'global', sample: stele.id, case: '' })}
                >
                  在全局评测中筛选本件 →
                </button>
              )}
            </div>
          </div>
        </>
      )}

      {/* 底部金石学考据学术免责 */}
      <footer className="border-t border-[#c8a86b]/20 mt-6 pt-3 text-[11px] text-[#7d8d82] flex justify-between items-center flex-wrap gap-2">
        <span>本报告如实记录本次算法运行数据与考据资料。图像去噪清晰不等于恢复原碑石原貌；文字释读须由专业金石学者人工复核。</span>
        <span className="font-serif text-[#c8a86b]/60">墨韵智考 · 金石档案</span>
      </footer>
    </article>
  );
};
