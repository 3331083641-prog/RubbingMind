# 墨韵智考 RubbingMind

金石碑拓数字典藏、图像处理与史料辅助检索的本地 Web 项目。系统包含 React/TypeScript 前端、FastAPI 后端、OpenCV 图像处理、四件核心演示样本、28 件第三轮审核馆藏、三维展陈和历史 GIS。

## 真实馆藏与授权

第三轮审核的 28 件真实影像已经入库，东汉、北魏、唐、宋、元、明、清各 4 件。标准数据位于 [data/catalog/steles28.json](data/catalog/steles28.json)；每件的封面、阅读图、档案图分开保存，名称、原刻年代、拓本年代、馆藏机构及编号按审核记录对应。旧 5 件记录独立归档，不作为新文物身份。四件核心算法样本与 28 件馆藏使用独立 ID。查看 [馆藏影像来源与许可](docs/museum-image-sources.md) 和 [入库说明](docs/museum-v3-integration.md)。各图像许可按逐件记录标示；文物本身与数字图像授权需分别判断。

## 现有功能与实验边界

- 工作台可以对选定的真实图像执行高斯/Butterworth 频域低通、在检测到周期峰时执行自动陷波，并结合 Fast NLM、CLAHE 和形态学处理。每次处理保存独立运行 ID、参数、输入哈希、输出图和耗时。
- 上传 PNG/JPEG 后，服务端验证并保存原件、生成唯一记录；上传属于用户私有数据，不进入 28 件权威馆藏。上传失败会显示错误，不生成假记录。
- 残字推演要求用户框选实际图像区域并提供上下文。可选的视觉模型由用户自行配置；未配置或不可用时，规则建议会明确标示为非图像实测、非校准概率。采纳和撤销操作保留记录。
- 报告按当前文物及所选运行 ID 展示实际处理、出处和推演状态，支持 JSON 与浏览器打印 PDF。没有运行时显示“尚未执行”；没有配对真值时 PSNR、SSIM 为“未评测”。
- 图谱和 GIS 展示已整理的史料关联和地点，不能替代人工金石学考证。地图公开使用与审图事项见 [历史图谱审计](docs/graph-history-audit.md)，尚未宣称取得正式审图许可。

受控退化实验位于 [experiments/](experiments/)。使用经许可的真实拓本局部作为实验参考、固定随机种子，对同一输入比较八种方法，保存输出图、CSV、JSON 和汇总。参考图只代表本次构造实验的真值，不能代表历史原始笔画；目前没有有标注的字符识别率评测。实验结果并未证明联合流程对所有退化类型都优于基线。

## 安装与运行

建议 Python 3.10–3.12、Node.js 18+。在仓库根目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/init_db.py
cd apps/web
npm ci
npm run build
cd ../..
.\start.ps1
```

`start.ps1` 使用脚本所在目录，必要时重建前端，启动 FastAPI 并记录本项目 PID；`stop.ps1` 仅停止它启动的进程。也可分别运行 `python -m uvicorn main:app --host 127.0.0.1 --port 8000` 与在 `apps/web` 运行 `npm run dev`。先检查 `/health`，再检查 `/generate`，然后打开 Vite 页面或构建后的服务页面。API 文档在 `/docs`。自检运行 `.\check.ps1`。

可选视觉模型通过环境变量 `RUBBINGMIND_VISION_API_KEY`、`RUBBINGMIND_VISION_BASE_URL` 和 `RUBBINGMIND_VISION_MODEL` 配置；请勿提交密钥。调用外部模型可能产生费用。

## 验证

```powershell
python -m pytest tests -q
python scripts/validate_museum_v3.py
python experiments/run_ablation.py
cd apps/web
npm run build
```

浏览器验收步骤和实际结果见 [整改报告](docs/audit/2026-10-15-remediation-report.md)。自动化通过不等于文物学术结论已获专家认证。地图、未标注残字和无真值历史拓本仍有明确的验证边界。
