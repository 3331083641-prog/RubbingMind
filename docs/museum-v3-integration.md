# 墨韵智考真实馆藏正式入库 v3

唯一权威数据为 `data/catalog/steles28.json`。`catalog.py`派生兼容字段；`scripts/migrate_museum_v3.py`导出React离线清单、JSON数据库、旧导入入口及图片状态，并按ID更新SQLite。后端启动只读，不再覆写数据库或备份。七朝代各4件；用户上传与核心演示样本不占这28件名额。

运行迁移前自动备份JSON及SQLite至 `data/runtime/museum-v3/backups/时间戳/`。重复执行只更新相同ID，保留额外用户记录和实验表。旧5件JSON独立归档；SQLite旧行不删除，以保留历史外键，并在`museum_catalog_status`标记下架。旧详情接口返回410及不同文物推荐ID，不伪装成另一件文物。

```powershell
python scripts/migrate_museum_v3.py
python scripts/validate_museum_v3.py
python -m pytest tests/ -q
python -m uvicorn main:app --host 127.0.0.1 --port 8000
# /health -> POST /generate -> 前端 -> 实际浏览器
cd apps/web
npm ci
npm run dev
```

可用`RUBBINGMIND_API_TARGET`调整Vite开发代理。生产部署先运行`npm run build`，FastAPI提供构建产物。

## 图片与身份

三种JPEG分别用于封面、阅读与审核档案画面；全部原样复制审核包，指纹查询参数防止缓存旧图。每张封面1100×1420，卡片`object-contain`不再二次裁断；按需打开阅读图及档案图。扫描原有残缺与第三轮选区保持不变。档案图是审核所选页，册页藏品不应称为全册PDF。

`data/catalog/image_sources.json`列出全部84张图像路径、校验和、逐件许可和署名。`processing/`记录源文件SHA、页码、裁切与增强参数；`evidence/`记录官方著录原文/API。原始ZIP/PDF只留本地，不纳入仓库。来源说明见`docs/museum-image-sources.md`。

`qing_02_chongli_wushi`是审核包同一文物ID的兼容别名，正式采用`qing_02_wushi_reerection`。五件旧文物与替换文物是不同历史身份。`core_sample_links.json`仅为多宝塔、曹全碑建立同作品关联，不认定为同一拓本；元怀和建义核心样本保留演示身份，不映射吴高黎或王诵。

未核定的原石地点、现藏机构、年份和作者保持空值或“未核定”。宋文宣王赞碑题名与释文纪年冲突、孙德彧碑原书与刊刻时间差异及陆献之册页性质均保留说明。重立武氏祠石记以馆方1787年新刻著录归清代；三希堂仅采用清代御序刻石，1747是撰序年。

## 实验与评测

馆藏图像不冒充人工退化或算法修复。修复工作台按当前ID加载阅读图，实际调用原有算法；输出、参数和SHA写入`static/results/文物ID/运行ID/`。无配对真值时，PSNR/SSIM/准确率显示未评测。引擎输入与输出比较留作诊断，不作为恢复准确率。后端不可用时明确失败，不返回模拟图片或指标。

未完成残字检测时仅展示馆方释文，不补齐35格、编造候选或固定置信度。未完成消融实验时报告图为空并注明未评测，JSON/PDF保留当前文物身份。新馆藏无核验地理轨迹时展示资料关联与支持范围；原四核心图谱入口保留。

四核心样本保留旧有预置残字推演案例，界面明确标注“演示，非本轮实测”；这些候选及概率不套用到28件真实馆藏，也不写入馆藏考据报告。

## 验收

`scripts/test_museum_v3_browser.py`用真实Edge/Playwright分别测试在线和阻断API的Fallback：28件卡片信息/图片、8种分类、搜索/风化组合、五件新馆藏及跨朝代详情、缩放/平移、图片失败/重试、28件工作台ID、4核心入口、图谱身份、JSON和打印PDF、1920×1080与1440×900。

```powershell
python scripts/test_museum_v3_browser.py --url http://127.0.0.1:5173
```

截图和实际验收记录位于`screenshots/museum-v3/`。不修改算法本体、Three.js模型、首页背景或地图视觉设计。
