/**
 * L4 消融与机制（panel=mechanism）：只展示已有 MEC 数据（derived/mechanism）。
 * - index.json：代表样本选取规则与 5 类案例列表（E-18）
 * - 点选后读 mechanism.json：真实决策链 / 保真门控 / 改动统计 / 说明图
 * 缺失如实空状态；不伪造算子；headCommit 只展示记录值，不宣称与当前 tip 一致（R7）。
 */
import React, { useEffect, useMemo, useState } from 'react';
import type { GlobalModel } from './data/globalModel';
import { ReportApi } from './data/reportData';
import type { Derived, Loadable, MechanismCase, MechanismDetail, MechanismIndex } from './data/types';
import { degradationLabel, SPLIT_LABELS } from './data/labels';
import { shortSha, signed } from './format';
import type { ReportFilters } from './reportFilters';

interface Props { model: GlobalModel; filters: ReportFilters; setFilters: (p: ReportFilters) => void }

const CATEGORY_LABEL: Record<string, string> = {
  improvement: '提升',
  negative: '负提升',
  passthrough: '原图返回',
  gate_reject: '门控拒绝',
  notch: '陷波',
};

const CATEGORY_ORDER = ['improvement', 'negative', 'passthrough', 'gate_reject', 'notch'];

export const MechanismPanel: React.FC<Props> = ({ model, filters, setFilters }) => {
  const [index, setIndex] = useState<Loadable<Derived<MechanismIndex>>>({ state: 'loading' });
  const [selectedId, setSelectedId] = useState<string>('');
  const [detail, setDetail] = useState<Loadable<Derived<MechanismDetail>> | null>(null);

  useEffect(() => {
    let live = true;
    setIndex({ state: 'loading' });
    setSelectedId('');
    setDetail(null);
    ReportApi.mechanismIndex(model.batch.id, model.batch.registry.directory).then(r => {
      if (!live) return;
      setIndex(r);
      if (r.state === 'ok' && r.data.file.cases?.length) {
        const cases = r.data.file.cases;
        const fromUrl = filters.case && cases.some(c => c.caseId === filters.case) ? filters.case : '';
        if (fromUrl) { setSelectedId(fromUrl); }
        else {
          const first = [...cases].sort((a, b) => {
            const ca = CATEGORY_ORDER.indexOf(a.category);
            const cb = CATEGORY_ORDER.indexOf(b.category);
            return (ca < 0 ? 99 : ca) - (cb < 0 ? 99 : cb) || a.caseId.localeCompare(b.caseId);
          })[0];
          setSelectedId(first.caseId);
        }
      }
    });
    return () => { live = false; };
  }, [model.batch.id, model.batch.registry.directory]);

  useEffect(() => {
    if (!selectedId) { setDetail(null); return; }
    let live = true;
    setDetail({ state: 'loading' });
    ReportApi.mechanismCase(model.batch.id, model.batch.registry.directory, selectedId).then(r => {
      if (live) setDetail(r);
    });
    return () => { live = false; };
  }, [selectedId, model.batch.id, model.batch.registry.directory]);

  const cases = index.state === 'ok' ? index.data.file.cases || [] : [];
  const byCat = useMemo(() => {
    const m = new Map<string, MechanismCase[]>();
    cases.forEach(c => {
      const list = m.get(c.category) || [];
      list.push(c);
      m.set(c.category, list);
    });
    return m;
  }, [cases]);
  const selected = cases.find(c => c.caseId === selectedId) || null;
  const mech = detail?.state === 'ok' ? detail.data.file.mechanism : null;
  const stored = detail?.state === 'ok' ? detail.data.file.storedDiagnostics : null;
  const decisions = mech?.decisions?.length ? mech.decisions : stored?.decisions || [];
  const gate = mech?.fidelityGate || stored?.fidelityGate;
  const images = detail?.state === 'ok' ? (detail.data.file.images || []).slice(0, 8) : [];

  const openInOverview = (c: MechanismCase) => {
    setFilters({ panel: 'overview', split: c.split, deg: c.degradation, method: 'adaptive_joint', sample: c.sampleId, case: c.caseId });
  };

  return <div className="space-y-4" data-testid="mechanism-panel">
    <section aria-label="机制样本索引" className="rounded-xl border border-gold/20 bg-[#0f1418] p-4 space-y-2">
      <h3 className="font-serif text-gold text-base">消融与机制 · {model.batch.title}</h3>
      <p className="text-[11px] text-slate-400">只展示评测科学家写入的 MEC（derived/mechanism）。决策链来自真实重放记录；保真门控是启发式规则，不是统计检验。不把未接入批次的空缺填成“无决策”。</p>
      {index.state === 'loading' && <p className="text-sm text-slate-400">读取机制索引…</p>}
      {(index.state === 'missing' || index.state === 'error') && (
        <p role="alert" className="text-sm text-slate-300" data-testid="mechanism-index-missing">
          本批机制样本未接入：{index.message}。同批复测/仅数值批次通常没有机制重放图；有受控退化批次时请确认 derived/mechanism/index.json 可读。
        </p>
      )}
      {index.state === 'ok' && <>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-1 text-[11px] text-slate-300">
          <div><dt className="text-slate-500 inline">批次 </dt><dd className="inline"><code>{index.data.file.batch || model.batch.id}</code></dd></div>
          <div><dt className="text-slate-500 inline">派生时间 </dt><dd className="inline">{index.data.file.derivedAt || '未记录'}</dd></div>
          <div className="md:col-span-2"><dt className="text-slate-500 inline">记录的 headCommit </dt>
            <dd className="inline"><code className="text-[10px]">{index.data.file.headCommit || '未记录'}</code>
              {index.data.file.baseCommit ? <> · baseCommit <code className="text-[10px]">{index.data.file.baseCommit}</code></> : null}
            </dd></div>
          {index.data.file.headCommit ? (
            <div className="md:col-span-2 rounded border border-amber-700/50 bg-amber-950/30 px-2 py-1.5 text-[11px] text-amber-100/90" data-testid="mechanism-head-lag-note" role="note">
              MECHANISM_HEAD_NOTE：机制产物绑定的 headCommit=<code className="text-[10px]">{index.data.file.headCommit.slice(0, 12)}</code>… 是派生写入时的记录值，可能落后于当前分支 tip。
              在评测科学家重跑 mechanism 并更新 index.json 之前，<strong className="font-semibold">不得宣称</strong>机制 PNG / 决策链与当前 tip 字节一致；本页只展示 MEC 记录，不表示已与 tip 对齐。
            </div>
          ) : (
            <p className="md:col-span-2 text-[11px] text-slate-500" data-testid="mechanism-head-unrecorded">index 未记录 headCommit；不推断与 tip 的关系。</p>
          )}
          <div className="md:col-span-2 text-[11px] text-slate-400" data-testid="mechanism-der-scope">口径：本面板只读 MEC（derived/mechanism），不是 DER 汇总统计；不把机制样本数当作全批处理率或提升结论。</div>
          <div className="md:col-span-2"><dt className="text-slate-500">选取规则</dt>
            <dd className="whitespace-pre-wrap text-slate-400 mt-0.5">{index.data.file.selectionRule || '未记录'}</dd></div>
          <div className="md:col-span-2 text-slate-500">来源：{index.data.source}</div>
        </dl>
        {!cases.length ? <p className="text-sm text-slate-400" data-testid="mechanism-cases-empty">索引存在但 cases 为空。</p> : (
          <div className="overflow-x-auto" data-testid="mechanism-cases-table">
            <table className="w-full text-[11px] text-left">
              <thead className="text-slate-400"><tr>{['类别', '划分', 'caseId', '文物', '退化', '强度', 'ΔPSNR', 'head对照', '操作'].map(h => <th key={h} className="py-1 pr-2 font-normal">{h}</th>)}</tr></thead>
              <tbody>
                {CATEGORY_ORDER.flatMap(cat => (byCat.get(cat) || [])).concat(cases.filter(c => !CATEGORY_ORDER.includes(c.category))).map(c => (
                  <tr key={c.caseId}
                    onClick={() => { setSelectedId(c.caseId); setFilters({ case: c.caseId }); }}
                    className={`border-t border-slate-800 cursor-pointer hover:bg-gold/5 ${selectedId === c.caseId ? 'bg-gold/10' : ''}`}
                    data-testid={`mechanism-case-${c.caseId}`}
                    data-selected={selectedId === c.caseId ? '1' : '0'}>
                    <td className="pr-2">{CATEGORY_LABEL[c.category] || c.category}</td>
                    <td className="pr-2">{SPLIT_LABELS[c.split] || c.split}</td>
                    <td className="pr-2"><code className="text-[10px]">{c.caseId}</code></td>
                    <td className="pr-2">{c.sampleId}</td>
                    <td className="pr-2">{degradationLabel(c.degradation)}</td>
                    <td className="pr-2">{c.strength ?? '—'}</td>
                    <td className="pr-2">{c.psnrGain == null ? '—' : signed(c.psnrGain, 3, 'dB')}</td>
                    <td className="pr-2 text-[10px] text-slate-400">{c.headEqualsBase == null && c.headChangedVsStored == null ? '—' : [c.headEqualsBase === true ? 'head=base' : c.headEqualsBase === false ? 'head≠base' : null, typeof c.headChangedVsStored === 'number' ? `Δvs存=${c.headChangedVsStored}` : null].filter(Boolean).join(' · ') || '—'}</td>
                    <td className="pr-2"><button type="button" className="underline text-gold-light" onClick={e => { e.stopPropagation(); openInOverview(c); }}>在总览打开</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="text-[11px] text-slate-500">各类条数：{CATEGORY_ORDER.map(c => `${CATEGORY_LABEL[c]} ${(byCat.get(c) || []).length}`).join(' · ')}</p>
      </>}
    </section>

    {index.state === 'ok' && selected && (
      <section aria-label="机制案例详情" className="rounded-xl border border-gold/20 bg-[#0c1013] p-4 space-y-3" data-testid="mechanism-detail">
        <h3 className="font-serif text-gold text-sm">案例详情 · {CATEGORY_LABEL[selected.category] || selected.category} · <code className="text-xs">{selected.caseId}</code></h3>
        <p className="text-[11px] text-slate-400">{SPLIT_LABELS[selected.split] || selected.split} · {selected.sampleId} · {degradationLabel(selected.degradation)}{selected.strength != null ? ` ${selected.strength}` : ''} · 索引 ΔPSNR {selected.psnrGain == null ? '未记录' : signed(selected.psnrGain, 3, 'dB')}</p>
        {detail?.state === 'loading' && <p className="text-sm text-slate-400">读取 mechanism.json…</p>}
        {detail && (detail.state === 'missing' || detail.state === 'error') && (
          <p role="alert" className="text-sm text-slate-300" data-testid="mechanism-detail-missing">单案文件不可用：{detail.message}。仍可按索引在总览中定位该 case，不展示虚构决策。</p>
        )}
        {detail && detail.state === 'ok' && <>
          <p className="text-[11px] text-slate-500">来源：{detail.data.source}{detail.data.file.headCommit ? <> · 案记录 headCommit <code className="text-[10px]">{detail.data.file.headCommit}</code></> : null}</p>
          <p className="text-[11px] text-amber-100/80" data-testid="mechanism-version-split">已存诊断/算子来自历史运行产物（通常 v2.0 已存）；下方决策链与改动统计优先取 mechanism 重放字段（记录为 head 重算）。两者不一致时以各自标注为准，不合并成单一“当前 tip”结论。</p>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-200">实际执行步骤（决策链）</h4>
              {decisions.length ? (
                <ol className="list-decimal pl-5 space-y-1 text-[11px] text-slate-300">
                  {decisions.map((d, i) => <li key={`${d.operator}-${i}`}><code>{d.operator}</code>{d.reason ? `：${d.reason}` : ''}</li>)}
                </ol>
              ) : <p className="text-[11px] text-slate-400">该案未记录 decisions。</p>}
              {stored?.operators?.length ? <p className="text-[11px] text-slate-400">存储算子：{stored.operators.join(' → ')}（版本 {stored.algorithmVersion || '未记录'}）</p> : null}
              {mech?.outputMode ? <p className="text-[11px]">重放 outputMode：<code>{mech.outputMode}</code>{mech.notchApplied != null ? ` · 陷波=${mech.notchApplied ? '是' : '否'}` : ''}</p> : null}
            </div>
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-200">保真门控与改动</h4>
              {gate ? (
                <p className="text-[11px] text-slate-300">
                  {gate.accepted === true ? '通过' : gate.accepted === false ? '拒绝' : '—'}
                  {typeof gate.strongEdgeRetention === 'number' ? ` · 强边缘保留 ${gate.strongEdgeRetention.toFixed(3)}` : ''}
                  {typeof gate.meanAbsoluteChange === 'number' ? ` · 平均改动 ${gate.meanAbsoluteChange.toFixed(3)}` : ''}
                  {gate.basis ? `。${gate.basis}` : '（启发式规则，不是统计检验）'}
                </p>
              ) : <p className="text-[11px] text-slate-400">未记录保真门控。</p>}
              {mech?.changeStats ? (
                <p className="text-[11px] text-slate-300" data-testid="mechanism-change-stats">
                  {mech.changeStats.isPassthrough === true ? '原图返回（逐像素相同）' : mech.changeStats.isPassthrough === false ? '已改动像素' : '未能判定是否改动'}
                  {mech.changeStats.changedPixelCount != null ? ` · ${mech.changeStats.changedPixelCount} 像素` : ''}
                  {mech.changeStats.changedPixelRatio != null ? `（${(mech.changeStats.changedPixelRatio * 100).toFixed(2)}%）` : ''}
                  {mech.changeStats.passthroughCriterion ? ` · 判据 ${mech.changeStats.passthroughCriterion}` : ''}
                </p>
              ) : null}
            </div>
          </div>
          {images.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-slate-200 mb-2">机制说明图（仅本案文件）</h4>
              <div className="flex flex-wrap gap-3">
                {images.map(img => {
                  const src = ReportApi.mechanismAssetUrl(model.batch.id, model.batch.registry.directory, selected.caseId, img.file);
                  return <figure key={img.file} className="w-36">
                    <img src={src} alt={img.description || img.file} loading="lazy"
                      className="w-36 h-36 object-contain bg-[#0A0D12] rounded border border-slate-800"
                      onError={e => { (e.currentTarget as HTMLImageElement).style.opacity = '0.25'; (e.currentTarget as HTMLImageElement).alt = `${img.file}（图不可用）`; }} />
                    <figcaption className="text-[10px] text-center text-slate-400 mt-1">{img.description || img.file}{img.batch ? ` · ${img.batch}` : ''}{img.derivedAt ? ` · ${img.derivedAt.slice(0, 10)}` : ''}{img.sourcePath ? ` · ${img.sourcePath}` : ''}{img.sha256 ? ` · SHA ${shortSha(img.sha256)}` : ''}{img.headCommit ? ` · head ${shortSha(img.headCommit)}` : ''}{img.captionNote ? ` · ${img.captionNote}` : ''}</figcaption>
                  </figure>;
                })}
              </div>
              <p className="text-[10px] text-slate-500 mt-1">图加载失败时保持半透明，不替换其他批次图像。</p>
            </div>
          )}
        </>}
      </section>
    )}
  </div>;
};
