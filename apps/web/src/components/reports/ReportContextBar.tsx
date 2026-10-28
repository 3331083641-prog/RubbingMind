/**
 * 上下文栏：文物 / 本件运行 / 实验批次 / 划分 / 退化 / 方法 / 文物筛选 / 分层切换，全部与 URL 同步。
 * 遵循文化沉静与高效交互设计，明确区分“全局评测”与“本件处理报告”的任务边界。
 */
import React, { useState } from 'react';
import type { SteleItem } from '../../types/stele';
import type { BatchInfo, RunInfo, RunSelection } from './data/reportData';
import type { GlobalModel } from './data/globalModel';
import type { Loadable } from './data/types';
import { degradationLabel, methodLabel, SPLIT_LABELS } from './data/labels';
import { formatTime } from './format';
import type { ReportFilters } from './reportFilters';

interface Props {
  stele: SteleItem;
  view: 'global' | 'artifact';
  panel: string;
  runs: Loadable<RunInfo[]>;
  runId: string;
  selection: Loadable<{ runSelection: RunSelection | null; runId: string }>;
  batches: Loadable<BatchInfo[]>;
  experimentId: string;
  model: GlobalModel | null;
  setFilters: (p: ReportFilters) => void;
  onSelectRun: (runId: string) => void;
  onSelectBatch: (b: BatchInfo) => void;
  onExportJson: () => void;
  onPrint: () => void;
  onNavigate: (tab: string) => void;
}

const batchCaption = (b: BatchInfo) =>
  b.id === 'controlled-rubbings-v2-text-2026-10-17'
    ? '文字区受控实验 · 10.17'
    : b.id === 'controlled-rubbings-v2-2026-10-17'
    ? '受控实验 v2 · 10.17'
    : b.kind === 'historical'
    ? '历史实验 · 先验泄漏'
    : b.title;

export const ReportContextBar: React.FC<Props> = ({
  stele,
  view,
  runs,
  runId,
  selection,
  batches,
  experimentId,
  model,
  setFilters,
  onSelectRun,
  onSelectBatch,
  onExportJson,
  onPrint,
  onNavigate,
}) => {
  const [copied, setCopied] = useState('');
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setCopied('链接已复制');
    } catch {
      setCopied('请复制浏览器地址栏');
    }
    setTimeout(() => setCopied(''), 2500);
  };

  return (
    <header className="report-context print:hidden" data-testid="report-context-bar" aria-label="报告上下文">
      <div className="studio-page-header">
        <div>
          <h1>{view === 'global' ? '碑拓图像修复 · 全局算法评测' : `碑拓图像修复 · 本件处理报告（《${stele.title}》）`}</h1>
          <p>
            {view === 'global'
              ? '受控实验配对比较与多维性能分析，沿着证据理解方法的作用与边界。'
              : '真实单件碑拓的高清修复前后对照、自适应决策留痕与金石学证据审计。'}
          </p>
        </div>

        {/* 移动端操作折叠 */}
        <details className="studio-mobile-actions">
          <summary>报告操作 ▾</summary>
          <div>
            <button onClick={copy}>复制链接</button>
            <button onClick={onExportJson}>导出 JSON</button>
            <button onClick={onPrint}>打印 / 保存 PDF</button>
          </div>
        </details>

        {/* 桌面端头部操作按钮 */}
        <div className="studio-header-actions">
          {copied && <span role="status" className="text-xs text-[#2eb88a] font-medium">{copied}</span>}
          <button onClick={copy} title="复制当前页面完整筛选 URL 链接">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" /><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" /></svg>
            复制链接
          </button>
          <button onClick={onExportJson} title="导出包含完整科研统计与派生证据的原始 JSON 文件">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>
            导出 JSON
          </button>
          <button onClick={onPrint} title="打开报告打印对话框或导出标准 A4 纵版 PDF">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><polyline points="6 9 6 2 18 2 18 9" /><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" /><rect x="6" y="14" width="12" height="8" /></svg>
            打印 / 保存 PDF
          </button>
        </div>
      </div>

      <div className="studio-toolbar">
        {/* 分层视图切换 Tab */}
        <div role="tablist" aria-label="报告分层" className="studio-view-tabs">
          <button
            role="tab"
            aria-selected={view === 'global'}
            onClick={() => setFilters({ view: 'global' })}
          >
            全局评测
          </button>
          <button
            role="tab"
            aria-selected={view === 'artifact'}
            onClick={() => setFilters({ view: 'artifact' })}
          >
            本件处理报告
          </button>
        </div>

        {/* 实验批次选择 */}
        <label className="studio-context-field">
          实验批次
          <select
            aria-label="实验批次"
            value={experimentId}
            onChange={e => {
              const b = batches.state === 'ok' ? batches.data.find(x => x.id === e.target.value) : undefined;
              if (b) onSelectBatch(b);
            }}
            disabled={batches.state !== 'ok'}
          >
            {!experimentId && <option value="">请选择批次</option>}
            {batches.state === 'ok' ? (
              batches.data.map(b => (
                <option key={b.id} value={b.id}>
                  {batchCaption(b)}
                  {b.isDefault ? ' · 默认' : ''}
                  {b.hasImages ? '' : ' · 仅数值'}
                </option>
              ))
            ) : (
              <option value="">{batches.state === 'loading' ? '读取中…' : '实验登记不可用'}</option>
            )}
          </select>
        </label>

        {/* 全局视图下快速切方法 */}
        {view === 'global' && model && (
          <label className="studio-context-field">
            方法
            <select
              aria-label="处理方法"
              value={model.method}
              onChange={e => setFilters({ method: e.target.value, case: '' })}
            >
              {model.methods.map(m => (
                <option key={m} value={m}>
                  {methodLabel(m)}
                </option>
              ))}
            </select>
          </label>
        )}

        {/* 详细筛选抽屉 */}
        <details className="studio-filter-more" open={view === 'artifact' || undefined}>
          <summary>{view === 'global' ? '筛选与实验上下文' : '文物与运行选择'}</summary>
          <div className="studio-filter-fields">
            <span className="text-[#dfc187] font-medium">文物：《{stele.title}》 · {stele.id}</span>
            <label className="studio-context-field">
              本件运行
              <select
                aria-label="本件运行"
                value={runId}
                onChange={e => onSelectRun(e.target.value)}
                disabled={runs.state !== 'ok'}
              >
                <option value="">
                  {runs.state === 'ok'
                    ? runs.data.length
                      ? '未选择'
                      : '本件尚无运行'
                    : runs.state === 'loading'
                    ? '读取中…'
                    : '运行记录不可用'}
                </option>
                {runs.state === 'ok' &&
                  runs.data.map(x => (
                    <option key={x.run.runId} value={x.run.runId}>
                      {x.legacy ? '［legacy 旧版未验证］' : ''}
                      {x.run.runId} · {x.time != null ? formatTime(x.run.finishedAt || x.run.startedAt) : '时间未记录'}
                    </option>
                  ))}
              </select>
            </label>
            <button
              type="button"
              className="px-2.5 py-1 rounded bg-[#c8a86b]/15 text-[#dfc187] border border-[#c8a86b]/30 hover:bg-[#c8a86b]/25 transition-colors text-xs"
              onClick={() => onNavigate('workbench')}
            >
              前往工作台 →
            </button>

            {view === 'global' && model && (
              <>
                {model.splitAvailable ? (
                  <label className="studio-context-field">
                    划分
                    <select
                      aria-label="数据分组"
                      value={model.split}
                      onChange={e => setFilters({ split: e.target.value, case: '' })}
                    >
                      {['test', 'development'].map(x => (
                        <option key={x} value={x}>
                          {SPLIT_LABELS[x]}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : (
                  <span data-testid="split-none" className="text-slate-400 text-xs">本批未划分</span>
                )}
                <label className="studio-context-field">
                  退化
                  <select
                    aria-label="退化类型筛选"
                    value={model.degradation}
                    onChange={e => setFilters({ deg: e.target.value === 'all' ? '' : e.target.value, case: '' })}
                  >
                    {['all', ...model.degradations].map(d => (
                      <option key={d} value={d}>
                        {degradationLabel(d)}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="studio-context-field">
                  文物
                  <select
                    aria-label="实验样本"
                    value={model.sample}
                    onChange={e => setFilters({ sample: e.target.value, case: '' })}
                  >
                    <option value="">全部（{model.samples.length} 件）</option>
                    {model.samples.map(x => (
                      <option key={x} value={x}>{x}</option>
                    ))}
                  </select>
                </label>
              </>
            )}

            {selection.state === 'ok' && selection.data.runSelection && (
              <span data-testid="run-selection-rule" className="text-xs text-[#8c9d90]">
                {selection.data.runSelection.rule === 'explicit'
                  ? '指定运行'
                  : selection.data.runSelection.rule === 'latest_non_legacy'
                  ? '默认：最新的非 legacy 运行（后端选定）'
                  : '没有可默认的运行'}
              </span>
            )}
            {selection.state === 'missing' && (
              <span role="alert" className="text-xs text-[#c83c23]">{selection.message}</span>
            )}
          </div>
        </details>
      </div>
    </header>
  );
};
