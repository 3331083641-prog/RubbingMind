/**
 * 独立 A4 纵版打印布局：反映当前选择（批次 / 划分 / 退化 / 方法 / 文物 / 运行），含图号、图题、来源与局限。
 * 图表用离屏 ECharts（打印配色）渲染后转成静态图片，避免打印时画布尺寸为 0。
 */
import React, { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts/core';
import type { GlobalModel } from './data/globalModel';
import { caseKeyOf } from './data/globalModel';
import { BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED, evaluationSummaryText, gainWord, glyphEvaluationText, GlyphEvaluation, mayClaimPositiveLift, RunReport, runOutcome, SCOPE_LABELS } from './data/reportData';
import type { Loadable } from './data/types';
import { degradationLabel, methodLabel, SPLIT_LABELS } from './data/labels';
import { buildOption } from './MethodComparisonChart';
import { triptychPanes, REFERENCE_NOTE } from './GlobalEvaluation';
import { formatTime, shortSha, signed } from './format';
import type { SteleItem } from '../../types/stele';
import './reportPrint.css';

interface Props { model: GlobalModel | null; stele: SteleItem; runId: string; report: Loadable<RunReport> | null; glyph: Loadable<GlyphEvaluation>; exportedAt: string; view: string }
const PRINT_W = 700;

export const ReportPrintLayout: React.FC<Props> = ({ model, stele, runId, report, glyph, exportedAt, view }) => {
  const host = useRef<HTMLDivElement>(null);
  const [chartUrl, setChartUrl] = useState('');
  const height = model ? Math.min(560, model.panels.length * (44 + model.methods.length * 11)) : 0;
  useEffect(() => {
    if (!model || !host.current) return;
    const c = echarts.init(host.current, undefined, { width: PRINT_W, height, renderer: 'canvas' });
    c.on('finished', () => setChartUrl(c.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#ffffff' })));
    c.setOption(buildOption(model.panels, model.methods, model.method, 'column', 'print', PRINT_W), true);
    return () => c.dispose();
  }, [model, height]);
  const panes = model ? triptychPanes(model, model.caseRow) : null;
  const run = report?.state === 'ok' && report.data.run?.runId === runId ? report.data.run : null;
  const outcome = run ? runOutcome(run) : null;
  let fig = 0;
  return <>
    <div ref={host} aria-hidden style={{ position: 'fixed', left: -20000, top: 0, width: PRINT_W, height }} className="print:hidden" />
    <section className="report-print" data-testid="report-print-layout">
      <h1>墨韵智考·算法评测报告</h1>
      <p className="rp-meta">导出于 {exportedAt.replace('T', ' ').replace('+08:00', '')}（UTC+8）· 当前分层：{view === 'artifact' ? '本件处理报告' : '全局评测'} · 文物 <code>{stele.id}</code>《{stele.title}》{runId ? <> · 运行 <code>{runId}</code></> : ' · 未选择运行'}</p>
      {model && <>
        <p className="rp-meta">实验批次：{model.batch.shortName}（<code>{model.batch.id}</code>）· 划分：{SPLIT_LABELS[model.split]} · 退化：{degradationLabel(model.degradation)} · 方法：{methodLabel(model.method)} · 文物筛选：{model.sample || '全部'}</p>
        <h2>一、研究结论（分级）</h2>
        <div className="rp-card"><b>结论 1</b><span className="rp-grade">{model.primaryGrade.grade}</span><br />
          {(() => { const p = model.primary; if (!p) return '当前筛选没有该方法的记录。'; const m = p.scopes[p.primaryScope];
            const main = m.value == null ? (p.passthroughN > 0 && p.processedN === 0 ? `未处理 ${p.passthroughN} 条` : '无数据') : `${signed(m.value, 2, 'dB')}（${m.ci && m.ciReliable ? `95% CI ${signed(m.ci[0], 2)} ~ ${signed(m.ci[1], 2)}` : m.ciNote || '无 CI'}；${gainWord(m)}）`;
            return `${methodLabel(model.method)} 相对退化输入的配对 ΔPSNR，主口径「${SCOPE_LABELS[p.primaryScope]}」：${main}；文物 ${m.nArtifacts} 件、${m.nRecords} 行（n = ${p.n}）。全部：${signed(p.scopes.all.value, 2, 'dB')}；${model.batch.kind === 'retest' ? `无法判定 ${p.undeterminedN} 条` : `实际处理 ${p.processedN} 条、原图返回未处理 ${p.passthroughN} 条${p.undeterminedN ? `、无法判定 ${p.undeterminedN} 条` : ''}`}。CI 来源：${m.ciSource === 'ci_by_artifact' ? 'derived/ci_by_artifact.json' : '临时口径，前端计算，待替换为 derived/ci_by_artifact'}。`; })()}<br />
          <span className="rp-meta">分级依据：{model.primaryGrade.reasons.join('；')}。</span></div>
        <div className="rp-card"><b>结论 2</b><span className="rp-grade">有限支持</span><br />
          {(() => { const items = model.panels.find(p => p.metric.key === 'psnr')?.items || []; const st = (i: typeof items[number]) => i.scopes[i.primaryScope];
            const pos = items.filter(i => mayClaimPositiveLift(st(i))), neg = items.filter(i => st(i).sign === 'negative' && st(i).ciReliable && !mayClaimPositiveLift(st(i)));
            return `配对增益 CI 下界 > 0（可写“提升”）：${pos.map(i => methodLabel(i.method)).join('、') || '无'}；CI 上界 < 0（下降）：${neg.map(i => `${methodLabel(i.method)} ${signed(st(i).value, 2, 'dB')}`).join('、') || '无'}；其余跨 0、不可靠或无数据。负提升全部保留。`; })()}</div>
        <div className="rp-card"><b>结论 3</b><span className="rp-grade">未评测</span><br />真实拓本修复质量：未评测（无配对参考）。古碑识字 Top-1/Top-3：{glyph.state === 'ok' ? glyphEvaluationText(glyph.data, 'short') : '状态不可用'}。</div>
        <h2>二、算法横向比较</h2>
        <figure>{chartUrl ? <img src={chartUrl} alt="算法横向比较图" style={{ width: '100%' }} /> : <p>图表生成中…</p>}
          <figcaption>图 {++fig}　{model.batch.shortName} · {SPLIT_LABELS[model.split]} · {degradationLabel(model.degradation)}：各方法相对退化输入的配对增益。柱为主口径（{model.batch.kind === 'retest' ? '全部' : '实际处理'}）文物均值，须为按文物聚类 95% CI（{model.ci ? 'derived/ci_by_artifact.json；细笔画与耗时为前端临时口径' : `临时口径，前端计算，${BOOTSTRAP_RESAMPLES} 次，种子 ${BOOTSTRAP_SEED}`}；文物 &lt; 3 不画），点为每件文物均值；全部原图返回的方法标“未处理 N 条”；每个量纲单独一轴，轴含 0。来源：<code>/api/experiments/{model.batch.id}</code>。</figcaption></figure>
        <h2>三、视觉对照</h2>
        {panes == null ? <p>本批次只保存了数值，没有保存对比图像；不使用其他批次的图代替。</p> : model.caseRow && panes.length ? <figure>
          <div className="rp-triptych">{panes.map(p => <div key={p.key}>{p.src ? <img src={p.src} alt={p.label} /> : <p>{p.emptyReason}</p>}<div className="rp-meta">{p.label}{p.sha ? ` · SHA ${shortSha(p.sha)}` : ''}</div></div>)}</div>
          <figcaption>图 {++fig}　{model.batch.shortName} · case <code>{caseKeyOf(model.caseRow)}</code>（{model.caseKind === 'median' ? '中位案例' : model.caseKind === 'worst' ? '最差一条' : model.caseKind === 'passthrough' ? '原图返回样例' : '手动选择'}） · {methodLabel(model.caseRow.method)}（{model.caseRow.algorithmVersion || '版本未记录'}）· seed {model.caseRow.seed ?? '未记录'}。PSNR {model.caseRow.psnr?.toFixed(2) ?? '未评测'} dB（输入 {model.caseBaseline?.psnr?.toFixed(2) ?? '—'}）。图像按 contain 完整显示，未裁切。</figcaption>
        </figure> : <p>当前筛选下没有记录。</p>}
      </>}
      {!model && <p>实验批次数据未载入，本页不含全局评测。</p>}
      <h2>{model ? '四' : '一'}、本件处理记录</h2>
      {run && outcome ? <>
        <p><b className={outcome.mode === 'passthrough' ? 'rp-warn' : ''}>{outcome.title}</b>{outcome.mode === 'passthrough' && (run as { passthroughSource?: string | null }).passthroughSource === 'computed-on-read' ? '（读取时校验）' : ''}：{outcome.detail}{outcome.changeText ? ` ${outcome.changeText}。` : ''}{outcome.grayText ? ` ${outcome.grayText}。` : ' 灰度域改动：后端尚未返回。'}<br /><span className="rp-meta">{outcome.criterion}{outcome.source ? `；来源：${outcome.source}` : ''}。{evaluationSummaryText(run)}</span></p>
        <p className="rp-meta">运行 <code>{run.runId}</code> · {run.algorithmVersion} · 开始 {formatTime(run.startedAt)} · 结束 {formatTime(run.finishedAt)} · 输入 SHA-256 <code>{run.inputImageSha256 || '未记录'}</code></p>
        <figure><div className="rp-pair">
          {run.outputImages?.original ? <img src={run.outputImages.original} alt="工作输入" /> : <p>未保存工作输入</p>}
          {run.outputImages?.restored ? <img src={run.outputImages.restored} alt="输出" /> : <p>未保存输出</p>}
        </div><figcaption>图 {++fig}　左：工作输入；右：{outcome.mode === 'passthrough' ? '本次未改动原图（与输入逐像素相同）' : outcome.mode === 'undetermined' ? '输出（未能判定是否改动）' : '算法已改动像素'}。真实拓本无配对参考，不计算 PSNR/SSIM。</figcaption></figure>
      </> : <p>{runId ? '运行报告未载入。' : '未选择本件运行（legacy 或无时间的旧运行不作默认）。'}</p>}
      <h2>{model ? '五' : '二'}、来源与局限</h2>
      <ul>
        <li>{REFERENCE_NOTE}</li>
        {model?.batch.kind === 'retest' && <li>同批复测：样本参与过 v2.1 的误差分析，不是独立验证，结论最高为“有限支持”。</li>}
        {model && !model.splitAvailable && <li>本批未划分 dev/test。</li>}
        {model?.notes.map(n => <li key={n}>{n}</li>)}
        {model && <li data-testid="print-failure-retention">负提升与运行失败记录均保留在失败案例页与 JSON 导出（failureRetention），未抽样删除。</li>}
        {(model?.batch.registry.limitations || []).map(t => <li key={t}>{t}</li>)}
        <li>原图返回判定：{model?.der.source ? `DER ${model.der.criterion}（${model.der.source}）` : '输出与输入文件 SHA-256 相同（前端兜底，DER 未接入）'}；“无法判定”的行单独计数。口径依 REPORT_DATA_SPEC v2 与评测科学家 2026-10-19 裁定。</li>
        <li>图像变清晰不等于恢复原刻文字；候选字只是建议，不是碑文释读结论。</li>
      </ul>
      {model && <p className="rp-meta">数据导出：<code>/api/experiments/{model.batch.id}/export/results.csv</code>、<code>summary.csv</code>；结果目录 <code>experiments/results/{model.batch.registry.directory}</code>；代码提交 <code>{String(model.detail.environment?.gitSha || model.detail.candidateCommit || '未记录')}</code>。</p>}
      <p className="rp-footer">墨韵智考 · 本报告由当前页面选择生成；数值与页面、JSON 导出同源（同一前端适配层）。</p>
    </section>
  </>;
};
