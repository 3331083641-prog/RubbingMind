"""Resolve the selected artifact explicitly and persist actual algorithm outputs."""
import base64, hashlib, json, uuid, re, shutil
from datetime import datetime,timezone
from pathlib import Path
from fastapi import HTTPException
from catalog import BASE, METRIC_KEYS

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
    else:raise HTTPException(status_code=400,detail='需要文物ID或用户图像')
    result=engine.process_rubbing(image_input=image,d0=req.d0,filter_order=req.filter_order,filter_type=req.filter_type,nlm_h=req.h_nlm,clahe_clip=req.clahe_clip,morph_kernel=req.morph_kernel,damage_mask=req.damage_mask,cinnabar_style=req.cinnabar_style,random_seed=req.random_seed)
    if result.get('error'):raise HTTPException(status_code=422,detail=result['error'])
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'_'+uuid.uuid4().hex[:8]
    artifact_id=record['id'] if record else 'uploaded-image'
    out=BASE/'static/results'/artifact_id/run_id;out.mkdir(parents=True,exist_ok=True)
    saved={};hashes={}
    images = {role: result.get(key,'') for role,key in [('original','original_b64'),('restored','restored_b64'),('frequency_spectrum','fft_spectrum_b64'),('character_skeleton','skeleton_b64'),('binary_skeleton','binary_skeleton_b64'),('contour','contour_b64'),('cinnabar_rubbing','cinnabar_b64')]}
    try:
        for role,encoded in images.items():
            if not encoded:continue
            try:raw=base64.b64decode(encoded.split(',',1)[-1],validate=True)
            except ValueError:continue
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
    response['algorithmVersion']='adaptive-rubbing-v2.0' if req.filter_type=='adaptive' else 'fixed-frequency-spatial-v2.1'
    response['adaptiveDiagnostics']=result.get('frequency_details',{}).get('adaptive')
    response['evaluationStatus']='unassessed'
    response['outputImages']=saved
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


def read_run(stele_id, run_id):
    if not re.fullmatch(r'[0-9]{8}T[0-9]{6}_[0-9a-f]{8}',run_id):
        return None
    path=BASE/'static/results'/stele_id/run_id/'processing.json'
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
    return data if data.get('runId')==run_id else None


def list_runs(stele_id):
    folder=BASE/'static/results'/stele_id
    if not folder.is_dir():return []
    records=[]
    for path in folder.glob('*/processing.json'):
        record=read_run(stele_id,path.parent.name)
        if record:records.append(record)
    return sorted(records,key=lambda row:row.get('finishedAt',row.get('runId','')),reverse=True)


def delete_run(stele_id,run_id):
    if read_run(stele_id,run_id) is None:
        return False
    root=(BASE/'static/results'/stele_id).resolve()
    target=(root/run_id).resolve()
    if target.parent!=root:
        return False
    shutil.rmtree(target)
    return True
