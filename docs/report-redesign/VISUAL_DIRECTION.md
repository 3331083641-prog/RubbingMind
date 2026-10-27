# 视觉方向与已安装 Skills

活动根目录 `D:\Codex\.codex\skills`；manifest 已核对，无重新安装。Taste v2.1.5 commit `12af471`、Classics `5e08c93`、Imagegen `beb16b0`。v1 / experimental 与旧备份不混用。

| 实际加载入口 | 应用 |
|---|---|
| `D:\Codex\.codex\skills\design-taste-frontend\SKILL.md` 与 `references/app-screens.md` | 数据清点、draw.mjs --app、inspect.mjs --app、lint.mjs；颜色用于数据、单一主问题、数字对齐 |
| `D:\Codex\.codex\skills\high-end-visual-design\SKILL.md` | 主舞台空间过渡、定制弹簧曲线、按压反馈、响应式和 GPU 性能约束 |
| `D:\Codex\.codex\skills\minimalist-ui\SKILL.md` | 编辑式层级、短结论、来源与参数折叠、平静面板、减少装饰 |
| `D:\Codex\.codex\skills\imagegen-frontend-web\SKILL.md` | 已实际生成一个横向主舞台参考，明确禁止生成实验曲线、数字和碑拓结果 |
| `D:\Codex\.codex\skills\image-to-code\SKILL.md` | 先观察参考图，提取舞台比例、排版、间距后转成现有 React 组件 |

`gpt-taste/SKILL.md` 已读取评估；其 AIDA / GSAP 营销结构不适合科研应用，不采用。其他技能中冲突的玻璃光效、巨大间距、强制浅色和不做入场动画规则，由用户明确的深墨主题、紧凑首屏和克制动效要求覆盖。

实际运行 draw.mjs 得到 true-black-flat 与 data-terminal 两个可用选项；采用 true-black-flat，seed **477876836**，保留品牌颜色和字形。既有应用顶栏保留，以深墨温度替代纯黑；不复制所抽签的侧栏。使用现有 ECharts，遵循用户要求不换成 Skill 的 SVG 图表实现。

主问题：同一批次、同一口径下，哪些方法有何种质量变化，证据边界是什么？主图单指标、横向比较，零线与负值完整保留。主舞台约 72%，右侧证据窗约 28%，24px 统一间距。独有元素是原始碑拓裁切、配对指标和历史机制链。

参考图只规定单个舞台区域。生成结果中主舞台宽约 74%、右导航约 23%，短标题与分级字号、安静表面、证据导航顺序清晰；实际实现缩短过高空白以适合 1366×768。图中的空坐标区域不会用于生产，必须替换为真实 ECharts。未采用生成参考中额外导航、纹理及未知文案。
