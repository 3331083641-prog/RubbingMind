"""Green 2026-10-19 item 5: no API may emit precise coordinates of retired records."""
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

import database
from catalog import BASE, load
from main import app

RETIRED = [r['oldId'] for r in load('replacement_mapping.json')]


def _retired_coordinates():
    coords = set()
    for r in load('replacement_mapping.json'):
        for value in (r.get('oldRecord') or {}).get('gis_coords') or []:
            coords.add(float(value))
    legacy = BASE / 'data' / 'museum_database.json'
    if legacy.is_file():
        for r in json.loads(legacy.read_text('utf-8')):
            if r.get('id') in RETIRED:
                coords.update(float(v) for v in r.get('gis_coords') or [])
    try:
        with sqlite3.connect(f'file:{database.DB_PATH}?mode=ro', uri=True) as conn:
            marks = ','.join('?' * len(RETIRED))
            for lng, lat in conn.execute(f'SELECT gis_lng, gis_lat FROM steles WHERE id IN ({marks})', RETIRED):
                coords.update(float(v) for v in (lng, lat) if v is not None)
    except sqlite3.Error:
        pass
    return coords


def _needles(coords):
    # Exact repr plus a 3-decimal prefix (≈100 m) — anything that precise is "precise".
    return {repr(c) for c in coords} | {f'{c:.3f}' for c in coords}


def test_reference_coordinates_exist():
    assert RETIRED and _retired_coordinates(), 'fixture lost: no retired coordinates to look for'


@pytest.mark.parametrize('path', ['/api/steles', '/api/id-mapping', '/api/health', '/api/experiments', '/generate']
                         + [p.format(i) for i in RETIRED for p in (
                             '/api/steles/{}', '/api/steles/rm:retired:{}', '/api/steles/{}/graph', '/api/steles/{}/report',
                             '/api/steles/{}/infer', '/api/steles/{}/runs', '/api/steles/{}/inferences',
                             '/api/research/steles/{}', '/api/id-mapping/{}', '/api/id-mapping/rm:retired:{}',
                             '/api/catalog/{}/assessment')])
def test_no_retired_coordinates_in_responses(path):
    response = TestClient(app).get(path)
    text = response.text
    leaked = [n for n in _needles(_retired_coordinates()) if n in text]
    assert not leaked, f'{path} ({response.status_code}) leaks retired coordinates {leaked}'


def test_mapping_entries_for_retired_records_drop_locations(monkeypatch, tmp_path):
    import id_mapping
    path = tmp_path / 'id_mapping.json'
    path.write_text(json.dumps({'version': 't', 'entries': [
        {'legacyId': RETIRED[0], 'newId': f'rm:retired:{RETIRED[0]}', 'kind': 'retired', 'gis_coords': [112.241, 30.335], 'originalLocation': '某地'},
        {'legacyId': 'tang_01_duobao', 'kind': 'rubbing', 'location': 'kept for non-retired'}]}), 'utf-8')
    monkeypatch.setattr(id_mapping, 'MAPPING_PATH', path)
    body = TestClient(app).get('/api/id-mapping').text
    assert '112.241' not in body and '某地' not in body and '已下架记录不输出坐标或地点' in body
    assert 'kept for non-retired' in body
