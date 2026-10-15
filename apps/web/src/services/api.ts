import { SteleItem, ProcessingResult, CharacterItem, GraphNode, GraphLink, GISWaypoint, AblationMetric } from '../types/stele';
import STILES_28_DATA from '../data/steles28.json';
import { CORE_SAMPLES, resolveSelected } from '../data/catalogSelection';
export const FALLBACK_STELES = STILES_28_DATA as unknown as SteleItem[];
export let backendAvailable = false;
function selected(id: string) { return resolveSelected(FALLBACK_STELES, id); }
export const SteleService = {
  async getSteles(): Promise<SteleItem[]> {
    try { const res=await fetch('/api/steles'); if(!res.ok) throw new Error('Unavailable'); const data=await res.json(); backendAvailable=true; return data.steles || data; }
    catch { backendAvailable=false; return FALLBACK_STELES; }
  },
  async getSteleById(id: string): Promise<SteleItem> {
    try { const res=await fetch(`/api/steles/${id}`); if(!res.ok) throw new Error('文物不可用'); return await res.json(); }
    catch { return selected(id); }
  },
  async processStele(params: { stele_id: string; d0: number; filter_order: number; filter_type: 'gaussian' | 'butterworth' | 'notch'; h_nlm: number; clahe_clip: number; morph_kernel: number }): Promise<ProcessingResult> {
    const res=await fetch('/api/process',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(params)});
    if(!res.ok) throw new Error('实际处理未成功，请检查后端服务；不会生成模拟结果');
    const result=await res.json(); if(result.stele_id!==params.stele_id) throw new Error('处理结果文物ID不一致'); return result;
  },
  async getInference(id: string): Promise<{transcript:string;characters:CharacterItem[];damaged_summary:string}> {
    try { const res=await fetch(`/api/steles/${id}/infer`); if(!res.ok) throw new Error(); return await res.json(); }
    catch { const record=selected(id); if(record.isDemo && record.inferenceDemo) return record.inferenceDemo; const text=record.translation || ''; const chars=Array.from(text).filter(c => /[\u3400-\u9fff]/.test(c)).slice(0,35);return {transcript:text,characters:chars.map((char,i)=>({id:`c${i+1}`,char,status:'clear',col:Math.floor(i/7)+1,row:i%7+1})),damaged_summary:'释文参考，未执行本图残字检测或概率推演。'}; }
  },
  async getGraph(stele_id: string) {
    const { loadHistory } = await import('./history');
    return loadHistory(stele_id);
  },
  async getReport(id: string): Promise<{ablation:AblationMetric[];evaluation_summary:string;scholarly_analysis:string;rubbing_dimensions:string;epigraphic_conclusion:string}> {
    try { const res=await fetch(`/api/steles/${id}/report`);if(!res.ok) throw new Error(); return await res.json(); }
    catch { const r=selected(id);return {ablation:[],evaluation_summary:'未评测：未建立配对真值或消融实验记录。',scholarly_analysis:r.description || r.summary,rubbing_dimensions:r.dimensions,epigraphic_conclusion:`《${r.title}》以馆藏记录为依据；未形成新增残字定论。`}; }
  },
  async uploadRubbing(formData: FormData): Promise<{success:boolean;stele:SteleItem}> {
    const res=await fetch('/api/upload',{method:'POST',body:formData});if(!res.ok) throw new Error('Upload failed');return await res.json();
  }
};
