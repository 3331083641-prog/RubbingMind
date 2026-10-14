"""Resolve the selected artifact explicitly and persist actual algorithm outputs."""
import base64, hashlib, json, uuid
from datetime import datetime,timezone
from pathlib import Path
from fastapi import HTTPException
from catalog import BASE, METRIC_KEYS

def process_verified_request(req, manager, engine):
    record=manager.get_stele_by_id(req.stele_id) if req.stele_id else None
    if req.stele_id and record is None:
        raise HTTPException(status_code=410 if req.stele_id in manager.retired else 404,detail='指定文物不可用，不替换为其他样本')
    if req.image_base64:
        image=req.image_base64
    elif record:
        url=(record.get('damaged_image') or record['raw_image']).split('?')[0]
        image=BASE/'apps/web/public'/url.lstrip('/')
        if not image.is_file():raise HTTPException(status_code=404,detail='该文物处理图像缺失')
        image=str(image)
    elif req.sample_id in ('sample_1.png','sample_2.png','sample_3.png','sample_4.png'):
        image=str(BASE/'static/samples'/req.sample_id)
    else:raise HTTPException(status_code=400,detail='需要文物ID或用户图像')
    result=engine.process_rubbing(image_input=image,d0=req.d0,nlm_h=req.h_nlm,clahe_clip=req.clahe_clip,morph_kernel=req.morph_kernel,damage_mask=req.damage_mask,cinnabar_style=req.cinnabar_style)
    if result.get('error'):raise HTTPException(status_code=422,detail=result['error'])
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'_'+uuid.uuid4().hex[:8]
    artifact_id=record['id'] if record else 'uploaded-image'
    out=BASE/'static/results'/artifact_id/run_id;out.mkdir(parents=True,exist_ok=True)
    saved={};hashes={}
    images = {role: result.get(key,'') for role,key in [('original','original_b64'),('restored','restored_b64'),('frequency_spectrum','fft_spectrum_b64'),('character_skeleton','skeleton_b64'),('cinnabar_rubbing','cinnabar_b64')]}
    for role,encoded in images.items():
        if not encoded:continue
        try:raw=base64.b64decode(encoded.split(',',1)[-1],validate=True)
        except ValueError:continue
        name=role+'.png';(out/name).write_bytes(raw);saved[role]=f'/static/results/{artifact_id}/{run_id}/{name}';hashes[role]=hashlib.sha256(raw).hexdigest()
    if 'restored' not in saved:raise HTTPException(status_code=422,detail='算法未产生可保存的修复图像')
    response=dict(stele_id=artifact_id,restored_image=saved['restored'],fft_spectrum=saved.get('frequency_spectrum',''),skeleton_b64=saved.get('character_skeleton',''),cinnabar_b64=saved.get('cinnabar_rubbing',''),processing_time_ms=result.get('metrics',{}).get('elapsed_ms'),**{k:None for k in METRIC_KEYS})
    # Existing engine calculates input-vs-output comparisons without paired ground truth.
    # Preserve those measurements, but do not present them as restoration accuracy.
    response['measurementBasis']='未评测：无配对真值；引擎输入／输出比较仅供诊断。'
    response['engineDiagnosticMetrics']=result.get('metrics',{})
    input_sha=hashlib.sha256(Path(image).read_bytes()).hexdigest() if not req.image_base64 else hashlib.sha256(base64.b64decode(req.image_base64.split(',',1)[-1])).hexdigest()
    (out/'processing.json').write_text(json.dumps(dict(response,parameters=req.model_dump(exclude={'image_base64'}),inputSha256=input_sha,outputSha256=hashes),ensure_ascii=False,indent=2),'utf-8')
    return response
