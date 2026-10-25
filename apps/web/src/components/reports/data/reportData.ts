/**
 * 报告页唯一的数据适配层。所有读取、口径判定、派生计算都集中在这里。
 * - 共享接口走 services/api.ts（listExperiments / getExperimentDiagnosis / getReportSelection / listRuns）。
 * - api.ts 没有的读取（批次明细、完整报告体、识字评测、DER/CI/NLC/MEC 派生文件）在这里用只读 GET 实现。
 * 规则：不伪造；拿不到就返回 missing / error，由界面显示真实空状态。
 */
import type { AppliedStatus, BatchDetail, BatchRegistry, CiFile, CiGroup, DerFile, Derived, Diagnosis, ExperimentRow, GainSign, Grade, Loadable, MechanismIndex, NlcFile } from './types';
import type { MetricKey } from './labels';
import { SteleService, type ProcessingRunR1, type RunSelection, type GlyphInferenceRecord } from '../../../services/api';
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
async function wrap<T>(p: Promise<T>, failMessage: string): Promise<Loadable<T>> {
  try { return { state: 'ok', data: await p }; }
  catch (e) { return { state: 'error', message: `${failMessage}（${e instanceof Error ? e.message : String(e)}）` }; }
}

/**
 * 派生文件位置。后端尚未提供 DER/CI/NLC/MEC 接口（已写入后端需求）；本地开发时可设
 * VITE_RM_DERIVED_BASE 指向从 agent/eval-sci 只读取出的副本（例如 /.cache/rm-derived，目录结构 <批次目录>/derived/<文件>）。
 * 未设置时走预留的 API 路径，404 即显示“未接入”。
 */
const DERIVED_BASE = ((import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env?.VITE_RM_DERIVED_BASE || "").replace(/\/$/, "");
function derivedUrl(experimentId: string, directory: string, name: string) {
  return DERIVED_BASE ? `${DERIVED_BASE}/${encodeURIComponent(directory)}/derived/${name}` : `/api/experiments/${encodeURIComponent(experimentId)}/derived/${name}`;
}
async function derived<T>(experimentId: string, directory: string | undefined, name: string): Promise<Loadable<Derived<T>>> {
  if (!directory) return { state: 'missing', status: 404, message: '批次目录未知' };
  const url = derivedUrl(experimentId, directory, name);
  const r = await getJson<T>(url, `派生文件 derived/${name} 尚未接入`);
  if (r.state !== 'ok') return r;
  const source = DERIVED_BASE ? `agent/eval-sci 只读副本：experiments/results/${directory}/derived/${name}` : `API ${url}`;
  return { state: 'ok', data: { file: r.data, source } };
}

export const ReportApi = {
  batches: () => wrap(SteleService.listExperiments() as unknown as Promise<BatchRegistry[]>, '实验登记不可用'),
  batch: (id: string) => getJson<BatchDetail>(`/api/experiments/${encodeURIComponent(id)}`, '没有这个实验批次'),
  diagnosis: (id: string) => wrap(SteleService.getExperimentDiagnosis(id) as unknown as Promise<Diagnosis>, '诊断接口不可用'),
  runs: (steleId: string) => wrap(SteleService.listRuns(steleId) as Promise<ProcessingRunR1[]>, '运行记录不可用'),
  selection: (steleId: string, runId?: string) => wrap(SteleService.getReportSelection(steleId, runId), '报告接口不可用'),
  /** 完整报告体（含识读建议记录、来源记录）。不走 api.ts getReport 的静态回退：后端失败要如实显示。 */
  report: (steleId: string, runId: string) => getJson<RunReport>(`/api/steles/${encodeURIComponent(steleId)}/report?run_id=${encodeURIComponent(runId)}`, '没有这条运行的报告'),
  glyphEvaluation: () => getJson<GlyphEvaluation>('/api/glyph-evaluation', '识字评测接口不存在'),
  appliedStatus: (id: string, dir?: string) => derived<DerFile>(id, dir, 'applied_status.json'),
  ciByArtifact: (id: string, dir?: string) => derived<CiFile>(id, dir, 'ci_by_artifact.json'),
  negativeLiftCauses: (id: string, dir?: string) => derived<NlcFile>(id, dir, 'negative_lift_causes.json'),
  mechanismIndex: (id: string, dir?: string) => derived<MechanismIndex>(id, dir, 'mechanism/index.json'),
  assetUrl: (experimentId: string, file: string) => `/api/experiments/${encodeURIComponent(experimentId)}/assets/${encodeURIComponent(file)}`,
  exportUrl: (experimentId: string, kind: string) => `/api/experiments/${encodeURIComponent(experimentId)}/export/${kind}`,
};
export type { ProcessingRunR1, RunSelection };

export interface RunReport { run: ProcessingRunR1 | null; runSelection?: RunSelection | null; inferenceRecords?: GlyphInferenceRecord[]; sourceRecords?: { title: string | null; url: string | null; license: string | null }[]; reportId?: string | null; evaluation_summary?: string }
export interface GlyphEvaluation { status: string; top1: number | null; top3: number | null; verifiedLabels: number; recordedLabels?: number; reason?: string }

/* ---------------- 批次分级与命名 ---------------- */

export type BatchKind = 'controlled' | 'retest' | 'historical' | 'unknown';
/** title：页面主标题与标签；shortName：tooltip、图例、导出文件名、PDF 图题（评测科学家 2026-10-19 裁定）。 */
export interface BatchInfo { id: string; title: string; shortName: string; displayName: string; kind: BatchKind; hasImages: boolean; registry: BatchRegistry; named: boolean; isDefault: boolean }

const FALLBACK_NAMES: Record<string, string> = {
  'controlled-rubbings-v2-text-2026-10-17': '受控退化 v2-text（文字区裁切，2026-10-17）',
  'controlled-rubbings-v2-2026-10-17': '受控退化 v2（2026-10-17）',
  'controlled-rubbings-2026-10-15': '历史批次 2026-10-15（先验泄漏，仅作记录）',
};
export const RETEST_TITLE = '同批复测 v2.1（非留出）';
export const RETEST_SHORT = '同批复测 v2.1';
const KIND_ORDER: BatchKind[] = ['controlled', 'retest', 'historical', 'unknown'];

export function classifyBatch(reg: BatchRegistry): BatchInfo {
  const retest = /heldout/i.test(reg.id) || /heldout/i.test(reg.directory || '');
  const kind: BatchKind = reg.status === 'historical-leakage' || reg.historicalWarning ? 'historical' : retest ? 'retest' : reg.metricsOnly ? 'unknown' : 'controlled';
  const fallback = FALLBACK_NAMES[reg.id];
  const named = !!(reg.displayName || fallback || kind === 'retest');
  const base = reg.displayName || fallback || `${reg.id}（未命名）`;
  const title = kind === 'retest' ? RETEST_TITLE : base;
  const shortName = kind === 'retest' ? RETEST_SHORT : base;
  return { id: reg.id, title, shortName, displayName: title, kind, hasImages: !!reg.imageComparisonAvailable && !reg.metricsOnly, registry: reg, named, isDefault: reg.defaultForReport === true };
}
/** 排序：后端指定的默认批次在前，其余有图像的受控批次、同批复测、历史批次依次在后。 */
export function orderBatches(regs: BatchRegistry[]): BatchInfo[] {
  return regs.map(classifyBatch).sort((a, b) => Number(b.isDefault) - Number(a.isDefault) || KIND_ORDER.indexOf(a.kind) - KIND_ORDER.indexOf(b.kind) || Number(b.hasImages) - Number(a.hasImages) || b.id.localeCompare(a.id));
}
/** 默认批次只认 ExperimentBatchMeta.defaultForReport；后端没指定时不猜，返回空串，由界面要求手动选择。 */
export const defaultBatchId = (ordered: BatchInfo[]) => ordered.find(b => b.isDefault && b.kind !== 'retest')?.id || '';

export type BatchResolution =
  | { state: 'ok'; id: string; via: 'experimentId' | 'batch' | 'default'; conflict?: string }
  | { state: 'unknown'; requested: string; param: 'experimentId' | 'batch' }
  | { state: 'no-default' };
/**
 * experimentId 是权威；batch 只是别名（接受目录名或 ID），解析后写回 experimentId。
 * 两者冲突时以 experimentId 为准；未知 ID 不回落到默认批次。
 */
export function resolveBatch(ordered: BatchInfo[], experimentId?: string | null, batch?: string | null): BatchResolution {
  const byAlias = (alias: string) => ordered.find(b => b.registry.directory === alias || b.id === alias);
  if (experimentId) {
    const hit = ordered.find(b => b.id === experimentId);
    if (!hit) return { state: 'unknown', requested: experimentId, param: 'experimentId' };
    const alias = batch ? byAlias(batch) : undefined;
    return { state: 'ok', id: hit.id, via: 'experimentId', conflict: batch && alias?.id !== hit.id ? batch : undefined };
  }
  if (batch) {
    const hit = byAlias(batch);
    return hit ? { state: 'ok', id: hit.id, via: 'batch' } : { state: 'unknown', requested: batch, param: 'batch' };
  }
  const id = defaultBatchId(ordered);
  return id ? { state: 'ok', id, via: 'default' } : { state: 'no-default' };
}

export const hasSplit = (rows: ExperimentRow[]) => rows.length > 0 && rows.every(r => typeof r.split === 'string' && r.split.length > 0);

/* ---------------- DER 合并 ---------------- */

export interface DerMerge { rows: ExperimentRow[]; source: string | null; criterion: string | null; mismatch: number; problem: string | null }
/**
 * 按 rowIndex 把 DER 的 appliedStatus 等字段并入批次行；逐行核对 sampleId / method / degradation，
 * 任何一行对不上就整份 DER 不用（不部分采用），并报告原因。
 */
export function mergeDer(detail: BatchDetail, der: Loadable<Derived<DerFile>>): DerMerge {
  const rows = detail.rows || [];
  if (der.state !== 'ok') return { rows: rows.map(r => ({ ...r, statusSource: 'frontend' as const })), source: null, criterion: null, mismatch: 0, problem: der.state === 'loading' ? null : der.message };
  const f = der.data.file;
  if (f.experimentId && detail.registry?.id && f.experimentId !== detail.registry.id) return { rows: rows.map(r => ({ ...r, statusSource: 'frontend' as const })), source: null, criterion: null, mismatch: rows.length, problem: `DER 属于 ${f.experimentId}，与当前批次不符` };
  const byIndex = new Map(f.rows.map(r => [r.rowIndex, r]));
  let mismatch = 0;
  const merged = rows.map((r, i) => {
    const d = byIndex.get(i);
    if (!d || d.sampleId !== r.sampleId || d.method !== r.method || d.degradation !== r.degradation) { mismatch++; return r; }
    return { ...r, appliedStatus: d.appliedStatus, isPassthrough: d.isPassthrough, changedPixelCount: d.changedPixelCount, changedPixelRatio: d.changedPixelRatio, maxAbsDiff: d.maxAbsDiff, byteIdentical: d.byteIdentical, statusSource: 'DER' as const };
  });
  if (mismatch > 0 || f.rows.length !== rows.length) return { rows: rows.map(r => ({ ...r, statusSource: 'frontend' as const })), source: null, criterion: null, mismatch, problem: `DER 与批次行对不上（${mismatch} 行不一致，DER ${f.rows.length} 行 / 批次 ${rows.length} 行），未采用` };
  return { rows: merged, source: der.data.source, criterion: f.criterion, mismatch: 0, problem: null };
}

/* ---------------- 原图返回 / 实际处理（7 值状态） ---------------- */

export interface StatusResult { status: AppliedStatus; criterion: string }
/**
 * SPEC §1(b)。优先 DER appliedStatus（pixel-equal-v1）；没有时前端兜底：
 * 输出 SHA-256 与输入相同 = 原图返回（byteIdentical，充分非必要条件）。没有 SHA = 无法判定，不猜测。
 */
export function appliedStatus(row: ExperimentRow): StatusResult {
  if (row.appliedStatus) return { status: row.appliedStatus, criterion: row.statusSource === 'DER' ? 'DER appliedStatus（pixel-equal-v1）' : 'appliedStatus' };
  if (row.error) return { status: 'failed', criterion: '运行错误' };
  if (row.method === 'degraded') return { status: 'baseline', criterion: '退化基线' };
  const na = row.applicability === 'not_applicable';
  if (row.isPassthrough === true) return { status: na ? 'passthrough_not_applicable' : 'passthrough', criterion: 'isPassthrough（pixel-equal-v1）' };
  if (row.isPassthrough === false) return { status: na ? 'processed_not_applicable_label' : 'processed', criterion: 'isPassthrough（pixel-equal-v1）' };
  if (!row.outputSha256 || !row.inputSha256) return { status: 'undetermined', criterion: '无输出/输入 SHA，无法判定' };
  if (row.outputSha256 === row.inputSha256) return { status: na ? 'passthrough_not_applicable' : 'passthrough', criterion: 'byteIdentical（输出与输入 SHA-256 相同；前端兜底，DER 未接入）' };
  return { status: na ? 'processed_not_applicable_label' : 'processed', criterion: '输出与输入 SHA-256 不同（前端兜底，DER 未接入）' };
}
export const isPassthroughStatus = (s: AppliedStatus) => s === 'passthrough' || s === 'passthrough_not_applicable';
export const isProcessedStatus = (s: AppliedStatus) => s === 'processed' || s === 'processed_not_applicable_label';

/* ---------------- 相对输入的 Δ ---------------- */

const caseKey = (r: ExperimentRow) => `${r.split || 'none'}|${r.caseId || `${r.sampleId}|${r.degradation}|${r.strength ?? ''}|${r.seed ?? ''}`}`;
export type BaselineMap = Map<string, ExperimentRow>;
export function baselineMap(rows: ExperimentRow[]): BaselineMap {
  const map: BaselineMap = new Map();
  rows.forEach(r => { if (r.method === 'degraded') map.set(caseKey(r), r); });
  return map;
}
export const baselineOf = (row: ExperimentRow, map: BaselineMap) => map.get(caseKey(row));

/** 单行配对增益：输出 − 同 caseId 的 degraded 行。thinStrokeMae 取 输入 − 输出（越大越好）。缺值返回 null。 */
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

/* ---------------- 按文物聚类 bootstrap（前端临时口径） ---------------- */

export const BOOTSTRAP_SEED = 20261019;
export const BOOTSTRAP_RESAMPLES = 1000;
export const MIN_RELIABLE_ARTIFACTS = 3;
function rng(seed: number) {
  let a = seed >>> 0;
  return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
/** numpy.percentile 默认的线性插值。 */
function percentile(sorted: number[], p: number) {
  const pos = (sorted.length - 1) * p / 100; const lo = Math.floor(pos), hi = Math.ceil(pos);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
}
/**
 * 评测科学家裁定（2026-10-19）：重采样单位是文物，抽中的文物带上它的全部行；B=1000，种子 20261019，取 2.5%/97.5% 分位。
 * 统计量与 ci_by_artifact 相同：先求每件文物的均值，再对 K 件文物有放回重采样求均值（与“带全部行”在每件行数相同时等价）。
 * 不按行重采样。K=0 返回 null（无数据）；K<3 照算但标为不可靠，界面不画误差线。
 */
export function clusterCI(artifactMeans: number[], seed = BOOTSTRAP_SEED): [number, number] | null {
  const K = artifactMeans.length;
  if (K === 0) return null;
  const r = rng(seed); const means: number[] = [];
  for (let i = 0; i < BOOTSTRAP_RESAMPLES; i++) { let s = 0; for (let j = 0; j < K; j++) s += artifactMeans[Math.floor(r() * K)]; means.push(s / K); }
  means.sort((a, b) => a - b);
  return [percentile(means, 2.5), percentile(means, 97.5)];
}
const mean = (xs: number[]) => xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null;
export function gainSign(ci: [number, number] | null): GainSign | null {
  if (!ci) return null;
  if (ci[0] === 0 && ci[1] === 0) return 'zero';
  if (ci[0] > 0) return 'positive';
  if (ci[1] < 0) return 'negative';
  return 'spans_zero';
}
export const GAIN_SIGN_TEXT: Record<GainSign, string> = { positive: '提升（CI 下界 > 0）', negative: '下降（CI 上界 < 0）', spans_zero: 'CI 跨 0，不能写“提升”', zero: '增益恒为 0（原图返回）' };

/* ---------------- 三口径聚合 ---------------- */

export type Scope = 'all' | 'processed' | 'passthrough';
export const SCOPE_LABELS: Record<Scope, string> = { all: '全部', processed: '实际处理', passthrough: '原图返回' };
export interface ScopeStat {
  scope: Scope;
  value: number | null;            // 文物均值的均值（Δ 或耗时绝对值）
  ci: [number, number] | null;
  ciReliable: boolean;
  sign: GainSign | null;
  nArtifacts: number;
  nRecords: number;
  ciSource: 'ci_by_artifact' | 'frontend';
  ciNote: string | null;
  points: { sampleId: string; value: number }[];
}
export interface MethodAggregate {
  method: string;
  primaryScope: Scope;             // 主显示口径：可判定时为“实际处理”，整批无法判定时为“全部”
  scopes: Record<Scope, ScopeStat>;
  n: number;                       // 该方法在筛选下的全部行
  processedN: number; passthroughN: number; undeterminedN: number; failedN: number; naChangedN: number;
  negativeProcessedN: number;      // 实际处理行中 Δ<0 的行数
  negativeAllN: number;            // 全部行中 Δ<0 的行数（含无法判定）
  // 兼容旧字段（主口径）
  value: number | null; ci: [number, number] | null; nArtifacts: number; nRecords: number; artifactPoints: { sampleId: string; value: number }[]; meanAll: number | null;
}

const CI_METRIC_KEY: Partial<Record<MetricKey, string>> = { psnr: 'psnrGain', ssim: 'ssimGain', edgeF1: 'edgeF1Gain' };
export interface CiLookup { file: CiFile; source: string }
function fromCiFile(ci: CiLookup | null, metric: MetricKey, split: string, method: string, degradation: string, scope: Scope): Omit<ScopeStat, 'points'> | null {
  const key = CI_METRIC_KEY[metric];
  if (!ci || !key || split === 'none') return null;
  const deg = degradation === 'all' ? 'ALL' : degradation;
  const g: CiGroup | undefined = ci.file.groups.find(x => x.split === split && x.method === method && x.degradation === deg && x.scope === scope);
  if (!g) return null;
  const lo = g[`${key}CI95Low`] as number | null, hi = g[`${key}CI95High`] as number | null;
  const value = g[`${key}ArtifactMean`] as number | null;
  const civ: [number, number] | null = lo != null && hi != null ? [lo, hi] : null;
  return { scope, value: value ?? null, ci: civ, ciReliable: !!g.ciReliable && !!civ, sign: (g[`${key}Sign`] as GainSign | null) ?? gainSign(civ), nArtifacts: g.artifactN, nRecords: g.rowN, ciSource: 'ci_by_artifact', ciNote: g.ciNote };
}

export interface AggregateContext { split: string; degradation: string; sampleFiltered: boolean; ci: CiLookup | null }
export function aggregate(rows: ExperimentRow[], map: BaselineMap, metric: MetricKey, methods: string[], ctx: AggregateContext): MethodAggregate[] {
  return methods.map(method => {
    const own = rows.filter(r => r.method === method);
    const st = own.map(r => ({ r, s: appliedStatus(r).status }));
    const processed = st.filter(x => isProcessedStatus(x.s)).map(x => x.r);
    const passthrough = st.filter(x => isPassthroughStatus(x.s)).map(x => x.r);
    const notFailed = st.filter(x => x.s !== 'failed').map(x => x.r);
    const processedN = processed.length, passthroughN = passthrough.length;
    const undeterminedN = st.filter(x => x.s === 'undetermined').length;
    const failedN = st.filter(x => x.s === 'failed').length;
    const naChangedN = st.filter(x => x.s === 'processed_not_applicable_label').length;
    const valueOf = (r: ExperimentRow) => metric === 'processingMs' ? (r.processingMs ?? null) : rowDelta(r, metric, map);
    const stat = (scope: Scope, subset: ExperimentRow[]): ScopeStat => {
      const by = new Map<string, number[]>();
      subset.forEach(r => { const v = valueOf(r); if (v != null && Number.isFinite(v)) { if (!by.has(r.sampleId)) by.set(r.sampleId, []); by.get(r.sampleId)!.push(v); } });
      const points = Array.from(by.entries()).map(([sampleId, vs]) => ({ sampleId, value: mean(vs)! }));
      const nRecords = Array.from(by.values()).reduce((a, v) => a + v.length, 0);
      // 有 ci_by_artifact 且筛选与文件分组一致（未按单件文物筛选）时以文件为准
      const file = !ctx.sampleFiltered ? fromCiFile(ctx.ci, metric, ctx.split, method, ctx.degradation, scope) : null;
      if (file) return { ...file, points };
      const ci = clusterCI(points.map(p => p.value));
      return { scope, value: mean(points.map(p => p.value)), ci, ciReliable: !!ci && points.length >= MIN_RELIABLE_ARTIFACTS, sign: metric === 'processingMs' ? null : gainSign(ci), nArtifacts: points.length, nRecords, ciSource: 'frontend', ciNote: points.length === 0 ? '无数据' : points.length < MIN_RELIABLE_ARTIFACTS ? `CI 不可靠（文物数 ${points.length}）` : null, points };
    };
    const scopes: Record<Scope, ScopeStat> = { all: stat('all', notFailed), processed: stat('processed', processed), passthrough: stat('passthrough', passthrough) };
    const determinable = processedN + passthroughN > 0;
    const primaryScope: Scope = metric === 'processingMs' || !determinable ? 'all' : 'processed';
    const neg = (subset: ExperimentRow[]) => metric === 'processingMs' ? 0 : subset.filter(r => { const v = valueOf(r); return v != null && v < 0; }).length;
    const p = scopes[primaryScope];
    return {
      method, primaryScope, scopes, n: own.length, processedN, passthroughN, undeterminedN, failedN, naChangedN,
      negativeProcessedN: neg(processed), negativeAllN: neg(notFailed),
      value: p.value, ci: p.ci, nArtifacts: p.nArtifacts, nRecords: p.nRecords, artifactPoints: p.points, meanAll: scopes.all.value,
    };
  });
}

/* ---------------- 证据分级（SPEC §0.2，只降不升） ---------------- */

export interface GradeResult { grade: Grade; reasons: string[] }
export function gradeDelta(agg: MethodAggregate | undefined, batch: BatchInfo | undefined, split: string): GradeResult {
  if (!agg) return { grade: '未评测', reasons: ['数据中没有该方法/指标的可比记录'] };
  const p = agg.scopes[agg.primaryScope];
  if (p.value == null) return { grade: '未评测', reasons: [agg.primaryScope === 'processed' && agg.passthroughN > 0 ? `当前筛选下全部 ${agg.passthroughN} 条为原图返回（未处理），没有实际处理的行` : '当前筛选下没有可比记录'] };
  const reasons: string[] = ['只在受控退化上成立（参考图是可读 JPG 裁切，不是碑石真值）'];
  if (batch?.kind === 'retest') reasons.push('样本参与过 v2.1 的误差分析（同批复测）');
  if (batch?.kind === 'historical') reasons.push('历史批次存在先验泄漏');
  if (split !== 'test') reasons.push(split === 'none' ? '本批未划分 dev/test' : '开发组数据可能参与过调参');
  if (p.nArtifacts < 10) reasons.push(`n_文物=${p.nArtifacts}<10`);
  if (!p.ci) reasons.push('无 CI');
  else if (!p.ciReliable) reasons.push(`CI 不可靠（文物数 ${p.nArtifacts}）`);
  else if (p.sign === 'spans_zero') reasons.push('配对增益 CI 跨 0');
  else if (p.sign === 'negative') reasons.push('配对增益 CI 整体在 0 以下');
  if (p.ciSource === 'frontend') reasons.push('CI 为前端临时口径，待替换为 derived/ci_by_artifact');
  if (agg.primaryScope === 'all' && agg.undeterminedN > 0) reasons.push('无法判定原图返回，主数字含全部行');
  return { grade: reasons.length > 1 ? '有限支持' : '已验证（受控退化）', reasons };
}
/** “提升”只能在配对增益 CI 下界 > 0 时使用。 */
export function gainWord(s: ScopeStat): string {
  if (s.value == null) return '无数据';
  if (s.sign === 'positive' && s.ciReliable) return '提升';
  if (s.sign === 'negative' && s.ciReliable) return '下降';
  if (s.sign === 'zero') return '未改动';
  return '变化不确定';
}

/* ---------------- 馆藏运行：排序、默认、原图返回 ---------------- */

export interface RunInfo { run: ProcessingRunR1; time: number | null; legacy: boolean }
const runTime = (r: ProcessingRunR1) => parseIsoTime(r.sortTimestamp || undefined) ?? parseIsoTime(r.finishedAt) ?? parseIsoTime(r.startedAt);
/** 后端已按时间排序并给 legacy 标记（96dce66）；这里只做同样规则的稳定兜底，不改后端顺序之外的含义。 */
export function sortRuns(runs: ProcessingRunR1[]): RunInfo[] {
  return runs.map(run => { const time = runTime(run); return { run, time, legacy: run.legacy === true || run.runKind === 'legacy_unverified' || time == null || /legacy/i.test(run.algorithmVersion || '') }; })
    .sort((a, b) => Number(a.legacy) - Number(b.legacy) || (b.time ?? 0) - (a.time ?? 0));
}

type RunExtras = ProcessingRunR1 & {
  /** 兼容旧字段名；优先用 api.ts 的 grayCriterion / graySource（arch-backend@9ba3a57）。 */
  grayMaxAbsDiff?: number | null;
  grayMeanAbsDiff?: number | null;
  grayPassthroughCriterion?: string | null;
  engineDiagnosticMetrics?: Record<string, number | null>;
  adaptiveDiagnostics?: { version?: string; features?: Record<string, unknown>; decisions?: { operator: string; reason?: string }[]; fidelityGate?: Record<string, unknown>; selectedOutput?: string; limitations?: string } | null;
  frequencyDetails?: { mode?: string; notchApplied?: boolean; adaptive?: RunExtras['adaptiveDiagnostics'] } | null;
};
export type RunOutputMode = 'passthrough' | 'processed' | 'undetermined';
export interface RunOutcome { mode: RunOutputMode; title: string; detail: string; criterion: string; source: string | null; changeText: string | null; grayText: string | null }

export function runAdaptive(run: ProcessingRunR1) {
  const r = run as RunExtras;
  return r.adaptiveDiagnostics || r.frequencyDetails?.adaptive || null;
}
export function ratioText(ratio: number | null | undefined) {
  if (ratio == null) return '无法判定';
  if (ratio > 0 && ratio < 0.0001) return '<0.01%';
  return `${(ratio * 100).toFixed(2)}%`;
}
/** SPEC §8 + 红队：isPassthrough=true →“本次未改动原图”（绝不写“本次算法输出”）；computed-on-read →“读取时校验”。
 * 主判据 pixel-equal-v1 = 全分辨率、全通道（IMREAD_UNCHANGED）；灰度域另列，字段暂无则真实空状态。 */
export function runOutcome(run: ProcessingRunR1): RunOutcome {
  const r = run as RunExtras;
  const source = r.passthroughSource === 'computed-on-read' ? '读取时校验（旧运行，原图与输出 SHA-256 与记录一致后在读取时逐像素比较，未回写）' : r.passthroughSource === 'recorded' ? '处理时记录' : null;
  const criterion = r.passthroughCriterion
    ? `判据：${r.passthroughCriterion}${r.passthroughCriterion === 'pixel-equal-v1' ? '（全通道、全分辨率，不转灰度、不缩放）' : ''}`
    : '判据：未记录';
  const changeText = r.changedPixelCount != null
    ? `全通道改动 ${r.changedPixelCount.toLocaleString()} 像素（${ratioText(r.changedPixelRatio)}），最大绝对差 ${r.maxAbsDiff ?? '—'}`
    : null;
  const grayCriterion = r.grayCriterion || r.grayPassthroughCriterion || null;
  const grayText = r.grayChangedPixelCount != null
    ? `灰度域改动 ${r.grayChangedPixelCount.toLocaleString()} 像素（${ratioText(r.grayChangedPixelRatio)}）${r.grayMaxAbsDiff != null ? `，最大差 ${r.grayMaxAbsDiff}` : ''}${grayCriterion ? `；灰度判据 ${grayCriterion}` : ''}${r.graySource === 'computed-on-read' ? '（读取时校验，仅参考，不决定 isPassthrough）' : r.graySource === 'recorded' ? '（处理时记录，仅参考）' : '（仅参考，不决定 isPassthrough）'}`
    : null;
  if (r.isPassthrough === true) return { mode: 'passthrough', title: '本次未改动原图', detail: '算法判断无需处理，输出与输入逐像素相同（全通道 pixel-equal-v1）。', criterion, source, changeText, grayText };
  if (r.isPassthrough === false) return { mode: 'processed', title: '算法已改动像素', detail: '输出与输入存在像素差异（全通道 pixel-equal-v1）。', criterion, source, changeText, grayText };
  return { mode: 'undetermined', title: '未能判定是否改动', detail: r.passthroughUndeterminedReason || '该运行保存于判据引入前，未记录改动量。', criterion, source, changeText, grayText };
}
/** 代替后端 evaluation_summary（main.py:426 对原图返回也写“实际处理已执行”）。后端修正前前端按 isPassthrough 改写。 */
export function evaluationSummaryText(run: ProcessingRunR1 | null): string {
  if (!run) return '尚未选择运行记录。';
  const o = runOutcome(run);
  if (o.mode === 'passthrough') return '本次未改动原图：算法判断无需处理，输出与输入逐像素相同；没有配对真值，配对质量未评测。';
  if (o.mode === 'processed') return '算法已改动图像（输出与输入存在像素差异）；没有配对真值，配对质量未评测。';
  return '未能判定本次是否改动图像；没有配对真值，配对质量未评测。';
}
