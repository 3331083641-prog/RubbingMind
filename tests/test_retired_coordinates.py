"""Task 0: the five retired records' unsourced coordinates never leave any API or web data path.

The archive JSON files (replacement_mapping.json, retired_steles.json, retired_database_records.json,
museum_database_backup.json) keep the historical values on purpose; they are not served (see C08_SYNC_SPEC.md).
"""
import json
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import evidence_retrieval as er
from main import app

ROOT = Path(__file__).resolve().parents[1]
RETIRED = {'qing_01_shilang': ('120.202', '22.997'), 'qing_02_gaocheng': ('117.939', '40.978'),
           'qing_03_yanjin': ('120.161', '23.001'), 'qing_04_gongchen': ('120.203', '22.987'),
           'yuan_04_jiulao': ('112.241', '30.335')}
ARCHIVES = ['data/catalog/replacement_mapping.json', 'data/catalog/retired_steles.json',
            'data/catalog/retired_database_records.json', 'data/museum_database_backup.json']


@pytest.fixture(autouse=True)
def isolated_index(tmp_path, monkeypatch):
    monkeypatch.setattr(er, 'INDEX', tmp_path / 'evidence.sqlite')


def has_pair(text, lng, lat):
    return re.search(re.escape(lng) + r'\d*\D{1,6}' + re.escape(lat), text) is not None


def assert_clean(text):
    for lng, lat in RETIRED.values():
        assert not has_pair(text, lng, lat)


@pytest.mark.parametrize('stele_id', sorted(RETIRED))
def test_retired_endpoints_return_ids_only(stele_id):
    client = TestClient(app)
    for path in (f'/api/steles/{stele_id}', f'/api/steles/{stele_id}/graph', f'/api/steles/{stele_id}/infer'):
        response = client.get(path)
        assert response.status_code == 410, path
        assert_clean(response.text)
        assert set(response.json()['detail']) == {'message', 'oldId', 'recommendedId'}
    assert client.get(f'/api/research/steles/{stele_id}').status_code == 404
    assert client.post('/api/research/query', json={'question': '坐标在哪里', 'steleId': stele_id}).status_code == 404


def test_lists_search_and_static_paths_are_clean():
    client = TestClient(app)
    listing = client.get('/api/steles')
    assert not {r['id'] for r in listing.json()} & set(RETIRED)
    assert_clean(listing.text)
    for question in ('靖海将军侯施公功德碑的地点', '中兴路重建九老仙都宫记在哪里', '严禁海口陋规碑记'):
        assert_clean(client.post('/api/research/query', json={'question': question}).text)
    for archive in ARCHIVES:
        response = client.get('/' + archive)
        assert response.status_code != 200 or archive not in response.text
        assert_clean(response.text)


def test_archives_still_hold_history_but_are_not_web_assets():
    for archive in ARCHIVES:
        assert (ROOT / archive).is_file()
        assert not archive.startswith(('apps/web/public', 'static'))
    files = [p for p in (ROOT / 'apps/web/src').rglob('*') if p.suffix in ('.json', '.ts', '.tsx')]
    files += [p for p in (ROOT / 'apps/web/public').rglob('*.json')]
    files += [ROOT / 'data/catalog/id_mapping.json', ROOT / 'data/catalog/c08_sync_diff.json', ROOT / 'data/catalog/review_ledger.json']
    for path in files:
        assert_clean(path.read_text(encoding='utf-8', errors='ignore'))


def test_history_graph_has_no_retired_entries():
    from history_graph import get_history_graph
    for stele_id in RETIRED:
        graph = get_history_graph(stele_id, [])
        assert graph is None or not graph.get('gis_route')
        assert_clean(json.dumps(graph, ensure_ascii=False))
