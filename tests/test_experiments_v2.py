import csv
import hashlib
import io
from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient
from main import app,PROCESS_LOCK
from experiments.run_v2 import degrade
from experiment_registry import batch,asset


ID='controlled-rubbings-v2-2026-10-17'


def test_v2_groups_identity_and_real_csv_metrics():
    client=TestClient(app)
    data=client.get('/api/experiments/'+ID).json()
    assert len(data['rows'])==1260
    assert len(data['sources'])==14 and len({s['dynasty'] for s in data['sources']})==7
    dev={r['sampleId'] for r in data['rows'] if r['split']=='development'}
    test={r['sampleId'] for r in data['rows'] if r['split']=='test'}
    assert not dev&test
    csv_response=client.get('/api/experiments/'+ID+'/export/results.csv')
    values=list(csv.DictReader(io.StringIO(csv_response.content.decode('utf-8-sig'))))
    for r,c in zip(data['rows'],values):
        assert float(c['psnr'])==r['psnr'] and float(c['ssim'])==r['ssim']
        assert r['error'] is None
    for field in ['output','input','reference']:
        r=data['rows'][0];response=client.get('/api/experiments/'+ID+'/assets/'+r[field])
        assert response.status_code==200
        assert hashlib.sha256(response.content).hexdigest()==r[field+'Sha256']
    assert client.get('/api/experiments/'+ID+'/assets/config-v2.json').status_code==404
    assert client.get('/api/experiments/missing').status_code==404
    assert asset(ID,'../../main.py') is None


def test_seeded_degradation_all_types():
    image=np.arange(65536,dtype=np.uint8).reshape(256,256)
    for method in ['gaussian','salt_pepper','periodic','blur','occlusion']:
        a,params=degrade(image,method,15,1.)
        b,_=degrade(image,method,15,1.)
        assert np.array_equal(a,b) and params['seed']==15


def test_text_batch_uses_new_artifacts_and_traceable_sampling():
    pilot=batch(ID);text=batch('controlled-rubbings-v2-text-2026-10-17')
    assert len(text['rows'])==1260
    assert not {r['id'] for r in pilot['sources']}&{r['id'] for r in text['sources']}
    assert len({r['id'] for r in pilot['sources']+text['sources']})==28
    assert text['config']['algorithmParameters']['adaptive_joint']=={'strength':1.,'notch_width':.8}
    for source in text['sources']:
        assert source['samplingDiagnostics']['eligibleRegionCount']>0 or source['id']=='song_03_daguan'
        assert source['license'] and source['sourceSha256']


def test_no_human_labels_no_invented_glyph_accuracy():
    from experiments.evaluate_glyphs import evaluate
    data=evaluate(Path(__file__).resolve().parents[1]/'data/catalog/glyph-benchmark-v2.json')
    assert data['status']=='not_evaluated' and data['top1'] is None and data['top3'] is None


def test_single_processing_job_and_remote_fail_closed(monkeypatch):
    client=TestClient(app)
    PROCESS_LOCK.acquire()
    try:assert client.post('/api/process',json={'stele_id':'han_01_caoquan'}).status_code==429
    finally:PROCESS_LOCK.release()
    monkeypatch.setenv('RUBBINGMIND_DEPLOYMENT','remote')
    monkeypatch.delenv('RUBBINGMIND_ADMIN_TOKEN',raising=False)
    assert client.get('/api/steles').status_code==401
    assert client.get('/static/results/anything.png').status_code==401
    assert client.get('/health').status_code==200
    monkeypatch.setenv('RUBBINGMIND_ADMIN_TOKEN','fixture-admin-token-not-real')
    assert client.get('/api/steles',headers={'Authorization':'Bearer fixture-admin-token-not-real'}).status_code==200


def test_body_limit_and_invalid_mask_are_real_failures():
    client=TestClient(app)
    assert client.post('/api/process',content=b'{}',headers={'content-length':str(20*1024*1024)}).status_code==413
    response=client.post('/api/process',json={'stele_id':'han_01_caoquan','damage_mask':'not-an-image'})
    assert response.status_code==422
