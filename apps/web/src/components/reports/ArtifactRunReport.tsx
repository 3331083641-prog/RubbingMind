/**
 * 本件处理报告（steleId + runId 驱动，纸色背景），与全局评测分层。
 * SPEC §8 文案：isPassthrough=true → “本次未改动原图”（不显示“算法输出”或“实际处理已执行”）；
 * passthroughSource=computed-on-read → 注明“读取时校验”；null → “未能判定是否改动”。浏览器逐像素比较仅作补充确认。
 */
import React, { useCallback, useState } from 'react';
import type { SteleItem } from '../../types/stele';
import { roleText } from '../../types/stele';
import type { GlyphEvaluation, RunInfo, RunReport, RunSelection } from './data/reportData';
import { evaluationSummaryText, runAdaptive, runOutcome } from './data/reportData';
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

const FEATURE_LABELS: Record<string, string> = { noiseSigmaMAD: '噪声 σ（MAD）', impulseFraction: '脉冲噪声比例', highFrequencyEnergyFraction: '高频能量占比', localContrastRMS: '局部对比度 RMS', laplacianVariance: '拉普拉斯方差', thinStrokeRisk: '细笔画风险', dynamicRange: '动态范围' };
const INTERMEDIATE: [string, string][] = [['frequency_spectrum', '频谱'], ['binary_skeleton', '二值前景骨架'], ['contour', '边缘轮廓'], ['character_skeleton', '字形骨架'], ['cinnabar_rubbing', '朱砂视图']];

export const ArtifactRunReport: React.FC<Props> = ({ stele, runs, runId, selection, report, glyph, batchDetail, batchName, onNavigate }) => {
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
  const features = (adaptive?.features || {}) as Record<string, unknown>;
  const gate = (adaptive?.fidelityGate || null) as Record<string, unknown> | null;
  const inBatch = batchDetail ? batchDetail.rows.filter(r => r.sampleId === stele.id) : [];
  const reportId = run ? `RM-${stele.id}-${run.runId}` : `RM-${stele.id}-未选择运行`;

  return <article className="bg-[#eee4d2] text-[#30271d] rounded-xl p-5 md:p-8 space-y-5 scroll-mt-40" data-testid="artifact-report" aria-label="本件处理报告">
    <header className="border-b border-[#937d5d] pb-3 flex flex-wrap justify-between gap-2">
      <div><h3 className="text-xl font-serif font-bold">本件处理报告 ·《{stele.title}》</h3>
        <p className="text-sm">{stele.dynasty} · 原刻：{stele.originalYear || stele.year} · 文物 ID <code>{stele.id}</code></p></div>
      <p className="text-xs self-end">编号：{reportId}</p>
    </header>

    <section className="space-y-1 text-sm"><h4 className="font-bold">馆藏身份与出处</h4>
      <p>拓本年代：{stele.rubbingPeriod || '未核定'}；馆藏：{stele.collectionInstitution || stele.museum}；编号：{stele.collectionNumber || '未提供'}；类型：{stele.artifactType || '拓本'}；书体：{stele.script_type || '未核定'}。</p>
      <p>撰文：{roleText(stele.inscriptionAuthor, stele.authorVerification)}；书丹：{roleText(stele.calligrapher, stele.calligrapherVerification)}；碑主/墓主：{roleText(stele.steleSubject, stele.steleSubjectVerification)}。</p>
      <p>拓本影像损伤：{stele.imageCondition || '待人工复核'}（{stele.imageConditionReviewStatus || '自动初筛，待人工复核'}）。影像许可：{stele.license || '需核查'}。{stele.sourceUrl && <> 来源：<a href={stele.sourceUrl} className="underline break-all">{stele.sourceUrl}</a></>}</p>
    </section>

    <section className="space-y-2"><h4 className="font-bold">本次运行</h4>
      {runs.state === 'error' && <p role="alert" className="text-[#9E2813]">后端不可用，无法读取运行记录（{runs.message}）。这不等于“尚未执行”。</p>}
      {runs.state === 'missing' && <p className="text-[#9E2813]">{runs.message}</p>}
      {runs.state === 'ok' && runs.data.length === 0 && <p>本件尚未执行处理。没有真实运行输出，也没有配对真值评测。<button className="ml-2 underline" onClick={() => onNavigate('workbench')}>前往工作台</button></p>}
      {selection.state === 'missing' && <p role="alert" className="text-[#9E2813]" data-testid="run-not-found">{selection.message}。不会改用其他运行；请在上方“本件运行”中选择。</p>}
      {selection.state === 'error' && <p role="alert" className="text-[#9E2813]">{selection.message}</p>}
      {runs.state === 'ok' && runs.data.length > 0 && !runId && selection.state === 'ok' && <p className="text-[#7a5a14]">{runs.data.every(x => x.legacy) ? '本件只有旧版未验证（legacy）运行，不作默认显示；请在上方“本件运行”中手动选择。' : '请在上方“本件运行”中选择一条运行。'}</p>}
      {runId && report?.state === 'loading' && <p>读取运行报告…</p>}
      {runId && report && (report.state === 'error' || report.state === 'missing') && <p role="alert" className="text-[#9E2813]">运行报告读取失败：{report.message}</p>}
      {run && outcome && <>
        <div className={`rounded-lg border-2 p-3 ${passthrough ? 'border-[#C83C23] bg-[#C83C23]/10' : outcome.mode === 'undetermined' ? 'border-[#937d5d]' : 'border-[#3E8E7E] bg-[#3E8E7E]/10'}`} data-testid="run-outcome" data-outcome={outcome.mode} data-source={(run as { passthroughSource?: string | null }).passthroughSource || ''}>
          <p className="font-serif text-lg font-bold">{outcome.title}{outcome.mode === 'passthrough' && (run as { passthroughSource?: string | null }).passthroughSource === 'computed-on-read' && <span className="ml-2 align-middle text-xs rounded border border-[#7a5a14] text-[#7a5a14] px-1.5 py-0.5" data-testid="computed-on-read">读取时校验</span>}{info?.legacy && <span className="ml-2 align-middle text-xs rounded bg-[#9E2813] text-white px-1.5 py-0.5">旧版未验证（legacy）</span>}</p>
          <p className="text-sm">{outcome.detail}{outcome.changeText ? ` ${outcome.changeText}。` : ''}</p>
          <p className="text-[11px] text-[#5d4c35]" data-testid="gray-change">{outcome.grayText ? outcome.grayText : '灰度域改动：后端尚未返回 grayChangedPixelCount（真实空状态，不推断）。'}</p>
          {effMissing && <p className="text-[11px] text-[#9E2813]" data-testid="eff-params-unavailable">实际生效参数不可用：{effMissing}。不伪造参数。</p>}
          <p className="text-[11px] text-[#5d4c35]">{outcome.criterion}{run.comparedImages ? `；比较对象 ${(run.comparedImages as string[]).join(' / ')}` : ''}{outcome.source ? `；来源：${outcome.source}` : ''}</p>
          {pixel?.sameSize && <p className="text-[11px] text-[#5d4c35]">浏览器逐像素补充确认：{confirmedSame ? `0 像素不同（${pixel.width}×${pixel.height}）` : `改动 ${(pixel.ratio * 100).toFixed(2)}% 像素，最大差 ${pixel.max}`}。</p>}
          {conflict && <p role="alert" className="text-[11px] text-[#9E2813]">后端判定与浏览器逐像素比较不一致，请人工复核。</p>}
          <p className="text-[11px] text-[#5d4c35] mt-1" data-testid="evaluation-summary">评测说明：{evaluationSummaryText(run)}</p>
        </div>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-0.5 text-sm">
          <div><dt className="inline text-[#6b5a43]">运行 ID：</dt><dd className="inline"><code>{run.runId}</code></dd></div>
          <div><dt className="inline text-[#6b5a43]">算法版本：</dt><dd className="inline">{run.algorithmVersion}</dd></div>
          <div><dt className="inline text-[#6b5a43]">开始：</dt><dd className="inline" title={String(run.startedAt)}>{formatTime(run.startedAt)}</dd></div>
          <div><dt className="inline text-[#6b5a43]">结束：</dt><dd className="inline" title={String(run.finishedAt)}>{formatTime(run.finishedAt)}</dd></div>
          <div><dt className="inline text-[#6b5a43]">耗时：</dt><dd className="inline">{run.processing_time_ms != null ? `${run.processing_time_ms} ms` : '未记录'}</dd></div>
          <div><dt className="inline text-[#6b5a43]">随机种子：</dt><dd className="inline">{run.randomSeed ?? '未记录'}</dd></div>
          <div className="md:col-span-2"><dt className="inline text-[#6b5a43]">输入 SHA-256：</dt><dd className="inline break-all"><code>{run.inputImageSha256 || '未记录'}</code></dd></div>
          <div className="md:col-span-2"><dt className="inline text-[#6b5a43]">工作图：</dt><dd className="inline">{run.workingImage ? `源 ${run.workingImage.sourceShape?.join('×')} → 工作 ${run.workingImage.workingShape?.join('×')}（缩放 ${run.workingImage.scale}，${run.workingImage.interpolation}）` : '未记录'}</dd></div>
        </dl>
        <div className="rounded-lg bg-[#0A0D12] p-3 text-slate-100">
          <SyncedTriptych testId="run-triptych" height={300} onDiffStats={onDiff} diffPair={['original', 'restored']} knownPassthrough={passthrough}
            panes={[
              { key: 'original', label: '工作输入（original.png）', src: run.outputImages?.original || null, sha: run.outputSha256?.original, tone: 'input', emptyReason: '该运行没有保存工作输入图' },
              { key: 'restored', label: passthrough ? '本次未改动原图（restored.png 与输入逐像素相同）' : outcome.mode === 'undetermined' ? '输出（restored.png，未能判定是否改动）' : '算法已改动像素（restored.png）', src: run.outputImages?.restored || run.restored_image || null, sha: run.outputSha256?.restored, tone: passthrough ? 'passthrough' : 'output', emptyReason: '该运行没有保存输出图' },
            ]}
            meta={<>真实拓本没有配对参考，只能对照输入与输出；不计算 PSNR/SSIM。</>} />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 text-sm">
          <div><p className="font-bold text-xs mb-1">决策链（真实执行记录）</p>
            {adaptive?.decisions?.length ? <ol className="list-decimal pl-5 space-y-0.5">{adaptive.decisions.map((d, i) => <li key={i}><code>{d.operator}</code>{d.reason ? `：${d.reason}` : ''}</li>)}</ol> : <p className="text-[#6b5a43]">该运行没有记录自适应决策（固定参数路径或旧版运行）。</p>}
            {gate && <p className="text-xs mt-1">保真门控：{gate.accepted === true ? '通过' : gate.accepted === false ? '拒绝' : '—'}；强边缘保留 {typeof gate.strongEdgeRetention === 'number' ? gate.strongEdgeRetention.toFixed(3) : '—'}；平均改动 {typeof gate.meanAbsoluteChange === 'number' ? gate.meanAbsoluteChange.toFixed(3) : '—'}。{String(gate.basis || '')}（启发式规则，不是统计检验）</p>}
          </div>
          <div><p className="font-bold text-xs mb-1">无参考诊断特征（不是修复准确率）</p>
            {Object.keys(features).length ? <dl className="grid grid-cols-2 gap-x-3 text-xs">{Object.entries(FEATURE_LABELS).filter(([k]) => typeof features[k] === 'number').map(([k, l]) => <React.Fragment key={k}><dt className="text-[#6b5a43]">{l}</dt><dd>{(features[k] as number).toFixed(4)}</dd></React.Fragment>)}</dl> : <p className="text-xs text-[#6b5a43]">未记录。</p>}
            <p className="font-bold text-xs mt-2 mb-1">实际生效参数</p>
            {eff ? <p className="text-xs break-all" data-testid="effective-parameters">{Object.entries(eff).filter(([k]) => k !== 'ignoredRequestParameters').map(([k, v]) => `${k}=${typeof v === 'object' ? JSON.stringify(v) : String(v)}`).join(' · ')}</p> : <p className="text-xs text-[#6b5a43]" data-testid="effective-parameters">未记录实际生效参数（effectiveParameters 为空）。</p>}
            <p className="font-bold text-xs mt-2 mb-1">请求参数</p>
            <p className="text-xs break-all">{Object.entries(run.algorithmParameters || {}).filter(([k]) => k !== 'stele_id').map(([k, v]) => { const ignored = eff?.ignoredRequestParameters?.includes(k); return <span key={k} className={ignored ? 'text-[#9b8b74]' : ''}>{k}={String(v ?? '—')}{ignored ? '（自适应路径未使用）' : ''} · </span>; })}</p>
          </div>
        </div>
        <div><p className="font-bold text-xs mb-1">本次运行的真实中间产物</p>
          <div className="flex flex-wrap gap-3">{INTERMEDIATE.map(([k, l]) => run.outputImages?.[k] ? <figure key={k} className="w-36"><img src={run.outputImages[k]} alt={l} loading="lazy" className="w-36 h-36 object-contain bg-[#0A0D12] rounded" /><figcaption className="text-[10px] text-center">{l} · SHA {shortSha(run.outputSha256?.[k])}</figcaption></figure> : null)}</div>
        </div>
      </>}
    </section>

    <section className="space-y-1 text-sm"><h4 className="font-bold">残字推演与人工确认</h4>
      {report?.state === 'ok' && report.data.inferenceRecords?.length ? <ul className="list-disc pl-5">{report.data.inferenceRecords.map((item, i) => <li key={item.inferenceId || i} className="mb-1">
        <p>记录 {item.inferenceId} · {item.source} · 状态 {item.status} · 人工采纳：{item.adoptedGlyph || '无'}</p>
        <p className="text-xs">候选（仅为建议，不是碑文释读结论）：{item.candidates.map(c => `${c.glyph}（${c.scoreBasis}）`).join('、') || '无可靠候选'}</p>
      </li>)}</ul> : <p>没有与本运行关联的残字推演记录；没有人工确认结论。</p>}
    </section>
    <section className="space-y-1 text-sm"><h4 className="font-bold">古碑识字</h4>
      <p>{glyph.state === 'ok' ? `状态：${glyph.data.status === 'not_evaluated' ? '未评测' : glyph.data.status}；已核验标注 ${glyph.data.verifiedLabels} 条。${glyph.data.reason || ''}` : glyph.state === 'loading' ? '读取中…' : `识字评测状态不可用（${glyph.message}）。`}</p>
      <p className="text-xs">图像处理指标与识字是两项不同能力；没有配对真值时，不把 PSNR 或候选分数写成识别准确率。</p>
    </section>
    <section className="space-y-1 text-sm"><h4 className="font-bold">本件在全局实验中的记录</h4>
      {batchDetail ? (inBatch.length ? <p>当前批次「{batchName}」中有本件 {inBatch.length} 条记录（划分：{Array.from(new Set(inBatch.map(r => r.split || '未划分'))).join('、')}）。<button className="ml-2 underline" onClick={() => writeFilters({ view: 'global', sample: stele.id, case: '' })}>在全局评测中只看本件</button></p>
        : <p>当前批次「{batchName}」中没有 sampleId = <code>{stele.id}</code> 的记录。{stele.source_kind !== 'verified_review_v3' ? '核心演示样本与实验 sampleId 不在同一命名空间，ID 映射接口待后端提供。' : ''}</p>) : <p>实验批次未载入。</p>}
    </section>
    <footer className="border-t border-[#937d5d] pt-2 text-xs">本报告只描述此次处理与已有资料。图像变清晰不等于恢复原刻文字；任何释读结论须由具备领域知识的人员复核。</footer>
  </article>;
};
