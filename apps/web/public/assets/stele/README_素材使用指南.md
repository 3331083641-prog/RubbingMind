# 中华贞石数字典藏馆 · Antigravity 视觉素材包

这套素材可直接放到项目的 `public/assets/stele/`，采用 PNG 文件，另附 `assets_manifest.json` 索引。

## 与五个页面的对应关系

| 页面 | 素材 | 用法 |
|---|---|---|
| 1 首页门户 | `backgrounds/bg_home_ink_landscape.png` | Hero 背景，CSS 渐变遮罩；叠加受损与修复概念图做倾斜对照画布 |
| 1 首页门户 | `rubbings/stele_tang_duobao_damaged.png`、`rubbings/stele_tang_duobao_restored_demo.png` | Before/After，必须同一坐标缩放 |
| 2 数字典藏馆 | `rubbings/stele_tang_duobao_clean.png`、`rubbings/stele_han_caoquan.png`、`rubbings/stele_wei_yuanhuai.png`、`rubbings/stele_wei_jianyi_fragment.png` | 四张主要碑拓封面，留白区域由前端排版元数据 |
| 2 数字典藏馆 | `backgrounds/bg_museum_hall.png` | 可选低亮度场馆背景 |
| 3 修复工作台 | 上述 before/after、`analysis/fft_duobao_spectrum.png`、`analysis/stroke_topology_demo.png`、`analysis/glyph_*.png` | 修复对照、频谱视图、骨架与候选字示意 |
| 3 修复工作台 | `backgrounds/texture_xuan_paper.png` | 乌丝栏宣纸背景；竖排汉字与格线使用 CSS (`writing-mode: vertical-rl`) |
| 4 时空图谱 | `backgrounds/bg_graph_antique_map.png`、`portraits/*.png`、`scenes/*.png` | ECharts Force 背景与图谱人物节点、时间轴场景封面 |
| 5 算法评测与报告 | 宣纸纹理、before/after 与字形素材 | 报告容器；数据表、雷达图、柱形图以及 PDF 输出由程序实际生成 |

## 严格说明

1. 所有碑拓为**程序化创作的展示模拟图像**，包括标题命名但不是相关古碑的准确文字拓本；不能作为博物馆藏品数字图或 OCR 基准真值。
2. `stele_tang_duobao_restored_demo.png` 是**概念性预期视觉效果**，不代表实际运行 2D-FFT、NLM、CLAHE 后得到的结果，不能证明 PSNR 32.45 dB 等指标。
3. 人物小头像从已生成的 UI 概念图中截取，是 AI 风格的**概念插画**，不是经证实的历史肖像，建议仅用于节点装饰。
4. 建筑、山水及舆图是古风氛围图，不作为真实地理或史实复原证据；GIS 的位置点和线路使用可核查的数据重新建模。
5. 按钮、筛选、滚动、拖动修复对比、GraphRAG 节点和 PDF 导出功能需要前端/后端实际完成，**不应将 5 张 UI 概念图直接设置为页面背景**。
6. 参赛时须将演示素材与可复现实验样本分别管理；未来替换为公开许可或获授权的高分辨率真实拓片，并记录来源、许可、碑名、年代及图像版本。
