import React, { useState, useEffect, useRef } from 'react';
import { SteleItem, GraphNode, GraphLink, GISWaypoint } from '../types/stele';
import { SteleService } from '../services/api';
import * as echarts from 'echarts';
import { Network, MapPin, Compass, Calendar, ArrowRight, User, BookOpen, Layers, Info } from 'lucide-react';

interface GraphPageProps {
  stele: SteleItem;
  onNavigate: (tab: string) => void;
}

export const GraphPage: React.FC<GraphPageProps> = ({ stele, onNavigate }) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [links, setLinks] = useState<GraphLink[]>([]);
  const [gisRoute, setGisRoute] = useState<GISWaypoint[]>([]);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedWaypoint, setSelectedWaypoint] = useState<number>(0);

  // Ganzhi Calculator State
  const [inputEra, setInputEra] = useState<string>('唐天宝十一载');
  const [ganzhiResult, setGanzhiResult] = useState({
    year: '公元 752 年',
    ganzhi: '壬辰年 (水龙)',
    zodiac: '属龙',
    eraDesc: '唐玄宗李隆基天宝盛世，四海丰稔。是年楚金禅师建多宝塔，颜真卿书碑。'
  });

  // Calculate Ganzhi
  const handleCalculateGanzhi = (eraText: string) => {
    setInputEra(eraText);
    if (eraText.includes('天宝十一') || eraText.includes('752')) {
      setGanzhiResult({
        year: '公元 752 年',
        ganzhi: '壬辰年',
        zodiac: '肖龙',
        eraDesc: '唐玄宗李隆基天宝盛世，四海丰稔。是年楚金禅师建多宝塔，颜真卿书碑。'
      });
    } else if (eraText.includes('中平二') || eraText.includes('185')) {
      setGanzhiResult({
        year: '公元 185 年',
        ganzhi: '乙丑年',
        zodiac: '肖牛',
        eraDesc: '东汉汉灵帝中平二年，黄巾余部掠界，郃阳令曹全平乱抚民，勒石纪功。'
      });
    } else if (eraText.includes('熙平二') || eraText.includes('517')) {
      setGanzhiResult({
        year: '公元 517 年',
        ganzhi: '丁酉年',
        zodiac: '肖鸡',
        eraDesc: '北魏孝明帝熙平二年，胡太后临朝称制，洛阳宗室元怀薨逝归葬邙山。'
      });
    } else if (eraText.includes('建义元') || eraText.includes('528')) {
      setGanzhiResult({
        year: '公元 528 年',
        ganzhi: '戊申年',
        zodiac: '肖猴',
        eraDesc: '北魏孝庄帝建义元年，尔朱荣掀起河阴之变，南北朝政局巨变，残碑存纪。'
      });
    } else {
      setGanzhiResult({
        year: '唐乾元元年 (758)',
        ganzhi: '戊戌年',
        zodiac: '肖狗',
        eraDesc: '安史之乱爆发后颜真卿起兵平原，肃宗即位改元。'
      });
    }
  };

  // Fetch Graph Data
  useEffect(() => {
    let isMounted = true;
    SteleService.getGraph(stele.id).then((data) => {
      if (isMounted) {
        setNodes(data.nodes);
        setLinks(data.links);
        setGisRoute(data.gis_route);
        if (data.nodes.length > 0) {
          setSelectedNode(data.nodes[1] || data.nodes[0]); // default to Yan Zhenqing
        }
      }
    });
    return () => { isMounted = false; };
  }, [stele.id]);

  // Render ECharts Graph
  useEffect(() => {
    if (!chartRef.current || nodes.length === 0) return;

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(chartRef.current);
    }

    const chart = chartInstance.current;

    // Node Categories & Colors: Song dynasty quad-colors
    const categoryColors = {
      stele: '#C83C23',    // Cinnabar
      person: '#D4AF37',   // Gold
      place: '#3E8E7E',    // Celadon
      office: '#A68524',   // Dark Gold
      script: '#62C0AC'    // Celadon light
    };

    const echartsNodes = nodes.map((n) => {
      const isCore = n.category === 'stele';
      const color = categoryColors[n.category] || '#D4AF37';

      return {
        id: n.id,
        name: n.name,
        value: n.value,
        symbolSize: n.symbolSize || (isCore ? 64 : 48),
        itemStyle: {
          color: color,
          borderColor: isCore ? '#FAF6EE' : '#D4AF37',
          borderWidth: isCore ? 3 : 1.5,
          shadowBlur: 15,
          shadowColor: color,
        },
        label: {
          show: true,
          position: 'bottom' as const,
          formatter: '{b}',
          color: '#FAF6EE',
          fontSize: isCore ? 14 : 12,
          fontWeight: (isCore ? 'bold' : 'normal') as any,
          fontFamily: 'serif',
          textBorderColor: '#0A0D12',
          textBorderWidth: 3,
        },
        raw: n
      };
    });

    const echartsLinks = links.map((l) => ({
      source: l.source,
      target: l.target,
      label: {
        show: true,
        formatter: l.relation,
        fontSize: 10,
        color: '#D4AF37',
        fontFamily: 'serif',
        textBorderColor: '#0A0D12',
        textBorderWidth: 2,
      },
      lineStyle: {
        color: 'rgba(212, 175, 55, 0.45)',
        width: 1.8,
        curveness: 0.12,
      }
    }));

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(21, 28, 32, 0.95)',
        borderColor: '#D4AF37',
        borderWidth: 1,
        textStyle: { color: '#FAF6EE', fontFamily: 'serif', fontSize: 12 },
        formatter: (params: any) => {
          if (params.dataType === 'node') {
            const data = params.data.raw;
            return `<b>${data.name}</b><br/><span style="color:#D4AF37">${data.desc || ''}</span>`;
          } else {
            return `关系: ${params.data.label.formatter}`;
          }
        }
      },
      series: [
        {
          type: 'graph',
          layout: 'force',
          data: echartsNodes,
          links: echartsLinks,
          roam: true,
          label: {
            show: true,
          },
          force: {
            repulsion: 550,
            edgeLength: [120, 200],
            gravity: 0.08,
            friction: 0.85,
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: {
              width: 3.5,
              color: '#F5D46E'
            }
          }
        }
      ]
    };

    chart.setOption(option);

    chart.on('click', (params: any) => {
      if (params.dataType === 'node') {
        setSelectedNode(params.data.raw);
      }
    });

    const handleResize = () => chart.resize();
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [nodes, links]);

  return (
    <div className="min-h-[calc(100vh-68px)] bg-[#0A0D12] text-slate-100 p-4 lg:p-6 flex flex-col space-y-6">
      {/* Top Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 px-2">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-celadon/20 border border-celadon/40 flex items-center justify-center text-celadon">
            <Network className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-serif font-bold text-white tracking-wide flex items-center gap-2">
              <span>{stele.title} · 金石时空知识图谱与 GIS 舆图</span>
            </h2>
            <p className="text-xs text-slate-400 font-sans mt-0.5">
              GraphRAG 实体网络 · 人物谱系 · 官制职阶 · 历法岁次换算 · 地理沿革互勘
            </p>
          </div>
        </div>

        {/* Quick Dynasty Presets for Calendar */}
        <div className="flex items-center space-x-1.5 text-xs font-serif">
          <span className="text-slate-400 mr-1 flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5 text-gold" /> 纪年快选:
          </span>
          <button
            onClick={() => handleCalculateGanzhi('唐天宝十一载')}
            className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 hover:text-gold border border-slate-700"
          >
            唐天宝十一载
          </button>
          <button
            onClick={() => handleCalculateGanzhi('东汉中平二年')}
            className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 hover:text-gold border border-slate-700"
          >
            东汉中平二年
          </button>
          <button
            onClick={() => handleCalculateGanzhi('北魏熙平二年')}
            className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 hover:text-gold border border-slate-700"
          >
            北魏熙平二年
          </button>
        </div>
      </div>

      {/* Main Grid: Graph + Side Converter (Height 540px) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left ECharts Graph Canvas (Col 8) */}
        <div className="lg:col-span-8 relative h-[540px] rounded-2xl overflow-hidden glass-panel border border-gold/30 bg-[#090C10] shadow-2xl flex flex-col">
          {/* Background Antique Map */}
          <div 
            className="absolute inset-0 opacity-20 pointer-events-none bg-center bg-cover mix-blend-screen"
            style={{ backgroundImage: `url('/assets/stele/backgrounds/bg_graph_antique_map.png')` }}
          />

          {/* Graph Title & Legend */}
          <div className="absolute top-3.5 left-4 z-10 flex items-center space-x-3 pointer-events-none">
            <div className="px-3 py-1 rounded-full bg-slate-900/80 border border-gold/30 text-xs font-serif text-gold-light backdrop-blur-md">
              GraphRAG 知识图谱 · 排斥力 550 · 碰撞检测
            </div>
            <div className="hidden sm:flex items-center space-x-2 text-[11px] text-slate-300 bg-slate-900/80 px-2.5 py-1 rounded-full border border-slate-800">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-cinnabar" /> 核心碑石</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-gold" /> 金石人物</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-celadon" /> 历史地望</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-600" /> 职官书体</span>
            </div>
          </div>

          {/* ECharts DOM Container */}
          <div ref={chartRef} className="w-full h-full cursor-grab active:cursor-grabbing" />
        </div>

        {/* Right Info & Ganzhi Converter (Col 4) */}
        <div className="lg:col-span-4 flex flex-col space-y-4">
          {/* Selected Node Details Card */}
          <div className="glass-panel p-5 rounded-2xl border border-gold/30 bg-gradient-to-b from-[#151D24] to-[#0D1217] shadow-xl">
            <div className="flex items-center justify-between border-b border-gold/15 pb-2.5 mb-3">
              <div className="flex items-center space-x-2">
                <User className="w-4 h-4 text-gold" />
                <h3 className="font-serif font-bold text-sm text-gold-light">
                  实体考据详录
                </h3>
              </div>
              <span className="text-[10px] font-mono text-celadon-light px-2 py-0.5 rounded bg-celadon/15 border border-celadon/30">
                {selectedNode ? selectedNode.category.toUpperCase() : 'ENTITY'}
              </span>
            </div>

            {selectedNode ? (
              <div className="space-y-3">
                <div className="flex items-center space-x-3.5">
                  {selectedNode.portrait ? (
                    <img 
                      src={selectedNode.portrait} 
                      alt={selectedNode.name} 
                      className="w-14 h-14 rounded-xl object-cover border-2 border-gold/50 shadow-gold-glow"
                    />
                  ) : (
                    <div className="w-14 h-14 rounded-xl bg-gold/10 border border-gold/30 flex items-center justify-center font-serif text-xl font-bold text-gold">
                      {selectedNode.name.charAt(0)}
                    </div>
                  )}

                  <div>
                    <h4 className="font-serif font-bold text-lg text-white">
                      {selectedNode.name}
                    </h4>
                    <p className="text-xs text-slate-400 font-sans mt-0.5">
                      图谱节点权重: <span className="font-mono text-gold-light font-bold">{selectedNode.value}</span>
                    </p>
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed font-sans bg-slate-950/50 p-3 rounded-xl border border-slate-800">
                  {selectedNode.desc || '该实体与本通碑拓在书丹撰文、刊石营建、佛法传承或地理沿革上存在强关联。'}
                </p>

                {/* Related Links in Graph */}
                <div className="text-[11px] text-slate-400 font-serif">
                  <span className="text-gold/90">关联拓扑路径:</span>
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {links
                      .filter(l => l.source === selectedNode.id || l.target === selectedNode.id)
                      .map((l, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[10px]">
                          {l.source} ➔ {l.relation} ➔ {l.target}
                        </span>
                      ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-slate-400 text-xs font-serif">
                在左侧图谱中点击任意节点查看人物画像与文献著录
              </div>
            )}
          </div>

          {/* Ganzhi Calendar Converter */}
          <div className="glass-panel p-5 rounded-2xl border border-gold/30 bg-gradient-to-b from-[#151D24] to-[#0D1217] shadow-xl flex-1 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between border-b border-gold/15 pb-2.5 mb-3">
                <div className="flex items-center space-x-2">
                  <Compass className="w-4 h-4 text-cinnabar" />
                  <h3 className="font-serif font-bold text-sm text-gold-light">
                    干支历法与金石纪年换算器
                  </h3>
                </div>
                <span className="text-[10px] font-sans text-slate-400">正史正朔对齐</span>
              </div>

              {/* Input */}
              <div className="flex items-center space-x-2 mb-3">
                <input
                  type="text"
                  value={inputEra}
                  onChange={(e) => setInputEra(e.target.value)}
                  placeholder="输入年号，例如：唐天宝十一载"
                  className="flex-1 bg-slate-950 border border-slate-700 focus:border-gold rounded-lg px-3 py-1.5 text-xs text-slate-200 outline-none"
                />
                <button
                  onClick={() => handleCalculateGanzhi(inputEra)}
                  className="px-3 py-1.5 rounded-lg bg-gold text-slate-950 font-serif font-bold text-xs hover:brightness-110 active:scale-95"
                >
                  换算
                </button>
              </div>

              {/* Result Grid */}
              <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800">
                  <span className="text-[10px] text-slate-400 font-serif">公历纪元:</span>
                  <div className="font-mono font-bold text-gold-light text-sm mt-0.5">{ganzhiResult.year}</div>
                </div>
                <div className="p-2 rounded-lg bg-slate-950/60 border border-slate-800">
                  <span className="text-[10px] text-slate-400 font-serif">干支生肖:</span>
                  <div className="font-serif font-bold text-cinnabar-light text-sm mt-0.5">{ganzhiResult.ganzhi} ({ganzhiResult.zodiac})</div>
                </div>
              </div>

              <p className="text-[11px] text-slate-300 leading-relaxed font-sans bg-slate-950/40 p-2.5 rounded-lg border border-slate-800">
                {ganzhiResult.eraDesc}
              </p>
            </div>

            <div className="pt-2 text-[10px] text-slate-500 font-serif flex items-center justify-between">
              <span>基于二十四史正史帝王本纪校核</span>
              <span className="text-gold">史历合参</span>
            </div>
          </div>
        </div>
      </div>

      {/* Spatio-temporal GIS Timeline Journey (Bottom Full Width) */}
      <div className="glass-panel p-5 rounded-2xl border border-gold/30 bg-[#0C1014] shadow-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-gold/15 pb-2.5">
          <div className="flex items-center space-x-2">
            <MapPin className="w-4 h-4 text-celadon" />
            <h3 className="font-serif font-bold text-sm text-gold-light">
              金石行旅与历史 GIS 时空轨迹
            </h3>
          </div>
          <span className="text-xs font-sans text-slate-400">
            从唐代长安千福寺立石，到宋代迁入京兆府学孔庙（今西安碑林）
          </span>
        </div>

        {/* Timeline Stages Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {gisRoute.map((wp, idx) => (
            <div
              key={idx}
              onClick={() => setSelectedWaypoint(idx)}
              className={`p-3.5 rounded-xl border transition-all cursor-pointer flex flex-col justify-between ${
                selectedWaypoint === idx
                  ? 'bg-gold/15 border-gold shadow-gold-glow'
                  : 'bg-slate-950/50 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="space-y-2">
                {wp.image && (
                  <div className="h-28 w-full rounded-lg overflow-hidden border border-slate-700">
                    <img src={wp.image} alt={wp.name} className="w-full h-full object-cover" />
                  </div>
                )}
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-celadon-light font-bold">
                      STAGE 0{idx + 1}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {wp.coords[0].toFixed(2)}°E, {wp.coords[1].toFixed(2)}°N
                    </span>
                  </div>
                  <h4 className="font-serif font-bold text-sm text-white mt-1">
                    {wp.name}
                  </h4>
                  <p className="text-[11px] text-gold-light font-serif mt-0.5">
                    {wp.year}
                  </p>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-sans line-clamp-2">
                  {wp.event}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
