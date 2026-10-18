import database
import glyph_inference
import glyph_ocr
import numpy as np
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path / 'inference.sqlite'))
    monkeypatch.setattr(glyph_inference, 'INFERENCE_DIR', tmp_path / 'crops')
    monkeypatch.delenv('RUBBINGMIND_VISION_API_KEY', raising=False)
    return TestClient(app)


def test_printed_ocr_probe_cannot_become_accuracy():
    image = np.full((32, 32, 3), 255, np.uint8)

    def engine(_image):
        return [[[[0, 0], [8, 0], [8, 8], [0, 8]], '十', 0.42]], None

    result = glyph_ocr.recognize(image, engine=engine)
    assert result['status'] == 'completed'
    assert result['candidates'][0]['glyph'] == '十'
    assert result['countsAsAccuracy'] is False
    assert '准确率' in result['limitation']


def test_ocr_baseline_does_not_adopt_its_guess(client, monkeypatch):
    monkeypatch.setattr(glyph_ocr, 'recognize_png', lambda _data, engine=None: {
        'engine': 'test', 'status': 'completed', 'candidates': [{'glyph': '十'}], 'texts': [{'text': '十', 'score': 0.1}],
        'countsAsAccuracy': False, 'limitation': '测试桩，不是古碑准确率。',
    })
    created = client.post('/api/steles/tang_01_duobao/inferences', json={'bbox': {'x': 80, 'y': 80, 'w': 64, 'h': 64}, 'context': ''})
    assert created.status_code == 200
    probed = client.post(f"/api/inferences/{created.json()['inferenceId']}/ocr-baseline")
    assert probed.status_code == 200
    body = probed.json()
    assert body['adoptedGlyph'] is None
    assert body['status'] == 'no_candidate'
    assert body['ocrBaseline']['candidates'][0]['glyph'] == '十'
    assert body['ocrBaseline']['countsAsAccuracy'] is False


def test_missing_ocr_engine_is_reported(monkeypatch):
    import builtins
    original = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == 'rapidocr_onnxruntime':
            raise ImportError('not installed')
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', blocked)
    result = glyph_ocr.recognize(np.zeros((8, 8), np.uint8))
    assert result['status'] == 'engine_unavailable'
    assert result['candidates'] == []
    assert result['countsAsAccuracy'] is False
