import hashlib
import json

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

import database
import glyph_inference
import museum_processing
from catalog import BASE, load
from main import app


RUN_ID = '20261018T010203_abcdef12'


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path / 'inference.sqlite'))
    monkeypatch.setattr(glyph_inference, 'INFERENCE_DIR', tmp_path / 'crops')
    monkeypatch.setattr(museum_processing, 'BASE', tmp_path)
    monkeypatch.delenv('RUBBINGMIND_VISION_API_KEY', raising=False)
    return TestClient(app), tmp_path


def _write_run(root, stele_id, image, sha=None, working_shape=None):
    folder = root / 'static' / 'results' / stele_id / RUN_ID
    folder.mkdir(parents=True)
    _ok, encoded = cv2.imencode('.png', image)
    raw = encoded.tobytes()
    (folder / 'restored.png').write_bytes(raw)
    height, width = image.shape[:2]
    record = {
        'steleId': stele_id, 'runId': RUN_ID,
        'outputImages': {'restored': f'/static/results/{stele_id}/{RUN_ID}/restored.png'},
        'outputSha256': {'restored': sha or hashlib.sha256(raw).hexdigest()},
        'inputImageSha256': 'b' * 64,
        'workingImage': {'sourceShape': [height, width], 'workingShape': working_shape or [height, width], 'scale': 1.0, 'interpolation': 'none'},
        'algorithmVersion': 'test-binding',
    }
    (folder / 'processing.json').write_text(json.dumps(record), encoding='utf-8')
    return hashlib.sha256(raw).hexdigest()


def test_original_and_restored_sources_stay_bound(client):
    api, root = client
    readable = next(item for item in load('steles28.json') if item['id'] == 'tang_01_duobao')
    original = BASE / 'apps/web/public' / readable['imageAssets']['readable'].split('?')[0].lstrip('/')
    original_sha = hashlib.sha256(original.read_bytes()).hexdigest()
    payload = {'bbox': {'x': 80, 'y': 80, 'w': 64, 'h': 64}, 'imageSource': 'original'}
    original_record = api.post('/api/steles/tang_01_duobao/inferences', json=payload)
    assert original_record.status_code == 200, original_record.text
    body = original_record.json()
    assert body['runId'] is None
    assert body['imageProvenance']['imageSource'] == 'original'
    assert body['imageProvenance']['runOwnership'] == 'not_applicable'
    assert body['selectedImageSha256'] == original_sha
    assert body['roi']['cropWidth'] == 64 and body['roi']['cropHeight'] == 64

    restored = api.post('/api/steles/tang_01_duobao/inferences', json={**payload, 'imageSource': 'restored'})
    assert restored.status_code == 422
    assert api.post('/api/steles/tang_01_duobao/inferences', json={**payload, 'imageSource': 'restored', 'runId': RUN_ID}).status_code == 404

    image = np_image()
    digest = _write_run(root, 'tang_01_duobao', image)
    bound = api.post('/api/steles/tang_01_duobao/inferences', json={**payload, 'imageSource': 'restored', 'runId': RUN_ID})
    assert bound.status_code == 200, bound.text
    bound_body = bound.json()
    assert bound_body['runId'] == RUN_ID
    assert bound_body['imageProvenance']['runOwnership'] == 'verified'
    assert bound_body['imageProvenance']['steleId'] == 'tang_01_duobao'
    assert bound_body['selectedImageSha256'] == digest
    assert bound_body['inputImageSha256'] == 'b' * 64
    crop = cv2.imdecode(np.frombuffer(api.get(bound_body['cropUrl']).content, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert crop.shape[:2] == (64, 64)
    assert int(crop.mean()) == 30

    still_original = api.post('/api/steles/tang_01_duobao/inferences', json={**payload, 'imageSource': 'original', 'runId': RUN_ID})
    assert still_original.status_code == 200
    assert still_original.json()['runId'] is None
    assert still_original.json()['selectedImageSha256'] == original_sha
    assert api.post('/api/steles/han_01_caoquan/inferences', json={**payload, 'imageSource': 'restored', 'runId': RUN_ID}).status_code == 404


def test_restored_sha_and_shape_must_match_the_run(client):
    api, root = client
    image = np_image()
    _write_run(root, 'tang_01_duobao', image, sha='a' * 64)
    payload = {'bbox': {'x': 80, 'y': 80, 'w': 64, 'h': 64}, 'imageSource': 'restored', 'runId': RUN_ID}
    assert api.post('/api/steles/tang_01_duobao/inferences', json=payload).status_code == 422
    folder = root / 'static' / 'results' / 'tang_01_duobao' / RUN_ID
    record = json.loads((folder / 'processing.json').read_text(encoding='utf-8'))
    record['outputSha256']['restored'] = hashlib.sha256((folder / 'restored.png').read_bytes()).hexdigest()
    record['workingImage']['workingShape'] = [8, 8]
    (folder / 'processing.json').write_text(json.dumps(record), encoding='utf-8')
    mismatch = api.post('/api/steles/tang_01_duobao/inferences', json=payload)
    assert mismatch.status_code == 422
    assert '尺寸' in mismatch.json()['detail']


def np_image():
    return np.full((160, 160, 3), 30, np.uint8)
