import React, { useEffect, useState } from 'react';
import { ProcessingRun, SteleItem, roleText } from '../types/stele';
import { SteleService } from '../services/api';
import { ExperimentExplorer } from '../components/ExperimentExplorer';
import { HeldoutComparison } from '../components/HeldoutComparison';

interface Props { stele: SteleItem; onNavigate: (tab: string) => void }
type Report = Awaited<ReturnType<typeof SteleService.getReport>>;

export const ReportsPage: React.FC<Props> = ({ stele, onNavigate }) => {
  useEffect(() => { document.body.classList.add('printing-report'); return () => document.body.classList.remove('printing-report'); }, []);
  const [runs, setRuns] = useState<ProcessingRun[]>([]);
  const [runId, setRunId] = useState('');
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    let active = true;
    setRunId(''); setRuns([]); setReport(null);
    SteleService.listRuns(stele.id).then(items => {
      if (active) { setRuns(items); setRunId(items[0]?.runId || ''); }
    }).catch(e => { if (active) setError(String(e)); });
    return () => { active = false; };
  }, [stele.id]);
  useEffect(() => {
    let active = true;
    SteleService.getReport(stele.id, runId || undefined).then(value => {
      if (active) setReport(value);
    }).catch(e => { if (active) setError(String(e)); });
    return () => { active = false; };
  }, [stele.id, runId]);

  const run = runId ? report?.run : null;
  const reportId = run ? `RM-${stele.id}-${run.runId}` : `RM-${stele.id}-未执行`;
  const exportData = () => {
    const data = {
      reportId, exportedAt: new Date().toISOString(),
      stele: { id: stele.id, title: stele.title, dynasty: stele.dynasty,
        originalYear: stele.originalYear || stele.year, rubbingPeriod: stele.rubbingPeriod,
        collectionInstitution: stele.collectionInstitution || stele.museum,
        collectionNumber: stele.collectionNumber, sourceUrl: stele.sourceUrl,
        license: stele.license },
      runId: run?.runId || null, algorithmVersion: run?.algorithmVersion || null,
      inputImageSha256: run?.inputImageSha256 || null,
      workingImage:run?.workingImage||null,randomSeed:run?.randomSeed??null,
      damageMaskSha256:run?.damageMaskSha256||null,outputSha256:run?.outputSha256||null,
      imageRoles:run?.imageRoles||null,adaptiveDiagnostics:run?.adaptiveDiagnostics||null,
      algorithmParameters: run?.algorithmParameters || null,
      startedAt: run?.startedAt || null, finishedAt: run?.finishedAt || null,
      processingTimeMs: run?.processing_time_ms || null, outputImages: run?.outputImages || null,
      evaluationStatus: run?.evaluationStatus || 'not_run',
      evaluationMetrics: run?.evaluationMetrics || null, diagnosticMetrics: run?.diagnosticMetrics || null,
      inferenceRecords: report?.inferenceRecords || [], sourceRecords: report?.sourceRecords || [],
      note: '无配对真值时，诊断变化量不代表修复质量；残字建议须经人工核实。'
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a'); link.href = url; link.download = `${reportId}.json`; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  return <div className="min-h-screen bg-[#0A0D12] text-slate-100 p-4 lg:p-8 space-y-5">
    <header className="flex flex-wrap justify-between items-center gap-4 print:hidden">
      <div><h2 className="text-xl font-serif text-gold">墨韵智考·金石数字化实验报告</h2>
        <p className="text-xs text-slate-400">真实运行记录、馆藏出处与人工释读状态</p></div>
      <div className="flex gap-2">
        <button onClick={exportData} className="px-4 py-2 border border-gold/40 rounded-lg">导出 JSON</button>
        <button onClick={() => window.print()} className="px-4 py-2 bg-cinnabar rounded-lg">打印 / 保存 PDF</button>
      </div>
    </header>
    <label className="block print:hidden text-sm">选择本件处理运行：
      <select aria-label="选择报告运行记录" value={runId} onChange={e=>setRunId(e.target.value)} className="ml-2 bg-slate-900 border border-gold/30 rounded p-2">
        <option value="">尚未执行 / 仅查看馆藏资料</option>
        {runs.map(item=><option key={item.runId} value={item.runId}>{item.runId} · {item.finishedAt}</option>)}
      </select>
      <button className="ml-4 text-gold underline" onClick={()=>onNavigate('workbench')}>前往工作台</button>
    </label>
    {error && <p role="alert" className="text-cinnabar">{error}</p>}
    <HeldoutComparison />
    <ExperimentExplorer />
    <article className="bg-[#eee4d2] text-[#30271d] p-6 md:p-10 rounded-xl max-w-5xl mx-auto space-y-6 print:shadow-none print:p-0">
      <div className="border-b border-[#937d5d] pb-4"><h1 className="text-2xl font-serif font-bold">墨韵智考·金石数字化实验报告</h1>
        <p>《{stele.title}》 · {stele.dynasty} · 原刻：{stele.originalYear || stele.year}</p>
        <p className="text-xs mt-2">编号：{reportId} · 生成：{new Date().toLocaleString('zh-CN')}</p></div>
      <section><h3 className="font-bold">馆藏身份与出处</h3>
        <p>拓本年代：{stele.rubbingPeriod || '未核定'}；馆藏：{stele.collectionInstitution || stele.museum}；编号：{stele.collectionNumber || '未提供'}。</p>
        <p>类型：{stele.artifactType || '拓本'}；书体：{stele.script_type || '未核定'}；撰文：{roleText(stele.inscriptionAuthor, stele.authorVerification)}；书丹：{roleText(stele.calligrapher, stele.calligrapherVerification)}；篆额：{roleText(stele.titleCalligrapher, stele.titleCalligrapherVerification)}；刻工：{roleText(stele.engraver, stele.engraverVerification)}；碑主/墓主：{roleText(stele.steleSubject, stele.steleSubjectVerification)}。</p>
        <p>拓本影像损伤：{stele.imageCondition || '待人工复核'}（{stele.imageConditionReviewStatus || '自动初筛，待人工复核'}）。原石：{stele.physicalStoneWeathering || stele.stoneWeathering || '无可靠原石证据，不评定'}。</p>
        {stele.assessmentRunId && <p>归档评估运行：{stele.assessmentRunId}。这是局部处理记录，不是全幅修复质量评分。</p>}
        {stele.sourceUrl && <p>馆藏来源：<a href={stele.sourceUrl} className="underline break-all">{stele.sourceUrl}</a></p>}
        <p>影像许可：{stele.license || '需核查'}。</p>
      </section>
      <section><h3 className="font-bold">处理与评测</h3>
        {run ? <div className="space-y-1">
          <p>运行 ID：{run.runId}；算法版本：{run.algorithmVersion}；耗时：{run.processing_time_ms} ms。</p>
          <p>开始：{run.startedAt}；结束：{run.finishedAt}。</p>
          <p>输入 SHA-256：<code className="break-all">{run.inputImageSha256}</code></p>
          <div>参数：<pre className="whitespace-pre-wrap break-all text-xs">{JSON.stringify(run.algorithmParameters, null, 2)}</pre></div>
          <p>评测状态：{run.evaluationStatus === 'paired_reference' ? '有配对真值' : '未进行配对质量评测'}。</p>
          {run.evaluationStatus === 'paired_reference' && <p>PSNR：{run.evaluationMetrics?.psnr ?? '未评测'}；SSIM：{run.evaluationMetrics?.ssim ?? '未评测'}。</p>}
          <div>输入／输出诊断变化量：<pre className="whitespace-pre-wrap break-all text-xs">{JSON.stringify(run.diagnosticMetrics, null, 2)}</pre>这些数值不代表原字修复正确率。</div>
          {run.outputImages?.restored && <figure className="max-w-lg"><img src={run.outputImages.restored} alt={`${stele.title}本次处理结果`} className="max-h-[460px] object-contain"/><figcaption className="text-xs">本次算法输出；不作为原刻真值。</figcaption></figure>}
        </div> : <p>尚未执行处理。没有真实运行输出或配对真值评测。</p>}
      </section>
      <section><h3 className="font-bold">残字推演与人工确认</h3>
        {report?.inferenceRecords?.length ? <ul className="list-disc pl-5">{report.inferenceRecords.map((item, index) => <li key={item.inferenceId || index} className="mb-2">
          <p>记录 {item.inferenceId} · {item.source} · {item.status} · 人工采纳：{item.adoptedGlyph || '无'}</p>
          <p>选区：{item.bbox.x}, {item.bbox.y}, {item.bbox.w}×{item.bbox.h}；上下文：{item.context || '未提供'}</p>
          <p>候选：{item.candidates.map(c=>`${c.glyph}（${c.scoreBasis}）`).join('、') || '无可靠候选'}</p>
          {item.candidates.flatMap(c=>c.sourceUrls).map(url=><p key={url}>候选建议来源（未作为核验引用）：<a href={url} className="underline break-all">{url}</a></p>)}
        </li>)}</ul> : <p>未完成与本运行关联的真实残字推演；没有人工确认结论。</p>}
      </section>
      <section><h3 className="font-bold">古碑识别</h3><p>古碑 OCR 准确率：未评测。尚无按碑刻隔离的独立人工标注测试集。</p></section>
      <footer className="border-t border-[#937d5d] pt-3 text-xs">实验结果仅描述此次处理与已有资料；任何文物释读结论须由具备领域知识的人员复核。</footer>
    </article>
  </div>;
};
