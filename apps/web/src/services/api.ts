import { SteleItem, ProcessingResult, ProcessingRun, CharacterItem, GraphNode, GraphLink, GISWaypoint, AblationMetric } from '../types/stele';
import STILES_28_DATA from '../data/steles28.json';
import { CORE_SAMPLES, resolveSelected } from '../data/catalogSelection';
export const FALLBACK_STELES = STILES_28_DATA as unknown as SteleItem[];
export let backendAvailable = false;
export interface GlyphInferenceRecord {
  inferenceId: string;
  steleId: string;
  runId?: string | null;
  imageProvenance?: {imageSource:'original'|'restored';selectedImageSha256?:string;runOwnership?:string;imageWidth?:number;imageHeight?:number};
  characterId: string | null;
  originalGlyph: string | null;
  originalStatus: string | null;
  bbox: {x:number;y:number;w:number;h:number};
  context: string;
  cropUrl: string;
  source: 'vision_model' | 'context_rule' | 'unavailable' | 'model_unavailable' | 'local_shape_retrieval';
  visualAnalysis?: {version:string;warnings:string[];componentCount:number;skeletonPixels:number;identityStatus:string;foregroundPolarity:string};
  analysisImages?: Record<string,string>;
  retrievalCandidates?: {glyph:string;visualEvidence:string;contextEvidence:string;sourceUrls:string[];scoreBasis:string}[];
  model: string | null;
  candidates: {glyph:string;visualEvidence:string;contextEvidence:string;sourceUrls:string[];scoreBasis:string}[];
  note: string;
  status: string;
  adoptedGlyph: string | null;
  decisions: {action:string;glyph:string|null;at:string;actor:string}[];
  ocrBaseline?: {status:string;engine:string;texts?:{text:string;score:number|null}[];limitation:string;countsAsAccuracy:boolean};
  createdAt: string;
}
// ---- R1 contracts (ARCHITECTURE_DECISIONS R1-1..R1-6). All fields optional so older backends still type-check. ----
export interface RunSelection { rule: 'explicit' | 'latest_non_legacy' | 'none'; runId: string | null; legacyRunCount: number }
/** REPORT_DATA_SPEC §8 run-level change fields; null = not determinable (see passthroughUndeterminedReason). */
export interface RunChangeStatus {
  isPassthrough?: boolean | null;
  changedPixelCount?: number | null;
  totalPixelCount?: number | null;
  changedPixelRatio?: number | null;
  maxAbsDiff?: number | null;
  meanAbsDiff?: number | null;
  /** 'pixel-equal-v1' (runs recorded on agent/eval-sci between f21ceaa and SPEC v3 may say 'working-gray-pixel-equal-v1'); null only when undeterminable. */
  passthroughCriterion?: string | null;
  passthroughSource?: 'recorded' | 'computed-on-read' | null;
  passthroughUndeterminedReason?: string | null;
  /** [before, after]; currently always ['original', 'restored'] */
  comparedImages?: string[];
  outputMode?: 'processed' | 'passthrough' | 'undetermined';
  /** Green 2026-10-19 (a): working-gray reference only; never decides isPassthrough. null = undeterminable. */
  grayChangedPixelCount?: number | null;
  grayChangedPixelRatio?: number | null;
  grayCriterion?: 'working-gray-pixel-equal-v1' | null;
  grayCriterionRule?: string | null;
  graySource?: 'recorded' | 'computed-on-read' | null;
  effectiveParameters?: Record<string, unknown> | null;
  effectiveParametersSource?: 'recorded' | 'derived-on-read' | null;
  /** set when effectiveParameters is null (not defined by REPORT_DATA_SPEC v3; added by the backend) */
  effectiveParametersUnavailableReason?: string | null;
}
export interface RunKindFields { legacy?: boolean; runKind?: 'processing' | 'legacy_unverified'; sortTimestamp?: string | null; sourceSteleId?: string }
export type ProcessingRunR1 = ProcessingRun & RunChangeStatus & RunKindFields;
export interface ExperimentBatchMeta {
  /** authoritative experimentId; `batch` is its readable one-to-one alias (results directory) */
  id: string; directory: string; batch?: string; rowCount: number; sampleCount: number; displayName?: string; heldOut?: boolean | null;
  imageComparisonAvailable: boolean; metricsOnly: boolean; limitations: string[];
  splitAvailable?: boolean; splits?: Record<string, number>; rowsWithoutSplit?: number;
  status?: 'valid' | 'historical-leakage' | 'metrics-only'; statusReasons?: string[];
  defaultForReport?: boolean; defaultForReportBasis?: string | null;
}
export interface ExperimentBatchIndex { items: {experimentId: string; batch: string}[]; basis: string }
/** Derived files are served read-only; available=false comes with status missing | stale and a reason. */
export interface DerivedFileState { experimentId: string; batch: string; file: string; servedBy: string; fileSha256: string | null;
  available: boolean; status: 'ok' | 'missing' | 'stale'; reason?: string }
export interface AppliedStatusResponse extends DerivedFileState {
  criterion?: string; imagesAvailable?: boolean; note?: string; sourceResultsSha256?: string;
  summaryByMethod?: Record<string, unknown>[]; summaryBySplitMethod?: Record<string, unknown>[]; summaryByMethodDegradation?: Record<string, unknown>[];
  rowCount?: number; rows?: Record<string, unknown>[];
}
export interface CiByArtifactResponse extends DerivedFileState {
  seed?: number; bootstrap?: number; percentiles?: number[]; minReliableArtifacts?: number; rngRule?: string; gainDefinition?: string;
  scopeSource?: string; groupCount?: number; filters?: Record<string, string>; groups?: Record<string, unknown>[];
}
export interface ExperimentDiagnosis {
  experimentId: string; diagnosisVersion?: 'heldout-legacy-heuristic' | 'baseline-delta-v1' | string;
  negativeLiftCount: number; cases: Record<string, unknown>[]; causeCounts: Record<string, number> | null; caveat: string;
  baselineMethod?: string; byMethod?: Record<string, {n:number;negativeLift:number;byteIdentical:number;/** @deprecated alias of byteIdentical, removed next version */byteIdenticalToInput?:number;byteIdentityUnknown:number;unmatched:number}>;
}

function selected(id: string) { return resolveSelected(FALLBACK_STELES, id); }
export type ReportStatus = 'ok' | 'stele_not_found' | 'stele_retired' | 'run_not_found' | 'backend_unavailable' | 'error';
export interface ReportPayload {
  ablation: AblationMetric[]; evaluation_summary: string; scholarly_analysis: string; rubbing_dimensions: string; epigraphic_conclusion: string;
  run: ProcessingRun | null; inferenceRecords: GlyphInferenceRecord[]; sourceRecords: {title: string | null; url: string | null; license: string | null}[];
  reportId: string | null; runSelection?: RunSelection | null;
  /** explicit state; anything but 'ok' means the report below is empty or offline for this same id */
  reportStatus: ReportStatus; reportStatusDetail: string | null;
}
function reportFallback(id: string, status: ReportStatus, message: string, useCatalogue = true): ReportPayload {
  let record: SteleItem | null = null;
  if (useCatalogue) { try { record = selected(id); } catch { record = null; } }
  return { ablation: [], evaluation_summary: message, scholarly_analysis: record ? (record.description || record.summary || '') : '',
    rubbing_dimensions: record?.dimensions || '', epigraphic_conclusion: record ? `《${record.title}》以馆藏记录为依据；未形成新增残字定论。` : '',
    run: null, inferenceRecords: [], sourceRecords: record ? [{ title: record.title, url: record.sourceUrl || null, license: record.license || null }] : [],
    reportId: null, runSelection: null, reportStatus: status, reportStatusDetail: message };
}
function transcriptionText(text:string):string {
  return text.replace(/\u0000/g,'').split('授權與引用')[0].split('License and attribution')[0].split(/\r?\n/)
    .filter(line=>!['（各記錄）Transcriptions','文物統一編號','釋文'].includes(line.trim())&&!/^(?:[贈購赠购]拓[0-9]+[A-Z0-9]*|[ivxlcdm]{1,7})$/.test(line.trim())).join('\n').trim();
}
export const SteleService = {
  async getSteles(): Promise<SteleItem[]> {
    try { const res=await fetch('/api/steles'); if(!res.ok) throw new Error('Unavailable'); const data=await res.json(); backendAvailable=true; return data.steles || data; }
    catch { backendAvailable=false; return FALLBACK_STELES; }
  },
  async getSteleById(id: string): Promise<SteleItem> {
    try { const res=await fetch(`/api/steles/${id}`); if(!res.ok) throw new Error('文物不可用'); return await res.json(); }
    catch { return selected(id); }
  },
  async processStele(params: { stele_id: string; d0: number; filter_order: number; filter_type: 'adaptive' | 'gaussian' | 'butterworth' | 'notch'; h_nlm: number; clahe_clip: number; morph_kernel: number }): Promise<ProcessingResult> {
    const res=await fetch('/api/process',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(params)});
    if(!res.ok) throw new Error('实际处理未成功，请检查后端服务；不会生成模拟结果');
    const result=await res.json(); if(result.stele_id!==params.stele_id) throw new Error('处理结果文物ID不一致'); return result;
  },
  async getInference(id: string): Promise<{transcript:string;characters:CharacterItem[];damaged_summary:string}> {
    try { const res=await fetch(`/api/steles/${id}/infer`); if(!res.ok) throw new Error(); return await res.json(); }
    catch { const record=selected(id); if(record.isDemo && record.inferenceDemo) return record.inferenceDemo; const text=transcriptionText(record.translation || ''); const chars=Array.from(text).filter(c => /[\u3400-\u9fff]/.test(c)).slice(0,35);return {transcript:text,characters:chars.map((char,i)=>({id:`c${i+1}`,char,status:'clear',col:Math.floor(i/7)+1,row:i%7+1})),damaged_summary:'释文参考，未执行本图残字检测或概率推演。'}; }
  },
  async getGraph(stele_id: string) {
    const { loadHistory } = await import('./history');
    return loadHistory(stele_id);
  },
  /**
   * P1 (7): never a silent fallback. Unknown artifact / unknown run / retired artifact / backend down
   * each return an explicit reportStatus with an empty report for THIS id; never another artifact,
   * run or batch. Only `backend_unavailable` keeps the bundled catalogue text of the same id.
   */
  async getReport(id: string, runId?: string): Promise<ReportPayload> {
    let res: Response;
    try { res = await fetch(`/api/steles/${encodeURIComponent(id)}/report${runId ? `?run_id=${encodeURIComponent(runId)}` : ''}`); }
    catch { return reportFallback(id, 'backend_unavailable', '后端不可用；仅显示本件的离线目录信息，未执行处理，无配对真值评测。'); }
    if (res.ok) return { ...(await res.json()), reportStatus: 'ok', reportStatusDetail: null };
    const body = await res.json().catch(() => ({}));
    const detail = typeof body.detail === 'string' ? body.detail : null;
    if (res.status === 410) return reportFallback(id, 'stele_retired', detail || `文物 ${id} 已下架`, false);
    if (res.status === 404 && runId && (detail || '').includes('处理记录')) return reportFallback(id, 'run_not_found', `本件没有运行 ${runId}；未替换为其他运行。`, false);
    if (res.status === 404) return reportFallback(id, 'stele_not_found', detail || `没有找到文物 ${id}；未替换为其他文物。`, false);
    return reportFallback(id, 'error', detail || `报告接口返回 HTTP ${res.status}`, false);
  },
  async uploadRubbing(formData: FormData): Promise<{success:boolean;stele:SteleItem}> {
    let res: Response;
    try { res=await fetch('/api/upload',{method:'POST',body:formData}); }
    catch { throw new Error('后端不可用，上传未保存'); }
    if(!res.ok){const body=await res.json().catch(()=>({}));throw new Error(typeof body.detail==='string'?body.detail:`上传失败（HTTP ${res.status}）`);}
    return await res.json();
  },
  /** R1-1: the backend picks the default run (never a legacy one); prefer this over items[0]. */
  async getReportSelection(id: string, runId?: string): Promise<{run: ProcessingRunR1 | null; runSelection: RunSelection | null; reportId: string | null}> {
    const res = await fetch(`/api/steles/${encodeURIComponent(id)}/report${runId ? `?run_id=${encodeURIComponent(runId)}` : ''}`);
    if (!res.ok) throw new Error('报告不可用');
    const body = await res.json();
    return { run: body.run ?? null, runSelection: body.runSelection ?? null, reportId: body.reportId ?? null };
  },
  /** R1-3 batch metadata (status / split / defaultForReport). */
  async listExperiments(): Promise<ExperimentBatchMeta[]> {
    const res = await fetch('/api/experiments');
    if (!res.ok) throw new Error('实验服务不可用');
    return res.json();
  },
  /** R2-8: one-to-one experimentId <-> batch mapping from the backend. */
  async getExperimentBatchIndex(): Promise<ExperimentBatchIndex> {
    const res = await fetch('/api/experiments/batch-index');
    if (!res.ok) throw new Error('实验登记不可用');
    return res.json();
  },
  /** applied_status (eval-sci derived file), served as written; 404 only for unknown experimentId. */
  async getAppliedStatus(experimentId: string, rows = false): Promise<AppliedStatusResponse> {
    const res = await fetch(`/api/experiments/${encodeURIComponent(experimentId)}/applied-status${rows ? '?rows=true' : ''}`);
    if (!res.ok) throw new Error(res.status === 404 ? '没有这个实验批次' : '派生状态不可用');
    return res.json();
  },
  /** Artifact-clustered CI (eval-sci ci_by_artifact.json), served as written; filters are exact matches. */
  async getCiByArtifact(experimentId: string, filters: {split?: string; method?: string; degradation?: string; scope?: string} = {}): Promise<CiByArtifactResponse> {
    const query = new URLSearchParams(Object.entries(filters).filter(([, v]) => v) as [string, string][]).toString();
    const res = await fetch(`/api/experiments/${encodeURIComponent(experimentId)}/ci-by-artifact${query ? `?${query}` : ''}`);
    if (!res.ok) throw new Error(res.status === 404 ? '没有这个实验批次' : 'CI 不可用');
    return res.json();
  },
  /** R1-4: available for every registered batch; 404 only for unknown ids. */
  async getExperimentDiagnosis(experimentId: string): Promise<ExperimentDiagnosis> {
    const res = await fetch(`/api/experiments/${encodeURIComponent(experimentId)}/diagnosis`);
    if (!res.ok) throw new Error('该批次诊断不可用');
    return res.json();
  },
  async listRuns(id: string): Promise<ProcessingRun[]> {
    const res = await fetch(`/api/steles/${encodeURIComponent(id)}/runs`);
    if (!res.ok) throw new Error('处理历史不可用');
    return res.json();
  },
  async deleteRun(id: string, runId: string): Promise<void> {
    const res=await fetch(`/api/steles/${encodeURIComponent(id)}/runs/${encodeURIComponent(runId)}?confirm=true`,{method:'DELETE'});
    if(!res.ok) throw new Error('处理记录删除失败');
  },
  async listGlyphInferences(id: string): Promise<GlyphInferenceRecord[]> {
    const res = await fetch(`/api/steles/${encodeURIComponent(id)}/inferences`);
    if (!res.ok) throw new Error('推演记录不可用');
    return res.json();
  },
  async inferGlyph(id: string, payload: {bbox:{x:number;y:number;w:number;h:number};context:string;characterId?:string;originalGlyph?:string;originalStatus?:string;imageSource?:'original'|'restored';runId?:string}): Promise<GlyphInferenceRecord> {
    const res = await fetch(`/api/steles/${encodeURIComponent(id)}/inferences`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    if (!res.ok) { const detail=await res.json().catch(()=>({})); throw new Error(typeof detail.detail==='string'?detail.detail:'残字推演失败'); }
    return res.json();
  },
  async decideGlyph(inferenceId: string, action:'accept'|'revoke'|'reject', glyph?:string): Promise<GlyphInferenceRecord> {
    const res=await fetch(`/api/inferences/${inferenceId}/decision`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,glyph})});
    if (!res.ok) throw new Error('人工确认记录保存失败');
    return res.json();
  },
  async saveGlyphAnnotation(payload:{steleId:string;inferenceId?:string;bbox:{x:number;y:number;width:number;height:number};glyph:string;sourceCitation:string;annotator:string;damageLevel:string;variantNote:string;imageSha256:string}):Promise<void> {
    const res=await fetch('/api/glyph-annotations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    if(!res.ok) throw new Error(await res.text() || '字符标注保存失败');
  },
  async runOcrBaseline(inferenceId:string):Promise<GlyphInferenceRecord> {
    const res=await fetch(`/api/inferences/${inferenceId}/ocr-baseline`,{method:'POST'});
    if(!res.ok) throw new Error(await res.text() || '印刷体 OCR 基线没有跑起来');
    return res.json();
  },
  async saveGlyphTemplate(inferenceId:string,glyph:string,basis:string,annotator:string):Promise<void> {
    const res=await fetch(`/api/inferences/${inferenceId}/template`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({glyph,basis,annotator})});
    if(!res.ok) throw new Error('参考字形保存失败，请检查标注内容');
  },
};
