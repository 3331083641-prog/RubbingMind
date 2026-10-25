"""R1-3: split availability, batch status and a single default batch."""
from fastapi.testclient import TestClient

import experiment_metadata
from main import app

EXPECTED_STATUS = {
    'controlled-rubbings-2026-10-15': 'historical-leakage',
    'controlled-rubbings-v2-2026-10-17': 'valid',
    'controlled-rubbings-v2-text-2026-10-17': 'valid',
    'heldout-v20-v21-2026-10-18': 'metrics-only',
}


def test_registered_batches_carry_metadata():
    client = TestClient(app)
    batches = {b['id']: b for b in client.get('/api/experiments').json()}
    assert {k: batches[k]['status'] for k in EXPECTED_STATUS} == EXPECTED_STATUS
    assert [k for k, b in batches.items() if b['defaultForReport']] == ['controlled-rubbings-v2-text-2026-10-17']
    assert 'REPORT_DATA_SPEC' in batches['controlled-rubbings-v2-text-2026-10-17']['defaultForReportBasis']
    for key in ('controlled-rubbings-v2-2026-10-17', 'controlled-rubbings-v2-text-2026-10-17'):
        assert batches[key]['splitAvailable'] is True and batches[key]['rowsWithoutSplit'] == 0
        assert sum(batches[key]['splits'].values()) == batches[key]['rowCount']
    for key in ('controlled-rubbings-2026-10-15', 'heldout-v20-v21-2026-10-18'):
        assert batches[key]['splitAvailable'] is False and batches[key]['splits'] == {}
        assert '本批未划分 development/test。' in batches[key]['statusReasons']
    detail = client.get('/api/experiments/controlled-rubbings-v2-2026-10-17').json()['registry']
    assert detail['status'] == 'valid' and detail['splitAvailable'] is True


def test_metadata_rules_are_independent_of_data_files():
    meta = experiment_metadata.batch_metadata({'directory': 'x', 'metricsOnly': False}, {'rows': [{'split': 'test'}, {'split': 'development'}, {}]})
    assert meta['splits'] == {'development': 1, 'test': 1} and meta['rowsWithoutSplit'] == 1 and meta['status'] == 'valid'
    entries = experiment_metadata.mark_default([{'id': 'a', 'status': 'valid'}, {'id': experiment_metadata.DEFAULT_REPORT_BATCH, 'status': 'metrics-only'}])
    assert not any(e['defaultForReport'] for e in entries)  # never default to a batch without images
