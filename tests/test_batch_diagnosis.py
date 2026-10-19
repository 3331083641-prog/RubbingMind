"""R1-4: /api/experiments/{id}/diagnosis for every registered batch (v2 used to be 404)."""
import json

from fastapi.testclient import TestClient

from catalog import BASE
from main import app
from restoration_diagnosis import diagnose, diagnose_batch


def _independent_negative_count(directory):
    rows = json.loads((BASE / 'experiments/results' / directory / 'results.json').read_text('utf-8'))['rows']
    key = lambda r: r.get('caseId') or (r['sampleId'], r['degradation'], r.get('strength'), r.get('seed'))
    base = {key(r): r['psnr'] for r in rows if r['method'] == 'degraded'}
    return sum(1 for r in rows if r['method'] != 'degraded' and r['psnr'] < base[key(r)])


def test_every_registered_batch_has_a_diagnosis():
    client = TestClient(app)
    batches = client.get('/api/experiments').json()
    assert len(batches) == 4
    for item in batches:
        response = client.get(f"/api/experiments/{item['id']}/diagnosis")
        assert response.status_code == 200, item['id']
        body = response.json()
        assert body['experimentId'] == item['id'] and body['diagnosisVersion']
        if body['diagnosisVersion'] == 'baseline-delta-v1':
            assert body['negativeLiftCount'] == _independent_negative_count(item['directory']) == len(body['cases'])
            assert body['unmatchedRowCount'] == 0 and body['causeCounts'] is None
    assert client.get('/api/experiments/no-such-batch/diagnosis').status_code == 404


def test_heldout_diagnosis_unchanged_except_version_tag():
    body = TestClient(app).get('/api/experiments/heldout-v20-v21-2026-10-18/diagnosis').json()
    assert body.pop('diagnosisVersion') == 'heldout-legacy-heuristic'
    assert body == diagnose()


def test_generic_rules_on_synthetic_rows():
    rows = [
        {'sampleId': 's', 'degradation': 'g', 'seed': 1, 'method': 'degraded', 'psnr': 20.0, 'outputSha256': 'in'},
        {'sampleId': 's', 'degradation': 'g', 'seed': 1, 'method': 'a', 'psnr': 19.0, 'outputSha256': 'x'},
        {'sampleId': 's', 'degradation': 'g', 'seed': 1, 'method': 'b', 'psnr': 20.0, 'outputSha256': 'in'},
        {'sampleId': 't', 'degradation': 'g', 'seed': 1, 'method': 'a', 'psnr': 30.0, 'outputSha256': 'y'},
    ]
    body = diagnose_batch({'rows': rows}, 'synthetic')
    assert body['negativeLiftCount'] == 1 and body['cases'][0]['method'] == 'a' and body['cases'][0]['psnrDeltaFromInput'] == -1.0
    assert body['byMethod']['b']['byteIdenticalToInput'] == 1 and body['byMethod']['a']['unmatched'] == 1
    assert body['unmatchedRowCount'] == 1
