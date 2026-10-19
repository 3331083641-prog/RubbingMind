/**
 * ECharts 横向比较（小多图）：每个量纲一个独立网格和坐标轴，绝不把两种单位画在同一根轴上。
 * - 坐标轴范围总是包含 0 和全部数据（含负值与 CI 端点），不做 scale 截断。
 * - 柱 = 按文物聚类的均值；黑须 = 按文物 bootstrap 95% CI；小点 = 每件文物的均值（真实数据点）。
 * - 负值用朱砂色画在零线左侧；标题注明指标方向。点击柱 → 选中方法；点击点 → 选中该文物（筛选联动）。
 */
import React, { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts/core';
import { BarChart, ScatterChart, CustomChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, TitleComponent, MarkLineComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { MethodAggregate } from './data/reportData';
import { MetricDef, directionText, methodLabel } from './data/labels';

echarts.use([BarChart, ScatterChart, CustomChart, GridComponent, TooltipComponent, TitleComponent, MarkLineComponent, CanvasRenderer]);

export interface ChartPanel { metric: MetricDef; items: MethodAggregate[] }
interface Props {
  panels: ChartPanel[];
  methods: string[];
  selectedMethod?: string;
  onSelectMethod?: (m: string) => void;
  onSelectSample?: (sampleId: string, method: string) => void;
  layout?: 'row' | 'column';
  theme?: 'screen' | 'print';
  height?: number;
  width?: number;
  testId?: string;
}

const C = {
  screen: { text: '#cbd5e1', sub: '#94a3b8', axis: '#334155', pos: '#3E8E7E', neg: '#C83C23', sel: '#D4AF37', point: 'rgba(245,212,110,0.85)', ci: '#e2e8f0', zero: '#F5D46E', bg: 'transparent', neutral: '#64748b' },
  print: { text: '#1f2937', sub: '#4b5563', axis: '#9ca3af', pos: '#2f6f62', neg: '#b3321b', sel: '#8a6d12', point: 'rgba(60,60,60,0.75)', ci: '#111827', zero: '#111827', bg: '#ffffff', neutral: '#9ca3af' },
};

function niceStep(range: number) {
  const raw = range / 4; const mag = Math.pow(10, Math.floor(Math.log10(raw || 1))); const n = raw / mag;
  return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * mag;
}
/** 轴范围：总是包含 0 与全部数据（均值、CI 端点、每件文物点），取整到“好看”的刻度，不做 scale 截断。 */
export function extent(items: MethodAggregate[]) {
  const vals: number[] = [0];
  items.forEach(i => { if (i.value != null) vals.push(i.value); if (i.ci) vals.push(i.ci[0], i.ci[1]); i.artifactPoints.forEach(p => vals.push(p.value)); });
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const step = niceStep((hi - lo) || Math.abs(hi) || 1);
  const min = lo < 0 ? Math.floor(lo / step) * step : 0;
  const max = hi > 0 ? Math.ceil(hi / step) * step : step;
  return { min, max, step };
}

export function buildOption(panels: ChartPanel[], methods: string[], selected: string | undefined, layout: 'row' | 'column', theme: 'screen' | 'print', containerWidth: number) {
  const col = C[theme]; const N = panels.length || 1;
  const leftLabel = 112; const gapPx = 22;
  const pw = Math.max(80, (containerWidth - leftLabel - 16 - gapPx * (N - 1)) / N);
  const leftOf = (i: number) => leftLabel + i * (pw + gapPx);
  const grids = panels.map((_, i) => layout === 'row'
    ? { left: leftOf(i), width: pw, top: 46, bottom: 26 }
    : { left: leftLabel, right: 16, top: `${(100 / N) * i + 7}%`, height: `${100 / N - 13}%` });
  const option: echarts.EChartsCoreOption = {
    backgroundColor: col.bg, animation: theme === 'screen',
    textStyle: { fontFamily: '"Noto Serif SC","Source Han Serif SC","SimSun",serif' },
    tooltip: { trigger: 'item', confine: true, backgroundColor: 'rgba(10,13,18,0.94)', borderColor: '#D4AF37', textStyle: { color: '#e2e8f0', fontSize: 12 } },
    title: panels.map((p, i) => ({
      text: `${p.metric.title}${p.metric.unit ? `（${p.metric.unit}）` : ''}`, subtext: `${directionText(p.metric.direction)}${p.metric.note ? ` · ${p.metric.note}` : ''}`,
      left: layout === 'row' ? leftOf(i) : leftLabel, top: layout === 'row' ? 0 : `${(100 / N) * i}%`,
      textStyle: { color: col.text, fontSize: 13, fontWeight: 600 }, subtextStyle: { color: p.metric.direction === 'higher' ? col.pos : col.neg, fontSize: 11 }, itemGap: 2,
    })),
    grid: grids,
    xAxis: panels.map((p, i) => { const e = extent(p.items); return {
      type: 'value', gridIndex: i, scale: false, min: e.min, max: e.max, interval: e.step,
      axisLabel: { color: col.sub, fontSize: 10, formatter: (v: number) => Math.abs(v) >= 100 ? v.toFixed(0) : Math.abs(v) >= 1 ? v.toFixed(1) : v.toFixed(2) },
      splitLine: { lineStyle: { color: col.axis, opacity: 0.35 } }, axisLine: { show: false },
    }; }),
    yAxis: panels.map((_, i) => ({
      type: 'category', gridIndex: i, data: methods, inverse: true,
      axisLabel: { show: layout === 'column' || i === 0, width: leftLabel - 8, overflow: 'truncate', color: col.text, fontSize: 11, formatter: (m: string) => methodLabel(m) },
      axisTick: { show: false }, axisLine: { lineStyle: { color: col.axis } },
    })),
    series: panels.flatMap((p, i) => {
      const byMethod = new Map(p.items.map(it => [it.method, it]));
      const unit = p.metric.unit ? ` ${p.metric.unit}` : '';
      const fmt = (v: number | null | undefined) => v == null ? '无数据' : `${p.metric.delta && v > 0 ? '+' : ''}${v.toFixed(p.metric.digits)}${unit}`;
      return [
        { type: 'bar', xAxisIndex: i, yAxisIndex: i, barMaxWidth: 14, name: p.metric.title,
          data: methods.map(m => { const it = byMethod.get(m); const v = it?.value ?? null;
            const color = !p.metric.delta ? col.neutral : v == null || v >= 0 ? col.pos : col.neg;
            return { value: v, method: m, itemStyle: { color, borderColor: m === selected ? col.sel : 'transparent', borderWidth: m === selected ? 2 : 0 } }; }),
          tooltip: { formatter: (q: { data: { method: string } }) => { const it = byMethod.get(q.data.method); if (!it) return '';
            const scope = it.scope === 'processed' ? `实际处理记录（排除原图返回 ${it.passthroughN} 条）` : p.metric.delta ? '全部记录（无法判定原图返回）' : '全部记录';
            return `<b>${methodLabel(it.method)}</b> · ${p.metric.title}<br/>按文物聚类均值：${fmt(it.value)}<br/>95% CI（文物 bootstrap）：${it.ci ? `${fmt(it.ci[0])} ~ ${fmt(it.ci[1])}` : '无（n_文物<2）'}<br/>口径：${scope}<br/>n_文物 ${it.nArtifacts} · 记录 ${it.nRecords}/${it.n}${p.metric.delta ? ` · 负提升 ${it.negativeN}` : ''}${it.failedN ? ` · 失败 ${it.failedN}` : ''}${p.metric.delta && it.meanAll != null && it.scope === 'processed' ? `<br/>对照：含原图返回的全部记录均值 ${fmt(it.meanAll)}` : ''}`; } },
          markLine: { silent: true, symbol: 'none', lineStyle: { color: col.zero, width: 1.2, type: 'solid' }, label: { show: false }, data: [{ xAxis: 0 }] },
        },
        { type: 'custom', xAxisIndex: i, yAxisIndex: i, name: 'CI', silent: true, z: 5,
          renderItem: (_params: unknown, api: { value: (d: number) => number; coord: (v: [number, number]) => number[]; size: (v: [number, number]) => number[] }) => {
            const lo = api.value(0), hi = api.value(1), y = api.value(2); if (!Number.isFinite(lo) || !Number.isFinite(hi)) return null;
            const a = api.coord([lo, y]), b = api.coord([hi, y]); const h = 4;
            const style = { stroke: col.ci, lineWidth: 1.2 };
            return { type: 'group', children: [
              { type: 'line', shape: { x1: a[0], y1: a[1], x2: b[0], y2: b[1] }, style },
              { type: 'line', shape: { x1: a[0], y1: a[1] - h, x2: a[0], y2: a[1] + h }, style },
              { type: 'line', shape: { x1: b[0], y1: b[1] - h, x2: b[0], y2: b[1] + h }, style },
            ] };
          },
          encode: { x: [0, 1], y: 2 },
          data: methods.map((m, idx) => { const it = byMethod.get(m); return it?.ci ? [it.ci[0], it.ci[1], idx] : [NaN, NaN, idx]; }),
        },
        { type: 'scatter', xAxisIndex: i, yAxisIndex: i, name: '每件文物均值', symbolSize: 5, z: 6,
          itemStyle: { color: col.point },
          data: methods.flatMap(m => (byMethod.get(m)?.artifactPoints || []).map(pt => ({ value: [pt.value, m], sampleId: pt.sampleId, method: m }))),
          tooltip: { formatter: (q: { data: { sampleId: string; method: string; value: [number, string] } }) => `${q.data.sampleId} · ${methodLabel(q.data.method)}<br/>该文物均值 ${fmt(q.data.value[0])}<br/><span style="color:#94a3b8">点击查看该文物的对照图</span>` },
        },
      ];
    }),
  };
  return option;
}

export const MethodComparisonChart: React.FC<Props> = ({ panels, methods, selectedMethod, onSelectMethod, onSelectSample, layout = 'row', theme = 'screen', height = 300, width, testId }) => {
  const ref = useRef<HTMLDivElement>(null);
  const chart = useRef<echarts.ECharts | null>(null);
  const [w, setW] = useState(width || 0);
  const handlers = useRef({ onSelectMethod, onSelectSample });
  handlers.current = { onSelectMethod, onSelectSample };
  useEffect(() => {
    if (!ref.current) return;
    const c = echarts.init(ref.current, undefined, width ? { width, height, renderer: 'canvas' } : { renderer: 'canvas' });
    chart.current = c;
    c.on('click', (ev) => {
      const p = ev as unknown as { seriesType?: string; data?: { method?: string; sampleId?: string } };
      if (p.seriesType === 'scatter' && p.data?.sampleId && p.data.method) handlers.current.onSelectSample?.(p.data.sampleId, p.data.method);
      else if (p.data?.method) handlers.current.onSelectMethod?.(p.data.method);
    });
    const ro = width ? null : new ResizeObserver(() => { c.resize(); setW(ref.current?.clientWidth || 0); });
    ro?.observe(ref.current);
    return () => { ro?.disconnect(); c.dispose(); chart.current = null; };
  }, [width, height]);
  useEffect(() => { const cw = width || ref.current?.clientWidth || w || 1200; chart.current?.setOption(buildOption(panels, methods, selectedMethod, layout, theme, cw), true); }, [panels, methods, selectedMethod, layout, theme, w, width]);
  return <div ref={ref} data-testid={testId} role="img" aria-label={`算法横向比较图：${panels.map(p => p.metric.title).join('、')}`} style={{ width: width ? `${width}px` : '100%', height }} />;
};
