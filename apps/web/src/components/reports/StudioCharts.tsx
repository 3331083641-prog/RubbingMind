import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts/core';
import { HeatmapChart, ScatterChart, BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, VisualMapComponent, MarkLineComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { GlobalModel } from './data/globalModel';
import { OUTCOME_LABELS, studioEvidence } from './data/studioData';
import { degradationLabel, methodLabel, type MetricDef } from './data/labels';
import { useQuietMotion } from './studioMotion';
echarts.use([HeatmapChart, ScatterChart, BarChart, GridComponent, TooltipComponent, VisualMapComponent, MarkLineComponent, CanvasRenderer]);
type Evidence = ReturnType<typeof studioEvidence>;
const colors = ['#2eb88a', '#c83c23', '#c8a86b', '#5b7682', '#434d4c', '#a83220'];

export const StudioCharts: React.FC<{ kind: 'heatmap' | 'distribution' | 'timing'; model: GlobalModel; evidence: Evidence; metric: MetricDef; onSelect: (method: string, degradation?: string) => void }> = ({ kind, model, evidence, metric, onSelect }) => {
  const ref = useRef<HTMLDivElement>(null); const quiet = useQuietMotion(); const callback = useRef(onSelect); callback.current = onSelect;
  const chartRef = useRef<echarts.ECharts | null>(null);
  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current); chartRef.current = chart;
    const ro = new ResizeObserver(() => chart.resize()); ro.observe(ref.current);
    chart.on('click', p => { const d = p.data as { method?: string; degradation?: string } | undefined; if (d?.method) callback.current(d.method, d.degradation); });
    return () => { ro.disconnect(); chart.dispose(); chartRef.current = null; };
  }, []);
  useEffect(() => {
    const chart = chartRef.current; if (!chart) return;
    const methods = model.methods; const labels = methods.map(methodLabel);
    const common = { backgroundColor: 'transparent', animation: !quiet, animationDuration: 640, animationDurationUpdate: quiet ? 0 : 320,
      textStyle: { fontFamily: 'system-ui,sans-serif', color: '#b7bcb7' },
      tooltip: { confine: true, backgroundColor: 'rgba(15, 21, 19, 0.96)', borderColor: '#c8a86b', borderWidth: 1, textStyle: { color: '#f0ede6', fontSize: 12 }, extraCssText: 'box-shadow: 0 4px 16px rgba(0,0,0,0.4); border-radius: 6px;' },
      grid: { left: 126, right: 30, top: 35, bottom: 70 } };
    let option: echarts.EChartsCoreOption;
    if (kind === 'heatmap') {
      const values = evidence.heatmap.filter(x => x.value != null).map(x => Math.abs(x.value!)); const max = Math.max(0.001, ...values);
      option = { ...common, grid: { left: 92, right: 24, top: 24, bottom: 116 },
        xAxis: { type: 'category', data: labels, axisLabel: { interval: 0, fontSize: 11, color: '#b7c2b8', formatter: (s: string) => s.replace(' ', '\n') }, axisLine: { show: false }, axisTick: { show: false } },
        yAxis: { type: 'category', data: model.degradations.map(degradationLabel), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { fontSize: 12, color: '#b7c2b8' } },
        visualMap: { min: metric.delta ? -max : 0, max, calculable: false, orient: 'horizontal', left: 'center', bottom: 14, itemWidth: 13, itemHeight: 150, text: [`+${max.toFixed(metric.digits)} ${metric.unit}`, metric.delta ? `−${max.toFixed(metric.digits)}` : '0'], textStyle: { color: '#98a69c' }, inRange: { color: metric.delta ? ['#c83c23', '#1b2320', '#2eb88a'] : ['#1b2320', '#2eb88a'] } },
        series: [{ type: 'heatmap', animationDelay: (i: number) => quiet ? 0 : Math.floor(i / methods.length) * 50, data: evidence.heatmap.map(x => ({ value: [methods.indexOf(x.method), model.degradations.indexOf(x.degradation), x.value], method: x.method, degradation: x.degradation, artifacts: x.artifacts, records: x.rows })),
          label: { show: true, color: '#f1f0e9', fontSize: 12, formatter: (p: unknown) => { const v = (p as { value: [number, number, number | null] }).value[2]; return v == null ? '—' : `${v > 0 && metric.delta ? '+' : ''}${v.toFixed(metric.digits)}`; } },
          itemStyle: { borderWidth: 4, borderColor: '#141919' }, tooltip: { formatter: (p: unknown) => { const d = (p as { data: { method: string; degradation: string; value: [number, number, number | null]; artifacts: number; records: number } }).data; return `${methodLabel(d.method)} · ${degradationLabel(d.degradation)}<br/>${metric.title} ${d.value[2]?.toFixed(metric.digits) ?? '无数据'} ${metric.unit}<br/>文物 ${d.artifacts} · 记录 ${d.records}<br/>点击筛选本方法与退化类型`; } } }] };
    } else if (kind === 'distribution') {
      option = { ...common, grid: { ...common.grid, bottom: 38 }, xAxis: { type: 'value', min: 0, minInterval: 1, axisLabel: { color: '#b7c2b8' }, nameTextStyle: { color: '#b7c2b8' }, splitLine: { lineStyle: { color: '#29312f' } }, name: '记录数' },
        yAxis: { type: 'category', inverse: true, data: labels, axisLabel: { color: '#b7c2b8' }, axisLine: { show: false }, axisTick: { show: false } },
        series: OUTCOME_LABELS.map((name, i) => ({ name, type: 'bar' as const, stack: 'records', barMaxWidth: 22, animationDelay: (n: number) => quiet ? 0 : n * 28, itemStyle: { color: colors[i] }, data: evidence.distribution.map(d => ({ value: d.counts[i], method: d.method })), tooltip: { formatter: (p: unknown) => { const d = p as { data: { method: string; value: number } }; return `${methodLabel(d.data.method)} · ${name}<br/>${d.data.value} 条`; } } })) };
    } else {
      option = { ...common, xAxis: { type: 'value', min: 0, axisLabel: { color: '#b7c2b8' }, nameTextStyle: { color: '#b7c2b8' }, name: '本批历史耗时 / ms', nameLocation: 'middle', nameGap: 30, splitLine: { lineStyle: { color: '#29312f' } } },
        yAxis: { type: 'value', axisLabel: { color: '#b7c2b8' }, nameTextStyle: { color: '#b7c2b8' }, name: metric.title === '单次耗时' ? 'ΔPSNR / dB' : `${metric.title} ${metric.unit}`, splitLine: { lineStyle: { color: '#29312f' } } },
        series: [{ type: 'scatter', symbolSize: 14, animationDelay: (i: number) => quiet ? 0 : i * 45, data: evidence.timing.map(d => ({ value: [d.milliseconds, d.quality], method: d.method })), itemStyle: { color: '#80b8aa' },
          label: { show: true, position: 'top', fontSize: 11, color: '#d3d6d1', formatter: (p: unknown) => methodLabel((p as { data: { method: string } }).data.method) }, labelLayout: { hideOverlap: true },
          markLine: { symbol: 'none', silent: true, label: { show: false }, lineStyle: { color: '#8a918b' }, data: [{ yAxis: 0 }] },
          tooltip: { formatter: (p: unknown) => { const d = (p as { data: { method: string; value: [number, number] } }).data; return `${methodLabel(d.method)}<br/>历史耗时 ${d.value[0].toFixed(1)} ms<br/>配对质量差 ${d.value[1].toFixed(3)}<br/>仅同批、同环境记录，非当前设备基准`; } } }] };
    }
    chart.setOption(option, true);
    const stable = setTimeout(() => chart.resize(), 420);
    return () => clearTimeout(stable);
  }, [kind, model, evidence, metric, quiet]);
  return <div className={`studio-chart-scroll ${kind === 'heatmap' ? 'is-heatmap' : ''}`}><div ref={ref} data-testid={`studio-${kind}-chart`} role="img" aria-label={kind === 'heatmap' ? `退化类型与方法热力图，${metric.title}` : kind === 'distribution' ? '配对结果与原图返回分布' : '同批历史质量与耗时图'} className="studio-chart" /></div>;
};

export const OutcomeLegend = () => <div className="studio-legend">{OUTCOME_LABELS.map((label, i) => <span key={label}><i style={{ background: colors[i] }} />{label}</span>)}</div>;
