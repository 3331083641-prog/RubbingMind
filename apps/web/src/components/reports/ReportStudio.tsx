import React, { useEffect, useMemo, useRef, useState } from 'react';
import { flushSync } from 'react-dom';
import type { GlobalModel } from './data/globalModel';
import { caseKeyOf } from './data/globalModel';
import { appliedStatus, baselineMap, baselineOf, BatchInfo, GlyphEvaluation, glyphEvaluationText, isPassthroughStatus, ReportApi, rowDelta, SCOPE_LABELS } from './data/reportData';
import { studioEvidence } from './data/studioData';
import type { Diagnosis, ExperimentRow, Loadable } from './data/types';
import { degradationLabel, methodLabel, METRICS, MetricKey, SPLIT_LABELS } from './data/labels';
import { MethodComparisonChart } from './MethodComparisonChart';
import { Reproducibility, REFERENCE_NOTE, ScopeTriple, triptychPanes } from './GlobalEvaluation';
import { SyncedTriptych } from './SyncedTriptych';
import { FailureCasesPanel } from './FailureCasesPanel';
import { MechanismPanel } from './MechanismPanel';
import { ExperimentExplorer } from '../ExperimentExplorer';
import { HeldoutComparison, RetestTeaser } from '../HeldoutComparison';
import { CrossBatchComparison } from './CrossBatchComparison';
import { AnimatedValue, useQuietMotion } from './studioMotion';
import { OutcomeLegend, StudioCharts } from './StudioCharts';
import type { ReportFilters } from './reportFilters';
import './reportStudio.css';

interface Props {
  model: GlobalModel;
  batches: BatchInfo[];
  glyph: Loadable<GlyphEvaluation>;
  diagnosis: Loadable<Diagnosis>;
  filters: ReportFilters;
  setFilters: (p: ReportFilters) => void;
  onSelectBatch: (b: BatchInfo) => void;
  onRunReport: () => void;
}

const PRIMARY_MODULES = [
  ['overview', '算法性能对比', '同批、同量纲的配对变化'],
  ['images', '真实图像对照', '同步缩放 · 滑杆 · 局部差分'],
  ['heatmap', '退化类型分析', '方法 × 退化的文物均值'],
  ['failures', '失败案例与不确定性', '不筛除不利结果'],
] as const;

const SECONDARY_MODULES = [
  ['distribution', '处理结果分布', '负提升与原图返回分别计数'],
  ['timing', '质量与耗时', '只比较本批历史环境'],
  ['mechanism', '消融与机制', '真实重放步骤与保真记录'],
  ['records', '完整记录与来源', '逐条数据 · 协议 · 复现'],
] as const;

const ALL_MODULES = [...PRIMARY_MODULES, ...SECONDARY_MODULES] as const;

export const ReportStudio: React.FC<Props> = ({
  model,
  batches,
  glyph,
  diagnosis,
  filters,
  setFilters,
  onSelectBatch,
  onRunReport,
}) => {
  const panel = ALL_MODULES.some(m => m[0] === filters.panel) ? filters.panel! : 'overview';
  const metricKey: MetricKey = METRICS.some(m => m.key === filters.metric) ? filters.metric as MetricKey : 'psnr';
  const metric = METRICS.find(m => m.key === metricKey)!;
  const chartPanel = model.panels.find(p => p.metric.key === metricKey);
  const selected = chartPanel?.items.find(i => i.method === model.method);
  const stat = selected?.scopes[selected.primaryScope];
  const verifiedCI = stat?.ciSource === 'ci_by_artifact' && !!model.ci;
  const evidence = useMemo(() => studioEvidence(model, metricKey), [model, metricKey]);
  const outcome = model.panels.find(p => p.metric.key === evidence.outcomeMetric)?.items.find(i => i.method === model.method);
  const [focus, setFocus] = useState(false);
  const focusButton = useRef<HTMLButtonElement>(null);
  const stage = useRef<HTMLElement>(null);
  const [archive, setArchive] = useState(false);
  const quiet = useQuietMotion();
  const busy = useRef(false);

  useEffect(() => {
    const escape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setFocus(false);
        focusButton.current?.focus();
      }
    };
    window.addEventListener('keydown', escape);
    return () => window.removeEventListener('keydown', escape);
  }, []);

  const open = (id: string) => {
    if (id === panel || busy.current) return;
    const update = () => flushSync(() => setFilters({ panel: id }));
    const reveal = () => {
      if (window.innerWidth <= 900) {
        stage.current?.scrollIntoView({ behavior: quiet ? 'auto' : 'smooth', block: 'start' });
      }
    };
    const doc = document as Document & { startViewTransition?: (fn: () => void) => { finished: Promise<void> } };
    if (quiet) {
      update();
      reveal();
      return;
    }
    if (!doc.startViewTransition) {
      const source = [...document.querySelectorAll<HTMLElement>(`[data-testid="studio-module-${id}"], [data-testid="studio-secondary-${id}"]`)].find(el => el.getBoundingClientRect().width > 0);
      const from = source?.getBoundingClientRect(), to = stage.current?.getBoundingClientRect();
      if (source && from && to && from.width && from.height) {
        const ghost = source.cloneNode(true) as HTMLElement;
        ghost.setAttribute('aria-hidden', 'true');
        ghost.setAttribute('inert', '');
        Object.assign(ghost.style, {
          position: 'fixed',
          left: `${from.left}px`,
          top: `${from.top}px`,
          width: `${from.width}px`,
          height: `${from.height}px`,
          margin: '0',
          zIndex: '30',
          pointerEvents: 'none',
          transformOrigin: 'top left',
        });
        document.body.appendChild(ghost);
        ghost.animate(
          [
            { transform: 'translate(0,0) scale(1)', opacity: 0.9 },
            { transform: `translate(${to.left - from.left}px,${to.top - from.top}px) scale(${to.width / from.width},${to.height / from.height})`, opacity: 0 },
          ],
          { duration: 420, easing: 'cubic-bezier(.22,1,.36,1)', fill: 'forwards' }
        ).finished.catch(() => {}).finally(() => ghost.remove());
      }
      update();
      reveal();
      return;
    }
    busy.current = true;
    doc.startViewTransition(update).finished.catch(() => {}).finally(() => {
      busy.current = false;
      reveal();
    });
  };

  const activeTitle = ALL_MODULES.find(m => m[0] === panel)![1];
  const counts = evidence.distribution.find(d => d.method === model.method);

  return (
    <div
      data-testid="global-evaluation"
      className={`report-studio ${focus ? 'is-focused' : ''}`}
      data-motion={quiet ? 'reduced' : 'full'}
    >
      {/* 核心结论横幅 */}
      <div className="studio-finding" data-testid="conclusion-primary">
        <div>
          <span>{methodLabel(model.method)} · {SPLIT_LABELS[model.split]} · {degradationLabel(model.degradation)}</span>
          <p>
            {metric.title}
            <strong data-testid="studio-primary">
              <AnimatedValue value={stat?.value} digits={metric.digits} signed={metric.delta} />
            </strong>
            <small>{metric.unit}</small>
          </p>
          <span data-testid="comparison-ci-source" data-ci-source={verifiedCI ? 'backend' : 'frontend'}>
            {stat?.value == null
              ? '当前口径没有可评测值'
              : stat.ci && stat.ciReliable
              ? `95% CI ${stat.ci[0].toFixed(metric.digits)} ～ ${stat.ci[1].toFixed(metric.digits)} · ${verifiedCI ? '后端核验' : '临时 bootstrap'}`
              : 'CI 不可靠或未记录'}
          </span>
        </div>
        <dl>
          <div>
            <dt>当前文物</dt>
            <dd>
              <AnimatedValue value={new Set(model.rows.map(r => r.sampleId)).size} />
              <small> 件</small>
            </dd>
          </div>
          <div>
            <dt>对照方法</dt>
            <dd>
              <AnimatedValue value={model.methods.length} />
              <small> 种</small>
            </dd>
          </div>
          <div
            className={outcome && outcome.negativeAllN > 0 ? 'studio-risk' : ''}
            title={`全部配对负差 ${outcome?.negativeAllN ?? '未评测'} 条，其中实际处理 ${counts?.counts[1] ?? '未评测'} 条；不确定及 E-05 行保留。`}
          >
            <dt>{metricKey === 'processingMs' ? 'ΔPSNR' : metric.title} 负差</dt>
            <dd data-testid="studio-negative-count">
              <AnimatedValue value={outcome?.negativeAllN ?? null} />
              <small> 条</small>
            </dd>
          </div>
        </dl>
      </div>

      {/* 科研可信度提示条 */}
      <p className="studio-trust" role="note">
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-[#2eb88a]" aria-hidden="true" />
        <span>
          受控参考不等于碑石真值 · {selected ? SCOPE_LABELS[selected.primaryScope] : '待评测'}口径 · {verifiedCI ? 'CI 来源已核验' : '临时统计，不作正式认证'}
          {model.batch.kind === 'retest' ? ' · 同批复测，非独立验证' : model.batch.kind === 'historical' ? ' · 历史先验泄漏批次，仅留档' : ''}
        </span>
      </p>

      {/* 主舞台与导航双栏布局 */}
      <div className="studio-layout">
        {/* 主舞台 */}
        <section
          ref={stage}
          className="studio-stage"
          id="report-analysis-stage"
          role="tabpanel"
          aria-label={activeTitle}
          data-testid="report-main-stage"
          data-panel={panel}
          style={{ viewTransitionName: quiet ? 'none' : `report-${panel}` } as React.CSSProperties}
        >
          <header className="studio-stage-heading">
            <div>
              <span className="studio-kicker">
                {model.batch.kind === 'controlled' ? '受控图像实验' : model.batch.kind === 'retest' ? '同批复测，非独立验证' : '历史实验记录'} · {SPLIT_LABELS[model.split]}
              </span>
              <h2>{activeTitle}</h2>
            </div>
            <div className="studio-stage-actions">
              {['overview', 'heatmap', 'distribution', 'timing'].includes(panel) && (
                <label>
                  <span className="sr-only">评价指标</span>
                  <select aria-label="评价指标" value={metricKey} onChange={e => setFilters({ metric: e.target.value })}>
                    {model.panels.map(p => (
                      <option key={p.metric.key} value={p.metric.key}>
                        {p.metric.title}{p.metric.unit ? ` / ${p.metric.unit}` : ''}
                      </option>
                    ))}
                  </select>
                </label>
              )}
              {panel !== 'overview' && (
                <button onClick={() => open('overview')} aria-label="返回算法总览">
                  总览
                </button>
              )}
              <button
                ref={focusButton}
                onClick={() => setFocus(v => !v)}
                aria-pressed={focus}
                aria-label={focus ? '退出专注查看' : '专注查看'}
              >
                {focus ? '退出专注 · Esc' : '专注查看'}
                <svg width="15" height="15" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
                  <path d="M7 3H3v4m10-4h4v4M3 13v4h4m10-4v4h-4" />
                </svg>
              </button>
            </div>
          </header>

          <div className="studio-stage-body" key={panel}>
            {panel === 'overview' && (
              <>
                <p className="studio-chart-note">
                  相对同一退化输入 · {metric.delta ? '右侧正差、左侧负差' : '耗时绝对值，越低越好'} · 按文物等权 · 点击柱选方法、点选文物
                </p>
                {chartPanel ? (
                  <MethodComparisonChart
                    testId="method-comparison-chart"
                    panels={[chartPanel]}
                    methods={model.methods}
                    selectedMethod={model.method}
                    onSelectMethod={m => setFilters({ method: m, case: '' })}
                    onSelectSample={(s, m) => setFilters({ method: m, sample: s, case: '', panel: 'images' })}
                    height={focus ? 540 : 350}
                  />
                ) : (
                  <p role="status">当前批次没有此指标记录。</p>
                )}
                <p className="studio-caption">
                  柱为{selected ? SCOPE_LABELS[selected.primaryScope] : '当前口径'}文物均值，点为单件文物；可靠且文物 ≥ 3 时显示 95% CI。未处理不算修复成功。
                </p>
                <details className="studio-details">
                  <summary>查看选中方法的完整口径与结论依据</summary>
                  {model.primary && <ScopeTriple it={model.primary} retest={model.batch.kind === 'retest'} />}
                  <p>{model.primaryGrade.reasons.join('；')}</p>
                  <p>{REFERENCE_NOTE}</p>
                  <p data-testid="glyph-topk-line">
                    古碑识字 Top-1 / Top-3：{glyph.state === 'ok' ? glyphEvaluationText(glyph.data, 'with-topk') : '评测状态不可用'}
                  </p>
                </details>
              </>
            )}

            {panel === 'images' && <ImageStage model={model} filters={filters} setFilters={setFilters} focus={focus} />}

            {(panel === 'heatmap' || panel === 'distribution' || panel === 'timing') && (
              <>
                <p className="studio-chart-note">
                  {panel === 'heatmap'
                    ? `每格为同批${metricKey === 'processingMs' ? '全部记录' : model.primary?.primaryScope === 'all' ? '全部记录' : '实际处理'}口径的文物等权均值；点击格子联动方法与退化。`
                    : panel === 'distribution'
                    ? `按 ${metricKey === 'processingMs' ? 'ΔPSNR' : metric.title} 分类；配对正差不是修复成功认证。负提升、未处理和未知分别保留。`
                    : '本批历史环境中的方法均值；两轴使用同一批配对记录。不能外推至当前机器。'}
                </p>
                {panel === 'timing' && !evidence.timing.length ? (
                  <p role="status" className="studio-empty">没有同环境下可配对的质量／耗时记录，不绘制散点。</p>
                ) : (
                  <StudioCharts
                    kind={panel}
                    model={model}
                    evidence={evidence}
                    metric={metric}
                    onSelect={(method, deg) => setFilters({ method, ...(deg ? { deg } : {}), case: '' })}
                  />
                )}
                {panel === 'distribution' && <OutcomeLegend />}
                <details className="studio-details">
                  <summary>查看绘图原值与口径</summary>
                  <p>热图只使用当前筛选；没有记录的格为空，不填 0。分布相加等于当前各方法记录数；E-05 不归入实际处理或原图返回。各方法统计口径与 JSON 一致。</p>
                  <pre data-testid="studio-visualization-data">{JSON.stringify(evidence, null, 2)}</pre>
                </details>
              </>
            )}

            {panel === 'failures' && (
              <>
                <FailureWall model={model} filters={filters} setFilters={setFilters} />
                <details className="studio-details" onToggle={e => setArchive(e.currentTarget.open)}>
                  <summary>完整失败记录、诊断与测量原因</summary>
                  {archive && <FailureCasesPanel model={model} diagnosis={diagnosis} setFilters={setFilters} />}
                </details>
              </>
            )}

            {panel === 'mechanism' && <MechanismPanel model={model} filters={filters} setFilters={setFilters} />}

            {panel === 'records' && (
              <>
                <ExperimentExplorer model={model} onOpenCase={(key, method) => setFilters({ method, case: key, panel: 'images' })} />
                <details className="studio-details">
                  <summary>跨批次可比性与同批复测</summary>
                  <CrossBatchComparison model={model} batches={batches} compareId={filters.cmp || ''} onCompare={cmp => setFilters({ cmp })} />
                  {model.batch.kind === 'retest' ? <HeldoutComparison model={model} /> : <RetestTeaser batches={batches} onSelect={onSelectBatch} />}
                </details>
                <Reproducibility model={model} />
              </>
            )}
          </div>
        </section>

        {/* 右侧导航栏：层次化重构，核心卡片 + 深入模块 */}
        <aside className="studio-navigator" aria-label="分析模块导航">
          <div className="studio-nav-heading">
            核心分析维度 <span>点击图窗展开</span>
          </div>

          {/* 核心 4 大图窗 */}
          <div role="tablist" aria-label="全局评测核心栏目" aria-orientation="vertical">
            {PRIMARY_MODULES.map(([id, title, note]) => (
              <button
                key={id}
                role="tab"
                aria-label={title}
                aria-selected={panel === id}
                aria-controls="report-analysis-stage"
                onClick={() => open(id)}
                className="studio-module"
                data-testid={`studio-module-${id}`}
                style={{ viewTransitionName: quiet || panel === id ? 'none' : `report-${id}` } as React.CSSProperties}
              >
                <MiniEvidence kind={id} model={model} evidence={evidence} />
                <span>
                  <strong>{title}</strong>
                  <small>{note}</small>
                </span>
                <span aria-hidden="true" className="studio-nav-arrow">↗</span>
              </button>
            ))}
          </div>

          {/* 深入分析与机制 (精简 2x2 导航格，紧凑美观) */}
          <div className="studio-subnav-section">
            <div className="text-[11.5px] font-medium text-[#8c9c90] px-1 py-1">深入研究与机制</div>
            <div className="studio-secondary-grid">
              {SECONDARY_MODULES.map(([id, title]) => (
                <button
                  key={id}
                  data-testid={`studio-module-${id}`}
                  role="tab"
                  aria-label={title}
                  aria-selected={panel === id}
                  aria-controls="report-analysis-stage"
                  className={`studio-chip-btn ${panel === id ? 'is-active' : ''}`}
                  onClick={() => open(id)}
                >
                  <span>{title}</span>
                  <span className="text-[10px] opacity-70" aria-hidden="true">↗</span>
                </button>
              ))}
            </div>
          </div>

          {/* 次级模块快捷直达（兼容自动化测试与紧凑导航） */}
          <div className="studio-secondary-links">
            {ALL_MODULES.filter(m => m[0] === 'timing' || m[0] === 'records').map(([id, title]) => (
              <button
                key={id}
                data-testid={`studio-secondary-${id}`}
                aria-pressed={panel === id}
                onClick={() => open(id)}
              >
                {title} ↗
              </button>
            ))}
          </div>

          <button className="studio-run-link" onClick={onRunReport}>
            本件处理报告 <span aria-hidden="true">→</span>
          </button>
          <p className="studio-nav-foot">
            当前实验 <code>{model.batch.registry.directory}</code><br />
            所有负提升保留；古碑识字未评测。
          </p>
        </aside>
      </div>

      {!!model.notes.length && (
        <details className="studio-details studio-notes">
          <summary>当前批次的异常与历史说明（{model.notes.length}）</summary>
          {model.notes.map(n => (
            <p key={n}>{n}</p>
          ))}
        </details>
      )}
    </div>
  );
};

function ImageStage({ model, filters, setFilters, focus }: { model: GlobalModel; filters: ReportFilters; setFilters: (p: ReportFilters) => void; focus?: boolean }) {
  const row = model.caseRow;
  const panes = triptychPanes(model, row);
  return (
    <div className="studio-images">
      <div className="studio-case-controls" role="group" aria-label="代表案例">
        {[
          ['median', '中位案例（默认）', ''],
          ['worst', '最差一条（负提升）', '@worst'],
          ['passthrough', '原图返回样例', '@passthrough'],
        ].map(([kind, label, value]) => (
          <button
            key={kind}
            data-testid={`case-${kind}`}
            aria-pressed={model.caseKind === kind}
            disabled={!model.representative[kind as 'median' | 'worst' | 'passthrough']}
            onClick={() => setFilters({ case: value })}
          >
            {label}
          </button>
        ))}
        <select
          aria-label="单次实验记录"
          value={row && model.caseKind === 'explicit' ? caseKeyOf(row) : ''}
          onChange={e => setFilters({ case: e.target.value })}
        >
          <option value="">按规则选择</option>
          {model.caseRows.map(r => (
            <option key={caseKeyOf(r)} value={caseKeyOf(r)}>
              {r.sampleId} · {degradationLabel(r.degradation)} {r.strength}
            </option>
          ))}
        </select>
      </div>
      {panes == null ? (
        <p data-testid="no-images" role="status" className="studio-empty">
          本批次只保存了数值，没有保存对比图像；不借用其他批次图像。
        </p>
      ) : !row ? (
        <p data-testid="no-case" role="status" className="studio-empty">
          当前筛选没有{filters.case === '@worst' ? '负提升的实际处理' : filters.case === '@passthrough' ? '原图返回的' : ''}记录。
        </p>
      ) : (
        <>
          <SyncedTriptych
            key={`${model.batch.id}|${caseKeyOf(row)}|${row.method}`}
            testId="experiment-triptych"
            panes={panes}
            diffPair={['in', 'out']}
            height={focus ? 520 : 380}
            knownPassthrough={isPassthroughStatus(appliedStatus(row).status) && row.statusSource === 'DER'}
          />
          <p className="studio-caption">
            {row.sampleId} · {methodLabel(row.method)} · PSNR {row.psnr?.toFixed(2) ?? '未评测'} / SSIM {row.ssim?.toFixed(3) ?? '未评测'} / 边缘 F1 {row.edgeF1?.toFixed(3) ?? '未评测'}
          </p>
        </>
      )}
      <details className="studio-details">
        <summary>案例来源、选择规则与完整标识</summary>
        <p>{REFERENCE_NOTE}</p>
        <p data-testid="case-rule">{model.caseKind === 'explicit' ? '手动选择。' : ''}{model.representative.rule}</p>
        <p>实验 {model.batch.id} · case {row ? caseKeyOf(row) : '无'} · seed {row?.seed ?? '未记录'} · SHA {row?.outputSha256 ?? '未记录'}</p>
      </details>
    </div>
  );
}

function FailureWall({ model, filters, setFilters }: { model: GlobalModel; filters: ReportFilters; setFilters: (p: ReportFilters) => void }) {
  const map = useMemo(() => baselineMap(model.rowsAll), [model.rowsAll]);
  const negatives = model.rows
    .filter(r => r.method !== 'degraded')
    .map(r => ({ row: r, delta: rowDelta(r, 'psnr', map) }))
    .filter((x): x is { row: ExperimentRow; delta: number } => x.delta != null && x.delta < 0)
    .sort((a, b) => a.delta - b.delta);
  const chosen = filters.case ? negatives.find(n => caseKeyOf(n.row) === filters.case && n.row.method === model.method) : null;
  const row = chosen?.row;
  const failed = model.rows.filter(r => r.error);

  return (
    <section data-testid="failure-cases">
      <p className="studio-chart-note">
        当前筛选全部负提升 <b>{negatives.length}</b> 条 · 执行失败 {failed.length} 条。下列展示最差 {Math.min(6, negatives.length)} 条，完整记录可展开核查，不删除任何样本。
      </p>
      {!model.batch.hasImages && <p className="studio-empty">本批只保存数值，没有失败案例图像。</p>}
      {row && model.batch.hasImages ? (
        <>
          <button onClick={() => setFilters({ case: '' })} className="mb-2 text-xs text-[#dfc187] hover:underline">
            ← 返回案例墙
          </button>
          <SyncedTriptych
            testId="failure-detail-triptych"
            panes={triptychPanes({ ...model, caseBaseline: baselineOf(row, map) }, row)!}
            diffPair={['in', 'out']}
            height={380}
          />
          <p className="studio-caption">
            {methodLabel(row.method)} · {row.sampleId} · ΔPSNR {chosen.delta.toFixed(3)} dB。原因须依据下方测量诊断，尚未确定时不猜测。
          </p>
        </>
      ) : (
        <div className="studio-failure-wall" data-testid="failure-image-gallery">
          {negatives.slice(0, 6).map(({ row: r, delta }) => (
            <button
              key={`${caseKeyOf(r)}|${r.method}`}
              data-testid={`failure-thumb-${caseKeyOf(r)}`}
              onClick={() => setFilters({ method: r.method, case: caseKeyOf(r) })}
            >
              <div className="studio-failure-images">
                {[r.input || baselineOf(r, map)?.output, r.output].map((file, i) =>
                  file && model.batch.hasImages ? (
                    <img
                      key={i}
                      src={ReportApi.assetUrl(model.batch.id, file)}
                      alt={`${i ? '输出' : '输入'} ${r.sampleId}`}
                      onError={e => {
                        e.currentTarget.hidden = true;
                        e.currentTarget.parentElement!.dataset.imageError = '图像不可用';
                      }}
                    />
                  ) : (
                    <span key={i}>未保存图像</span>
                  )
                )}
              </div>
              <strong>
                {methodLabel(r.method)} <em>{delta.toFixed(2)} dB</em>
              </strong>
              <small>{r.sampleId} · {degradationLabel(r.degradation)}</small>
            </button>
          ))}
        </div>
      )}
      {!negatives.length && <p role="status" className="studio-empty">当前筛选没有负提升；原图返回不计作成功。</p>}
    </section>
  );
}

function MiniEvidence({ kind, model, evidence }: { kind: string; model: GlobalModel; evidence: ReturnType<typeof studioEvidence> }) {
  const map = baselineMap(model.rowsAll);
  const failing = model.rows
    .filter(r => r.method !== 'degraded')
    .map(row => ({ row, delta: rowDelta(row, 'psnr', map) }))
    .filter(x => x.delta != null && x.delta < 0)
    .sort((a, b) => a.delta! - b.delta!)[0]?.row;
  const image = kind === 'failures' ? failing?.input : model.caseRow?.input;
  if ((kind === 'images' || kind === 'failures') && model.batch.hasImages && image) {
    return <img className="studio-mini-image" src={ReportApi.assetUrl(model.batch.id, image)} alt="" onError={e => { e.currentTarget.hidden = true; }} />;
  }
  if (kind === 'mechanism' || kind === 'records') {
    return <span className="studio-mini-word">{kind === 'mechanism' ? '记录链' : '原始表'}</span>;
  }
  const panel = model.panels.find(p => p.metric.key === evidence.metric);
  const values = panel?.items.map(i => i.scopes[i.primaryScope].value) || [];
  const max = Math.max(0.001, ...values.filter((v): v is number => v != null).map(Math.abs));
  const counts = evidence.distribution.find(d => d.method === model.method)?.counts || [];
  const total = counts.reduce((a, b) => a + b, 0) || 1;
  const maxMs = Math.max(1, ...evidence.timing.map(t => t.milliseconds!));
  const maxQuality = Math.max(0.001, ...evidence.timing.map(t => Math.abs(t.quality!)));

  return (
    <svg className="studio-mini" viewBox="0 0 60 40" aria-hidden="true">
      {kind === 'heatmap'
        ? evidence.heatmap.slice(0, 12).map((v, i) => (
            <rect
              key={i}
              x={(i % 4) * 14}
              y={Math.floor(i / 4) * 12 + 2}
              width="11"
              height="9"
              fill={v.value == null ? '#202925' : v.value < 0 ? '#c83c23' : '#2eb88a'}
              opacity={v.value == null ? 0.3 : 0.8}
            />
          ))
        : kind === 'timing'
        ? evidence.timing.map((t, i) => (
            <circle
              key={i}
              cx={4 + (t.milliseconds! / maxMs) * 50}
              cy={20 - (t.quality! / maxQuality) * 16}
              r="2.5"
              fill="#2eb88a"
            />
          ))
        : kind === 'distribution'
        ? counts.map((n, i) => (
            <rect
              key={i}
              x={(counts.slice(0, i).reduce((a, b) => a + b, 0) / total) * 56}
              y="13"
              width={(n / total) * 56}
              height="12"
              fill={['#2eb88a', '#c83c23', '#c8a86b', '#5b7682', '#434d4c', '#a83220'][i]}
            />
          ))
        : values.map((v, i) =>
            v == null ? null : (
              <rect
                key={i}
                x={v < 0 ? 30 - (Math.abs(v) / max) * 27 : 30}
                y={i * 5 + 1}
                width={(Math.abs(v) / max) * 27}
                height="3.5"
                fill={v < 0 ? '#c83c23' : '#2eb88a'}
              />
            )
          )}
    </svg>
  );
}
