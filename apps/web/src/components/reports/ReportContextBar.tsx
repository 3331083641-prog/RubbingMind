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
  panel: 'overview' | 'failures';
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

const sel = 'bg-slate-950 border border-slate-700 rounded px-1.5 py-1 text-xs text-slate-100 max-w-[16rem]';
const tab = (on: boolean) => `px-3 py-1.5 text-xs rounded-md border transition ${on ? 'bg-gold text-slate-950 border-gold font-bold' : 'border-slate-600 text-slate-300 hover:border-gold/60'}`;

export const ReportContextBar: React.FC<Props> = ({ stele, view, panel, runs, runId, selection, batches, experimentId, model, setFilters, onSelectRun, onSelectBatch, onExportJson, onPrint, onNavigate }) => {
  const [copied, setCopied] = useState('');
  const copy = async () => { try { await navigator.clipboard.writeText(window.location.href); setCopied('链接已复制'); } catch { setCopied('无法写入剪贴板，请手动复制地址栏'); } setTimeout(() => setCopied(''), 2500); };
  return <div className="sticky top-[68px] z-20 rounded-xl border border-gold/25 bg-[#0c1115]/95 backdrop-blur px-3 py-2 space-y-2 print:hidden" data-testid="report-context-bar" aria-label="报告上下文">
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
      <h2 className="font-serif text-gold text-lg mr-2">算法评测报告</h2>
      <div role="tablist" aria-label="报告分层" className="flex gap-1">
        <button role="tab" aria-selected={view === 'global'} className={tab(view === 'global')} onClick={() => setFilters({ view: 'global' })}>全局评测</button>
        <button role="tab" aria-selected={view === 'artifact'} className={tab(view === 'artifact')} onClick={() => setFilters({ view: 'artifact' })}>本件处理报告</button>
      </div>
      {view === 'global' && <div role="tablist" aria-label="全局评测栏目" className="flex gap-1">
        <button role="tab" aria-selected={panel === 'overview'} className={tab(panel === 'overview')} onClick={() => setFilters({ panel: 'overview' })}>总览与对照</button>
        <button role="tab" aria-selected={panel === 'failures'} className={`${tab(panel === 'failures')} ${panel !== 'failures' ? 'border-cinnabar/50 text-cinnabar-light' : ''}`} onClick={() => setFilters({ panel: 'failures' })}>失败案例与不确定性</button>
      </div>}
      <div className="ml-auto flex items-center gap-2">
        {copied && <span className="text-[11px] text-celadon-light">{copied}</span>}
        <button type="button" onClick={copy} className="px-2.5 py-1 text-xs border border-slate-600 rounded-md">复制链接</button>
        <button type="button" onClick={onExportJson} className="px-2.5 py-1 text-xs border border-gold/40 rounded-md">导出 JSON</button>
        <button type="button" onClick={onPrint} className="px-2.5 py-1 text-xs bg-cinnabar rounded-md">打印 / 保存 PDF</button>
      </div>
    </div>
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-slate-300">
      <span title="在页头“当前碑刻”中切换">文物：<b className="text-slate-100">《{stele.title}》</b> <code className="text-slate-400">{stele.id}</code></span>
      <label>本件运行
        <select aria-label="选择报告运行记录" className={`${sel} ml-1`} value={runId} onChange={e => onSelectRun(e.target.value)} disabled={runs.state !== 'ok'}>
          <option value="">{runs.state === 'ok' ? (runs.data.length ? '未选择' : '本件尚无运行') : runs.state === 'loading' ? '读取中…' : '运行记录不可用'}</option>
          {runs.state === 'ok' && runs.data.map(x => <option key={x.run.runId} value={x.run.runId}>{x.legacy ? '［legacy 旧版未验证］' : ''}{x.run.runId} · {x.time != null ? formatTime(x.run.finishedAt || x.run.startedAt) : '时间未记录'}</option>)}
        </select>
      </label>
      {selection.state === 'ok' && selection.data.runSelection && <span className="text-[11px] text-slate-400" data-testid="run-selection-rule">{selection.data.runSelection.rule === 'explicit' ? '指定运行' : selection.data.runSelection.rule === 'latest_non_legacy' ? '默认：最新的非 legacy 运行（后端选定）' : '没有可默认的运行'}{selection.data.runSelection.legacyRunCount ? ` · legacy ${selection.data.runSelection.legacyRunCount} 条不作默认` : ''}</span>}
      {selection.state === 'missing' && <span role="alert" className="text-[11px] text-cinnabar-light">{selection.message}</span>}
      <button type="button" className="text-gold underline" onClick={() => onNavigate('workbench')}>前往工作台</button>
      <label>实验批次
        <select aria-label="实验批次" className={`${sel} ml-1`} value={experimentId} onChange={e => { const b = batches.state === 'ok' ? batches.data.find(x => x.id === e.target.value) : undefined; if (b) onSelectBatch(b); }} disabled={batches.state !== 'ok'}>
          {!experimentId && <option value="">请选择批次</option>}
          {batches.state === 'ok' ? batches.data.map(b => <option key={b.id} value={b.id}>{b.title}{b.isDefault ? ' · 默认' : ''}{b.hasImages ? '' : ' · 仅数值'}</option>) : <option value="">{batches.state === 'loading' ? '读取中…' : '实验登记不可用'}</option>}
        </select>
      </label>
      {model && <>
        <label>划分
          {model.splitAvailable
            ? <select aria-label="数据分组" className={`${sel} ml-1`} value={model.split} onChange={e => setFilters({ split: e.target.value, case: '' })}>{['test', 'development'].map(s => <option key={s} value={s}>{SPLIT_LABELS[s]}</option>)}</select>
            : <span className="ml-1 rounded border border-slate-600 px-1.5 py-0.5 text-slate-300" data-testid="split-none" title="记录没有 split 字段">本批未划分</span>}
        </label>
        <span className="flex flex-wrap gap-1" role="group" aria-label="退化类型">
          {['all', ...model.degradations].map(d => <button key={d} type="button" aria-pressed={model.degradation === d} onClick={() => setFilters({ deg: d === 'all' ? '' : d, case: '' })} className={`px-1.5 py-0.5 rounded border ${model.degradation === d ? 'bg-celadon/30 border-celadon text-celadon-bright' : 'border-slate-700 text-slate-400'}`}>{degradationLabel(d)}</button>)}
        </span>
        <label>方法
          <select aria-label="处理方法" className={`${sel} ml-1`} value={model.method} onChange={e => setFilters({ method: e.target.value, case: '' })}>{model.methods.map(m => <option key={m} value={m}>{methodLabel(m)}</option>)}</select>
        </label>
        <label>文物
          <select aria-label="实验样本" className={`${sel} ml-1`} value={model.sample} onChange={e => setFilters({ sample: e.target.value, case: '' })}><option value="">全部（{model.samples.length} 件）</option>{model.samples.map(s => <option key={s} value={s}>{s}</option>)}</select>
        </label>
      </>}
    </div>
  </div>;
};
