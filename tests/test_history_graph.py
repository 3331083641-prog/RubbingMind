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

def test_admin_region_containment():
    from scripts.validate_history_gis import validate
    assert len(validate())==12
