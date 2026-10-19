"""R1-5 / R2: namespaced ids, optional id_mapping.json, graph steleId/entity, sourceSteleId."""
import json

import pytest
from fastapi.testclient import TestClient

import id_mapping
import museum_processing
from main import app

# Shape copied from agent/jinshi's draft (data/catalog/id_mapping.json); fixture only, never committed as data.
FIXTURE = {
    'version': 'fixture', 'status': 'test fixture', 'author': 'tests',
    'namespaces': {'rm:demo:': 'demo', 'rm:rubbing:': 'rubbing'},
    'entries': [
        {'legacyId': 'tang_01_duobao', 'newId': 'rm:rubbing:tang_01_duobao', 'kind': 'rubbing', 'title': '多宝塔碑'},
        {'legacyId': 'tang-duobao', 'newId': 'rm:demo:tang-duobao', 'kind': 'demo_sample',
         'depictsSameWorkAs': {'relation': 'depicts_same_work_as', 'rubbingId': 'tang_01_duobao', 'evidenceGrade': '待人工复核'}},
        {'legacyId': 'qing_02_chongli_wushi', 'newId': 'rm:rubbing:qing_02_wushi_reerection', 'kind': 'review_alias', 'aliasOf': 'qing_02_wushi_reerection'},
    ],
}


@pytest.fixture
def no_mapping(monkeypatch, tmp_path):
    monkeypatch.setattr(id_mapping, 'MAPPING_PATH', tmp_path / 'absent.json')


@pytest.fixture
def with_mapping(monkeypatch, tmp_path):
    path = tmp_path / 'id_mapping.json'
    path.write_text(json.dumps(FIXTURE, ensure_ascii=False), 'utf-8')
    monkeypatch.setattr(id_mapping, 'MAPPING_PATH', path)


def test_missing_mapping_is_empty_not_an_error(no_mapping):
    body = TestClient(app).get('/api/id-mapping').json()
    assert body['available'] is False and body['entries'] == [] and body['mappingError'] is None
    assert body['aggregation']['enabled'] is False
    assert body['unreviewedLegacyLinks']['usedForAggregation'] is False and len(body['unreviewedLegacyLinks']['links']) == 4
    entity = TestClient(app).get('/api/id-mapping/tang-duobao').json()
    assert entity['kind'] == 'demo_sample' and entity['newId'] == 'rm:demo:tang-duobao' and entity['depictsSameWorkAs'] is None


def test_broken_mapping_reports_error_without_failing(monkeypatch, tmp_path):
    path = tmp_path / 'id_mapping.json'
    path.write_text('{not json', 'utf-8')
    monkeypatch.setattr(id_mapping, 'MAPPING_PATH', path)
    body = TestClient(app).get('/api/id-mapping').json()
    assert body['entries'] == [] and body['mappingError']


def test_mapping_fixture_is_read_but_never_merges(with_mapping):
    client = TestClient(app)
    assert client.get('/api/id-mapping').json()['version'] == 'fixture'
    demo = client.get('/api/id-mapping/rm:demo:tang-duobao').json()
    assert demo['kind'] == 'demo_sample' and demo['depictsSameWorkAs']['rubbingId'] == 'tang_01_duobao'
    assert demo['relationReviewed'] is False and demo['mappingSource'] == 'data/catalog/id_mapping.json'
    alias = client.get('/api/id-mapping/qing_02_chongli_wushi').json()
    assert alias['kind'] == 'review_alias' and alias['aliasOf'] == 'qing_02_wushi_reerection'


@pytest.mark.parametrize('bare,namespaced', [('tang-duobao', 'rm:demo:tang-duobao'), ('tang_01_duobao', 'rm:rubbing:tang_01_duobao')])
def test_new_and_old_ids_return_identical_records(no_mapping, bare, namespaced):
    client = TestClient(app)
    old = client.get(f'/api/steles/{bare}')
    new = client.get(f'/api/steles/{namespaced}')
    assert old.status_code == new.status_code == 200 and old.content == new.content
    assert 'entity' not in old.json()  # BR-02: legacy /api/steles/{id} response unchanged


def test_namespace_must_match_kind(no_mapping):
    client = TestClient(app)
    assert client.get('/api/steles/rm:rubbing:tang-duobao').status_code == 404
    assert client.get('/api/steles/rm:demo:tang_01_duobao').status_code == 404
    assert client.get('/api/steles/rm:work:duobao').status_code == 404
    assert client.get('/api/steles/rm:retired:yuan_04_jiulao').status_code == 410
    assert client.get('/api/id-mapping/rm:demo:tang_01_duobao').status_code == 404


def test_collection_graph_returns_stele_id_and_entity(no_mapping):
    client = TestClient(app)
    graph = client.get('/api/steles/tang_01_duobao/graph').json()
    assert graph['steleId'] == 'tang_01_duobao' and graph['entity']['kind'] == 'rubbing'
    assert client.get('/api/steles/rm:rubbing:tang_01_duobao/graph').json()['steleId'] == 'tang_01_duobao'
    demo = client.get('/api/steles/rm:demo:tang-duobao/graph').json()
    assert demo['entity']['kind'] == 'demo_sample'


def test_runs_carry_source_id_and_are_not_aggregated(no_mapping, monkeypatch, tmp_path):
    monkeypatch.setattr(museum_processing, 'BASE', tmp_path)
    monkeypatch.setattr(museum_processing, 'RESULTS_DIR', None)
    for stele, run in [('tang_01_duobao', '20261018T000001_00000001'), ('tang-duobao', '20261018T000002_00000002')]:
        folder = tmp_path / 'static/results' / stele / run
        folder.mkdir(parents=True)
        (folder / 'processing.json').write_text(json.dumps({'runId': run, 'steleId': stele, 'algorithmVersion': 'adaptive-rubbing-v2.1'}), 'utf-8')
    client = TestClient(app)
    museum = client.get('/api/steles/tang_01_duobao/runs').json()
    demo = client.get('/api/steles/rm:demo:tang-duobao/runs').json()
    assert [(r['runId'], r['sourceSteleId']) for r in museum] == [('20261018T000001_00000001', 'tang_01_duobao')]
    assert [(r['runId'], r['sourceSteleId']) for r in demo] == [('20261018T000002_00000002', 'tang-duobao')]
    assert client.get('/api/steles/rm:demo:tang-duobao/report').json()['run']['runId'] == '20261018T000002_00000002'
