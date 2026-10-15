"""Upload behavior against an isolated SQLite database and image directory."""
import io
import hashlib

import numpy as np
import pytest
from PIL import Image
from fastapi.testclient import TestClient

import database
import museum_processing
import upload_storage
from main import app, ProcessRequest
from museum_manager import MuseumManager
from algorithm_engine import algorithm_engine


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path / 'rubbingmind.sqlite'))
    monkeypatch.setattr(upload_storage, 'UPLOAD_DIR', tmp_path / 'uploads')
    monkeypatch.setattr(museum_processing, 'BASE', tmp_path)
    return tmp_path, TestClient(app)


def image_bytes(format='PNG', size=(64, 64)):
    image = Image.fromarray(np.tile(np.arange(size[0], dtype=np.uint8), (size[1], 1)), mode='L')
    output = io.BytesIO()
    image.save(output, format=format)
    return output.getvalue()


@pytest.mark.parametrize('format,mime', [('PNG','image/png'), ('JPEG','image/jpeg')])
def test_upload_persists_reload_and_processes_real_image(isolated, format, mime):
    tmp_path, client = isolated
    payload = image_bytes(format)
    response = client.post('/api/upload', files={'file': ('untrusted-path.png', payload, mime)}, data={'title': '用户自选拓片'})
    assert response.status_code == 200, response.text
    record = response.json()['stele']
    assert record['id'].startswith('upload-')
    assert record['metrics']['psnr'] is None and not record['restored_image']
    assert record['originalFileSha256'] == hashlib.sha256(payload).hexdigest()
    assert client.get(record['raw_image']).content == payload
    assert client.get(f"/api/steles/{record['id']}").json()['title'] == '用户自选拓片'
    assert MuseumManager().get_stele_by_id(record['id'])['raw_image'] == record['raw_image']
    assert record['id'] in [r['id'] for r in client.get('/api/steles').json()]
    result = museum_processing.process_verified_request(ProcessRequest(stele_id=record['id']), MuseumManager(), algorithm_engine)
    assert result['stele_id'] == record['id'] and result['psnr'] is None
    assert (tmp_path / result['restored_image'].lstrip('/')).is_file()
    assert len([r for r in client.get('/api/steles').json() if r['source_kind'] == 'verified_review_v3']) == 28


@pytest.mark.parametrize('payload,mime,status', [
    (b'plain text', 'text/plain', 415),
    (b'broken png', 'image/png', 400),
    (image_bytes('PNG'), 'image/jpeg', 415),
    (image_bytes('PNG', (5100, 64)), 'image/png', 413),
    (b'0' * (12 * 1024 * 1024 + 1), 'image/png', 413),
], ids=['non-image', 'corrupt', 'mime-mismatch', 'oversized-dimensions', 'oversized-bytes'])
def test_invalid_upload_never_creates_record(isolated, payload, mime, status):
    tmp_path, client = isolated
    response = client.post('/api/upload', files={'file': ('bad.png', payload, mime)}, data={'title': '坏图'})
    assert response.status_code == status
    assert upload_storage.list_uploads() == []
    assert not list((tmp_path / 'uploads').glob('*')) if (tmp_path / 'uploads').exists() else True
