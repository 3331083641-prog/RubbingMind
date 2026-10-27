/** Additional views derived from the same rows; no cross-batch pooling or new claims. */
import type { GlobalModel } from './globalModel';
import type { ExperimentRow } from './types';
import type { MetricKey } from './labels';
import { appliedStatus, baselineMap, isPassthroughStatus, rowDelta } from './reportData';

const mean = (values: number[]) => values.length ? values.reduce((a, b) => a + b, 0) / values.length : null;

export function artifactMean(rows: ExperimentRow[], all: ExperimentRow[], metric: MetricKey) {
  const map = baselineMap(all); const groups = new Map<string, number[]>();
  rows.forEach(row => {
    if (row.error) return;
    const value = metric === 'processingMs' ? row.processingMs : rowDelta(row, metric, map);
    if (value == null || !Number.isFinite(value)) return;
    const values = groups.get(row.sampleId) || []; values.push(value); groups.set(row.sampleId, values);
  });
  return { value: mean([...groups.values()].map(v => mean(v)!)), artifacts: groups.size, rows: [...groups.values()].reduce((n, v) => n + v.length, 0) };
}

export const OUTCOME_LABELS = ['配对正差', '负提升', '配对零差', '原图返回', '无法判定 / E-05', '执行失败'];

export function studioEvidence(model: GlobalModel, metric: MetricKey = 'psnr') {
  const map = baselineMap(model.rowsAll);
  const outcomeMetric: MetricKey = metric === 'processingMs' ? 'psnr' : metric;
  const distribution = model.methods.map(method => {
    const counts = [0, 0, 0, 0, 0, 0];
    model.rows.filter(r => r.method === method).forEach(r => {
      const status = appliedStatus(r).status; const delta = rowDelta(r, outcomeMetric, map);
      if (r.error || status === 'failed') counts[5]++;
      else if (isPassthroughStatus(status)) counts[3]++;
      else if (status !== 'processed' || delta == null) counts[4]++;
      else counts[delta > 0 ? 0 : delta < 0 ? 1 : 2]++;
    });
    return { method, counts, total: counts.reduce((a, b) => a + b, 0) };
  });
  const heatmap = model.degradations.flatMap(degradation => model.methods.map(method => {
    const rows = model.rows.filter(r => r.method === method && r.degradation === degradation);
    const scope = model.primary?.primaryScope || 'processed';
    const selected = metric === 'processingMs' || scope === 'all' ? rows : rows.filter(r => appliedStatus(r).status === 'processed');
    return { method, degradation, scope: metric === 'processingMs' ? 'all' : scope, ...artifactMean(selected, model.rowsAll, metric) };
  }));
  const environmentRecorded = !!model.detail.environment && Object.keys(model.detail.environment).length > 0;
  const timing = environmentRecorded ? model.methods.map(method => {
    const panel = model.panels.find(p => p.metric.key === outcomeMetric);
    const it = panel?.items.find(i => i.method === method);
    const scope = it?.primaryScope || 'processed';
    // Both axes must use the same rows, with the same artifact weighting. A
    // missing time or missing paired metric excludes that row from both axes.
    const rows = model.rows.filter(r => r.method === method && !r.error &&
      (scope === 'all' || appliedStatus(r).status === 'processed') &&
      r.processingMs != null && Number.isFinite(r.processingMs) && rowDelta(r, outcomeMetric, map) != null);
    const milliseconds = artifactMean(rows, model.rowsAll, 'processingMs');
    const quality = artifactMean(rows, model.rowsAll, outcomeMetric);
    return { method, milliseconds: milliseconds.value, quality: quality.value, artifacts: quality.artifacts, rows: quality.rows, scope };
  }).filter(p => p.milliseconds != null && p.quality != null) : [];
  return { metric, outcomeMetric, heatmap, distribution, timing, environmentRecorded,
    note: 'Only current batch/split/degradation/sample. Heatmap means weight artifacts equally; distribution is record counts, positive differences are not certified successes; timing pairs both axes on the same rows and artifacts in the recorded historical environment.' };
}
