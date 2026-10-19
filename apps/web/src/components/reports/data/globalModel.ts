/** 由批次明细 + URL 筛选派生出全局评测视图所需的全部数据（屏幕与打印共用，保证一致）。 */
import { useMemo } from 'react';
import type { BatchDetail, ExperimentRow } from './types';
import { aggregate, appliedStatus, baselineMap, baselineOf, BatchInfo, gradeDelta, hasSplit, MethodAggregate, GradeResult } from './reportData';
import { METRICS, MetricDef, sortDegradations, sortMethods } from './labels';
import type { UrlState } from '../useReportUrlState';

export interface GlobalModel {
  detail: BatchDetail;
  batch: BatchInfo;
  splitAvailable: boolean;
  split: string;              // 'test' | 'development' | 'none'
  degradation: string;        // 'all' | id
  sample: string;             // '' = 全部
  method: string;             // 当前方法（不含 degraded）
  methods: string[];          // 参与比较的方法（固定顺序，不含 degraded）
  degradations: string[];
  samples: string[];
  rows: ExperimentRow[];      // 当前筛选（划分/退化/文物）下的全部行
  panels: { metric: MetricDef; items: MethodAggregate[] }[];
  primary: MethodAggregate | undefined;   // 当前方法 ΔPSNR
  primaryGrade: GradeResult;
  caseRows: ExperimentRow[];  // 当前方法在筛选下的候选 case
  caseRow: ExperimentRow | undefined;
  caseBaseline: ExperimentRow | undefined;
  notes: string[];
}

const DEFAULT_METHODS = ['adaptive_v21', 'adaptive_joint', 'adaptive_v20'];

export function useGlobalModel(detail: BatchDetail | null, batch: BatchInfo | undefined, url: UrlState): GlobalModel | null {
  return useMemo(() => {
    if (!detail || !batch) return null;
    const all = detail.rows || [];
    const splitAvailable = hasSplit(all);
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
    const panels = metricDefs.map(metric => ({ metric, items: aggregate(rows, map, metric.key, methods) }));
    const primary = panels.find(p => p.metric.key === 'psnr')?.items.find(i => i.method === method);
    const primaryGrade = gradeDelta(primary, batch, split);
    const caseRows = rows.filter(r => r.method === method).sort((a, b) => a.sampleId.localeCompare(b.sampleId) || a.degradation.localeCompare(b.degradation) || (a.strength ?? 0) - (b.strength ?? 0));
    const keyOf = (r: ExperimentRow) => r.caseId || `${r.sampleId}|${r.degradation}|${r.strength ?? ''}`;
    // 默认 case：按文物、退化、强度排序后第一条“实际处理”记录；没有实际处理的才退回第一条（会被标成原图返回）
    const caseRow = caseRows.find(r => keyOf(r) === url.case) || caseRows.find(r => appliedStatus(r).status === 'processed') || caseRows[0];
    const caseBaseline = caseRow ? baselineOf(caseRow, map) : undefined;
    const notes: string[] = [];
    const psnrItems = panels.find(p => p.metric.key === 'psnr')?.items || [];
    psnrItems.forEach(it => {
      if (it.processedN === 0 && it.passthroughN > 0) notes.push(`${it.method}：当前筛选下 ${it.passthroughN} 条全部原图返回（未处理），不计入提升。`);
      if (it.naChangedN > 0) notes.push(`${it.method}：${it.naChangedN} 条标为“不适用”但输出与输入 SHA 不同——不适用分支仍有轻微像素改动（E-05，待修）。`);
      if (it.failedN > 0) notes.push(`${it.method}：${it.failedN} 条运行失败，保留在记录中，不计 0 分。`);
    });
    return { detail, batch, splitAvailable, split, degradation, sample, method, methods, degradations, samples, rows, panels, primary, primaryGrade, caseRows, caseRow, caseBaseline, notes };
  }, [detail, batch, url.split, url.deg, url.sample, url.method, url.case]);
}

export const caseKeyOf = (r: ExperimentRow) => r.caseId || `${r.sampleId}|${r.degradation}|${r.strength ?? ''}`;
export const statusOf = appliedStatus;
