# 墨韵智考：石碑三维最终精修与验收

验收日期：2026-10-14。工程位于 `D:\RubbingMind`。模型为用户六张生成图引导的概念展陈石碑，不是考古测绘成果；图片中的字符明确称为概念铭文。提交和 GitHub Actions 的最终定位见交付消息。

## 原工程问题及修复

| 原问题 | 实际修复 |
| --- | --- |
| 首页使用 SteleViewer，但 HeroSteleScene 仍维护独立的旧模型 | HeroSteleScene 改为兼容入口，普通、全屏、典藏馆均加载同一 GLB |
| 碑首仅有半圆挤出；原生挤出 UV 未针对弧面与正背面展开 | 重建前后浮雕皮层和连续弧壁，形成焊接闭合冠体；各面显式展开 |
| 双龙主要依赖整幅图片和过强法线 | 手工登记龙头、角、爪、盘曲龙身的体量，结合受限深度场生成真实雕刻网格；细纹另用法线补充 |
| 宝珠为独立半球，无颜色贴图，朝向与嵌入关系不可靠 | 宝珠作为冠体皮层内的约 52mm 石雕圆顶，与同一闭合网格相连 |
| 莲瓣是旋转半圆柱，缺颜色图，形成白片 | 莲瓣直接雕刻在闭合承托层表面，四面均使用完整石材 PBR |
| 底台把整张底座图分别映射到各块，侧纹重复拉伸 | 承重台四面、左右莲瓣、左右卷草、顶面和拱壁分别登记；平面石纹按物理宽高生成 |
| 背面使用重复拼接石图，缺少完整内凹边框视觉 | 使用本次背面参考登记和真实内凹边界，独立背面 UV |
| 铭文为额外平面，Shader 不使用所声明的正常石材法线 | 字面位于闭合碑身皮层，PBR 材质保留场景灯光、法线、粗糙度和 AO，扫描/修复作为局部扩展 |
| 半径、相机位置写死，无仰视；地面和双面光环挡住底面 | 根据 GLB 包围盒、画布宽高和操作栏占用计算观察距离；补充仰视；移除遮底地面/光环 |
| 正背面线性相机动画可能经过碑体，固定帧插值影响低帧率到位 | 绕观察中心转动，保留安全距离；使用时间步长计算动画并等待真正到位 |
| 热点仅检测热点本身，可能从背面拾取 | 对实际石体和热点一起做遮挡拾取，热点坐标统一为碑文字面的局部坐标 |
| 旧验收脚本发出点击后直接标记通过 | 比較相机坐标、Shader 状态、渲染像素、弹窗反馈和资源释放；失败立即报错 |
| 原清理仅释放材质与贴图 | 去重释放几何、材质、贴图、ImageBitmap、阴影缓冲和 WebGL context，并处理异步卸载竞态 |

原 BoxGeometry 的六面材质数组索引次序本身正确；没有将“错误 Mesh 索引”作为未经证实的根因。新 GLB 的所有三角索引另外完成二进制检查。

## 工程与建模

Blender 实测版本 **5.1.2**，可执行文件位于 `D:\Codex\blender-5.1.2\blender-5.1.2-windows-x64\blender.exe`。采用 Blender Python 建模、UV 登记、真实 Cycles AO 烘焙和 GLB 导出，再接入现有 React/Three.js。

本地可编辑工程：`D:\RubbingMind\design\blender\stele-final\stele-final.blend`。GitHub 可编辑源文件包：[stele-final-source.zip](../design/blender/stele-final/stele-final-source.zip)（含原始 Blend 与雕刻深度场，解压即可打开）。最终资源：[stele-final.glb](../apps/web/public/assets/stele/model3d/final/stele-final.glb)。关键文件原始备份保存在 `D:\Codex\backups\RubbingMind-stele-final-20261014`，不进入 Git 提交。

建模脚本读取既有 `steleDimensions.ts` 的尺寸。总高 3.30m、碑宽 1.28m、厚 0.24m、基底 1.85×0.72m、台座高 0.55m。碑身 2.15m 包含 0.04m 插入段，露出部分高约 2.11m；圆拱高 0.64m，和碑宽构成自洽半圆。前后各有约 52mm 最大宝珠起伏，龙身细部深度被限制在数厘米以内，避免从参考光影生成尖峰。

模型包含七个闭合石材体积：碑身、双龙冠体、承重台、卷草腰台、腰台檐口、莲瓣承托和嵌槽压顶。成品合并为 **一个材质、一个 GLB primitive**，七个石体岛保留可编辑性。双龙、宝珠、莲瓣、卷草不是独立悬浮图板。碑身有真实边缘小缺损；底面有闭合的浅凹中心。移除平顶/底无用密集网格后，面数从首轮 517,760 降至 **319,024 个三角面**，关键浮雕采样密度保留。

## PBR 与逐面验收

| 资源 | 尺寸 | 处理 |
| --- | --- | --- |
| Base Color | 3072×4096 | JPEG；sRGB；图集留白边缘防止 Mipmap 串色 |
| Normal | 1536×2048 | PNG；线性数据；概念字迹采用凹刻方向 |
| Roughness / Metallic | 1536×2048 | 线性数据；高粗糙度，Metallic=0 |
| AO | 2048×2048 | 实际 Cycles 12-sample 几何烘焙，独立无重叠 UV1 |

四张运行贴图全部嵌入 GLB；网页无需额外外链图像。原始图集及编辑用深度场也保留在专项目录。仓库原安全扫描器误将 Blend/NPZ 二进制坐标识别为手机号，因此不修改全仓库扫描逻辑：这两项编辑资源以现有扫描器支持的标准 ZIP 包提交，本地原始文件保留，包内容逐字节核对且无其他目录或环境配置。GLB 约 **24.42 MiB**，可编辑 Blend 约 21 MiB；精确字节数和 SHA256 以 [asset-validation.json](../screenshots/stele-final/asset-validation.json) 为准。

二进制验收确认：索引均在顶点范围内，所有位置/UV/法线均有限，法线单位长度正确，无零面积三角形，UV0/UV1 完整，材质不透明且启用背面剔除，BaseColor/Normal/Roughness/AO 四项完整，没有外部图像 URI。Blender 七构件各自 **0 条非流形边**，详见 [geometry-audit.json](../apps/web/public/assets/stele/model3d/final/geometry-audit.json)。

| 方向 | 检查结论 | PBR | Clay |
| --- | --- | --- | --- |
| 正面 | 双龙、嵌入宝珠、概念铭文和回纹完整；无漂浮字面 | [正面](../screenshots/stele-final/pbr/stele_front.png) | [灰模](../screenshots/stele-final/clay/stele_front.png) |
| 背面 | 无字石面、风化裂纹、内凹框和背面浮雕完整 | [背面](../screenshots/stele-final/pbr/stele_back.png) | [灰模](../screenshots/stele-final/clay/stele_back.png) |
| 左侧 | 实体厚度、左侧石纹、六瓣侧承托和卷草完整 | [左侧](../screenshots/stele-final/pbr/stele_left.png) | [灰模](../screenshots/stele-final/clay/stele_left.png) |
| 右侧 | 独立右侧石纹及四面连续台座，无白片/空白 | [右侧](../screenshots/stele-final/pbr/stele_right.png) | [灰模](../screenshots/stele-final/clay/stele_right.png) |
| 俯视 | 连续圆拱厚度、顶面石材、底座平面完整 | [俯视](../screenshots/stele-final/pbr/stele_top.png) | [灰模](../screenshots/stele-final/clay/stele_top.png) |
| 仰视 | 下表面闭合，有浅凹石框；没有地面挡住模型 | [仰视](../screenshots/stele-final/pbr/stele_bottom.png) | [灰模](../screenshots/stele-final/clay/stele_bottom.png) |
| 45°透视 | 碑首、碑身、须弥座连接关系可见 | [透视](../screenshots/stele-final/pbr/stele_perspective.png) | [灰模](../screenshots/stele-final/clay/stele_perspective.png) |

这些截图均取自网页的同一个 Three.js 模型，纯白摄影检查模式只临时隐藏控制层、扫描及热点。实际网页截图保留交互控件。它们不是离线 Blender 渲染替代品。逐图对照页面见 [六面参考对照](stele-final-review.html)。

参考的俯视图本身是斜俯视，因此预设采用约 72° 俯角；仰视近似垂直朝上。侧图显示的底座纵深与正面、俯视图不完全一致，统一按 0.72m 厚度处理；石材裁取保持合理纹理比例。没有为六个方向分别制作模型。

## 真实网页测试与性能

实际顺序：检查后端 `/health`（404）、实际 `/api/health`（200）；检查 `/generate`（404）、实际 `/api/process`（200，返回 PSNR）；启动现有 `npm run dev`；完成浏览器验证。没有为满足路径名称添加或修改后端业务接口。中途外部后端服务停止，重新启动原服务后重新进行完整验收。

生产构建也完成相同浏览器验收，地址为 `http://127.0.0.1:8000/?steleQA=1`。生产 `dist` 中的 GLB 与 `public` 成品逐字节一致。**62 项浏览器断言全部通过**，详见 [browser-validation.json](../screenshots/stele-final/browser-validation.json)：七视角、拖动旋转、滚轮缩放、右键平移、扫描运动/关闭、滑块驱动 Shader 和实际像素变化、热点点击反馈、背面遮挡拾取、全屏及典藏馆三维调用、四页面访问、卸载释放均核验。

三个分辨率均测试普通与全屏：1920×1080、1440×900、1366×768。模型完整留在标题栏和操作栏之间。示例：[普通窗口](../screenshots/stele-final/web_normal_1366x768.png)、[全屏窗口](../screenshots/stele-final/web_fullscreen_1920x1080.png)、[热点](../screenshots/stele-final/web_hotspot.png)。完整截图清单见 [文件清单](stele-final-files.txt)。

实测设备为 **NVIDIA GeForce RTX 4060 Laptop GPU / ANGLE D3D11**，Edge 无头浏览器，devicePixelRatio=1。普通和全屏稳定采样约 **60 FPS**；带三个双环热点时为 7 个 Draw Calls（石材本体 1 个），319,276 个可见三角面；关闭检查用热点时本体为 319,024 面。FPS 是该设备上的 requestAnimationFrame 采样，不是所有机器的性能承诺。每次卸载后记录的几何/纹理数量均回到 0。

`npm run build` 成功；仓库 Python 测试 **16/16** 通过，其中新增成品 GLB 检查将在现有 CI 中运行。现有大型 JS bundle 提示及 httpx 弃用提示仍存在，不改变前端架构或后端依赖以处理这两个非三维范围问题。生产浏览器没有 JavaScript/WebGL 错误或资源请求失败。

## 修改范围及保留项

修改的原有文件仅：`SteleModelBuilder.ts`、`SteleViewer.tsx`、`SteleFullscreenViewer.tsx`、`steleDimensions.ts`、`HeroSteleScene.tsx`、`test_and_capture_stele3d.py`、`docs/stele-model-spec.md`。新增文件仅模型、PBR 图集、Blender 源工程/脚本、六张参考、三维测试、截图和本文等技术说明，完整名单见 [文件清单](stele-final-files.txt)。

调用兼容的最小改动包括：旧 Hero 组件转发到统一 Viewer；全屏事件暂停下层画布减少重复渲染；全屏已有标题和退出按钮，因此 Viewer 不再重复叠加一份；视角栏新增仰视。**HomePage、MuseumPage、WorkbenchPage、GraphPage、ReportsPage 源码均未修改**。28 件馆藏、七朝代筛选、FastAPI 图像算法、GraphRAG、GIS、报告导出与项目名称保持原状。原有及并行出现的非三维未提交工作均保留并排除在提交外。

## 复现与界限

按顺序执行 `prepare_textures.py`、Blender `build_stele.py`、Blender `bake_ao.py`，即可重新生成图集、闭合石体、AO 与 GLB。启动后端、检查原有接口、启动前端后运行 `python test_and_capture_stele3d.py`，或 `python scripts/validate_stele_final.py --url http://127.0.0.1:8000/?steleQA=1` 验证生产服务；`python scripts/validate_stele_asset.py` 独立检查二进制资源。

没有留下已知缺面、悬浮白球、白色莲瓣、反向法线或渲染缺失。仍需明确的界限：单组生成图无法反推唯一的真实浮雕深度；龙鳞、裂纹和字口的微观深度为受限视觉重建，和参考不会逐像素一致。修复滑块保留拓片驱动的石质微痕对比度演示，没有把生成字形变成历史释读，也没有改动实际图像修复算法。
