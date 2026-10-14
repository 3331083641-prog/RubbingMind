# 墨韵智考：四碑史料、地望与素材身份审计

核验日期：2026-10-14。范围仅为时空图谱中心，不更改28件馆藏目录与修复算法。

## 文物身份与事件

| 核心入口 | 独立记录 | 史料核验与限制 |
|---|---|---|
| tang-duobao | 多宝塔感应碑；馆藏对应 tang_01_duobao | [西安碑林条目](https://www.beilin-museum.com/index.php?a=index&aid=147&c=View&m=home)确认752年立碑、岑勋撰、颜真卿书、徐浩题额、楚金相关建塔活动、1103年移藏碑林。千福寺在唐长安安定坊，馆方给出现代西站西南区域，未提供考古GPS。 |
| han-caoquan | 郃阳令曹全碑；馆藏对应 han_01_caoquan | [西安碑林条目](https://www.beilin-museum.com/index.php?a=index&aid=145&c=View&m=home)确认185年立、明万历间莘里村出土、1956年移碑林。[台北故宫完整释文](https://digitalarchive.npm.gov.tw/Collection/Detail/34589?dep=P)支持景完、敦煌效谷、疏勒及酒泉禄福任职。169年记录举孝廉与任职，不强定征讨年份；184年酒泉任职来自光和七年。1573是万历区间起点，不是确定出土年份。 |
| wei-yuanhuai | 广平王元怀墓志；已有核心图像样本 | [刘军《魏书·广平王元怀传》补疑](https://ygx.sxu.edu.cn/db/%E6%9C%9F%E5%88%8A/gdwm/gdwm2013/1304pdf/1304009.pdf)引用墓志，支持497年册封、517年薨卒及元宏、元恪、高照容亲属关系。论文指出墓志第四子与史书第五子表述分歧。具体出土地、墓址、原石馆藏和本地图像真拓身份未建立完整来源链。 |
| wei-jianyi | 北魏碑拓数字化退化测试样本 | `sample_generator.py`的sample_4合成文字是昌黎夫人；`knowledge_agent.py`又有韩夫人；现代馆藏wei_04_wangsong则对应赠拓000382。缺少证明核心图像与王诵拓本同一性的材料，不能混合。528只是测试标签，不确认其真实文物纪年。没有已核验人物、地点或迁移路线。 |

## 原石与数字拓本

多宝塔、曹全原石保存于西安碑林。当前图谱缩略图分别使用赠拓000365册页和购拓000033轴的项目既有真实图像，署名“国立故宫博物院，台北，CC BY 4.0”。新增图谱资源只复制真实文字页，未更改馆藏封面或生成古文字。

[赠拓000365官方记录](https://digitalarchive.npm.gov.tw/Collection/Detail/33063?dep=P)定名为明拓；旧摄影标签写时代不明，界面保留这一差异。购拓000033未据资料推定具体拓制年份。

[王诵墓志官方记录](https://digitalarchive.npm.gov.tw/Collection/Detail/29482?dep=P)确实存在，但它是对照资料，不能作为核心退化图的身份认证。第四入口不冒用王诵名字、藏号、原石地点或生平。

图谱API不再将元怀入口转为吴高黎。保留吴高黎、王诵原有馆藏记录；两者在图谱接口中得到未建立专项历史网络的真实目录占位信息，不生成虚构人物或默认西安。

## 坐标与定位方法

基础数据以WGS84 `[经度,纬度]`存储。现代行政面原始坐标是CGCS2000（EPSG:4490），本项目只将其用作公里级地望索引；在此精度下采用零参数近似，在MapLibre中投影至Web Mercator（EPSG:3857）。这不是测量级基准转换，没有GCJ-02，也没有常数偏移。

| 地点ID | WGS84索引 | 精度及含义 |
|---|---|---|
| beilin | [108.948132, 34.254721] | [Gary Todd实地照片的相机地理标记](https://commons.wikimedia.org/wiki/File:Beilin_Museum_Map_(14185587169).jpg)，仅馆区近似，不是碑石展位，CC0。 |
| xian | [108.93, 34.21] | 雁塔区行政面内部代表点，表示西安区域；不是唐城中心或千福寺。 |
| heyang | [110.20, 35.20] | 合阳县行政面内部代表点，不是汉代县治或莘里村。 |
| dunhuang | [94.05, 40.61] | 敦煌市行政面内部代表点，不是古效谷县治。 |
| jiuquan | [98.75, 39.57] | 酒泉肃州区行政面内部代表点，不是古禄福县治。 |
| shule | [76.21, 39.52] | 喀什市行政面内部代表点，仅索引疏勒国关联区域，非现代疏勒县或汉代王城。 |
| luoyang | [112.43, 34.72] | 洛阳老城区行政面内部代表点，仅城市级地望，不是元怀墓葬或北魏乘轩里。 |
| qianfu / xinli / yuan-tomb / npm-taipei | null | 无可靠坐标；只显示史料文字。前三项可通过公开注明的区域代理定位，代理点不改写原地点坐标。 |

行政点来自已保存的天地图镜像行政面，不是语言模型估计。代表点计算为面内点，取两位小数。未获得测量误差数据，`accuracyKm`保持null，不虚构米级精度。`coordinate-regions.geojson`保留对应行政面，验证脚本检查点位在县区及省域内。

## 地图来源、版图与许可限制

国界、省界、台湾、海南、香港、澳门及南海诸岛与界线统一取自[geodeparse保存的天地图数据](https://github.com/MisterChangRay/geodeparse/tree/dfb4ce2c1f7f48a5da5ad7842cbfbe1b2cd29757/geo)。原始文件未改动，包含34省级面、8界线要素，共42要素，CGCS2000；SHA-256写入资源provenance.json。全国主视图包含东北、西北、西南及沿海岛屿，南海附图使用同一源的实际坐标范围，不用艺术轮廓或移位岛屿替代。

镜像README声称上游审图号为GS(2024)0650，镜像仓库是MIT许可。**该声明不是本应用审图证明，也不能替代上游平台授权条款核对。** 本次从自然资源部标准地图及天地图官方入口下载时遇到连接关闭/SSL失败，不能声称已完成官方原件比对及本应用公开地图合规审批。界面明确显示“上游声明”“应用未单独审图”，适合作为有来源的本地验证实现；正式公开地图的许可与审图验收仍需完成。

水系仅使用[Natural Earth](https://www.naturalearthdata.com/about/terms-of-use/)公有领域50m级黄河/长江真实中心线，适合全国概览，不用于河道测绘。地形阴影来自[Mapzen Terrain Tiles / AWS开放数据](https://registry.opendata.aws/terrain-tiles/)，原始Terrarium编码0–3级瓦片，附完整[数据署名](../apps/web/public/assets/gis/terrain/ATTRIBUTION.md)，包括USGS、NOAA等提供者。低分辨率地形只是阴影，局部放大不增添虚构细节。关闭光晕/地形后边界、地点仍来自真实投影。

时间轴山水、亭塔背景是AI生成概念装饰，提示词与资源来源写入素材provenance文件；不是地形数据或历史建筑复原，未用作GIS底图。

## 路线与纪年边界

`routes`为空：没有可靠史料证明具体连续行进道路。地图可开启泥金起讫关联虚线及青绿人物关联点线；它们明确标注为关联，不是迁移线路。敦煌、酒泉、疏勒绝非曹全碑原石迁移地。

纪年支持公元1–9999年与天宝、中平、熙平、建义的有效年次，输出年度干支。752壬辰、185乙丑、517丁酉、528戊申；未知年号、越界年次、含具体月日输入返回“暂不支持或待考证”，不退回乾元元年，不虚构朔闰或公历日。

## 复验

```powershell
cd D:\RubbingMind
python -m pytest tests/ -q
python scripts/validate_history_gis.py
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/generate
cd apps/web
npm run dev -- --host 127.0.0.1
# 在另外一个终端运行
cd D:\RubbingMind
python scripts/test_graph_browser.py
```

浏览器脚本使用Microsoft Edge + Playwright真实页面，检查1920×1080、1440×900、1366×768四碑，保存指定9张截图及12张四碑分辨率截图。API/地理测试属于CI常规pytest范围；浏览器脚本另需安装Playwright及Edge，不隐含已部署网站。
