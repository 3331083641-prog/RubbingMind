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
  createdAt: string;
}
function selected(id: string) { return resolveSelected(FALLBACK_STELES, id); }
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
  async getReport(id: string, runId?: string): Promise<{ablation:AblationMetric[];evaluation_summary:string;scholarly_analysis:string;rubbing_dimensions:string;epigraphic_conclusion:string;run:ProcessingRun|null;inferenceRecords:GlyphInferenceRecord[];sourceRecords:{title:string|null;url:string|null;license:string|null}[];reportId:string|null}> {
    try { const res=await fetch(`/api/steles/${id}/report${runId?`?run_id=${encodeURIComponent(runId)}`:''}`);if(!res.ok) throw new Error(); return await res.json(); }
    catch { const r=selected(id);return {ablation:[],evaluation_summary:'尚未执行处理或后端不可用；无配对真值评测。',scholarly_analysis:r.description || r.summary,rubbing_dimensions:r.dimensions,epigraphic_conclusion:`《${r.title}》以馆藏记录为依据；未形成新增残字定论。`,run:null,inferenceRecords:[],sourceRecords:[{title:r.title,url:r.sourceUrl||null,license:r.license||null}],reportId:null}; }
  },
  async uploadRubbing(formData: FormData): Promise<{success:boolean;stele:SteleItem}> {
    let res: Response;
    try { res=await fetch('/api/upload',{method:'POST',body:formData}); }
    catch { throw new Error('后端不可用，上传未保存'); }
    if(!res.ok){const body=await res.json().catch(()=>({}));throw new Error(typeof body.detail==='string'?body.detail:`上传失败（HTTP ${res.status}）`);}
    return await res.json();
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
  async saveGlyphTemplate(inferenceId:string,glyph:string,basis:string,annotator:string):Promise<void> {
    const res=await fetch(`/api/inferences/${inferenceId}/template`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({glyph,basis,annotator})});
    if(!res.ok) throw new Error('参考字形保存失败，请检查标注内容');
  },
};
