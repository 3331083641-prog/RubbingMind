# 墨韵智考

**基于频空域联合去噪、多模态残字推演与 GraphRAG 时空考据的金石碑拓智能修复系统**

[![RubbingMind CI](https://github.com/3331083641-prog/RubbingMind/actions/workflows/ci.yml/badge.svg)](https://github.com/3331083641-prog/RubbingMind/actions)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-gold.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![React 18](https://img.shields.io/badge/React-18.2-61dafb.svg)](https://react.dev/)
[![Three.js](https://img.shields.io/badge/Three.js-r163-black.svg)](https://threejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)

---

## 1. 项目介绍

中国历代金石碑刻是承载中华文明正史、宗法谱系、典章制度与书法演进的国之重宝。然而，传世碑石在千百年岁月风霜中，普遍面临自然风化剥蚀、雨水酸蚀、拓工经纬织纹混叠、外力斩凿以及拓墨斑驳漫漶等多重退化困境。传统人工金石学考据高度依赖专家经验，微痕肉眼辨识难、拓本残字存疑争议大、碑刻流布谱系考证繁复。

**“墨韵智考”** 针对上述痛点，首创**频空域联合去噪微痕重建管线**，并融合 **Three.js 高精度三维碑刻数字孪生**、**古籍多模态拓扑贝叶斯残字推演** 与 **GraphRAG 历代金石时空图谱**，构筑了从“底层高保真数字微痕恢复”到“顶层多源史实互勘”的全栈数字人文科研与展陈系统。系统兼具工程复现性与学术严谨性，致力于为博物馆、古籍研究所及数字人文学者提供商业级与科研级的一体化解决方案。

---

## 2. 核心功能

系统由五大核心模块组成，支持跨页面状态同步与全流程金石考据闭环：

| 模块名称 | 核心功能定位 | 关键技术与交互亮点 |
| :--- | :--- | :--- |
| **1. 首页门户与三维数字展陈** | 沉浸式数字碑林孪生门户 | 基于 Three.js 实现多层次石材质感渲染（龙首、螭纽、字口、赑屃龟趺底座）、环境光遮蔽、鼠标多角度悬停旋转、微痕激光扫描动画与 4 通核心碑拓漫反射动态贴图切换。 |
| **2. 中华贞石数字典藏馆** | 28件跨越七朝代的真实馆藏库 | 严格收录东汉、北魏、唐代、宋代、元代、明代、清代七个朝代各 4 件（共 28 件）真实馆藏善拓；提供 8 标签独立朝代切换、风化等级与模糊检索多条件组合过滤；支持馆藏原件著录与授权说明。 |
| **3. 频空域微痕修复工作台** | 图像去噪增强与古籍释读 | 左右可拖拽对比拉杆画布、2D-FFT 幅度谱可视化、玄金笔画骨架图与宣纸朱砂拓渲染；右栏 35 字古籍竖排释读卷轴、Top-3 贝叶斯候选残字推演卡与一键采纳修补。 |
| **4. GraphRAG 与 GIS 时空图谱** | 金石人物知识图谱与行旅轨迹 | ECharts 5 力导向拓扑网络（碑刻-书家-撰文者-藏所-官职）、防重叠力场排斥算法；联动历史 GIS 空间地图展示原刻立石故址到现代博物馆入藏的流转时空轨迹；内置干支历法与西历双向换算器。 |
| **5. 算法评测及考据报告** | 量化指标消融实验与学术建档 | Baseline 至频空域联合模型的 PSNR / SSIM / 噪声抑制率对比柱状图与五维雷达图；宣纸风格金石学术鉴定报告书（带朱砂印信）；支持导出学术 PDF 与 JSON 评测数据。 |

---

## 3. 真实系统运行截图

> 以下截图均通过自动化 Playwright 测试脚本从本机真实运行的 Web 服务（`http://127.0.0.1:8000`）中直接截取，非概念设计图：

### 3.1 首页门户与三维数字展陈
![首页门户与三维数字展陈](screenshots/01_home_portal_3d.png)

### 3.2 中华贞石数字典藏馆（七朝代 28 件真实馆藏）
![中华贞石数字典藏馆](screenshots/02_digital_museum.png)

### 3.3 频空域微痕修复与残字释读工作台
![频空域微痕修复与古籍释读工作台](screenshots/03_restoration_workbench.png)

### 3.4 GraphRAG 人物关系与 GIS 时空流传轨迹
![GraphRAG 与 GIS 时空图谱](screenshots/04_graphrag_gis.png)

### 3.5 算法消融实验与金石考据学术报告
![算法评测及考据报告](screenshots/05_ablation_reports.png)

---

## 4. 技术架构

系统采用微服务前后端解耦架构，全站代码遵循严格的类型约束与新中式玄青泥金（`#0A0D12` + `#D4AF37`）宋式美学视觉规范：

```mermaid
flowchart TD
    subgraph Frontend["前端展示层 (React 18 + TypeScript + Vite)"]
        UI["SPA 单页应用 (HashRouter)"]
        Three["Three.js 3D 碑刻仿真渲染器 (PBR材质 + 激光扫描)"]
        Work["去噪拉杆画布 + 竖排古籍卷轴"]
        Chart["ECharts 5 (力导向知识图谱 + 消融图表)"]
    end

    subgraph Backend["服务端应用层 (FastAPI + Python 3.10+)"]
        API["RESTful API 路由 (/api/steles, /api/process, /api/infer)"]
        Life["Lifespan 样本自检与数据库同步"]
    end

    subgraph Engines["核心算法与计算引擎"]
        Algo["频空域联合去噪引擎 (OpenCV + NumPy + SciPy)"]
        Agent["知识智能体与贝叶斯残字推演 (Knowledge Agent)"]
        DB["SQLite3 / JSON 统一元数据仓储 (Museum Manager)"]
    end

    UI --> API
    Three --> API
    Work --> API
    Chart --> API
    API --> Algo
    API --> Agent
    API --> DB
```

### 技术栈选型与版本依据
- **前端核心**：React 18.2, TypeScript 5.4, Vite 5.1, TailwindCSS 3.4, Lucide React 0.363
- **三维可视化**：Three.js r163（程序化多层碑首、碑身漫反射/法线凹凸贴图、定向聚光扫描着色）
- **图表与图谱**：ECharts 5.5（力导向图谱防重叠引力、双向 GIS 轨迹线）
- **数学排版**：KaTeX 0.16.10
- **后端服务**：FastAPI 0.110+, Uvicorn 0.28+, Pydantic 2.6+, Python-Multipart
- **图像与算法**：OpenCV 4.9+, NumPy 1.26+, SciPy 1.11+, Scikit-Image 0.22+, Pillow 10.2+
- **数据持久化**：SQLite 3 + JSON 规范化种子数据

---

## 5. 核心算法与数学建模

```mermaid
flowchart LR
    A["退化拓片 f(x,y)"] --> B["2D-FFT 频域变换"]
    B --> C["高斯带阻/陷波 H(u,v)"]
    C --> D["2D-IFFT 逆变换"]
    D --> E["Fast NLM 非局部均值"]
    E --> F["CLAHE 对比度限幅"]
    F --> G["形态学拓扑骨架提取"]
    G --> H["微痕高保真复原拓本"]
```

### 5.1 频域自适应陷波滤波 (2D-FFT)
拓工在手工捶拓时产生的拓布经纬网格，在二维频域呈现为轴对称的周期性高频离散亮点。系统通过 2D-FFT 将图像变换至频域：
$$F(u, v) = \sum_{x=0}^{M-1} \sum_{y=0}^{N-1} f(x, y) e^{-j 2\pi \left(\frac{ux}{M} + \frac{vy}{N}\right)}$$
构造高斯陷波抑制传递函数 $H(u,v)$，在滤除周期性条纹的同时最大程度保全字口边缘能量：
$$H(u, v) = 1.0 - \exp\left(-\frac{D^2(u, v)}{2 D_0^2}\right)$$
其中 $D_0$ 为截止频率（缺省推荐 $D_0 \in [35, 60]$）。

### 5.2 空域快速非局部均值去噪 (Fast NLM)
针对频域滤波后残留的石花椒盐噪点，利用自然图像的块自相似性进行加权平均：
$$NL[v](i) = \sum_{j \in I} w(i, j) v(j), \quad w(i, j) = \frac{1}{Z(i)} \exp\left(-\frac{\|v(N_i) - v(N_j)\|^2_{2,a}}{h^2}\right)$$
式中 $h$ 为滤波平滑强度衰减参数，有效避免了传统均值或高斯模糊造成的文字笔画断裂。

### 5.3 对比度受限自适应直方图均衡化 (CLAHE)
将图像切分为 $8 \times 8$ 的上下文区域块，对直方图局部峰值进行阈值剪截（Clip Limit = 2.5），避免背景微弱噪声被过度放大，使得漫漶字口边缘对比度显著提升 3.8 倍。

### 5.4 贝叶斯候选残字推演 (Context-Glyph Fusion)
针对风化残损字口，系统综合**字形拓扑轮廓相似度**与**金石互勘文本上下文转移概率**：
$$P(c_i \mid \text{Res}, \text{Ctx}) \propto P(\text{Res} \mid c_i)^{\alpha} \cdot P(c_i \mid c_{i-1}, c_{i+1})^{1-\alpha}$$
其中先验语料来源于传世宋元拓本互勘矩阵与《金石萃编》古籍知识库。

---

## 6. 本地部署与一键复现

### 6.1 环境要求
- 操作系统：Windows 10/11, macOS, 或 Linux (Ubuntu 20.04+)
- Python 环境：Python 3.10 至 3.12
- Node.js 环境（可选，已预置免编译 `dist/`）：Node.js 18+ 与 npm

### 6.2 快速克隆与安装
```powershell
# 1. 克隆代码仓库
git clone https://github.com/3331083641-prog/RubbingMind.git
cd RubbingMind

# 2. 安装 Python 核心后端依赖
pip install -r requirements.txt

# 3. 初始化 SQLite 本地数据库 (包含 28 件真实馆藏种子数据)
python scripts/init_db.py

# 4. 执行本地安全与质量检查
python scripts/security_scan.py
pytest tests/ -v
```

### 6.3 一键启动服务
```powershell
# 方式 A: 直接运行 Python 入口
python main.py

# 方式 B: Windows 用户双击执行
.\start.bat
# 或在 PowerShell 中执行
.\start.ps1
```
服务启动后，打开浏览器访问：
- **系统门户入口**：[http://127.0.0.1:8000](http://127.0.0.1:8000)
- **数字典藏馆**：[http://127.0.0.1:8000/#/museum](http://127.0.0.1:8000/#/museum)
- **微痕修复工作台**：[http://127.0.0.1:8000/#/workbench](http://127.0.0.1:8000/#/workbench)
- **Swagger API 文档**：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 7. 快速体验与离线自包含说明

- **无需大模型即可体验全量功能**：系统内置了纯 CPU/GPU 可计算的 OpenCV 频空域去噪管线与基于金石字典的贝叶斯推演引擎。用户无需配置商业 API Key 或下载十余 GB 的本地大模型权重，克隆后立即可进行去噪对比、图谱浏览与消融实验。
- **大模型增强（可选）**：若需开启在线多模态残字智能体推演，可复制 `.env.example` 为 `.env`，填入兼容 OpenAI 规范的 API Key（如阿里云百炼通义千问 `qwen-vl-max`）。系统会自动切换至大模型多轮考据模式。

---

## 8. 数据来源与版权声明

本系统秉持文博数字人文的学术真实性原则，严禁使用 AI 幻觉图像冒充传世文物：
1. **公开高清馆藏母本（23件）**：
   - 来源于台北故宫博物院、维基媒体共享资源（Wikimedia Commons）开放馆藏数字化特藏，遵循 **CC BY 4.0** 授权协议；
   - 涵盖东汉《曹全碑》《乙瑛碑》《礼器碑》，唐代《多宝塔碑》《颜氏家庙碑》《九成宫醴泉铭》等传世名碑，每通碑拓均完整保留藏所馆藏号与官方溯源链接。
2. **馆藏著录记录（5件）**：
   - 包括元代中国国家图书馆藏《香山九老会诗碑》、清代台湾大学图书馆藏《施琅功德碑》《高成墓志》《严禁碑》《功臣墓碑》；
   - 本系统仅收录其学术元数据、著录编号与立石经纬度，原图状态明确标识为“原图待授权或待获取”，点击卡片可查看馆藏调阅指引。

---

## 9. 项目限制与免责声明

1. **去噪评价指标说明**：界面中呈现的 PSNR（+18.6 dB）与 SSIM（0.9482）指标基于合成加噪对比样本测定。在完全无无损 Ground Truth 的极度风化古代原石残片上，量化指标仅作为算法相对迭代增益参考，学术定论应以金石学家双盲互勘为准。
2. **三维模型精度**：当前 Three.js 碑刻模型采用几何参数化建模结合法线纹理映射技术（PBR），在保证网页 60 FPS 丝滑交互的同时兼顾视觉真实感，但尚未达到毫米级激光三维点云拓扑逆向工程精度。
3. **商业用途限制**：本项目作为“全球校园人工智能算法精英大赛”科研参赛作品，遵循非商用学术探索与文化传承用途。

---

**墨韵智考研制团队 · 2026**
