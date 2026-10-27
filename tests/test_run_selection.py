"""R1-1: legacy runs never become the default and always sort after verified runs."""
import json

from fastapi.testclient import TestClient

import museum_processing
from main import app

STELE = 'qing_02_wushi_reerection'


def _write(base, run_id, payload):
    folder = base / 'static' / 'results' / STELE / run_id
    folder.mkdir(parents=True)
    (folder / 'processing.json').write_text(json.dumps(payload, ensure_ascii=False), 'utf-8')


def _verified(run_id, finished):
    return {'runId': run_id, 'steleId': STELE, 'algorithmVersion': 'adaptive-rubbing-v2.1', 'finishedAt': finished,
            'evaluationStatus': 'unassessed', 'outputImages': {}}


def _patch(monkeypatch, tmp_path):
    monkeypatch.setattr(museum_processing, 'BASE', tmp_path)
    monkeypatch.setattr(museum_processing, 'RESULTS_DIR', None)


def test_legacy_sorts_last_even_with_unrecorded_finish_time(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    _write(tmp_path, '20261014T165542_5fc44fba', {'stele_id': STELE, 'restored_image': '/x.png'})  # legacy: no runId
    _write(tmp_path, '20261020T000000_aaaaaaaa', {'stele_id': STELE, 'restored_image': '/y.png'})  # newer legacy
    _write(tmp_path, '20261017T010101_11111111', _verified('20261017T010101_11111111', '2026-10-17T01:01:02+00:00'))
    _write(tmp_path, '20261018T072201_13772747', _verified('20261018T072201_13772747', '2026-10-18T07:22:03+00:00'))
    runs = museum_processing.list_runs(STELE)
    assert [r['runId'] for r in runs] == ['20261018T072201_13772747', '20261017T010101_11111111',
                                          '20261020T000000_aaaaaaaa', '20261014T165542_5fc44fba']
    assert [r['legacy'] for r in runs] == [False, False, True, True]
    assert runs[2]['runKind'] == 'legacy_unverified' and runs[2]['finishedAt'] == '未记录'
    assert runs[0]['runKind'] == 'processing' and runs[0]['sortTimestamp'] == '2026-10-18T07:22:01+00:00'

    client = TestClient(app)
    assert [r['runId'] for r in client.get(f'/api/steles/{STELE}/runs').json()][0] == '20261018T072201_13772747'
    report = client.get(f'/api/steles/{STELE}/report').json()
    assert report['run']['runId'] == '20261018T072201_13772747'
    assert report['runSelection'] == {'rule': 'latest_non_legacy', 'runId': '20261018T072201_13772747', 'legacyRunCount': 2}
    assert report['reportId'].endswith('20261018T072201_13772747')
    explicit = client.get(f'/api/steles/{STELE}/report?run_id=20261014T165542_5fc44fba').json()
    assert explicit['run']['legacy'] is True and explicit['runSelection']['rule'] == 'explicit'


def test_only_legacy_runs_means_no_default(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    _write(tmp_path, '20261014T165542_5fc44fba', {'stele_id': STELE, 'restored_image': '/x.png'})
    report = TestClient(app).get(f'/api/steles/{STELE}/report').json()
    assert report['run'] is None and report['reportId'] is None
    assert report['runSelection'] == {'rule': 'none', 'runId': None, 'legacyRunCount': 1}
    assert report['evaluation_summary'].startswith('只有旧版未核验运行')


def test_no_runs(monkeypatch, tmp_path):
    _patch(monkeypatch, tmp_path)
    report = TestClient(app).get(f'/api/steles/{STELE}/report').json()
    assert report['run'] is None and report['runSelection']['rule'] == 'none'
