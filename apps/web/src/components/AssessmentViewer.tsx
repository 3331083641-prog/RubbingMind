import React, { useEffect, useState } from 'react';

type Review = {
  reviewer: string;
  damageTypes: string[];
  note: string;
  suggestedCondition?: string | null;
  savedAt: string;
  basis: string;
};
type Cell = { row: number; col: number; contrastStd?: number; laplacianVariance?: number };
type AssessmentRecord = {
  steleId: string;
  title: string;
  runId: string;
  algorithmVersion: string;
  parameters: Record<string, number>;
  processingTimeMs: number;
  restorationScope: string;
  cropBox: { x: number; y: number; width: number; height: number };
  imageDimensions: { readable: number[] };
  sourcePublicUrl: string;
  sourceImageSha256: string;
  inputImageSha256: string;
  outputImageSha256: string;
  inputRoiUrl: string;
  outputUrl: string;
  fidelityGate: { accepted?: boolean; meanAbsoluteChange?: number; basis?: string };
  adaptiveDecisions: { operator: string; reason: string }[];
  imageCondition: string;
  gradeReasons: string[];
  imageConditionReviewStatus: string;
  humanReview: Review | null;
  unchanged: boolean;
  unchangedNote: string | null;
  evaluationStatus: string;
  physicalStoneWeathering: string;
  authorship: {
    roles: Record<string, { name?: string | null; verificationStatus?: string; note?: string } | null>;
    evidence: { field: string; quote: string; verificationStatus: string; sourceLabel?: string; location: string }[];
    conflicts: { field: string; detail: string }[];
  } | null;
  regionAnalysis: {
    capture: { note: string };
    mountingAndScan: { note: string; borderContrastStd: number };
    suspectedLocalFading: Cell[];
    suspectedNonTextTexture: Cell[];
    limitations: string[];
    reviewStatus: string;
  } | null;
  limitations: string[];
  coverage: string;
};

const DAMAGE = ['拓纸破损', '扫描模糊', '墨色不均', '字迹漫漶', '残笔', '缺字', '裱边或接缝', '石花纹理', '无法判断'];
const ROLE_LABEL: Record<string, string> = {
  inscriptionAuthor: '撰文', calligrapher: '书丹', titleCalligrapher: '篆额', engraver: '刻工', steleSubject: '碑主或墓主',
};

export const AssessmentViewer: React.FC<{ steleId: string; onClose: () => void }> = ({ steleId, onClose }) => {
  const [record, setRecord] = useState<AssessmentRecord | null>(null);
  const [error, setError] = useState('');
  const [split, setSplit] = useState(50);
  const [zoom, setZoom] = useState(1);
  const [reviewer, setReviewer] = useState('');
  const [note, setNote] = useState('');
  const [types, setTypes] = useState<string[]>([]);
  const [suggestion, setSuggestion] = useState('');
  useEffect(() => {
    let live = true;
    setRecord(null); setError('');
    fetch(`/api/catalog/${encodeURIComponent(steleId)}/assessment`).then(async response => {
      if (!response.ok) throw new Error('评估记录不可用');
      return response.json();
    }).then(data => { if (live) setRecord(data); }).catch(reason => { if (live) setError(String(reason)); });
    return () => { live = false; };
  }, [steleId]);
  const save = async () => {
    const response = await fetch(`/api/catalog/${encodeURIComponent(steleId)}/assessment/review`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer, damageTypes: types, note, suggestedCondition: suggestion || null }),
    });
    if (!response.ok) { setError(await response.text()); return; }
    const saved = await response.json();
    setRecord(current => current ? { ...current, humanReview: saved, imageConditionReviewStatus: '已保存复核意见，尚未作为正式鉴定' } : current);
  };
  const box = record?.cropBox;
  const frame = record?.imageDimensions?.readable;
  return <div role="dialog" aria-modal="true" aria-label="馆藏评估" className="fixed inset-0 z-[80] bg-black/90 overflow-auto p-4 md:p-8 text-slate-100">
    <div className="max-w-6xl mx-auto space-y-5">
      <div className="flex justify-between gap-3"><h2 className="font-serif text-xl text-gold">{record?.title || steleId} · 馆藏评估</h2><button onClick={onClose}>关闭</button></div>
      {error && <p role="alert" className="text-cinnabar-light">{error}</p>}
      {!record ? <p>正在读取归档评估…</p> : <>
        {record.unchanged && <p className="border border-gold/40 bg-gold/10 p-3 text-sm">算法判定无需增强。处理前后像素没有发生变化，这里不用视觉效果假装修复有效。</p>}
        <section className="grid lg:grid-cols-[1.4fr_0.8fr] gap-4">
          <div>
            <div className="flex gap-2 text-xs mb-2">
              <button onClick={() => setZoom(1)}>原始大小</button>
              <button onClick={() => setZoom(1.5)}>放大</button>
              <button onClick={() => setZoom(2)}>再放大</button>
            </div>
            <div className="overflow-auto bg-black border border-gold/20">
              <div className="relative inline-block" style={{ width: 512 * zoom }}>
                <img src={record.outputUrl} alt="处理后局部" className="block w-full h-auto" />
                <img src={record.inputRoiUrl} alt="处理前局部" className="absolute inset-0 w-full h-auto" style={{ clipPath: `inset(0 ${100 - split}% 0 0)` }} />
              </div>
            </div>
            <label className="block text-xs mt-2">处理前 / 处理后<input aria-label="处理前后对比" type="range" min={0} max={100} value={split} onChange={event => setSplit(Number(event.target.value))} className="block w-full" /></label>
            <p className="text-xs text-slate-400">左侧是处理前的同一 ROI，右侧是归档输出。拖动分隔线对照。</p>
          </div>
          <div className="space-y-2 text-sm">
            <h3 className="text-gold font-serif">ROI 位置</h3>
            {frame && box && <div className="relative bg-slate-950 border border-slate-700" style={{ aspectRatio: `${frame[0]} / ${frame[1]}`, maxHeight: 360 }}>
              <img src={record.sourcePublicUrl} alt="阅读图上的处理范围" className="w-full h-full object-contain opacity-80" />
              <div className="absolute border-2 border-cinnabar" style={{ left: `${box.x / frame[0] * 100}%`, top: `${box.y / frame[1] * 100}%`, width: `${box.width / frame[0] * 100}%`, height: `${box.height / frame[1] * 100}%` }} />
            </div>}
            <p className="text-xs">范围：{record.restorationScope} · x {box?.x}，y {box?.y}，{box?.width}×{box?.height}。这是局部结果，不是全幅。</p>
          </div>
        </section>
        <section className="grid md:grid-cols-2 gap-4 text-sm">
          <div>
            <h3 className="text-gold font-serif">实际损伤诊断</h3>
            <p>自动初筛：{record.imageCondition}</p>
            <p>{record.imageConditionReviewStatus}</p>
            <ul className="list-disc pl-5 text-xs text-slate-300">{record.gradeReasons?.map(item => <li key={item}>{item}</li>)}</ul>
            {record.regionAnalysis && <div className="text-xs mt-2 space-y-1">
              <p>{record.regionAnalysis.capture.note}</p>
              <p>{record.regionAnalysis.mountingAndScan.note}外缘对比度标准差 {record.regionAnalysis.mountingAndScan.borderContrastStd}。</p>
              <p>疑似局部变淡分区 {record.regionAnalysis.suspectedLocalFading.length} 个；疑似非文字纹理分区 {record.regionAnalysis.suspectedNonTextTexture.length} 个。均未改写已发布等级。</p>
              {record.regionAnalysis.limitations.map(item => <p key={item}>{item}</p>)}
            </div>}
          </div>
          <div>
            <h3 className="text-gold font-serif">本件算法处理</h3>
            <p>运行 {record.runId} · {record.algorithmVersion} · {record.processingTimeMs.toFixed(1)} ms</p>
            <p>参数：{JSON.stringify(record.parameters)}</p>
            <p>门控：{record.fidelityGate?.accepted ? '通过' : '未通过'} · 平均绝对变化 {record.fidelityGate?.meanAbsoluteChange}</p>
            <p className="text-xs break-all">输入 ROI SHA {record.inputImageSha256}</p>
            <p className="text-xs break-all">输出 SHA {record.outputImageSha256}</p>
            <p className="text-xs break-all">阅读图 SHA {record.sourceImageSha256}</p>
            <ul className="text-xs list-disc pl-5">{record.adaptiveDecisions?.map(item => <li key={item.operator + item.reason}>{item.operator}：{item.reason}</li>)}</ul>
            <p>配对真值：{record.evaluationStatus}。PSNR、SSIM 不报告。</p>
            <p>原石：{record.physicalStoneWeathering}</p>
          </div>
        </section>
        <section>
          <h3 className="text-gold font-serif">史料与署名核定</h3>
          {record.authorship ? <div className="text-sm space-y-1">
            {Object.entries(record.authorship.roles).map(([key, role]) => <p key={key}>{ROLE_LABEL[key] || key}：{role?.name || '未核定'} · {role?.verificationStatus || 'unknown'} · {role?.note || ''}</p>)}
            {record.authorship.evidence.filter(item => item.field === 'otherSignature' || item.field === 'characterCompilation').map(item => <p key={item.quote}>其他署名：{item.quote} · {item.verificationStatus} · {item.sourceLabel}</p>)}
            {record.authorship.conflicts.map(item => <p key={item.detail}>争议：{item.detail}</p>)}
          </div> : <p>没有署名核定记录。</p>}
        </section>
        <section className="text-xs text-slate-400 space-y-1">
          <h3 className="text-gold font-serif text-sm">来源及评估限制</h3>
          <p>{record.coverage}</p>
          {record.limitations.map(item => <p key={item}>{item}</p>)}
        </section>
        <form className="border border-slate-700 p-3 space-y-2 text-sm" onSubmit={event => { event.preventDefault(); void save(); }}>
          <h3 className="text-gold font-serif">人工复核</h3>
          <p className="text-xs">提交后只保存为复核意见，不会把自动初筛改成已鉴定。</p>
          {record.humanReview && <p>已有意见：{record.humanReview.reviewer} · {record.humanReview.damageTypes.join('、')} · {record.humanReview.note}</p>}
          <input aria-label="复核者" value={reviewer} onChange={event => setReviewer(event.target.value)} placeholder="复核者" className="bg-slate-950 border border-slate-700 p-2" />
          <div className="flex flex-wrap gap-2 text-xs">{DAMAGE.map(item => <label key={item}><input type="checkbox" checked={types.includes(item)} onChange={() => setTypes(current => current.includes(item) ? current.filter(value => value !== item) : [...current, item])} /> {item}</label>)}</div>
          <textarea aria-label="复核依据" value={note} onChange={event => setNote(event.target.value)} placeholder="看到了什么，依据是哪一处图像" className="w-full bg-slate-950 border border-slate-700 p-2" />
          <label className="text-xs">建议等级（可选，不覆盖自动初筛）
            <select aria-label="建议等级" value={suggestion} onChange={event => setSuggestion(event.target.value)} className="ml-2 bg-slate-950 p-1"><option value="">不建议改级</option>{['轻度影像损伤', '中度影像损伤', '重度影像损伤', '严重漫漶', '无法判断'].map(item => <option key={item}>{item}</option>)}</select>
          </label>
          <button className="block text-gold" disabled={!reviewer || !note || types.length === 0}>保存复核意见</button>
        </form>
      </>}
    </div>
  </div>;
};
