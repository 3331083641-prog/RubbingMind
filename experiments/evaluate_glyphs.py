"""Evaluate human-verified artifact-disjoint glyph references, or report not assessed."""
import hashlib
import json
import sys
from pathlib import Path
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from glyph_vision import analyze_crop,shape_similarity


def evaluate(manifest):
    data=json.loads(Path(manifest).read_text('utf8'));records=data['annotations']
    if not records:return {'status':'not_evaluated','n':0,'top1':None,'top3':None,'rejectionRate':None,'reason':data['limitation'],'predictions':[]}
    catalogue={r['id']:r for r in json.loads((ROOT/'data/catalog/steles28.json').read_text('utf8'))}
    processed=[]
    for r in records:
        if not all(r.get(k) for k in ['annotator','annotationBasis','sourceUrl','humanVerified']):raise ValueError('需要人工核验标注和来源')
        artifact=catalogue[r['steleId']];path=ROOT/'apps/web/public'/artifact['imageAssets']['readable'].split('?')[0].lstrip('/')
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=r['imageSha256']:raise ValueError('标注源图SHA不符')
        image=cv2.imdecode(np.frombuffer(raw,np.uint8),0);x,y,w,h=r['bbox'];crop=image[y:y+h,x:x+w]
        if crop.shape!=(h,w):raise ValueError('标注选区越界')
        processed.append((r,analyze_crop(crop)[1]['foreground']))
    train=[r for r in processed if r[0]['split']=='reference'];test=[r for r in processed if r[0]['split']=='test']
    if {r[0]['steleId'] for r in train}&{r[0]['steleId'] for r in test}:raise ValueError('同一文物跨参考/测试集，存在泄漏')
    if not train or not test:raise ValueError('需要非空参考与独立测试集')
    predictions=[]
    for r,image in test:
        scores={}
        for t,shape in train:scores[t['glyph']]=max(scores.get(t['glyph'],0),shape_similarity(image,shape))
        ranked=sorted(scores,key=lambda g:-scores[g])[:3];rejected=not ranked or scores[ranked[0]]<.45
        predictions.append({'id':r['id'],'expected':r['glyph'],'ranked':ranked,'scores':scores,'rejected':rejected,
                            'top1':not rejected and ranked[0]==r['glyph'],'top3':not rejected and r['glyph'] in ranked})
    return {'status':'human_reference_test','n':len(test),'top1':sum(p['top1'] for p in predictions)/len(test),
            'top3':sum(p['top3'] for p in predictions)/len(test),'rejectionRate':sum(p['rejected'] for p in predictions)/len(test),'predictions':predictions}


if __name__=='__main__':
    result=evaluate(ROOT/'data/catalog/glyph-benchmark-v2.json')
    path=ROOT/'experiments/results/glyph-v2-evaluation.json';path.write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
    print(json.dumps(result,ensure_ascii=False))
