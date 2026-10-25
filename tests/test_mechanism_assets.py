"""Mechanism-layer PNG route: whitelist under derived/mechanism/, reject traversal and symlinks."""
import json

from fastapi.testclient import TestClient

import experiment_registry
from main import app

EXP, DIR = 'mech-exp', '2026-10-19-mech'


def _batch(tmp_path, monkeypatch, with_png=True, with_symlink=False):
    monkeypatch.setattr(experiment_registry, 'RESULTS', tmp_path)
    folder = tmp_path / DIR / 'derived' / 'mechanism' / 'case_a'
    folder.mkdir(parents=True)
    (tmp_path / DIR / 'results.json').write_text(json.dumps({
        'config': {'experimentId': EXP}, 'rows': [{'sampleId': 's', 'method': 'degraded'}], 'summary': []}), 'utf-8')
    (tmp_path / DIR / 'derived' / 'mechanism' / 'index.json').write_text(json.dumps([{'caseId': 'case_a'}]), 'utf-8')
    if with_png:
        (folder / 'edges_input.png').write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 16)
    if with_symlink:
        try:
            (folder / 'escape.png').symlink_to('/etc/passwd')
        except OSError:
            pass
    # outside file to tempt traversal
    (tmp_path / DIR / 'secret.png').write_bytes(b'secret')
    return TestClient(app)


def test_index_and_png_served(tmp_path, monkeypatch):
    client = _batch(tmp_path, monkeypatch)
    body = client.get(f'/api/experiments/{EXP}/mechanism').json()
    assert body['status'] == 'ok' and body['cases'][0]['caseId'] == 'case_a'
    res = client.get(f'/api/experiments/{EXP}/mechanism-assets/case_a/edges_input.png')
    assert res.status_code == 200 and res.headers['content-type'].startswith('image/png')


def test_rejects_traversal_absolute_and_non_png(tmp_path, monkeypatch):
    client = _batch(tmp_path, monkeypatch)
    for path in ('../secret.png', '..%2Fsecret.png', '/etc/passwd', 'case_a/edges_input.jpg', 'case_a/../../secret.png'):
        res = client.get(f'/api/experiments/{EXP}/mechanism-assets/{path}')
        assert res.status_code in (400, 404), path


def test_unknown_experiment_is_404(tmp_path, monkeypatch):
    client = _batch(tmp_path, monkeypatch)
    assert client.get('/api/experiments/nope/mechanism').status_code == 404
    assert client.get('/api/experiments/nope/mechanism-assets/a.png').status_code in (400, 404)
