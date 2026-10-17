# -*- coding: utf-8 -*-
"""
墨韵智考 - FastAPI 主服务入口
全栈数字人文金石碑拓微痕修复与史料考据系统
"""

import os
import sys
import logging
import io
import threading
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any, Literal

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image, UnidentifiedImageError

from sample_generator import ensure_samples, SAMPLES_DIR, BASE_DIR
from algorithm_engine import algorithm_engine, safe_read_image, mat_to_base64
from knowledge_agent import knowledge_agent, AUTHENTIC_RUBBING_DATABASE
from museum_manager import museum_manager
from catalog import inference as catalog_inference, report as catalog_report, graph as catalog_graph
from museum_processing import process_verified_request, list_runs, read_run, delete_run
from upload_storage import create_upload, get_upload, image_path
from glyph_inference import infer as infer_crop, list_inferences, get_inference, decide as decide_glyph, crop_path

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("RubbingMindApp")

# Web 生产构建输出目录
DIST_DIR = os.path.join(BASE_DIR, "apps", "web", "dist")
DIST_ASSETS_DIR = os.path.join(DIST_DIR, "assets")
STATIC_DIR = os.path.join(BASE_DIR, "static")

STELE_MAP = {
    "tang-duobao": "sample_1.png",
    "han-caoquan": "sample_2.png",
    "wei-yuanhuai": "sample_3.png",
    "wei-jianyi": "sample_4.png",
}

STELE_REVERSE_MAP = {v: k for k, v in STELE_MAP.items()}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """服务启动时生命周期事件：确保 4 张核心碑拓样本就绪"""
    logger.info("=== 正在启动【墨韵智考】系统 ===")
    try:
        samples_status = ensure_samples()
        logger.info(f"碑刻拓片样本库检查完毕，可用样本数: {len(samples_status)}")
    except Exception as e:
        logger.error(f"样本库初始化异常: {e}")
    yield
    logger.info("=== 【墨韵智考】服务正常终止 ===")


app = FastAPI(
    title="墨韵智考——金石碑拓微痕修复及史料考据系统",
    description="全球校园人工智能算法精英大赛（智能文化赛道）全栈 Web 科研演示平台",
    version="2.0.0",
    lifespan=lifespan,
)

# Development clients use the same-origin proxy; limit direct CORS to local Vite.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(127\.0\.0\.1|localhost):517[0-9]$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)

# 挂载静态资源目录
from runtime_guard import RuntimeGuard
app.add_middleware(RuntimeGuard)
PROCESS_LOCK=threading.Lock()
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.mount("/assets", StaticFiles(directory=DIST_ASSETS_DIR if os.path.exists(DIST_ASSETS_DIR) else os.path.join(BASE_DIR,"apps","web","public","assets")), name="assets")


# Pydantic 请求数据模型
class ProcessRequest(BaseModel):
    stele_id: Optional[str] = "tang-duobao"
    sample_id: Optional[str] = None
    image_base64: Optional[str] = Field(default=None,max_length=17_000_000)
    d0: float = Field(default=45.0, ge=1, le=500)
    filter_order: int = Field(default=2, ge=1, le=8)
    filter_type: Literal['adaptive', 'gaussian', 'butterworth', 'notch'] = 'adaptive'
    h_nlm: float = Field(default=10.0, ge=0, le=50)
    clahe_clip: float = Field(default=2.5, ge=0.1, le=10)
    morph_kernel: int = Field(default=3, ge=1, le=9)
    damage_mask: Optional[str] = Field(default=None,max_length=17_000_000)
    cinnabar_style: Optional[str] = "cinnabar"
    random_seed: int = Field(default=0, ge=0, le=4294967295)


class DeduceRequest(BaseModel):
    image_crop_b64: Optional[str] = ""
    context_text: str = ""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None


class GlyphBox(BaseModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    w: int = Field(ge=16, le=1024)
    h: int = Field(ge=16, le=1024)


class GlyphInferenceRequest(BaseModel):
    bbox: GlyphBox
    context: str = Field(default='', max_length=1000)
    characterId: Optional[str] = Field(default=None, max_length=80)
    originalGlyph: Optional[str] = Field(default=None, max_length=1)
    originalStatus: Optional[str] = Field(default=None, max_length=20)
    runId: Optional[str] = Field(default=None, max_length=40)


class GlyphDecisionRequest(BaseModel):
    action: Literal['accept', 'revoke', 'reject']
    glyph: Optional[str] = None


class GlyphTemplateRequest(BaseModel):
    glyph: str = Field(min_length=1,max_length=1)
    basis: str = Field(min_length=1,max_length=500)
    annotator: str = Field(min_length=1,max_length=80)


class CalendarRequest(BaseModel):
    query: str


class EvidenceQueryRequest(BaseModel):
    question: str = Field(min_length=2,max_length=500)
    steleId: Optional[str] = Field(default=None,max_length=100)


@app.post('/api/research/query')
def query_evidence(request: EvidenceQueryRequest):
    from evidence_retrieval import query
    if request.steleId and not museum_manager.get_stele_by_id(request.steleId):
        raise HTTPException(status_code=404,detail='文物不存在')
    return query(request.question,request.steleId)


@app.get('/api/research/steles/{stele_id}')
def get_research_graph(stele_id: str):
    if not museum_manager.get_stele_by_id(stele_id):raise HTTPException(status_code=404,detail='文物不存在')
    from evidence_retrieval import artifact_graph
    return artifact_graph(stele_id)


@app.get('/api/experiments')
def list_experiments():
    from experiment_registry import batches
    return batches()


@app.get('/api/experiments/{experiment_id}')
def get_experiment(experiment_id: str):
    from experiment_registry import batch
    data=batch(experiment_id)
    if data is None:raise HTTPException(status_code=404,detail='实验批次不存在')
    return data


@app.get('/api/experiments/{experiment_id}/assets/{filename}')
def get_experiment_asset(experiment_id: str,filename: str):
    from experiment_registry import asset
    try:path=asset(experiment_id,filename)
    except ValueError as exc:raise HTTPException(status_code=409,detail=str(exc))
    if path is None:raise HTTPException(status_code=404,detail='未登记的实验影像')
    return FileResponse(path)


@app.get('/api/experiments/{experiment_id}/export/{kind}')
def export_experiment(experiment_id: str,kind: str):
    from experiment_registry import export_file
    path=export_file(experiment_id,kind)
    if path is None or not path.is_file():raise HTTPException(status_code=404,detail='实验导出不存在')
    return FileResponse(path,filename=experiment_id+'-'+kind)


@app.get("/")
async def root():
    """主页优先渲染 React + Three.js 现代化数字人文大屏前端"""
    dist_index = os.path.join(DIST_DIR, "index.html")
    if os.path.exists(dist_index):
        return FileResponse(dist_index)
    static_index = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(static_index):
        return FileResponse(static_index)
    return JSONResponse({"status": "running", "message": "墨韵智考系统服务已启动"})


@app.get("/health")
@app.get("/api/health")
async def health_check():
    """系统运行健康状态"""
    return {
        "status": "healthy",
        "system": "墨韵智考",
        "version": "2.0.0",
        "samples_available": [k for k in AUTHENTIC_RUBBING_DATABASE.keys()],
    }


@app.post("/generate")
async def compatibility_generate():
    return {'steleId':'tang-duobao',**catalog_graph(await get_stele("tang-duobao"))}


@app.get("/api/steles")
async def get_steles():
    """获取所有真实馆藏碑拓列表 (28件馆藏 + 本地上传样本)"""
    return museum_manager.get_all_steles()


@app.get("/api/steles/{stele_id}")
async def get_stele(stele_id: str):
    item = museum_manager.get_stele_by_id(stele_id)
    if item: return item
    if stele_id in museum_manager.retired:
        mapping = museum_manager.retired[stele_id]
        raise HTTPException(status_code=410, detail={"message":"原记录已下架，推荐查看新馆藏（不同文物）", "oldId":stele_id,"recommendedId":mapping["newId"]})
    raise HTTPException(status_code=404, detail="未找到该文物，不自动切换样本")


@app.get("/api/steles/{stele_id}/infer")
async def get_stele_inference(stele_id: str):
    return catalog_inference(await get_stele(stele_id))


@app.get("/api/steles/{stele_id}/graph")
async def get_stele_graph(stele_id: str):
    verified = await get_stele(stele_id)
    if verified.get("source_kind") == "verified_review_v3":
        return catalog_graph(verified)
    from history_graph import get_history_graph
    graph = get_history_graph(stele_id, museum_manager.get_all_steles())
    if graph is None:
        raise HTTPException(status_code=404, detail="Historical record not found")
    return graph


@app.get("/generate")
async def generate_historical_graph(stele_id: str = "tang-duobao"):
    """Graph-only compatibility entry for /health -> /generate validation."""
    return await get_stele_graph(stele_id)



@app.get("/api/steles/{stele_id}/report")
async def get_stele_report(stele_id: str, run_id: Optional[str] = None):
    record=await get_stele(stele_id)
    result=catalog_report(record)
    runs=list_runs(stele_id)
    selected=read_run(stele_id,run_id) if run_id else (runs[0] if runs else None)
    if run_id and not selected:
        raise HTTPException(status_code=404,detail='处理记录不存在')
    result['run']=selected
    result['inferenceRecords']=[item for item in list_inferences(stele_id) if not selected or item.get('runId')==selected['runId']]
    result['sourceRecords']=[{'title':record['title'],'url':record.get('sourceUrl'),'license':record.get('license')}]
    result['evaluation_summary']='实际处理已执行，但没有配对真值；配对质量未评测。' if selected else '尚未执行处理；配对质量未评测。'
    result['reportId']=f"RM-{stele_id}-{selected['runId']}" if selected else None
    return result


@app.get('/api/steles/{stele_id}/runs')
async def get_processing_runs(stele_id: str):
    await get_stele(stele_id)
    return list_runs(stele_id)


@app.delete('/api/steles/{stele_id}/runs/{run_id}')
async def remove_processing_run(stele_id: str, run_id: str, confirm: bool = False):
    await get_stele(stele_id)
    if not confirm:
        raise HTTPException(status_code=400,detail='删除单次处理记录需要明确确认')
    if not delete_run(stele_id,run_id):
        raise HTTPException(status_code=404,detail='处理记录不存在')
    return {'deleted':run_id,'steleId':stele_id}


@app.post("/api/process")
def process_rubbing(req: ProcessRequest):
    if not PROCESS_LOCK.acquire(blocking=False):raise HTTPException(status_code=429,detail='已有图像任务运行，请稍后重试')
    try:return process_verified_request(req, museum_manager, algorithm_engine)
    except (ValueError,TypeError) as exc:raise HTTPException(status_code=422,detail=str(exc))
    finally:PROCESS_LOCK.release()


@app.post("/api/upload")
async def upload_custom_image(
    file: UploadFile = File(...),
    title: str = Form("用户上传碑拓"),
    dynasty: str = Form("未考证"),
    author: str = Form(""),
    script_type: str = Form("楷书"),
    weathering_level: str = Form("重度风化"),
):
    """Validate and persist a user-owned image without inventing a restoration result."""
    max_bytes = 12 * 1024 * 1024
    mime_to_format = {'image/png': 'png', 'image/jpeg': 'jpeg', 'image/webp': 'webp'}
    if file.content_type not in mime_to_format:
        raise HTTPException(status_code=415, detail='仅支持 PNG、JPG 或 WEBP 图像')
    try:
        content = await file.read(max_bytes + 1)
        if len(content) > max_bytes:
            raise HTTPException(status_code=413, detail='文件超过 12 MiB 限制')
        if not content:
            raise HTTPException(status_code=400, detail='文件为空')
        with Image.open(io.BytesIO(content)) as image:
            actual_format = image.format.lower()
            width, height = image.size
            if actual_format != mime_to_format[file.content_type]:
                raise HTTPException(status_code=415, detail='文件内容与 MIME 类型不一致')
            if min(width, height) < 32 or max(width, height) > 5000 or width * height > 12_000_000:
                raise HTTPException(status_code=413, detail='图像尺寸超出 32–5000 像素或 1200 万像素限制')
            image.verify()
        if not title.strip() or len(title.strip()) > 120:
            raise HTTPException(status_code=422, detail='名称长度需为 1–120 个字符')
        new_stele = create_upload(content, actual_format, width, height, {
            'title': title.strip(), 'dynasty': dynasty[:40], 'author': author[:120],
            'script_type': script_type[:40], 'weathering_level': weathering_level[:40]
        })
        return {'success': True, 'stele': new_stele}
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(status_code=400, detail='图像损坏或无法解码')
    except HTTPException:
        raise
    except Exception:
        logger.exception('用户图像保存失败')
        raise HTTPException(status_code=500, detail='服务端保存失败，未创建上传记录')
    finally:
        await file.close()


@app.get('/api/uploads/{upload_id}/image')
async def get_uploaded_image(upload_id: str):
    record = get_upload(upload_id)
    path = image_path(upload_id) if record else None
    if path is None or not path.is_file():
        raise HTTPException(status_code=404, detail='上传图像不存在')
    return FileResponse(path, media_type={'png': 'image/png', 'jpeg': 'image/jpeg', 'webp': 'image/webp'}[record['uploadFormat']])


@app.post('/api/steles/{stele_id}/inferences')
async def create_glyph_inference(stele_id: str, request: GlyphInferenceRequest):
    record = await get_stele(stele_id)
    if request.runId and not read_run(stele_id, request.runId):
        raise HTTPException(status_code=404, detail='关联的处理运行不存在')
    try:
        return await infer_crop(record, request.bbox.model_dump(), request.context, request.characterId, request.originalGlyph, request.originalStatus, request.runId)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get('/api/steles/{stele_id}/inferences')
async def get_glyph_inferences(stele_id: str):
    await get_stele(stele_id)
    return list_inferences(stele_id)


@app.get('/api/inferences/{inference_id}/crop')
async def get_glyph_crop(inference_id: str):
    path = crop_path(inference_id)
    if path is None or not path.is_file():
        raise HTTPException(status_code=404, detail='选区图像不存在')
    return FileResponse(path, media_type='image/png')


@app.post('/api/inferences/{inference_id}/decision')
async def decide_glyph_inference(inference_id: str, request: GlyphDecisionRequest):
    try:
        return decide_glyph(inference_id, request.action, request.glyph)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get('/api/inferences/{inference_id}/analysis/{role}')
async def get_glyph_analysis(inference_id: str,role: str):
    from glyph_inference import analysis_path
    path=analysis_path(inference_id,role)
    if path is None:raise HTTPException(status_code=404,detail='分析图不存在')
    return FileResponse(path,media_type='image/png')


@app.post('/api/inferences/{inference_id}/template')
async def save_glyph_template(inference_id: str,request: GlyphTemplateRequest):
    from glyph_inference import register_template
    try:return register_template(inference_id,request.glyph,request.basis,request.annotator)
    except LookupError as exc:raise HTTPException(status_code=404,detail=str(exc))
    except ValueError as exc:raise HTTPException(status_code=422,detail=str(exc))


@app.post("/api/calendar")
async def convert_calendar(req: CalendarRequest):
    """古代干支历法与西历公元年号双向换算"""
    from history_graph import convert_historical_year
    return convert_historical_year(req.query)


if __name__ == "__main__":
    import uvicorn
    # 本地 Windows 启动
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False, workers=1)
