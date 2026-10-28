# -*- coding: utf-8 -*-
"""
墨韵智考 - FastAPI 主服务入口
全栈数字人文金石碑拓微痕修复与史料考据系统
"""

import os
import json
import sys
import logging
import io
import threading
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any, Literal

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image, UnidentifiedImageError

from sample_generator import ensure_samples, check_samples, SAMPLES_DIR, BASE_DIR
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
    """服务启动时生命周期事件：检查核心碑拓样本（RT-002：不下载/不合成）"""
    logger.info("=== 正在启动【墨韵智考】系统 ===")
    try:
        report = check_samples()
        if report["ok"]:
            logger.info("碑刻拓片样本库检查完毕，可用样本数: %s", len(report["present"]))
        else:
            logger.error(
                "RT-002: samples degraded missing=%s sha_mismatch=%s (no auto-fetch)",
                report["missing"],
                [m["key"] for m in report["sha_mismatch"]],
            )
    except Exception as e:
        logger.error(f"样本库初始化异常: {e}")
    yield
    logger.info("=== 【墨韵智考】服务正常终止 ===")


_REMOTE_DEPLOYMENT = os.getenv('RUBBINGMIND_DEPLOYMENT', 'local') != 'local'
app = FastAPI(
    title="墨韵智考——金石碑拓微痕修复及史料考据系统",
    description="金石碑拓微痕修复与史料考据系统全栈 Web 科研平台",
    version="2.0.0",
    lifespan=lifespan,
    # RT-005: hide OpenAPI surface in remote/demo exposure mode
    docs_url=None if _REMOTE_DEPLOYMENT else '/docs',
    redoc_url=None if _REMOTE_DEPLOYMENT else '/redoc',
    openapi_url=None if _REMOTE_DEPLOYMENT else '/openapi.json',
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
from runtime_guard import RuntimeGuard, SecurityHeadersMiddleware
app.add_middleware(RuntimeGuard)
app.add_middleware(SecurityHeadersMiddleware)
# R1-5: rm:rubbing:/rm:demo:/rm:retired: ids are accepted everywhere under /api/steles/
# (outermost, so the guard and every route see the legacy id).
from id_mapping import NamespacedSteleIdMiddleware, local_id, namespace_mismatch, split_namespace
from history_graph import resolve_id as resolve_history_id
app.add_middleware(NamespacedSteleIdMiddleware)
PROCESS_LOCK=threading.Lock()
os.makedirs(STATIC_DIR, exist_ok=True)
# R1-7: when RUBBINGMIND_RESULTS_DIR relocates run storage, serve it under the
# unchanged URL prefix /static/results (mounted first so it wins over /static).
from runtime_paths import describe as describe_runtime_paths, results_override
if results_override() is not None:
    os.makedirs(results_override(), exist_ok=True)
    app.mount("/static/results", StaticFiles(directory=str(results_override())), name="static-results")


@app.get('/static/index.html', include_in_schema=False)
async def legacy_frontend_bookmark():
    """Retain old bookmarks without exposing the obsolete API-key entry page."""
    return RedirectResponse('/', status_code=308)


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
if describe_runtime_paths()['overridden']:
    logger.warning('RubbingMind 数据路径已重定向: %s', describe_runtime_paths())

app.mount("/assets", StaticFiles(directory=DIST_ASSETS_DIR if os.path.exists(DIST_ASSETS_DIR) else os.path.join(BASE_DIR,"apps","web","public","assets")), name="assets")


# Pydantic 请求数据模型
class ProcessRequest(BaseModel):
    # RT-014: no silent default artifact. Callers must name stele_id (or a built-in sample_id);
    # a missing id is a 422, never a run filed under tang-duobao.
    stele_id: Optional[str] = None
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
    imageSource: Literal['original', 'restored'] = 'original'
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



def _lookup_stele_id(stele_id: str) -> str:
    """Map rm:demo:/rm:rubbing:/rm:retired: to legacy id for museum_manager lookup.

    Rejects rm:work: and wrong-kind namespaces (same rules as NamespacedSteleIdMiddleware).
    """
    if not stele_id:
        return stele_id
    if stele_id.startswith('rm:'):
        err = namespace_mismatch(stele_id)
        if err:
            raise HTTPException(status_code=404, detail=err)
        prefix, kind, local = split_namespace(stele_id)
        if prefix is None:
            return stele_id
        resolved = resolve_history_id(stele_id)
        if resolved.get('evidenceId'):
            return resolved['evidenceId']
        return local_id(stele_id) or local
    return stele_id


class EvidenceQueryRequest(BaseModel):
    question: str = Field(min_length=2,max_length=500)
    steleId: Optional[str] = Field(default=None,max_length=100)
    # BR-08 / C-16: default excludes synthetic demo samples; jinshi owns include_demo in evidence_retrieval.
    includeDemo: bool = False


@app.post('/api/research/query')
def query_evidence(request: EvidenceQueryRequest):
    from evidence_retrieval import query
    scope_id = request.steleId
    if scope_id:
        lookup = _lookup_stele_id(scope_id)
        if not museum_manager.get_stele_by_id(lookup):
            raise HTTPException(status_code=404, detail='文物不存在')
        # Pass original id so demo_opt_in / resolve_id see rm:demo: and kind=demo_sample.
    return query(request.question, scope_id, include_demo=request.includeDemo)


@app.get('/api/research/steles/{stele_id}')
def get_research_graph(stele_id: str):
    lookup = _lookup_stele_id(stele_id)
    if not museum_manager.get_stele_by_id(lookup):
        raise HTTPException(status_code=404, detail='文物不存在')
    from evidence_retrieval import artifact_graph
    return artifact_graph(stele_id)


@app.get('/api/experiments')
def list_experiments():
    from experiment_registry import batches
    return batches()


@app.get('/api/experiments/batch-index')
def experiment_batch_index():
    # experimentId is authoritative; batch (results directory) is a readable alias, one-to-one.
    from experiment_derived import batch_index
    return batch_index()


@app.get('/api/experiments/resolve')
def resolve_experiment_batch(batch: str):
    from experiment_derived import resolve_batch
    item=resolve_batch(batch)
    if item is None:raise HTTPException(status_code=404,detail='没有这个实验批次（batch）；不会回落到其他批次')
    return item


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


@app.get('/api/experiments/{experiment_id}/diagnosis')
def experiment_diagnosis(experiment_id: str):
    # R1-4: every registered batch has a diagnosis; only unknown batches are 404.
    from restoration_diagnosis import diagnose, diagnose_batch
    if experiment_id == 'heldout-v20-v21-2026-10-18':
        return {**diagnose(), 'diagnosisVersion': 'heldout-legacy-heuristic'}
    from experiment_registry import batch
    data = batch(experiment_id)
    if data is None:
        raise HTTPException(status_code=404, detail='实验批次不存在')
    return diagnose_batch(data, experiment_id)


@app.get('/api/experiments/{experiment_id}/mechanism')
def experiment_mechanism_index(experiment_id: str):
    from experiment_derived import mechanism_index
    body=mechanism_index(experiment_id)
    if body is None:raise HTTPException(status_code=404,detail='实验批次不存在')
    return body


@app.get('/api/experiments/{experiment_id}/derived/{relative:path}')
def report_derived_file(experiment_id: str, relative: str):
    from experiment_derived import resolve_report_derived
    path, status, reason = resolve_report_derived(experiment_id, relative)
    if path is None:
        raise HTTPException(status_code=status, detail=reason)
    return FileResponse(path, media_type='image/png' if path.suffix == '.png' else 'application/json')


@app.get('/api/experiments/{experiment_id}/mechanism-assets/{asset_path:path}')
def experiment_mechanism_asset(experiment_id: str, asset_path: str):
    from experiment_derived import resolve_mechanism_png
    path, reason = resolve_mechanism_png(experiment_id, asset_path)
    if path is None:
        raise HTTPException(status_code=404 if '不存在' in (reason or '') and '越界' not in (reason or '') and '不合法' not in (reason or '') else 400,
                            detail=reason or '不可用')
    return FileResponse(path, media_type='image/png')


@app.get('/api/experiments/{experiment_id}/applied-status')
def experiment_applied_status(experiment_id: str, rows: bool = False):
    from experiment_derived import applied_status
    body=applied_status(experiment_id, include_rows=rows)
    if body is None:raise HTTPException(status_code=404,detail='实验批次不存在')
    return body


@app.get('/api/experiments/{experiment_id}/ci-by-artifact')
def experiment_ci_by_artifact(experiment_id: str, split: Optional[str] = None, method: Optional[str] = None,
                              degradation: Optional[str] = None, scope: Optional[str] = None):
    from experiment_derived import ci_by_artifact
    body=ci_by_artifact(experiment_id, {'split':split,'method':method,'degradation':degradation,'scope':scope})
    if body is None:raise HTTPException(status_code=404,detail='实验批次不存在')
    return body


@app.get('/api/experiments/{experiment_id}/export/{kind}')
def export_experiment(experiment_id: str,kind: str):
    from experiment_registry import export_payload
    payload=export_payload(experiment_id,kind)
    if payload is None:raise HTTPException(status_code=404,detail='实验导出不存在')
    body,media=payload
    return Response(content=body,media_type=media,headers={'Content-Disposition':f'attachment; filename="{experiment_id}-{kind}"'})


class ReviewBox(BaseModel):
    x: int
    y: int
    width: int
    height: int


class ConditionReviewRequest(BaseModel):
    reviewer: str = Field(min_length=1, max_length=80)
    damageTypes: List[str] = Field(min_length=1, max_length=8)
    note: str = Field(min_length=1, max_length=500)
    suggestedCondition: Optional[str] = None
    roi: Optional[ReviewBox] = None


class GlyphAnnotationRequest(BaseModel):
    steleId: str
    inferenceId: Optional[str] = None
    bbox: ReviewBox
    glyph: str
    sourceCitation: str
    annotator: str
    damageLevel: str = '未分级'
    variantNote: str = ''
    imageSha256: str


@app.get('/api/catalog/{stele_id}/assessment')
def get_catalog_assessment(stele_id: str):
    from catalog_assessment import public_record
    try:
        record=public_record(stele_id)
    except ValueError as exc:
        raise HTTPException(status_code=409,detail=str(exc))
    if record is None:raise HTTPException(status_code=404,detail='没有这件馆藏的归档评估')
    return record


@app.get('/api/catalog/{stele_id}/assessment/assets/{kind}')
def get_catalog_assessment_asset(stele_id: str, kind: str):
    from catalog_assessment import asset_path
    try:
        path=asset_path(stele_id, kind)
    except ValueError as exc:
        raise HTTPException(status_code=409,detail=str(exc))
    if path is None:raise HTTPException(status_code=404,detail='未登记的评估影像')
    return FileResponse(path)


@app.post('/api/catalog/{stele_id}/assessment/review')
def save_catalog_condition_review(stele_id: str, body: ConditionReviewRequest, request: Request):
    from catalog_assessment import review_allowed, save_review
    host = request.client.host if request.client else ''
    if not review_allowed(host, request.headers.get('x-rubbingmind-review-token'), headers=request.headers):
        raise HTTPException(status_code=403, detail='公网请求不能写入复核意见')
    try:
        roi=None if body.roi is None else {'x': body.roi.x, 'y': body.roi.y, 'width': body.roi.width, 'height': body.roi.height}
        record=save_review(stele_id, body.reviewer, body.damageTypes, body.note, body.suggestedCondition, roi)
    except ValueError as exc:
        raise HTTPException(status_code=400,detail=str(exc))
    if record is None:raise HTTPException(status_code=404,detail='没有这件馆藏的归档评估')
    return record


@app.get('/api/catalog/{stele_id}/assessment/region-crop')
def get_region_crop(stele_id: str, x: int, y: int, width: int, height: int):
    from catalog_assessment import region_crop
    try:
        payload=region_crop(stele_id, x, y, width, height)
    except ValueError as exc:
        raise HTTPException(status_code=400,detail=str(exc))
    if payload is None:raise HTTPException(status_code=404,detail='没有这件馆藏的归档评估')
    return Response(payload, media_type='image/png')


@app.get('/api/glyph-evaluation')
def glyph_evaluation_status():
    from glyph_annotations import evaluate
    measured=evaluate()
    status='not_evaluated' if measured.get('evaluationStatus')!='measured' else 'measured'
    return {'status':status,'top1':measured.get('top1'),'top3':measured.get('top3'),
        'rejectionRate':measured.get('rejectionRate'),
        'verifiedLabels':measured.get('verifiedLabels'),'recordedLabels':measured.get('recordedLabels'),
        'reason':measured.get('reason')}


@app.post('/api/glyph-annotations')
def save_glyph_annotation(body: GlyphAnnotationRequest, request: Request):
    from catalog_assessment import review_allowed
    from glyph_annotations import save_human_annotation
    host = request.client.host if request.client else ''
    if not review_allowed(host, request.headers.get('x-rubbingmind-review-token'), headers=request.headers):
        raise HTTPException(status_code=403, detail='公网请求不能写入字符标注')
    try:
        return save_human_annotation(body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/")
async def root():
    """主页优先渲染 React 前端；无 dist 时不回退到遗留 static/index.html（RT-006）。"""
    dist_index = os.path.join(DIST_DIR, "index.html")
    if os.path.exists(dist_index):
        return FileResponse(dist_index)
    return JSONResponse(
        {
            "status": "frontend_build_required",
            "message": "请先构建前端（在 apps/web 执行 npm run build）。遗留 static/index.html 不再作为回退首页。",
        },
        status_code=503,
    )


@app.get("/health")
@app.get("/api/health")
async def health_check():
    """系统运行健康状态（RT-002: expose samples_missing / sha mismatch）"""
    report = check_samples()
    status = "healthy" if report["ok"] else "degraded"
    return {
        "status": status,
        "system": "墨韵智考",
        "version": "2.0.0",
        "samples_available": sorted(report["present"].keys()),
        "samples_missing": list(report["missing"]),
        "samples_sha_mismatch": list(report["sha_mismatch"]),
        "catalog_keys": [k for k in AUTHENTIC_RUBBING_DATABASE.keys()],
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
    # Path /api/steles/rm:demo:… is rewritten by NamespacedSteleIdMiddleware; query-param
    # callers (e.g. GET /generate?stele_id=rm:demo:…) bypass that rewrite — resolve here so
    # TestClient and live uvicorn share one boundary (jinshi _resolve_stele_for_api 口径).
    lookup = _lookup_stele_id(stele_id)
    item = museum_manager.get_stele_by_id(lookup)
    if item: return item
    for key in (stele_id, lookup):
        if key in museum_manager.retired:
            mapping = museum_manager.retired[key]
            raise HTTPException(status_code=410, detail={"message":"原记录已下架，推荐查看新馆藏（不同文物）", "oldId":key,"recommendedId":mapping["newId"]})
    raise HTTPException(status_code=404, detail="未找到该文物，不自动切换样本")


@app.get("/api/steles/{stele_id}/infer")
async def get_stele_inference(stele_id: str):
    return catalog_inference(await get_stele(stele_id))


@app.get("/api/steles/{stele_id}/graph")
async def get_stele_graph(stele_id: str):
    verified = await get_stele(stele_id)
    from id_mapping import resolve as resolve_entity
    if verified.get("source_kind") == "verified_review_v3":
        # R1-5 / BR-03: collection graphs now carry their steleId and entity classification.
        return {**catalog_graph(verified), 'steleId': verified['id'], 'entity': resolve_entity(stele_id)}
    from history_graph import get_history_graph
    graph = get_history_graph(stele_id, museum_manager.get_all_steles())
    if graph is None:
        raise HTTPException(status_code=404, detail="Historical record not found")
    graph.setdefault('entity', resolve_entity(stele_id))
    return graph


@app.get('/api/id-mapping')
def get_id_mapping():
    from id_mapping import mapping_overview
    return mapping_overview()


@app.get('/api/id-mapping/{raw_id}')
def get_id_mapping_entry(raw_id: str):
    from id_mapping import namespace_mismatch, resolve
    error = namespace_mismatch(raw_id)
    if error:
        raise HTTPException(status_code=404, detail=error)
    return resolve(raw_id)


@app.get('/api/roi-geometry/normalize')
def normalize_roi_geometry(x: int, y: int, w: int = None, h: int = None, width: int = None, height: int = None, schema: str = None):
    """Phase2 R2: normalize dual ROI schemas to canonical glyph-bbox {x,y,w,h}."""
    from roi_geometry import RoiGeometryError, normalize_roi
    box = {'x': x, 'y': y}
    if w is not None:
        box['w'] = w
    if h is not None:
        box['h'] = h
    if width is not None:
        box['width'] = width
    if height is not None:
        box['height'] = height
    try:
        return normalize_roi(box, source_schema=schema)
    except RoiGeometryError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get('/api/steles/{stele_id}/roi-compare')
async def get_roi_compare_session(
    stele_id: str,
    runId: Optional[str] = None,
    x: Optional[int] = None,
    y: Optional[int] = None,
    w: Optional[int] = None,
    h: Optional[int] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    schema: Optional[str] = None,
):
    """Phase2 R3: paired before/after ROI compare session (never fabricates SHA)."""
    await get_stele(stele_id)
    from roi_compare import build_roi_compare_session
    bbox = None
    if x is not None and y is not None and (w is not None or width is not None):
        bbox = {'x': x, 'y': y}
        if w is not None:
            bbox['w'] = w
        if h is not None:
            bbox['h'] = h
        if width is not None:
            bbox['width'] = width
        if height is not None:
            bbox['height'] = height
    return build_roi_compare_session(stele_id, runId, bbox, source_schema=schema)


@app.get('/api/case-stele-mapping')
def get_case_stele_mapping():
    """Phase2 R6: experiment caseId <-> product steleId mapping overview."""
    from case_stele_mapping import mapping_overview
    return mapping_overview()


@app.get('/api/case-stele-mapping/{case_id}')
def get_case_stele_mapping_entry(case_id: str):
    from case_stele_mapping import resolve_case
    return resolve_case(case_id)


@app.get('/api/case-stele-mapping/{case_id}/claim/{stele_id}')
def claim_case_same_artifact(case_id: str, stele_id: str):
    """Gate: refuse same-artifact claim without human_reviewed mapping."""
    from case_stele_mapping import assert_same_artifact_claim
    result = assert_same_artifact_claim(case_id, stele_id)
    if not result['allowed']:
        raise HTTPException(status_code=409, detail=result['reason'])
    return result



@app.get("/generate")
async def generate_historical_graph(stele_id: str = "tang-duobao"):
    """Graph-only compatibility entry for /health -> /generate validation."""
    return await get_stele_graph(stele_id)



@app.get("/api/steles/{stele_id}/report")
async def get_stele_report(stele_id: str, run_id: Optional[str] = None):
    record=await get_stele(stele_id)
    result=catalog_report(record)
    from museum_processing import select_report_run
    selected,run_selection=select_report_run(stele_id,run_id)
    if run_id and not selected:
        raise HTTPException(status_code=404,detail='处理记录不存在')
    result['run']=selected
    result['runSelection']=run_selection
    from inference_trace import enrich_many
    from roi_compare import report_roi_compare_stub
    result['inferenceRecords']=enrich_many(
        [{**item,'sourceSteleId':item.get('steleId',stele_id)} for item in list_inferences(stele_id) if not selected or item.get('runId')==selected['runId']],
        stele_id=stele_id,
    )
    result['roiCompareSession']=report_roi_compare_stub(stele_id, selected)
    result['sourceRecords']=[{'title':record['title'],'url':record.get('sourceUrl'),'license':record.get('license')}]
    mode=(selected or {}).get('outputMode')
    if selected and mode=='passthrough':
        # REPORT_DATA_SPEC §8: an unchanged output must never be described as "actually processed".
        result['evaluation_summary']='本次未改动原图：算法判断无需处理，输出与输入逐像素相同；没有配对真值，配对质量未评测。'
    elif selected and mode=='undetermined':
        reason=selected.get('passthroughUndeterminedReason') or '原因未记录'
        result['evaluation_summary']=f'未能判定是否改动原图（{reason}）；没有配对真值，配对质量未评测。'
    elif selected:
        result['evaluation_summary']='实际处理已执行，但没有配对真值；配对质量未评测。'
    elif run_selection['legacyRunCount']:
        result['evaluation_summary']='只有旧版未核验运行，默认不选用（可在运行历史中显式打开）；配对质量未评测。'
    else:
        result['evaluation_summary']='尚未执行处理；配对质量未评测。'
    result['reportId']=f"RM-{stele_id}-{selected['runId']}" if selected else None
    return result


@app.get('/api/steles/{stele_id}/runs')
async def get_processing_runs(stele_id: str):
    await get_stele(stele_id)
    return list_runs(stele_id)


@app.delete('/api/steles/{stele_id}/runs/{run_id}')
async def remove_processing_run(stele_id: str, run_id: str, confirm: bool = False):
    """RT-013: confirm-gated soft-delete into runtime trash; 409 if referenced."""
    await get_stele(stele_id)
    if not confirm:
        raise HTTPException(status_code=400,detail='删除单次处理记录需要明确确认')
    try:
        result = delete_run(stele_id, run_id)
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith('run_referenced:'):
            refs = json.loads(msg.split(':', 1)[1])
            raise HTTPException(
                status_code=409,
                detail={'error': 'run_referenced', 'message': 'run is referenced by glyph inferences; refuse delete', 'references': refs},
            )
        raise HTTPException(status_code=400, detail=msg)
    if not result:
        raise HTTPException(status_code=404,detail='处理记录不存在')
    if isinstance(result, dict):
        return result
    return {'deleted': run_id, 'steleId': stele_id}


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
    if request.imageSource == 'restored' and not request.runId:
        raise HTTPException(status_code=422, detail='选择修复结果时必须提供本次运行 ID')
    if request.runId and not read_run(stele_id, request.runId):
        raise HTTPException(status_code=404, detail='关联的处理运行不存在')
    try:
        created = await infer_crop(record, request.bbox.model_dump(), request.context, request.characterId, request.originalGlyph, request.originalStatus, request.runId, request.imageSource)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    from inference_trace import enrich_inference_traceability
    return enrich_inference_traceability(created, stele_id=stele_id)


@app.get('/api/steles/{stele_id}/inferences')
async def get_glyph_inferences(stele_id: str):
    await get_stele(stele_id)
    from inference_trace import enrich_many
    return enrich_many(
        [{**item, 'sourceSteleId': item.get('steleId', stele_id)} for item in list_inferences(stele_id)],
        stele_id=stele_id,
    )


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


@app.post('/api/inferences/{inference_id}/ocr-baseline')
async def run_glyph_ocr_baseline(inference_id: str):
    from glyph_inference import attach_ocr_baseline
    try:
        return attach_ocr_baseline(inference_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


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
