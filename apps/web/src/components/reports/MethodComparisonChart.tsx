/**
 * ECharts 横向比较（小多图）：每个量纲一个独立网格和坐标轴，绝不把两种单位画在同一根轴上。
 * - 坐标轴范围总是包含 0 和全部数据（含负值与 CI 端点），不做 scale 截断。
 * - 柱 = 主口径（可判定时为“实际处理”）的文物均值；须 = 按文物聚类 bootstrap 95% CI（文物数 < 3 或空组不画）；小点 = 每件文物的均值。
 * - 全部原图返回、没有实际处理行的方法不画柱，在零线处写“未处理 N 条”，不显示成“提升 0”。
 * - 负值用朱砂色画在零线左侧；标题注明指标方向。点击柱 → 选中方法；点击点 → 选中该文物（筛选联动）。
 */
import React, { useEffect, useRef, useState } from 'react';
import * as echarts from 'echarts/core';
import { BarChart, ScatterChart, CustomChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, TitleComponent, MarkLineComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { GAIN_SIGN_TEXT, liftClaimDisplay, mayClaimPositiveLift, SCOPE_LABELS, type MethodAggregate, type Scope } from './data/reportData';
import { MetricDef, directionText, methodLabel } from './data/labels';
import { useQuietMotion } from './studioMotion';

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
  screen: { text: '#f0ede6', sub: '#98a69c', axis: '#2d3a33', pos: '#2eb88a', neg: '#c83c23', sel: '#c8a86b', point: 'rgba(223, 193, 135, 0.9)', ci: '#eef2ec', zero: '#c8a86b', bg: 'transparent', neutral: '#5a6860' },
  print: { text: '#1f2937', sub: '#4b5563', axis: '#9ca3af', pos: '#2f6f62', neg: '#b3321b', sel: '#8a6d12', point: 'rgba(60,60,60,0.75)', ci: '#111827', zero: '#111827', bg: '#ffffff', neutral: '#9ca3af' },
};

function niceStep(range: number) {
  const raw = range / 4; const mag = Math.pow(10, Math.floor(Math.log10(raw || 1))); const n = raw / mag;
  return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * mag;
}
/** 轴范围：总是包含 0 与全部数据（均值、CI 端点、每件文物点），取整到“好看”的刻度，不做 scale 截断。 */
export function extent(items: MethodAggregate[]) {
  const vals: number[] = [0];
  items.forEach(i => { const p = i.scopes[i.primaryScope]; if (p.value != null) vals.push(p.value); if (p.ci && p.ciReliable) vals.push(p.ci[0], p.ci[1]); p.points.forEach(pt => vals.push(pt.value)); });
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const step = niceStep((hi - lo) || Math.abs(hi) || 1);
  const min = lo < 0 ? Math.floor(lo / step) * step : 0;
  const max = hi > 0 ? Math.ceil(hi / step) * step : step;
  return { min, max, step };
}

export function buildOption(panels: ChartPanel[], methods: string[], selected: string | undefined, layout: 'row' | 'column', theme: 'screen' | 'print', containerWidth: number, motion = true) {
  const col = C[theme]; const N = panels.length || 1;
  const leftLabel = 112; const gapPx = 22;
  const pw = Math.max(80, (containerWidth - leftLabel - 16 - gapPx * (N - 1)) / N);
  const leftOf = (i: number) => leftLabel + i * (pw + gapPx);
  const grids = panels.map((_, i) => layout === 'row'
    ? { left: leftOf(i), width: pw, top: 46, bottom: 26 }
    : { left: leftLabel, right: 16, top: `${(100 / N) * i + 7}%`, height: `${100 / N - 13}%` });
  const option: echarts.EChartsCoreOption = {
    backgroundColor: col.bg, animation: theme === 'screen' && motion, animationDuration: 620, animationDurationUpdate: motion ? 320 : 0,
    textStyle: { fontFamily: 'system-ui,sans-serif' },
    tooltip: { trigger: 'item', confine: true, backgroundColor: 'rgba(15, 21, 19, 0.96)', borderColor: '#c8a86b', borderWidth: 1, textStyle: { color: '#f0ede6', fontSize: 12 }, extraCssText: 'box-shadow: 0 4px 16px rgba(0,0,0,0.4); border-radius: 6px;' },
    title: panels.map((p, i) => ({
      text: `${p.metric.title}${p.metric.unit ? `（${p.metric.unit}）` : ''}`, subtext: `${directionText(p.metric.direction)}${p.metric.note ? ` · ${p.metric.note}` : ''}`,
      left: layout === 'row' ? leftOf(i) : leftLabel, top: layout === 'row' ? 0 : `${(100 / N) * i}%`,
      textStyle: { color: col.text, fontSize: 13, fontWeight: 600 }, subtextStyle: { color: p.metric.direction === 'higher' ? col.pos : col.neg, fontSize: 11 }, itemGap: 2,
    })),
    grid: grids,
    xAxis: panels.map((p, i) => { const e = extent(p.items); return {
      type: 'value', gridIndex: i, scale: false, min: e.min, max: e.max, interval: e.step,
      axisLabel: { color: col.sub, fontSize: 11, formatter: (v: number) => Math.abs(v) >= 100 ? v.toFixed(0) : Math.abs(v) >= 1 ? v.toFixed(1) : v.toFixed(2) },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)', type: 'dashed' } }, axisLine: { show: false },
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
          data: methods.map(m => { const it = byMethod.get(m); const v = it ? it.scopes[it.primaryScope].value : null;
            const st0 = it ? it.scopes[it.primaryScope] : null; const color = !p.metric.delta ? col.neutral : !st0 || st0.value == null ? col.neutral : mayClaimPositiveLift(st0) ? col.pos : st0.sign === 'negative' && st0.ciReliable ? col.neg : col.neutral;
            return { value: v, method: m, itemStyle: { color, borderColor: m === selected ? col.sel : 'transparent', borderWidth: m === selected ? 2 : 0 } }; }),
          tooltip: { formatter: (q: { data: { method: string } }) => { const it = byMethod.get(q.data.method); if (!it) return '';
            const line = (sc: Scope) => { const st = it.scopes[sc]; const ci = st.ci && st.ciReliable ? `［${fmt(st.ci[0])}, ${fmt(st.ci[1])}］` : st.ciNote ? `（${st.ciNote}）` : st.ci ? '' : '（无数据）';
              return `${sc === it.primaryScope ? '<b>' : ''}${SCOPE_LABELS[sc]}：${fmt(st.value)} ${ci} · 文物 ${st.nArtifacts} / 行 ${st.nRecords}${p.metric.delta && st.sign ? ` · ${GAIN_SIGN_TEXT[st.sign]}` : ''}${p.metric.delta ? ` · 声明 ${liftClaimDisplay(st)}${st.liftClaimLabel ? `（${st.liftClaimLabel}）` : ''}` : ''}${sc === it.primaryScope ? '</b>' : ''}`; };
            const src = it.scopes[it.primaryScope].ciSource === 'ci_by_artifact' ? 'CI 来源：derived/ci_by_artifact.json' : 'CI：临时口径，前端计算，待替换为 derived/ci_by_artifact';
            return `<b>${methodLabel(it.method)}</b> · ${p.metric.title}（主口径：${SCOPE_LABELS[it.primaryScope]}）<br/>${p.metric.delta ? (['processed', 'all', 'passthrough'] as Scope[]).map(line).join('<br/>') : line('all')}<br/>n ${it.n} · 实际处理 ${it.processedN} · 原图返回 ${it.passthroughN} · 无法判定 ${it.undeterminedN}${it.naChangedN ? ` · E-05 ${it.naChangedN}` : ''}${it.failedN ? ` · 失败 ${it.failedN}` : ''}${p.metric.delta ? ` · 实际处理中负提升 ${it.negativeProcessedN}` : ''}<br/><span style="color:#94a3b8">${src}</span>`; } },
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
          data: methods.map((m, idx) => { const st = byMethod.get(m)?.scopes[byMethod.get(m)!.primaryScope]; return st?.ci && st.ciReliable ? [st.ci[0], st.ci[1], idx] : [NaN, NaN, idx]; }),
        },
        { type: 'custom', xAxisIndex: i, yAxisIndex: i, name: '未处理', silent: true, z: 7,
          renderItem: (_params: unknown, api: { value: (d: number) => number; coord: (v: [number, number]) => number[] }) => {
            const n = api.value(1); if (!Number.isFinite(n) || n <= 0) return null;
            const a = api.coord([0, api.value(0)]);
            return { type: 'text', style: { x: a[0] + 4, y: a[1], text: `未处理 ${n} 条`, fill: col.sub, fontSize: 10, verticalAlign: 'middle' } };
          },
          encode: { y: 0 },
          data: methods.map((m, idx) => { const it = byMethod.get(m); const empty = it && p.metric.delta && it.scopes[it.primaryScope].value == null && it.passthroughN > 0; return [idx, empty ? it!.passthroughN : NaN]; }),
        },
        { type: 'scatter', xAxisIndex: i, yAxisIndex: i, name: '每件文物均值', symbolSize: 5, z: 6,
          itemStyle: { color: col.point },
          data: methods.flatMap(m => { const it = byMethod.get(m); return (it ? it.scopes[it.primaryScope].points : []).map(pt => ({ value: [pt.value, m], sampleId: pt.sampleId, method: m })); }),
          tooltip: { formatter: (q: { data: { sampleId: string; method: string; value: [number, string] } }) => `${q.data.sampleId} · ${methodLabel(q.data.method)}<br/>该文物均值 ${fmt(q.data.value[0])}<br/><span style="color:#94a3b8">点击查看该文物的对照图</span>` },
        },
      ];
    }),
  };
  return option;
}

export const MethodComparisonChart: React.FC<Props> = ({ panels, methods, selectedMethod, onSelectMethod, onSelectSample, layout = 'row', theme = 'screen', height = 300, width, testId }) => {
  const quiet = useQuietMotion();
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
  useEffect(() => { const cw = width || ref.current?.clientWidth || w || 1200; chart.current?.setOption(buildOption(panels, methods, selectedMethod, layout, theme, cw, !quiet), true); }, [panels, methods, selectedMethod, layout, theme, w, width, quiet]);
  return <div ref={ref} data-testid={testId} role="img" aria-label={`算法横向比较图：${panels.map(p => p.metric.title).join('、')}`} style={{ width: width ? `${width}px` : '100%', height }} />;
};
