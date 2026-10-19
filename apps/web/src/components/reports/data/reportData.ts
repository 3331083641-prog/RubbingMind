/**
 * 报告页唯一的数据适配层。所有 fetch、口径判定、派生计算都集中在这里，
 * REPORT_DATA_SPEC v1 的后端字段（DER / displayName / isPassthrough …）到位后只需改本文件。
 * 规则：不伪造；拿不到就返回 missing / error，由界面显示真实空状态。
 */
import type { AppliedStatus, BatchDetail, BatchRegistry, Diagnosis, ExperimentRow, Grade, Loadable } from './types';
import type { MetricKey } from './labels';
import type { ProcessingRun } from '../../../types/stele';
import type { GlyphInferenceRecord } from '../../../services/api';
import { parseIsoTime } from '../format';

async function getJson<T>(url: string, missingMessage: string): Promise<Loadable<T>> {
  let res: Response;
  try { res = await fetch(url); }
  catch { return { state: 'error', message: '后端不可用，无法读取数据' }; }
  if (res.status === 404) return { state: 'missing', status: 404, message: missingMessage };
  if (!res.ok) return { state: 'error', message: `读取失败（HTTP ${res.status}）` };
  try { return { state: 'ok', data: await res.json() as T }; }
  catch { return { state: 'error', message: '返回内容不是有效 JSON' }; }
}

export const ReportApi = {
  batches: () => getJson<BatchRegistry[]>('/api/experiments', '实验登记接口不存在'),
  batch: (id: string) => getJson<BatchDetail>(`/api/experiments/${encodeURIComponent(id)}`, '没有这个实验批次'),
  diagnosis: (id: string) => getJson<Diagnosis>(`/api/experiments/${encodeURIComponent(id)}/diagnosis`, '该批次暂无失败案例诊断数据（诊断接口返回 404）'),
  runs: (steleId: string) => getJson<ProcessingRun[]>(`/api/steles/${encodeURIComponent(steleId)}/runs`, '本件没有运行记录接口'),
  /** 不走 services/api.ts 的静态回退：后端失败要如实显示“后端不可用”，不能伪装成“尚未执行”（AUDIT §4 空状态）。 */
  report: (steleId: string, runId: string) => getJson<RunReport>(`/api/steles/${encodeURIComponent(steleId)}/report?run_id=${encodeURIComponent(runId)}`, '没有这条运行的报告'),
  glyphEvaluation: () => getJson<GlyphEvaluation>('/api/glyph-evaluation', '识字评测接口不存在'),
  assetUrl: (experimentId: string, file: string) => `/api/experiments/${encodeURIComponent(experimentId)}/assets/${encodeURIComponent(file)}`,
  exportUrl: (experimentId: string, kind: string) => `/api/experiments/${encodeURIComponent(experimentId)}/export/${kind}`,
};

export interface RunReport { run: ProcessingRun | null; inferenceRecords?: GlyphInferenceRecord[]; sourceRecords?: { title: string | null; url: string | null; license: string | null }[]; reportId?: string | null; evaluation_summary?: string }
export interface GlyphEvaluation { status: string; top1: number | null; top3: number | null; verifiedLabels: number; recordedLabels?: number; reason?: string }

/* ---------------- 批次分级与命名 ---------------- */

export type BatchKind = 'controlled' | 'retest' | 'historical' | 'unknown';
export interface BatchInfo { id: string; displayName: string; kind: BatchKind; hasImages: boolean; registry: BatchRegistry; named: boolean }

/** REPORT_DATA_SPEC §1(a)：显示名优先用注册表 displayName；缺失时用这里的兜底名。UI 不出现“留出/held-out”。 */
const FALLBACK_NAMES: Record<string, string> = {
  'controlled-rubbings-v2-text-2026-10-17': '受控退化 v2-text（文字区裁切，2026-10-17）',
  'controlled-rubbings-v2-2026-10-17': '受控退化 v2（2026-10-17）',
  'heldout-v20-v21-2026-10-18': '同批复测 v2.1（v2.0 对照，2026-10-18）',
  'controlled-rubbings-2026-10-15': '历史批次 2026-10-15（先验泄漏，仅作记录）',
};
const KIND_ORDER: BatchKind[] = ['controlled', 'retest', 'historical', 'unknown'];

export function classifyBatch(reg: BatchRegistry): BatchInfo {
  const retest = reg.heldOut === false || /heldout/i.test(reg.id) || /heldout/i.test(reg.directory || '');
  const kind: BatchKind = reg.historicalWarning ? 'historical' : retest ? 'retest' : reg.metricsOnly ? 'unknown' : 'controlled';
  const fallback = FALLBACK_NAMES[reg.id];
  const displayName = reg.displayName || fallback || `${reg.id}（未命名）`;
  return { id: reg.id, displayName, kind, hasImages: !!reg.imageComparisonAvailable && !reg.metricsOnly, registry: reg, named: !!(reg.displayName || fallback) };
}

/** 排序：有图像的受控批次在前（同类按 ID 倒序，即较新的在前），同批复测其次，历史批次最后。 */
export function orderBatches(regs: BatchRegistry[]): BatchInfo[] {
  return regs.map(classifyBatch).sort((a, b) => KIND_ORDER.indexOf(a.kind) - KIND_ORDER.indexOf(b.kind) || Number(b.hasImages) - Number(a.hasImages) || preferText(a.id, b.id));
}
const preferText = (a: string, b: string) => {
  // v2-text 与 v2 同日：SPEC §1(a) 要求默认选最新的有图像批次（BVT = v2-text）
  const rank = (id: string) => (id.includes('v2-text') ? 0 : id.includes('v2') ? 1 : 2);
  return rank(a) - rank(b) || b.localeCompare(a);
};
/** 默认批次：禁止是同批复测或历史批次（SPEC §1(a)、E-07）。 */
export function defaultBatchId(ordered: BatchInfo[]): string {
  return (ordered.find(b => b.kind === 'controlled' && b.hasImages) || ordered.find(b => b.kind === 'controlled') || ordered[0])?.id || '';
}
export const batchByDirectory = (ordered: BatchInfo[], dir: string) => ordered.find(b => b.registry.directory === dir)?.id;

export const hasSplit = (rows: ExperimentRow[]) => rows.length > 0 && rows.every(r => typeof r.split === 'string' && r.split.length > 0);

/* ---------------- 原图返回 / 实际处理 ---------------- */

export interface StatusResult { status: AppliedStatus; criterion: string }
/**
 * SPEC §1(b)。优先用 DER/新字段 appliedStatus、isPassthrough；没有时前端兜底：
 * 输出文件 SHA-256 与输入相同 = 原图返回（byteIdentical，SPEC 指出它是充分条件；
 * BV2 65 行 / BVT 47 行原图返回全部字节相同）。没有 SHA（如同批复测、历史批次）= 无法判定，不猜测。
 */
export function appliedStatus(row: ExperimentRow): StatusResult {
  if (row.appliedStatus) return { status: row.appliedStatus, criterion: 'DER appliedStatus' };
  if (row.error) return { status: 'failed', criterion: '运行错误' };
  if (row.method === 'degraded') return { status: 'baseline', criterion: '退化基线' };
  const na = row.applicability === 'not_applicable';
  if (row.isPassthrough === true) return { status: na ? 'passthrough_not_applicable' : 'passthrough', criterion: 'isPassthrough（pixel-equal-v1）' };
  if (row.isPassthrough === false) return { status: na ? 'processed_not_applicable_label' : 'processed', criterion: 'isPassthrough（pixel-equal-v1）' };
  if (!row.outputSha256 || !row.inputSha256) return { status: 'undetermined', criterion: '无输出/输入 SHA，无法判定' };
  if (row.outputSha256 === row.inputSha256) return { status: na ? 'passthrough_not_applicable' : 'passthrough', criterion: 'byteIdentical（输出与输入 SHA-256 相同；前端兜底）' };
  return { status: na ? 'processed_not_applicable_label' : 'processed', criterion: '输出与输入 SHA-256 不同（前端兜底；像素级判据待 DER）' };
}
export const isPassthroughStatus = (s: AppliedStatus) => s === 'passthrough' || s === 'passthrough_not_applicable';

/* ---------------- 相对输入的 Δ 与按文物聚类 ---------------- */

const caseKey = (r: ExperimentRow) => `${r.split || 'none'}|${r.caseId || `${r.sampleId}|${r.degradation}|${r.strength ?? ''}|${r.seed ?? ''}`}`;
export type BaselineMap = Map<string, ExperimentRow>;
export function baselineMap(rows: ExperimentRow[]): BaselineMap {
  const map: BaselineMap = new Map();
  rows.forEach(r => { if (r.method === 'degraded') map.set(caseKey(r), r); });
  return map;
}
export const baselineOf = (row: ExperimentRow, map: BaselineMap) => map.get(caseKey(row));

/** 单行 Δ。thinStrokeMae 取 in − out（SPEC §0.3），其余 out − in。缺参考值时返回 null。 */
export function rowDelta(row: ExperimentRow, metric: MetricKey, map: BaselineMap): number | null {
  if (metric === 'processingMs') return null;
  const base = baselineOf(row, map);
  const out = row[metric];
  let input: number | null | undefined = base ? base[metric] : undefined;
  if (input == null && metric === 'psnr') input = row.inputPsnr;
  if (input == null && metric === 'ssim') input = row.inputSsim;
  if (out == null || input == null || !Number.isFinite(out) || !Number.isFinite(input)) return null;
  return metric === 'thinStrokeMae' ? input - out : out - input;
}

/** 固定种子的伪随机数（mulberry32），保证 CI 可复现。 */
export const BOOTSTRAP_SEED = 20261019;
export const BOOTSTRAP_RESAMPLES = 1000;
function rng(seed: number) {
  let a = seed >>> 0;
  return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
/** SPEC §0.3 按文物聚类 bootstrap：输入为每件文物的均值；K<2 返回 null。 */
export function clusterCI(values: number[], seed = BOOTSTRAP_SEED): [number, number] | null {
  if (values.length < 2) return null;
  const r = rng(seed); const means: number[] = [];
  for (let i = 0; i < BOOTSTRAP_RESAMPLES; i++) { let s = 0; for (let j = 0; j < values.length; j++) s += values[Math.floor(r() * values.length)]; means.push(s / values.length); }
  means.sort((a, b) => a - b);
  return [means[Math.floor(0.025 * (BOOTSTRAP_RESAMPLES - 1))], means[Math.ceil(0.975 * (BOOTSTRAP_RESAMPLES - 1))]];
}
const mean = (xs: number[]) => xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null;

export interface MethodAggregate {
  method: string;
  scope: 'processed' | 'all';
  value: number | null;          // 主数字：scope 内按文物聚类的均值（Δ 或耗时绝对值）
  ci: [number, number] | null;
  nArtifacts: number;
  nRecords: number;              // 进入主数字的记录数
  n: number;                     // 该方法的全部记录数（含原图返回、失败）
  processedN: number; passthroughN: number; undeterminedN: number; failedN: number; naChangedN: number;
  negativeN: number;             // Δ<0 的记录数（scope 内）
  meanAll: number | null;        // 全部有值记录的聚类均值（对照用）
  artifactPoints: { sampleId: string; value: number }[];
}

/**
 * 主口径：有可判定的原图返回时用 MeanProcessed（SPEC §1(b)），并给出 passthroughN；
 * 整批无法判定（同批复测 BRT）时退回全部记录，scope='all' 并在界面上注明。
 */
export function aggregate(rows: ExperimentRow[], map: BaselineMap, metric: MetricKey, methods: string[]): MethodAggregate[] {
  return methods.map(method => {
    const own = rows.filter(r => r.method === method);
    const st = own.map(r => ({ r, s: appliedStatus(r).status }));
    const processedN = st.filter(x => x.s === 'processed' || x.s === 'processed_not_applicable_label').length;
    const passthroughN = st.filter(x => isPassthroughStatus(x.s)).length;
    const undeterminedN = st.filter(x => x.s === 'undetermined').length;
    const failedN = st.filter(x => x.s === 'failed').length;
    const naChangedN = st.filter(x => x.s === 'processed_not_applicable_label').length;
    const determinable = processedN + passthroughN > 0;
    const scope: 'processed' | 'all' = determinable ? 'processed' : 'all';
    const valueOf = (r: ExperimentRow) => metric === 'processingMs' ? (r.processingMs ?? null) : rowDelta(r, metric, map);
    const clusterMean = (subset: ExperimentRow[]) => {
      const by = new Map<string, number[]>();
      subset.forEach(r => { const v = valueOf(r); if (v != null && Number.isFinite(v)) { if (!by.has(r.sampleId)) by.set(r.sampleId, []); by.get(r.sampleId)!.push(v); } });
      const points = Array.from(by.entries()).map(([sampleId, vs]) => ({ sampleId, value: mean(vs)! }));
      const recs = Array.from(by.values()).reduce((a, v) => a + v.length, 0);
      return { points, recs, value: mean(points.map(p => p.value)) };
    };
    const scoped = scope === 'processed' && metric !== 'processingMs'
      ? st.filter(x => x.s === 'processed' || x.s === 'processed_not_applicable_label').map(x => x.r)
      : st.filter(x => x.s !== 'failed').map(x => x.r);
    const main = clusterMean(scoped);
    const all = clusterMean(st.filter(x => x.s !== 'failed').map(x => x.r));
    const negativeN = metric === 'processingMs' ? 0 : scoped.filter(r => { const v = valueOf(r); return v != null && v < 0; }).length;
    return {
      method, scope: metric === 'processingMs' ? 'all' : scope, value: main.value, ci: clusterCI(main.points.map(p => p.value)),
      nArtifacts: main.points.length, nRecords: main.recs, n: own.length,
      processedN, passthroughN, undeterminedN, failedN, naChangedN, negativeN, meanAll: all.value, artifactPoints: main.points,
    };
  });
}

/* ---------------- 证据分级（SPEC §0.2，只降不升） ---------------- */

export interface GradeResult { grade: Grade; reasons: string[] }
export function gradeDelta(agg: MethodAggregate | undefined, batch: BatchInfo | undefined, split: string): GradeResult {
  if (!agg || agg.value == null) return { grade: '未评测', reasons: ['数据中没有该方法/指标的可比记录'] };
  const reasons: string[] = ['只在受控退化上成立（参考图是可读 JPG 裁切，不是碑石真值）'];
  if (batch?.kind === 'retest') reasons.push('样本参与过 v2.1 的误差分析（同批复测）');
  if (batch?.kind === 'historical') reasons.push('历史批次存在先验泄漏');
  if (split !== 'test') reasons.push(split === 'none' ? '本批未划分 dev/test' : '开发组数据可能参与过调参');
  if (agg.nArtifacts < 10) reasons.push(`n_文物=${agg.nArtifacts}<10`);
  if (!agg.ci) reasons.push('无 CI');
  else if (agg.ci[0] <= 0 && agg.ci[1] >= 0) reasons.push('CI 跨 0');
  else if (agg.ci[1] < 0) reasons.push('CI 整体在 0 以下（负提升）');
  if (agg.scope === 'all') reasons.push('无法判定原图返回，主数字含全部记录');
  const limited = reasons.length > 1;
  return { grade: limited ? '有限支持' : '已验证（受控退化）', reasons };
}

/* ---------------- 馆藏运行：排序、默认、原图返回 ---------------- */

export interface RunInfo { run: ProcessingRun; time: number | null; legacy: boolean }
const runTime = (r: ProcessingRun) => parseIsoTime(r.finishedAt) ?? parseIsoTime(r.startedAt);
/** P0-1 前端兜底：按可解析 ISO 时间倒序；无时间或 legacy 版本的排后并标 legacy。 */
export function sortRuns(runs: ProcessingRun[]): RunInfo[] {
  return runs.map(run => { const time = runTime(run); return { run, time, legacy: time == null || /legacy/i.test(run.algorithmVersion || '') }; })
    .sort((a, b) => Number(a.legacy) - Number(b.legacy) || (b.time ?? 0) - (a.time ?? 0));
}
/** 默认运行：URL 指定且存在 → 用它；否则第一条非 legacy；没有非 legacy 则不默认（要求手动选择）。 */
export function defaultRunId(sorted: RunInfo[], requested?: string | null): string {
  if (requested && sorted.some(x => x.run.runId === requested)) return requested;
  return sorted.find(x => !x.legacy)?.run.runId || '';
}

type RunExtras = ProcessingRun & {
  isPassthrough?: boolean | null; changedPixelRatio?: number | null; maxAbsDiff?: number | null; passthroughCriterion?: string; passthroughUndeterminedReason?: string | null;
  engineDiagnosticMetrics?: Record<string, number | null>;
  adaptiveDiagnostics?: { version?: string; features?: Record<string, unknown>; decisions?: { operator: string; reason?: string }[]; fidelityGate?: Record<string, unknown>; selectedOutput?: string; limitations?: string } | null;
  frequencyDetails?: { mode?: string; notchApplied?: boolean; adaptive?: RunExtras['adaptiveDiagnostics'] } | null;
};
export type RunOutputMode = 'passthrough' | 'processed' | 'passthrough-indicated' | 'processed-indicated' | 'undetermined';
export interface RunOutcome { mode: RunOutputMode; title: string; detail: string; criterion: string }

export function runAdaptive(run: ProcessingRun) {
  const r = run as RunExtras;
  return r.adaptiveDiagnostics || r.frequencyDetails?.adaptive || null;
}
/**
 * SPEC §8 文案规则。优先后端 isPassthrough；没有时用引擎记录的平均绝对差（MAD）作为“指示”，
 * 并注明“像素级判据字段未记录”；浏览器内逐像素比较（ArtifactRunReport 中）可进一步确认。
 */
export function runOutcome(run: ProcessingRun): RunOutcome {
  const r = run as RunExtras;
  if (r.isPassthrough === true) return { mode: 'passthrough', title: '本次未改动原图', detail: '算法判断无需处理，输出与输入逐像素相同。', criterion: r.passthroughCriterion || 'isPassthrough' };
  if (r.isPassthrough === false) return { mode: 'processed', title: '算法输出', detail: '输出与输入存在像素差异。', criterion: r.passthroughCriterion || 'isPassthrough' };
  const mad = r.diagnosticMetrics?.input_output_mean_absolute_difference ?? r.engineDiagnosticMetrics?.input_output_mean_absolute_difference;
  if (mad === 0) return { mode: 'passthrough-indicated', title: '未修改输入', detail: '引擎记录的输入／输出平均绝对差为 0：算法判定不修改，输出不是“算法输出”。', criterion: '指示量：diagnosticMetrics.input_output_mean_absolute_difference = 0（该运行保存于判据引入前，未记录改动像素数）' };
  if (typeof mad === 'number' && mad > 0) return { mode: 'processed-indicated', title: '算法输出', detail: `引擎记录的输入／输出平均绝对差为 ${mad.toFixed(3)}。`, criterion: '指示量：input_output_mean_absolute_difference > 0' };
  return { mode: 'undetermined', title: '未能判定是否改动', detail: r.passthroughUndeterminedReason || '该运行保存于判据引入前，未记录改动量。', criterion: '无判据字段' };
}
