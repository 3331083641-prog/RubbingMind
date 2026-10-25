"""Regression checks for evidence, identity, CRS and geographic associations."""
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from main import app
from history_graph import CORE_IDS, get_history_graph, convert_historical_year
from museum_manager import museum_manager

ROOT=Path(__file__).resolve().parents[1]
client=TestClient(app)
@pytest.mark.parametrize('stele',CORE_IDS)
def test_evidence_and_references(stele):
    d=get_history_graph(stele,museum_manager.get_all_steles())
    assert d['steleId']==stele
    location_ids={p['id'] for p in d['locations']}
    node_ids={p['id'] for p in d['nodes']}
    source_ids={p['id'] for p in json.loads((ROOT/'data/history/sources.json').read_text(encoding='utf-8'))}
    assert len(location_ids)==len(d['locations'])
    assert len(node_ids)==len(d['nodes'])
    for p in d['locations']:
        assert p['coordinateSystem']=='WGS84'
        assert p['sourceUrl'] and p['sourceId'] in source_ids
        assert (p['longitude'] is None)==(p['latitude'] is None)
        if p['longitude'] is not None:
            # Chinese longitudes make a swapped [latitude,longitude] immediately invalid.
            assert 73 <= p['longitude'] <= 136
            assert 3 <= p['latitude'] <= 54
            assert p['coordinateSourceUrl'] and p['precision']!='unknown'
        if p.get('regionLocationId'):
            assert p['regionLocationId'] in location_ids
    for n in d['nodes']:
        assert set(n['locationIds'])<=location_ids
        assert set(n['sourceIds'])<=source_ids
    for e in d['events']:
        assert e['steleId']==stele and e['sourceUrl'] and e['sourceId'] in source_ids
        assert e['locationId'] is None or e['locationId'] in location_ids
    for l in d['links']:
        assert l['source'] in node_ids and l['target'] in node_ids and l['sourceUrl']
    for route in d['routes']:
        assert route['verified'] and route['sourceUrl']
        assert set(route['locationIds'])<=location_ids

@pytest.mark.parametrize('id,bounds,province',[
    ('beilin',(108.9,34.2,109,34.3),'陕西省'),('heyang',(109.9,35,110.5,35.6),'陕西省'),
    ('luoyang',(112.2,34.5,112.7,34.9),'河南省'),('dunhuang',(92,39,96,42),'甘肃省'),
    ('jiuquan',(98,39,100,40.5),'甘肃省'),('shule',(75,39,77,40.5),'新疆维吾尔自治区'),
])
def test_fixed_geography(id,bounds,province):
    places=[p for core in CORE_IDS for p in get_history_graph(core,[])['locations'] if p['id']==id]
    assert places
    for p in places:
        west,south,east,north=bounds
        assert west<=p['longitude']<=east and south<=p['latitude']<=north
        assert p['province']==province

@pytest.mark.parametrize('query,year,gz',[('唐天宝十一载',752,'壬辰'),('东汉中平二年',185,'乙丑'),('北魏熙平二年',517,'丁酉'),('北魏建义元年',528,'戊申'),('公元2026年',2026,'丙午'),('天宝十五载',756,'丙申')])
def test_year_conversion(query,year,gz):
    r=client.post('/api/calendar',json={'query':query}).json()
    assert r['supported'] and r['solar_year']==year and r['ganzhi']==gz

@pytest.mark.parametrize('query',['乾元元年','天宝九十九载','中平零年','熙平十三年','建义二年','大概752年','xyz','0','唐天宝十一载四月二十日','天宝十十载','天宝十元载','东汉天宝十一载','唐中平二年'])
def test_unsupported_year(query):
    r=convert_historical_year(query)
    assert r['supported'] is False and r['solar_year'] is None

def test_identity_boundaries():
    assert get_history_graph('wei_02_wugaoli',museum_manager.get_all_steles())['formalName']=='吴高黎墓志'
    yuan=get_history_graph('wei-yuanhuai',[])
    assert yuan['yearCE']==517 and all('吴高黎' not in n['name'] for n in yuan['nodes'])
    sample=get_history_graph('wei-jianyi',[])
    assert sample['locations']==[] and sample['routes']==[]
    assert all(n['category']!='person' for n in sample['nodes'])
    assert all(e['verification']=='unverified' for e in sample['events'])
    assert client.get('/api/steles/does-not-exist/graph').status_code==404
    assert get_history_graph('wei_04_wangsong',museum_manager.get_all_steles())['steleId']=='wei_04_wangsong'

def test_map_coverage_and_crs():
    d=json.loads((ROOT/'apps/web/public/assets/gis/china-provinces.cgcs2000.geojson').read_text(encoding='utf-8'))
    assert '4490' in d['crs']['properties']['name']
    provinces=[f for f in d['features'] if f['geometry']['type']=='MultiPolygon']
    assert len(provinces)==34
    names={f['properties']['name'] for f in provinces}
    assert {'台湾省','海南省','香港特别行政区','澳门特别行政区','新疆维吾尔自治区','西藏自治区','黑龙江省'}<=names
    assert len(d['features'])==42
    assert any(f['geometry']['type']=='MultiLineString' for f in d['features'])
    # No AI contour; the exact downloaded file is pinned by digest.
    import hashlib
    provenance=json.loads((ROOT/'apps/web/public/assets/gis/provenance.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((ROOT/'apps/web/public/assets/gis/china-provinces.cgcs2000.geojson').read_bytes()).hexdigest()==provenance['sha256']

def test_health_then_generate():
    assert client.get('/health').json()['status']=='healthy'
    assert client.get('/generate?stele_id=han-caoquan').json()['steleId']=='han-caoquan'


@pytest.mark.parametrize('core,museum', [('han-caoquan', 'han_01_caoquan'), ('tang-duobao', 'tang_01_duobao')])
def test_graph_images_use_reviewed_rubbings(core, museum):
    """馆藏实体用已审影像；演示 id（含 rm:demo:）永不回落馆藏图（RV-AI06）。"""
    from catalog import museum_records
    import history_graph as hg
    records = museum_records()
    record = next(r for r in records if r['id'] == museum)
    museum_graph = hg.get_history_graph(museum, records)
    assert museum_graph['image'] == record['imageAssets']['readable']
    assert 'museum-rubbings' in museum_graph['image']
    assert record['collectionNumber'].replace('贈', '赠').replace('冊', '册') in museum_graph['collectionNumber'] or record['collectionNumber'] in museum_graph['collectionNumber']
    core_row = hg._core_sample(core)
    assert core_row and core_row.get('raw_image')
    demo_http = client.get(f'/api/steles/{core}/graph').json()
    assert demo_http['image'] == core_row['raw_image']
    assert 'museum-rubbings' not in demo_http['image']
    assert demo_http.get('imageStatus', '').startswith('演示样本')
    demo_ns_http = client.get(f'/api/steles/rm:demo:{core}/graph').json()
    assert demo_ns_http['image'] == core_row['raw_image']
    assert 'museum-rubbings' not in demo_ns_http['image']
    assert demo_ns_http['steleId'] == core
    assert demo_ns_http.get('entity', {}).get('kind') == 'demo_sample'
    offline = json.loads((ROOT / 'data/history' / f'{core}.json').read_text(encoding='utf-8'))
    assert offline['image'] == core_row['raw_image']
    assert 'museum-rubbings' not in offline['image']


def test_rm_demo_path_query_api_match_bare_demo():
    """路径参数、查询参数、研究 API 均接受 rm:demo:<id>，行为与裸演示 id 一致。"""
    bare = client.get('/api/steles/han-caoquan')
    ns = client.get('/api/steles/rm:demo:han-caoquan')
    assert bare.status_code == 200 and ns.status_code == 200
    assert bare.json()['id'] == ns.json()['id'] == 'han-caoquan'
    assert bare.json()['source_kind'] == ns.json()['source_kind'] == 'core_demo'
    assert 'museum-rubbings' not in (bare.json().get('raw_image') or '')
    g_bare = client.get('/generate?stele_id=han-caoquan')
    g_ns = client.get('/generate?stele_id=rm:demo:han-caoquan')
    assert g_bare.status_code == 200 and g_ns.status_code == 200
    assert g_bare.json()['steleId'] == g_ns.json()['steleId'] == 'han-caoquan'
    assert g_ns.json()['image'] == g_bare.json()['image']
    assert 'museum-rubbings' not in g_ns.json()['image']
    q = client.post('/api/research/query', json={
        'question': '书丹者是谁？', 'steleId': 'rm:demo:han-caoquan'
    })
    assert q.status_code == 200
    body = q.json()
    assert body['scopeSteleId'] == 'han-caoquan'
    assert body['scopeResolution']['kind'] == 'demo_sample'
    assert body['demoScope']['included'] is True
    q2 = client.post('/api/research/query', json={
        'question': '魏氏墓志的释文写了什么？', 'includeDemo': True
    })
    assert q2.status_code == 200
    assert q2.json()['demoScope']['included'] is True


def test_admin_region_containment():
    from scripts.validate_history_gis import validate
    assert len(validate())==12
