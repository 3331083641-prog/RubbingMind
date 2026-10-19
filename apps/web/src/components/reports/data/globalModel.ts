/** 由批次明细 + DER/CI + URL 筛选派生出全局评测视图所需的全部数据（屏幕与打印共用，保证一致）。 */
import { useMemo } from 'react';
import type { BatchDetail, ExperimentRow } from './types';
import { aggregate, appliedStatus, baselineMap, baselineOf, BatchInfo, CiLookup, DerMerge, gradeDelta, hasSplit, isPassthroughStatus, isProcessedStatus, MethodAggregate, GradeResult, rowDelta } from './reportData';
import { METRICS, MetricDef, sortDegradations, sortMethods } from './labels';
import type { ReportFilters } from '../reportFilters';

export type CaseKind = 'median' | 'worst' | 'passthrough';
export interface RepresentativeCases { median?: ExperimentRow; worst?: ExperimentRow; passthrough?: ExperimentRow; rule: string; processedN: number }

export interface GlobalModel {
  detail: BatchDetail;
  batch: BatchInfo;
  rowsAll: ExperimentRow[];   // 合并 DER 后的全部行
  der: DerMerge;
  ci: CiLookup | null;
  splitAvailable: boolean;
  split: string;              // 'test' | 'development' | 'none'
  degradation: string;        // 'all' | id
  sample: string;             // '' = 全部
  method: string;
  methods: string[];
  degradations: string[];
  samples: string[];
  rows: ExperimentRow[];      // 当前筛选（划分/退化/文物）下的全部行
  panels: { metric: MetricDef; items: MethodAggregate[] }[];
  primary: MethodAggregate | undefined;
  primaryGrade: GradeResult;
  caseRows: ExperimentRow[];
  caseRow: ExperimentRow | undefined;
  caseKind: CaseKind | 'explicit' | 'none';
  representative: RepresentativeCases;
  caseBaseline: ExperimentRow | undefined;
  notes: string[];
}

const DEFAULT_METHODS = ['adaptive_v21', 'adaptive_joint', 'adaptive_v20'];
export const caseKeyOf = (r: ExperimentRow) => r.caseId || `${r.sampleId}|${r.degradation}|${r.strength ?? ''}`;

export const REPRESENTATIVE_RULE = '临时规则（评测科学家 2026-10-19）：在当前批次、划分、方法与退化类型下，把“实际处理”的行按配对 ΔPSNR（输出 − 同 case 退化输入）升序排序（并列按 caseId），取中位位次 ⌊n/2⌋ 作默认；另给“最差一条（负提升）”与“原图返回样例”（按 caseId 排序取中位位次）。将来改读 REPRESENTATIVE_CASES.md 与 derived/mechanism/<样本>/。';

export function representativeCases(caseRows: ExperimentRow[], allRows: ExperimentRow[], hasImages: boolean): RepresentativeCases {
  if (!hasImages) return { rule: '本批次没有图像，不取对照案例。', processedN: 0 };
  const map = baselineMap(allRows);
  const processed = caseRows.filter(r => isProcessedStatus(appliedStatus(r).status)).map(r => ({ r, d: rowDelta(r, 'psnr', map) }))
    .filter((x): x is { r: ExperimentRow; d: number } => x.d != null)
    .sort((a, b) => a.d - b.d || caseKeyOf(a.r).localeCompare(caseKeyOf(b.r)));
  const median = processed.length ? processed[Math.floor(processed.length / 2)].r : undefined;
  const worst = processed.length && processed[0].d < 0 ? processed[0].r : undefined;
  const pass = caseRows.filter(r => isPassthroughStatus(appliedStatus(r).status)).sort((a, b) => caseKeyOf(a).localeCompare(caseKeyOf(b)));
  return { median, worst, passthrough: pass.length ? pass[Math.floor(pass.length / 2)] : undefined, rule: REPRESENTATIVE_RULE, processedN: processed.length };
}

export function useGlobalModel(detail: BatchDetail | null, batch: BatchInfo | undefined, der: DerMerge | null, ci: CiLookup | null, url: ReportFilters): GlobalModel | null {
  return useMemo(() => {
    if (!detail || !batch || !der) return null;
    const all = der.rows;
    const splitAvailable = hasSplit(all) && batch.kind !== 'retest';
    const split = splitAvailable ? (url.split === 'development' || url.split === 'test' ? url.split : 'test') : 'none';
    const degradations = sortDegradations(Array.from(new Set(all.map(r => r.degradation))));
    const degradation = url.deg && degradations.includes(url.deg) ? url.deg : 'all';
    const inSplit = all.filter(r => split === 'none' || r.split === split);
    const samples = Array.from(new Set(inSplit.map(r => r.sampleId))).sort();
    const sample = url.sample && samples.includes(url.sample) ? url.sample : '';
    const rows = inSplit.filter(r => (degradation === 'all' || r.degradation === degradation) && (!sample || r.sampleId === sample));
    const methods = sortMethods(Array.from(new Set(all.map(r => r.method)))).filter(m => m !== 'degraded');
    const method = url.method && methods.includes(url.method) ? url.method : (DEFAULT_METHODS.find(m => methods.includes(m)) || methods[0] || '');
    const map = baselineMap(all);
    const metricDefs = METRICS.filter(m => m.key === 'processingMs' || all.some(r => r[m.key] != null && Number.isFinite(r[m.key] as number)));
    const ctx = { split, degradation, sampleFiltered: !!sample, ci };
    const panels = metricDefs.map(metric => ({ metric, items: aggregate(rows, map, metric.key, methods, ctx) }));
    const primary = panels.find(p => p.metric.key === 'psnr')?.items.find(i => i.method === method);
    const primaryGrade = gradeDelta(primary, batch, split);
    const caseRows = rows.filter(r => r.method === method).sort((a, b) => caseKeyOf(a).localeCompare(caseKeyOf(b)));
    const representative = representativeCases(caseRows, all, batch.hasImages);
    const explicit = url.case ? caseRows.find(r => caseKeyOf(r) === url.case) : undefined;
    const kindParam = url.case === '@worst' ? 'worst' : url.case === '@passthrough' ? 'passthrough' : null;
    let caseRow: ExperimentRow | undefined; let caseKind: GlobalModel['caseKind'] = 'none';
    if (!batch.hasImages) { caseRow = undefined; caseKind = 'none'; }
    else if (explicit) { caseRow = explicit; caseKind = 'explicit'; }
    else if (kindParam) { caseRow = representative[kindParam]; caseKind = kindParam; }
    else if (representative.median) { caseRow = representative.median; caseKind = 'median'; }
    else if (representative.passthrough) { caseRow = representative.passthrough; caseKind = 'passthrough'; }
    const caseBaseline = caseRow ? baselineOf(caseRow, map) : undefined;
    const notes: string[] = [];
    const psnrItems = panels.find(p => p.metric.key === 'psnr')?.items || [];
    psnrItems.forEach(it => {
      if (it.processedN === 0 && it.passthroughN > 0) notes.push(`${it.method}：当前筛选下 ${it.passthroughN} 条全部原图返回（未处理 ${it.passthroughN} 条），该方法对这类退化不做处理，不计入提升，也不算“无负提升”。`);
      if (it.naChangedN > 0) notes.push(`${it.method}：${it.naChangedN} 条为“标为不适用但有改动”——历史批次：不适用分支仍有轻微像素改动（E-05，已在新代码修复）。`);
      if (it.failedN > 0) notes.push(`${it.method}：${it.failedN} 条运行失败，保留在记录中，不计 0 分。`);
    });
    if (der.problem) notes.push(`派生状态（DER）未采用：${der.problem}；7 值状态改用前端兜底（SHA-256 比较）。`);
    return { detail, batch, rowsAll: all, der, ci, splitAvailable, split, degradation, sample, method, methods, degradations, samples, rows, panels, primary, primaryGrade, caseRows, caseRow, caseKind, representative, caseBaseline, notes };
  }, [detail, batch, der, ci, url.split, url.deg, url.sample, url.method, url.case]);
}

export const statusOf = appliedStatus;
