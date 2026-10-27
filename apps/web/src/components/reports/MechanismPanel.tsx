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
  const [step, setStep] = useState(0);
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
  const images = detail?.state === 'ok' ? (detail.data.file.images || []) : [];

  const openInOverview = (c: MechanismCase) => {
    setFilters({ panel: 'images', split: c.split, deg: c.degradation, method: 'adaptive_joint', sample: c.sampleId, case: c.caseId });
  };

  const row = selected ? model.rowsAll.find(r => r.caseId === selected.caseId && r.method === 'adaptive_joint') : undefined;
  const stepFiles = ['', 'spectrum_input.png', '', 'foreground_output.png', 'edges_output.png', 'diff_output_input.png'];
  const image = images.find(i => i.file === stepFiles[step]);
  const src = step === 0 && row?.input ? ReportApi.assetUrl(model.batch.id, row.input) : image && selected ? ReportApi.mechanismAssetUrl(model.batch.id, model.batch.registry.directory, selected.caseId, image.file) : null;
  return <div className="studio-mechanism" data-testid="mechanism-panel">
    <p className="studio-chart-note">只展示真实 MEC 重放记录；保真门控是启发式规则。没有记录的步骤保留空状态。</p>
    {index.state === 'loading' && <p role="status">读取机制索引…</p>}
    {(index.state === 'missing' || index.state === 'error') && <p role="alert" data-testid="mechanism-index-missing">本批机制样本未接入：{index.message}。不使用其他批次代替。</p>}
    {index.state === 'ok' && <>
      <label className="studio-context-field">机制案例<select aria-label="机制案例" value={selectedId} onChange={e => { setSelectedId(e.target.value); setStep(0); setFilters({ case: e.target.value }); }}>{cases.map(c => <option key={c.caseId} value={c.caseId}>{CATEGORY_LABEL[c.category] || c.category} · {c.sampleId} · {degradationLabel(c.degradation)} · {c.split}</option>)}</select></label>
      <p className="studio-caption" data-testid="mechanism-head-lag-note">历史重放 · head {index.data.file.headCommit?.slice(0, 12) || '未记录'}。机制图尚未与最新交付代码对齐。</p>
      <div className="studio-mechanism-steps" role="tablist" aria-label="真实机制步骤">{['输入图像', '频域分析', '方法选择', '处理前景', '保真判断', '输出差分'].map((label, i) => <button role="tab" key={label} aria-selected={step === i} onClick={() => setStep(i)}>{label}<span aria-hidden="true">{i < 5 ? '→' : ''}</span></button>)}</div>
      {detail?.state === 'loading' && <p role="status">读取 mechanism.json…</p>}
      {detail && (detail.state === 'missing' || detail.state === 'error') && <p role="alert" data-testid="mechanism-detail-missing">单案文件不可用：{detail.message}，不展示虚构决策。</p>}
      {selected && detail?.state === 'ok' && <div data-testid="mechanism-detail">
        <div className="studio-mechanism-view"><figure>{src ? <img key={src} src={src} alt={step === 0 ? '本案例退化输入原图' : image?.description || stepFiles[step]} onError={e => { e.currentTarget.hidden = true; e.currentTarget.parentElement!.dataset.imageError = '图像不可用'; }} /> : <div className="studio-empty">{step === 2 ? '本步以实际决策记录说明' : '本步影像未记录'}</div>}<figcaption>{step === 0 ? '原始实验输入，完整显示' : image?.description || '没有本步影像'}{image?.sha256 ? ` · SHA ${shortSha(image.sha256)}` : ''}</figcaption></figure>
          <div><h3>{['实际输入', '频谱观测', '真实方法选择', '处理后的前景掩膜', '保真门控记录', '输出与输入差分'][step]}</h3>
            {step === 2 ? <ol>{decisions.length ? decisions.map((d, i) => <li key={i}><code>{d.operator}</code>：{d.reason || '原因未记录'}</li>) : <li>未记录 decisions。</li>}</ol> : step === 4 ? <p>{gate ? `${gate.accepted === true ? '通过' : gate.accepted === false ? '拒绝' : '未记录结果'} · 强边缘保留 ${gate.strongEdgeRetention?.toFixed(3) ?? '未记录'} · 平均改动 ${gate.meanAbsoluteChange?.toFixed(3) ?? '未记录'}。${gate.basis || '启发式规则，不是统计检验'}` : '未记录保真门控。'}</p> : <p>{selected.sampleId} · {degradationLabel(selected.degradation)} · {SPLIT_LABELS[selected.split] || selected.split}<br />索引 ΔPSNR {selected.psnrGain == null ? '未记录' : signed(selected.psnrGain, 3, 'dB')}</p>}
            <p className="studio-caption" data-testid="mechanism-version-split">输入来自已存实验；机制掩膜与决策链来自历史 head 重放。两者分别追溯，不冒充当前生产版本。</p>
            <button onClick={() => openInOverview(selected)}>在图像对照打开 →</button>
          </div></div>
        <details className="studio-details"><summary>全部机制证据、参数、SHA 与历史版本说明</summary><p data-testid="mechanism-der-scope">MEC 个案不是 DER 全批统计，不能以机制样本数推断处理率。</p><p>MECHANISM_HEAD_NOTE：记录 headCommit={index.data.file.headCommit}，在重跑并更新索引前不得宣称 PNG 与当前 tip 字节一致。{index.data.file.selectionRule}</p><p data-testid="mechanism-change-stats">{mech?.changeStats ? JSON.stringify(mech.changeStats) : '改动统计未记录'}</p><p>已存算法 {stored?.algorithmVersion || '未记录'}；重放输出模式 {mech?.outputMode || '未记录'}；来源 {detail.data.source}</p>
          <div className="studio-mechanism-evidence">{images.map(img => <figure key={img.file}><img src={ReportApi.mechanismAssetUrl(model.batch.id, model.batch.registry.directory, selected.caseId, img.file)} alt={img.description || img.file} loading="lazy" /><figcaption>{img.description} · {img.file} · SHA {img.sha256 || '未记录'} · head {img.headCommit || '未记录'} · {img.captionNote}</figcaption></figure>)}</div><pre>{JSON.stringify(detail.data.file, null, 2)}</pre>
        </details>
      </div>}
    </>}
  </div>;
};
