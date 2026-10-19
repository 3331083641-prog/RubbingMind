"""Resolve the selected artifact explicitly and persist actual algorithm outputs."""
import base64, hashlib, json, uuid, re, shutil
from datetime import datetime,timezone
from pathlib import Path
from fastapi import HTTPException
from catalog import BASE, METRIC_KEYS
from degradation_analysis import VERSION as ADAPTIVE_VERSION, change_stats
from runtime_paths import results_override

# Green 2026-10-19: one criterion name for runs and experiments. pixel-equal-v1 = both
# images decoded at their stored resolution with every channel kept (IMREAD_UNCHANGED);
# equal shape and every value equal. No gray conversion, no resizing.
RUN_PASSTHROUGH_CRITERION='pixel-equal-v1'
COMPARED_IMAGES=['original','restored']
# Green 2026-10-19 (a): a working-gray count is reported next to pixel-equal-v1 for reference only.
# It never decides isPassthrough / outputMode / the "本次未改动原图" wording.
GRAY_CRITERION='working-gray-pixel-equal-v1'
GRAY_CRITERION_RULE=('两张图各自按处理管线同一灰度化（algorithm_engine.process_rubbing 的 cv2.cvtColor(BGR→GRAY)；'
                     '单通道图不转换，四通道先去掉 alpha）后，形状相同则逐像素比较；仅供参考，不决定 isPassthrough。')
GRAY_FIELDS=('grayChangedPixelCount','grayChangedPixelRatio','grayCriterion','grayCriterionRule','graySource')
CHANGE_FIELDS=('isPassthrough','changedPixelCount','totalPixelCount','changedPixelRatio','maxAbsDiff','meanAbsDiff',
               'passthroughCriterion','passthroughSource','passthroughUndeterminedReason')+GRAY_FIELDS


def _decode_full(raw):
    import cv2, numpy as np
    if not raw:return None
    return cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_UNCHANGED)


def _gray_undetermined():
    return {key:None for key in GRAY_FIELDS}


def _undetermined(reason):
    return {'isPassthrough':None,'changedPixelCount':None,'totalPixelCount':None,'changedPixelRatio':None,
            'maxAbsDiff':None,'meanAbsDiff':None,'passthroughCriterion':None,'passthroughSource':None,
            'passthroughUndeterminedReason':reason,**_gray_undetermined()}


def _working_gray(image):
    import cv2
    if image.ndim==2:return image
    if image.shape[2]==1:return image[:,:,0]
    return cv2.cvtColor(image[:,:,:3],cv2.COLOR_BGR2GRAY)


def gray_change_status(before,after,source='recorded'):
    """Reference count on the pipeline's working gray image; None when it cannot be determined."""
    if before is None or after is None:return _gray_undetermined()
    try:
        a=_working_gray(before);b=_working_gray(after)
    except Exception:
        return _gray_undetermined()
    if a.shape!=b.shape or a.dtype!=b.dtype:return _gray_undetermined()
    stats=change_stats(a,b)
    return {'grayChangedPixelCount':stats['changedPixelCount'],'grayChangedPixelRatio':stats['changedPixelRatio'],
            'grayCriterion':GRAY_CRITERION,'grayCriterionRule':GRAY_CRITERION_RULE,'graySource':source}


def run_change_status(original_png, restored_png, source='recorded'):
    """pixel-equal-v1 between the saved working input (original.png) and the saved output.

    Undeterminable (missing, undecodable, different shape) -> every field None,
    including passthroughCriterion and passthroughSource; never guessed.
    """
    if not original_png or not restored_png:
        return _undetermined('缺少输入或输出图像')
    before=_decode_full(original_png);after=_decode_full(restored_png)
    if before is None or after is None:
        return _undetermined('输入或输出图像无法解码')
    if before.shape!=after.shape or before.dtype!=after.dtype:
        return {**_undetermined(f'输入与输出的数组形状或位深不同（{before.shape}/{before.dtype} vs {after.shape}/{after.dtype}），按 pixel-equal-v1 无法逐像素比较'),
                **gray_change_status(before,after,source)}
    stats=change_stats(before,after)
    stats['passthroughCriterion']=RUN_PASSTHROUGH_CRITERION
    stats['passthroughSource']=source
    stats['passthroughUndeterminedReason']=None
    stats.update(gray_change_status(before,after,source))
    return stats


def output_mode(status):
    flag=status.get('isPassthrough')
    return 'passthrough' if flag is True else 'processed' if flag is False else 'undetermined'


def _run_file(stele_id,run_id,url):
    prefix=f'/static/results/{stele_id}/{run_id}/'
    if not isinstance(url,str) or not url.startswith(prefix):return None
    root=(results_root()/stele_id/run_id).resolve()
    path=(root/url[len(prefix):]).resolve()
    return path if path.parent==root and path.is_file() else None


def _verified_bytes(path,expected_sha):
    if path is None or not expected_sha:return None
    raw=path.read_bytes()
    return raw if hashlib.sha256(raw).hexdigest()==expected_sha else None


_READ_CACHE={}


def computed_on_read_status(stele_id,run_id,data):
    """Old runs only: compute pixel-equal-v1 (and the gray reference) from the stored PNGs if BOTH
    SHA-256 match the run record. Read-only: nothing is written back."""
    images=data.get('outputImages') or {};hashes=data.get('outputSha256') or {}
    if not isinstance(hashes,dict) or not hashes.get('original') or not hashes.get('restored'):
        return _undetermined('该运行保存于判据引入前，且未记录输入/输出 SHA-256，无法校验后读取计算')
    paths={role:_run_file(stele_id,run_id,images.get(role)) for role in ('original','restored')}
    if None in paths.values():
        return _undetermined('该运行保存于判据引入前，本地缺少输入或输出图像')
    key=tuple((str(p),p.stat().st_mtime_ns,hashes[r]) for r,p in sorted(paths.items()))
    if key in _READ_CACHE:return dict(_READ_CACHE[key])
    raw={role:_verified_bytes(path,hashes[role]) for role,path in paths.items()}
    if raw['original'] is None or raw['restored'] is None:
        status=_undetermined('该运行保存于判据引入前，本地图像与记录的 SHA-256 不一致，拒绝计算')
    else:
        status=run_change_status(raw['original'],raw['restored'],source='computed-on-read')
    if len(_READ_CACHE)>512:_READ_CACHE.clear()
    _READ_CACHE[key]=dict(status)
    return status


def effective_parameters(req):
    """Parameters that actually reached the algorithm (E-10)."""
    if req.filter_type=='adaptive':
        return {'mode':'adaptive','strength':max(.1,req.h_nlm/10),'notchWidth':max(.5,req.d0/60),
                'derivedFrom':{'strength':'max(0.1, h_nlm/10)','notchWidth':'max(0.5, d0/60)'},
                'ignoredRequestParameters':['filter_order','clahe_clip','morph_kernel'],
                'note':'NLM 实际 h 与是否陷波由自适应决策决定，见 adaptiveDiagnostics.decisions。'}
    return {'mode':req.filter_type,'d0':req.d0,'filterOrder':req.filter_order,'nlmH':req.h_nlm,
            'claheClip':req.clahe_clip,'morphKernel':req.morph_kernel,'ignoredRequestParameters':[]}

def process_verified_request(req, manager, engine):
    started_at=datetime.now(timezone.utc).isoformat()
    record=manager.get_stele_by_id(req.stele_id) if req.stele_id else None
    if req.stele_id and record is None:
        raise HTTPException(status_code=410 if req.stele_id in manager.retired else 404,detail='指定文物不可用，不替换为其他样本')
    if record and req.image_base64:
        raise HTTPException(status_code=422,detail='文物ID不能与外部图像混用；请先上传到独立用户样本空间')
    if req.image_base64:
        raise HTTPException(status_code=422,detail='请通过上传接口建立独立样本后再处理')
        image=req.image_base64
    elif record:
        if record.get('source_kind') == 'user_upload':
            from upload_storage import image_path
            image=image_path(record['id'])
        else:
            url=(record.get('damaged_image') or record['raw_image']).split('?')[0]
            image=BASE/'apps/web/public'/url.lstrip('/')
        if image is None or not image.is_file():raise HTTPException(status_code=404,detail='该文物处理图像缺失')
        image=str(image)
    elif req.sample_id in ('sample_1.png','sample_2.png','sample_3.png','sample_4.png'):
        image=str(BASE/'static/samples'/req.sample_id)
    else:raise HTTPException(status_code=422,detail='缺少 stele_id：请明确指定要处理的文物（或内置样本 sample_id）；不会默认处理任何文物')
    result=engine.process_rubbing(image_input=image,d0=req.d0,filter_order=req.filter_order,filter_type=req.filter_type,nlm_h=req.h_nlm,clahe_clip=req.clahe_clip,morph_kernel=req.morph_kernel,damage_mask=req.damage_mask,cinnabar_style=req.cinnabar_style,random_seed=req.random_seed)
    if result.get('error'):raise HTTPException(status_code=422,detail=result['error'])
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'_'+uuid.uuid4().hex[:8]
    artifact_id=record['id'] if record else 'uploaded-image'
    out=results_root()/artifact_id/run_id;out.mkdir(parents=True,exist_ok=True)
    saved={};hashes={};raw_images={}
    images = {role: result.get(key,'') for role,key in [('original','original_b64'),('restored','restored_b64'),('frequency_spectrum','fft_spectrum_b64'),('character_skeleton','skeleton_b64'),('binary_skeleton','binary_skeleton_b64'),('contour','contour_b64'),('cinnabar_rubbing','cinnabar_b64')]}
    try:
        for role,encoded in images.items():
            if not encoded:continue
            try:raw=base64.b64decode(encoded.split(',',1)[-1],validate=True)
            except ValueError:continue
            raw_images[role]=raw
            name=role+'.png';(out/name).write_bytes(raw);saved[role]=f'/static/results/{artifact_id}/{run_id}/{name}';hashes[role]=hashlib.sha256(raw).hexdigest()
        if 'restored' not in saved:raise HTTPException(status_code=422,detail='算法未产生可保存的修复图像')
    except Exception:
        shutil.rmtree(out,ignore_errors=True)
        raise
    response=dict(stele_id=artifact_id,restored_image=saved['restored'],fft_spectrum=saved.get('frequency_spectrum',''),skeleton_b64=saved.get('character_skeleton',''),cinnabar_b64=saved.get('cinnabar_rubbing',''),processing_time_ms=result.get('metrics',{}).get('elapsed_ms'),**{k:None for k in METRIC_KEYS})
    # Existing engine calculates input-vs-output comparisons without paired ground truth.
    # Preserve those measurements, but do not present them as restoration accuracy.
    response['measurementBasis']='未评测：无配对真值；输入／输出变化量仅供诊断。'
    response['engineDiagnosticMetrics']=result.get('diagnostic_metrics',{})
    response['frequencyDetails']=result.get('frequency_details',{})
    response['runId']=run_id
    response['algorithmVersion']=ADAPTIVE_VERSION if req.filter_type=='adaptive' else 'fixed-frequency-spatial-v2.2'
    response['adaptiveDiagnostics']=result.get('frequency_details',{}).get('adaptive')
    response['evaluationStatus']='unassessed'
    response['outputImages']=saved
    change=run_change_status(raw_images.get('original'),raw_images.get('restored'))
    response.update({key:change[key] for key in CHANGE_FIELDS},comparedImages=list(COMPARED_IMAGES),outputMode=output_mode(change))
    response['effectiveParameters']=effective_parameters(req)
    input_sha=hashlib.sha256(Path(image).read_bytes()).hexdigest() if not req.image_base64 else hashlib.sha256(base64.b64decode(req.image_base64.split(',',1)[-1])).hexdigest()
    record_json=dict(response,steleId=artifact_id,algorithmParameters=req.model_dump(exclude={'image_base64','damage_mask'}),
        inputImageSha256=input_sha,outputSha256=hashes,startedAt=started_at,finishedAt=datetime.now(timezone.utc).isoformat(),
        processingTime=result.get('metrics',{}).get('elapsed_ms'),evaluationMetrics={'psnr':None,'ssim':None},
        diagnosticMetrics=result.get('diagnostic_metrics',{}),inferenceRecords=[],
        workingImage=result.get('working_image'),randomSeed=req.random_seed,
        damageMaskSha256=hashlib.sha256(base64.b64decode(req.damage_mask.split(',',1)[-1],validate=True)).hexdigest() if req.damage_mask else None,
        imageRoles={'source':'immutable_source','original':'synthetic_degradation' if req.damage_mask else 'working_input','restored':'algorithm_output','cinnabar_rubbing':'artistic_display_not_evaluated'},
        sourceRecords=[{'title':record.get('title'),'url':record.get('sourceUrl'),'license':record.get('license')} ] if record else [])
    (out/'processing.json').write_text(json.dumps(record_json,ensure_ascii=False,indent=2,allow_nan=False),'utf-8')
    return response


# None = historical default <BASE>/static/results; RUBBINGMIND_RESULTS_DIR relocates
# run storage while URLs stay /static/results/... (tests patch BASE and RESULTS_DIR).
RESULTS_DIR=results_override()


def results_root():
    return RESULTS_DIR or BASE/'static'/'results'


def read_run(stele_id, run_id):
    if not re.fullmatch(r'[0-9]{8}T[0-9]{6}_[0-9a-f]{8}',run_id):
        return None
    path=results_root()/stele_id/run_id/'processing.json'
    if not path.is_file():return None
    data=json.loads(path.read_text(encoding='utf-8'))
    if data.get('steleId',data.get('stele_id'))!=stele_id:return None
    if not data.get('runId'):
        # Keep older output files accessible, but their calibrated diagnostics
        # were not measured under the current protocol and must not be reported.
        data.update(runId=run_id,steleId=stele_id,algorithmVersion='legacy-unverified',
            evaluationStatus='unassessed',evaluationMetrics={'psnr':None,'ssim':None},
            diagnosticMetrics={},inputImageSha256='未记录',startedAt='未记录',
            finishedAt='未记录',algorithmParameters=data.get('parameters',{}),
            outputImages={'restored':data.get('restored_image','')},inferenceRecords=[],sourceRecords=[])
    if 'isPassthrough' not in data:
        # Runs saved before the criterion: computed on read when both SHA-256 verify; never written back.
        status=computed_on_read_status(stele_id,run_id,data)
        data.update(status,comparedImages=list(COMPARED_IMAGES),outputMode=output_mode(status))
    elif 'grayCriterion' not in data:
        # Runs recorded before the gray reference existed: only the gray fields are computed on read.
        status=computed_on_read_status(stele_id,run_id,data)
        data.update({key:status.get(key) for key in GRAY_FIELDS})
    return data if data.get('runId')==run_id else None


def list_runs(stele_id):
    folder=results_root()/stele_id
    if not folder.is_dir():return []
    records=[]
    for path in folder.glob('*/processing.json'):
        record=read_run(stele_id,path.parent.name)
        if record:records.append(annotate_run(record))
    # R1-1: verified runs newest first, then legacy runs newest first, then undatable ones.
    # (Sorting the legacy placeholder finishedAt='未记录' as a string put it first.)
    return sorted(records,key=lambda row:(row['legacy'],row['sortTimestamp'] is None,_neg_ts(row['sortTimestamp'])))


LEGACY_VERSION='legacy-unverified'


def run_timestamp(run_id):
    """UTC ISO time encoded in the runId prefix (runs are named with UTC strftime)."""
    try:
        return datetime.strptime(str(run_id)[:15],'%Y%m%dT%H%M%S').replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return None


def _neg_ts(value):
    return -datetime.fromisoformat(value).timestamp() if value else 0


def annotate_run(record):
    """Additive run-kind fields (R1-1); never rewrites the stored processing.json."""
    if record is None:return None
    legacy=record.get('algorithmVersion')==LEGACY_VERSION
    record.update(legacy=legacy,runKind='legacy_unverified' if legacy else 'processing',sortTimestamp=run_timestamp(record.get('runId')))
    # R1-5: no cross-id aggregation; each run states the id it is stored under.
    record['sourceSteleId']=record.get('steleId',record.get('stele_id'))
    # REPORT_DATA_SPEC §8 lists these for every run; runs saved before the criterion lack them.
    for key in ('totalPixelCount','meanAbsDiff'):
        record.setdefault(key,None)
    return record


def select_report_run(stele_id,run_id=None):
    """Return (run, runSelection). Explicit ids may open legacy runs; the default never does."""
    runs=list_runs(stele_id)
    legacy_count=sum(1 for row in runs if row['legacy'])
    if run_id:
        run=annotate_run(read_run(stele_id,run_id))
        return run,{'rule':'explicit','runId':run['runId'] if run else None,'legacyRunCount':legacy_count}
    run=next((row for row in runs if not row['legacy']),None)
    return run,{'rule':'latest_non_legacy' if run else 'none','runId':run['runId'] if run else None,'legacyRunCount':legacy_count}


def delete_run(stele_id,run_id):
    if read_run(stele_id,run_id) is None:
        return False
    root=(results_root()/stele_id).resolve()
    target=(root/run_id).resolve()
    if target.parent!=root:
        return False
    shutil.rmtree(target)
    return True
