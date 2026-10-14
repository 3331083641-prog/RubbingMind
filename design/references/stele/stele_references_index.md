# 墨韵智考 - 六视图高精度三维石碑参考图规范索引

本规范索引记录了系统高精度三维数字碑刻建模所依据的 6 张官方六面正交基准参考图集合。

所有参考图统一存放于：[`design/references/stele-v2/`](file:///D:/RubbingMind/design/references/stele-v2/)

## 官方六视图参考图清单（共 6 张）

| 视角编号 | 文件名 | 视角 | 图像规格 | 特征要素说明 |
| :--- | :--- | :---: | :---: | :--- |
| **01** | [`stele_front.png`](file:///D:/RubbingMind/design/references/stele-v2/stele_front.png) | **正视图** (Front) | 768 × 1024 | 双龙圆拱浮雕碑首、回纹外框、正体阴刻楷书碑文（10列）、仰覆莲瓣须弥座 |
| **02** | [`stele_back.png`](file:///D:/RubbingMind/design/references/stele-v2/stele_back.png) | **背视图** (Back) | 768 × 1024 | 双龙碑首背面浮雕、青石天然风化断裂斜纹、实心整石打磨质感、无文字平整石体 |
| **03** | [`stele_left.png`](file:///D:/RubbingMind/design/references/stele-v2/stele_left.png) | **左侧视图** (Left) | 768 × 1024 | 碑侧实石厚度（0.34m规制）、侧边断裂痕迹、须弥座凹凸收分阶梯线脚 |
| **04** | [`stele_right.png`](file:///D:/RubbingMind/design/references/stele-v2/stele_right.png) | **右侧视图** (Right) | 768 × 1024 | 碑身右侧厚度切面、风化凹坑、基座层次与榫卯定位关系 |
| **05** | [`stele_top.png`](file:///D:/RubbingMind/design/references/stele-v2/stele_top.png) | **俯视图** (Top) | 1024 × 1024 | 拱形碑首顶弧抛物面曲率、碑身纵深比例、须弥座顶面承托台边缘 |
| **06** | [`stele_bottom.png`](file:///D:/RubbingMind/design/references/stele-v2/stele_bottom.png) | **仰视图** (Bottom) | 1024 × 1024 | 夯土承重基台底面、矩形底板实石轮廓、底座四角稳固承载面 |

## 建模执行依据

- 建模规范技术文档：[`docs/stele-v2-modeling-spec.md`](file:///D:/RubbingMind/docs/stele-v2-modeling-spec.md)
- Blender 程序化建模脚本：[`scripts/build_stele_blender.py`](file:///D:/RubbingMind/scripts/build_stele_blender.py)
- PBR 材质生成脚本：[`scripts/generate_pbr_textures_v2.py`](file:///D:/RubbingMind/scripts/generate_pbr_textures_v2.py)
- 渲染与测试脚本：[`scripts/render_six_views_blender.py`](file:///D:/RubbingMind/scripts/render_six_views_blender.py) 与 [`scripts/test_stele_interactive_v2.py`](file:///D:/RubbingMind/scripts/test_stele_interactive_v2.py)
