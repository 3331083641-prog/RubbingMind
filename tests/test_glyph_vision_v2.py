import base64
import hashlib
import json
import cv2
import numpy as np
import pytest
import database
import glyph_inference
from glyph_vision import analyze_crop,shape_similarity
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(database,'DB_PATH',str(tmp_path/'test.sqlite'))
    monkeypatch.setattr(glyph_inference,'INFERENCE_DIR',tmp_path/'crops')
    monkeypatch.delenv('RUBBINGMIND_VISION_API_KEY',raising=False)
    return TestClient(app)


def test_structure_rejection_and_cross_topology():
    blank = np.full((96, 96), 240, np.uint8)
    rejected, _images = analyze_crop(blank)
    assert rejected['rejectRecognition'] is True
    assert rejected['contentBox'] is None
    cross = np.zeros((96, 96), np.uint8)
    cross[20:80, 45:50] = 230
    cross[45:50, 20:80] = 230
    analysis, _images = analyze_crop(cross)
    assert analysis['rejectRecognition'] is False
    assert analysis['branchCount'] >= 1 and analysis['endpointCount'] >= 4
    assert analysis['version'] == 'glyph-shape-v2.1'


def test_visual_features_actual_pixels_and_not_ocr():
    image=np.zeros((96,96),np.uint8);image[20:80,45:50]=230;image[45:50,20:80]=230
    analysis,images=analyze_crop(image)
    assert analysis['componentCount']==1 and analysis['skeletonPixels']>80
    assert shape_similarity(images['foreground'],images['foreground'])==pytest.approx(1)
    assert analyze_crop(np.zeros((96,96),np.uint8))[0]['contentBox'] is None
    assert '有效字迹不足' in analyze_crop(np.zeros((96,96),np.uint8))[0]['warnings']


def test_crop_analysis_templates_and_artifact_isolation(client):
    record=client.post('/api/steles/tang_01_duobao/inferences',json={'bbox':{'x':80,'y':80,'w':64,'h':64}}).json()
    for role,url in record['analysisImages'].items():
        response=client.get(url);assert response.status_code==200 and response.headers['content-type']=='image/png'
    crop=client.get(record['cropUrl']).content
    assert hashlib.sha256(crop).hexdigest()==record['cropSha256']
    saved=client.post(f"/api/inferences/{record['inferenceId']}/template",json={'glyph':'十','basis':'synthetic pipeline test only, not verified inscription','annotator':'automated fixture'})
    assert saved.status_code==200
    second=client.post('/api/steles/tang_01_duobao/inferences',json={'bbox':record['bbox']}).json()
    # Tests plumbing, never claimed as historical-character accuracy.
    assert second['retrievalCandidates'][0]['glyph']=='十'
    assert client.get('/api/steles/han_01_caoquan/inferences').json()==[]
    rejected=client.post(f"/api/inferences/{record['inferenceId']}/decision",json={'action':'reject'}).json()
    assert rejected['status']=='human_rejected' and rejected['decisions'][-1]['action']=='reject'
    assert client.get('/api/inferences/missing/analysis/gray').status_code==404
    assert client.post(f"/api/inferences/{record['inferenceId']}/template",json={'glyph':'十','basis':'','annotator':'x'}).status_code==422


def test_actual_visual_api_payload_and_unverified_sources(client,monkeypatch):
    monkeypatch.setenv('RUBBINGMIND_VISION_API_KEY','fixture-only-not-a-key')
    seen={}
    class Response:
        def raise_for_status(self):pass
        def json(self):return {'choices':[{'message':{'content':json.dumps([{'glyph':'十','visualEvidence':'交叉残迹','contextEvidence':'未知','sourceUrls':['https://unverified.example/test']}])}}]}
    class Client:
        def __init__(self,**kw):pass
        async def __aenter__(self):return self
        async def __aexit__(self,*a):pass
        async def post(self,url,**kw):seen.update(kw['json']);return Response()
    monkeypatch.setattr(glyph_inference.httpx,'AsyncClient',Client)
    result=client.post('/api/steles/tang_01_duobao/inferences',json={'bbox':{'x':80,'y':80,'w':64,'h':64}}).json()
    assert seen['messages'][0]['content'][1]['image_url']['url'].startswith('data:image/png;base64,')
    assert result['source']=='vision_model' and '尚未单独核实' in result['note']
    assert result['candidates'][0]['scoreBasis']=='模型排序，未经概率校准'
