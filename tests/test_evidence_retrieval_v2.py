import pytest
from fastapi.testclient import TestClient
from main import app
import evidence_retrieval as er
from catalog import load


@pytest.fixture(autouse=True)
def isolated_index(tmp_path,monkeypatch):
    monkeypatch.setattr(er,'INDEX',tmp_path/'evidence.sqlite')


@pytest.mark.parametrize('question,required',[
    ('《多宝塔碑》的撰文者与书丹者是谁？',['岑勋','颜真卿']),
    ('《曹全碑》原刻于什么年代？',['185']),
    ('《多宝塔碑》原石与台北故宫藏拓本是什么关系？',['西安碑林','台北故宫']),
    ('多宝塔碑拓本年代与原刻年代是否相同？',['明拓','752']),
    ('北魏建义元年演示样本是否已经确认真实文物身份？',['未确认','测试标签']),
])
def test_sourced_queries(question,required):
    result=er.query(question)
    assert result['status']=='evidence_found'
    text=result['answer']+' '.join(e['text'] for e in result['evidence'])
    for phrase in required:assert phrase in text
    assert result['generation'] is None
    assert all(e['sourceId'] and e['originalPosition'] and e['textSha256'] and e['url'] for e in result['evidence'])
    assert all(e['sourceIds'] and e['sourceUrl'] for e in result['relations'])
    if '建义' in question:
        assert all(e['steleId']=='wei-jianyi' for e in result['evidence'])
        assert not result['places']


def test_no_evidence_no_fabrication_and_scope():
    assert er.query('请解释暗物质粒子')['status']=='insufficient_evidence'
    assert er.query('多宝塔碑的未知秘密是什么')['status']=='insufficient_evidence'
    result=er.query('曹全碑的原刻年代','tang_01_duobao')
    assert result['status']=='insufficient_evidence' and not result['evidence']
    assert all(e['steleId']=='tang_01_duobao' for e in result['evidence'])
    assert not any(n['name']=='曹全碑' for n in result['entities'])


def test_all_28_have_distinct_stone_rubbing_and_sources():
    for r in load('steles28.json'):
        graph=er.artifact_graph(r['id'])
        assert graph['sources']
        assert {'stone','rubbing'} <= set(n['category'] for n in graph['nodes'])
        assert all(e['sourceIds'] for e in graph['links'])
        assert graph['routes']==[]


def test_api_search_validation_and_deterministic_rebuild():
    client=TestClient(app)
    request={'question':'《多宝塔碑》的书丹者是谁？','steleId':'tang_01_duobao'}
    a=client.post('/api/research/query',json=request)
    assert a.status_code==200
    er.INDEX.unlink()
    b=client.post('/api/research/query',json=request)
    assert a.json()==b.json()
    assert client.post('/api/research/query',json={'question':'x'}).status_code==422
    assert client.get('/api/research/steles/missing').status_code==404
