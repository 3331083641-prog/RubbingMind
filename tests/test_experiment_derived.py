"""P1 (4)(5): applied_status and artifact-clustered CI are served read-only from eval-sci derived files,
with explicit states for missing / mismatched / stale files; experimentId <-> batch is one-to-one."""
import hashlib
import json

from fastapi.testclient import TestClient

import experiment_registry
from main import app

EXP, DIR = 'synthetic-exp-2026-10-19', '2026-10-19-synthetic'


def _batch(tmp_path, monkeypatch, *, applied=True, ci=True, stale=False, wrong_id=False):
    monkeypatch.setattr(experiment_registry, 'RESULTS', tmp_path)
    folder = tmp_path / DIR
    (folder / 'derived').mkdir(parents=True)
    results = {'config': {'experimentId': EXP}, 'rows': [{'sampleId': 's1', 'method': 'degraded', 'split': 'test'}], 'summary': []}
    (folder / 'results.json').write_text(json.dumps(results), 'utf-8')
    results_sha = hashlib.sha256((folder / 'results.json').read_bytes()).hexdigest()
    status_sha = None
    if applied:
        status = {'experimentId': 'other' if wrong_id else EXP, 'batch': DIR, 'criterion': 'pixel-equal-v1',
                  'sourceResultsSha256': '0' * 64 if stale else results_sha, 'imagesAvailable': True,
                  'summaryByMethod': [{'method': 'a', 'n': 1}], 'summaryBySplitMethod': [], 'summaryByMethodDegradation': [],
                  'rows': [{'rowIndex': 0, 'appliedStatus': 'passthrough'}]}
        (folder / 'derived/applied_status.json').write_text(json.dumps(status), 'utf-8')
        status_sha = hashlib.sha256((folder / 'derived/applied_status.json').read_bytes()).hexdigest()
    if ci:
        payload = {'experimentId': EXP, 'batch': DIR, 'seed': 20261019, 'bootstrap': 1000, 'percentiles': [2.5, 97.5],
                   'sourceResultsSha256': results_sha, 'appliedStatusSha256': status_sha, 'groups': [
                       {'split': 'test', 'method': 'a', 'degradation': 'ALL', 'scope': 'all', 'psnrGainCI95Low': 0.1, 'psnrGainSign': 'positive'},
                       {'split': 'test', 'method': 'b', 'degradation': 'ALL', 'scope': 'processed', 'psnrGainCI95Low': None, 'ciReliable': False}]}
        (folder / 'derived/ci_by_artifact.json').write_text(json.dumps(payload), 'utf-8')
    return TestClient(app)


def test_batch_index_is_one_to_one_and_resolves(tmp_path, monkeypatch):
    client = _batch(tmp_path, monkeypatch)
    index = client.get('/api/experiments/batch-index').json()
    assert index['items'] == [{'experimentId': EXP, 'batch': DIR}]
    assert client.get('/api/experiments').json()[0]['batch'] == DIR
    assert client.get('/api/experiments/resolve', params={'batch': DIR}).json() == {'experimentId': EXP, 'batch': DIR}
    assert client.get('/api/experiments/resolve', params={'batch': 'nope'}).status_code == 404


def test_applied_status_served_as_written(tmp_path, monkeypatch):
    client = _batch(tmp_path, monkeypatch)
    body = client.get(f'/api/experiments/{EXP}/applied-status').json()
    assert body['available'] is True and body['status'] == 'ok' and body['criterion'] == 'pixel-equal-v1'
    assert body['summaryByMethod'] == [{'method': 'a', 'n': 1}] and body['rowCount'] == 1 and 'rows' not in body
    assert client.get(f'/api/experiments/{EXP}/applied-status?rows=true').json()['rows'][0]['appliedStatus'] == 'passthrough'
    assert client.get('/api/experiments/unknown-exp/applied-status').status_code == 404


def test_ci_served_without_recomputation_and_filters(tmp_path, monkeypatch):
    client = _batch(tmp_path, monkeypatch)
    body = client.get(f'/api/experiments/{EXP}/ci-by-artifact').json()
    assert body['available'] is True and body['seed'] == 20261019 and body['bootstrap'] == 1000 and body['groupCount'] == 2
    assert body['groups'][0]['psnrGainCI95Low'] == 0.1 and '不重算' in body['servedBy']
    only = client.get(f'/api/experiments/{EXP}/ci-by-artifact', params={'method': 'b', 'scope': 'processed'}).json()
    assert only['groupCount'] == 1 and only['groups'][0]['ciReliable'] is False and only['groups'][0]['psnrGainCI95Low'] is None
    assert client.get('/api/experiments/unknown-exp/ci-by-artifact').status_code == 404


def test_missing_and_stale_files_give_explicit_states(tmp_path, monkeypatch):
    client = _batch(tmp_path, monkeypatch, applied=False, ci=False)
    for route in ('applied-status', 'ci-by-artifact'):
        body = client.get(f'/api/experiments/{EXP}/{route}').json()
        assert body['available'] is False and body['status'] == 'missing' and body['reason']
    experiment_registry._read.cache_clear()


def test_stale_or_foreign_derived_file_is_not_served(tmp_path, monkeypatch):
    client = _batch(tmp_path, monkeypatch, stale=True)
    body = client.get(f'/api/experiments/{EXP}/applied-status').json()
    assert body['available'] is False and body['status'] == 'stale' and 'sourceResultsSha256' in body['reason']
    assert 'summaryByMethod' not in body
    ci = client.get(f'/api/experiments/{EXP}/ci-by-artifact').json()
    assert ci['available'] is True  # CI file itself still matches results.json and the applied_status bytes it recorded


def test_foreign_experiment_id_rejected(tmp_path, monkeypatch):
    client = _batch(tmp_path, monkeypatch, wrong_id=True)
    body = client.get(f'/api/experiments/{EXP}/applied-status').json()
    assert body['available'] is False and 'experimentId=other' in body['reason']
