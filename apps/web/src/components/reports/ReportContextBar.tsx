/** 上下文栏：文物 / 本件运行 / 实验批次 / 划分 / 退化 / 方法 / 文物筛选 / 分层切换，全部与 URL 同步。 */
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

const batchCaption = (b: BatchInfo) => b.id === 'controlled-rubbings-v2-text-2026-10-17' ? '文字区受控实验 · 10.17' : b.id === 'controlled-rubbings-v2-2026-10-17' ? '受控实验 v2 · 10.17' : b.kind === 'historical' ? '历史实验 · 先验泄漏' : b.title;
export const ReportContextBar: React.FC<Props> = ({ stele, view, runs, runId, selection, batches, experimentId, model, setFilters, onSelectRun, onSelectBatch, onExportJson, onPrint, onNavigate }) => {
  const [copied, setCopied] = useState('');
  const copy = async () => { try { await navigator.clipboard.writeText(window.location.href); setCopied('链接已复制'); } catch { setCopied('请复制浏览器地址栏'); } setTimeout(() => setCopied(''), 2500); };
  return <header className="report-context print:hidden" data-testid="report-context-bar" aria-label="报告上下文">
    <div className="studio-page-header"><div><h1>碑拓图像修复 · 算法实验</h1><p>比较真实处理结果，沿着证据理解方法的作用与边界。</p></div><details className="studio-mobile-actions"><summary>报告操作</summary><div><button onClick={copy}>复制链接</button><button onClick={onExportJson}>导出 JSON</button><button onClick={onPrint}>打印 / 保存 PDF</button></div></details><div className="studio-header-actions">{copied && <span role="status">{copied}</span>}<button onClick={copy}>复制链接</button><button onClick={onExportJson}>导出 JSON</button><button onClick={onPrint}>打印 / 保存 PDF</button></div></div>
    <div className="studio-toolbar"><div role="tablist" aria-label="报告分层" className="studio-view-tabs"><button role="tab" aria-selected={view === 'global'} onClick={() => setFilters({ view: 'global' })}>全局评测</button><button role="tab" aria-selected={view === 'artifact'} onClick={() => setFilters({ view: 'artifact' })}>本件处理报告</button></div>
      <label className="studio-context-field">实验批次<select aria-label="实验批次" value={experimentId} onChange={e => { const b = batches.state === 'ok' ? batches.data.find(x => x.id === e.target.value) : undefined; if (b) onSelectBatch(b); }} disabled={batches.state !== 'ok'}>{!experimentId && <option value="">请选择批次</option>}{batches.state === 'ok' ? batches.data.map(b => <option key={b.id} value={b.id}>{batchCaption(b)}{b.isDefault ? ' · 默认' : ''}{b.hasImages ? '' : ' · 仅数值'}</option>) : <option value="">{batches.state === 'loading' ? '读取中…' : '实验登记不可用'}</option>}</select></label>
      {view === 'global' && model && <label className="studio-context-field">方法<select aria-label="处理方法" value={model.method} onChange={e => setFilters({ method: e.target.value, case: '' })}>{model.methods.map(m => <option key={m} value={m}>{methodLabel(m)}</option>)}</select></label>}
      <details className="studio-filter-more" open={view === 'artifact' || undefined}><summary>{view === 'global' ? '筛选与实验上下文' : '文物与运行选择'}</summary><div className="studio-filter-fields"><span>文物：《{stele.title}》 · {stele.id}</span>
        <label className="studio-context-field">本件运行<select aria-label="本件运行" value={runId} onChange={e => onSelectRun(e.target.value)} disabled={runs.state !== 'ok'}><option value="">{runs.state === 'ok' ? (runs.data.length ? '未选择' : '本件尚无运行') : runs.state === 'loading' ? '读取中…' : '运行记录不可用'}</option>{runs.state === 'ok' && runs.data.map(x => <option key={x.run.runId} value={x.run.runId}>{x.legacy ? '［legacy 旧版未验证］' : ''}{x.run.runId} · {x.time != null ? formatTime(x.run.finishedAt || x.run.startedAt) : '时间未记录'}</option>)}</select></label>
        <button onClick={() => onNavigate('workbench')}>前往工作台 →</button>
        {view === 'global' && model && <>{model.splitAvailable ? <label className="studio-context-field">划分<select aria-label="数据分组" value={model.split} onChange={e => setFilters({ split: e.target.value, case: '' })}>{['test', 'development'].map(x => <option key={x} value={x}>{SPLIT_LABELS[x]}</option>)}</select></label> : <span data-testid="split-none">本批未划分</span>}
          <label className="studio-context-field">退化<select aria-label="退化类型筛选" value={model.degradation} onChange={e => setFilters({ deg: e.target.value === 'all' ? '' : e.target.value, case: '' })}>{['all', ...model.degradations].map(d => <option key={d} value={d}>{degradationLabel(d)}</option>)}</select></label>
          <label className="studio-context-field">文物<select aria-label="实验样本" value={model.sample} onChange={e => setFilters({ sample: e.target.value, case: '' })}><option value="">全部（{model.samples.length} 件）</option>{model.samples.map(x => <option key={x}>{x}</option>)}</select></label></>}
        {selection.state === 'ok' && selection.data.runSelection && <span data-testid="run-selection-rule">{selection.data.runSelection.rule === 'explicit' ? '指定运行' : selection.data.runSelection.rule === 'latest_non_legacy' ? '默认：最新的非 legacy 运行（后端选定）' : '没有可默认的运行'}</span>}{selection.state === 'missing' && <span role="alert">{selection.message}</span>}
      </div></details>
    </div>
  </header>;
};
