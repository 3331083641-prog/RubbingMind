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


def test_author_proposition_support_contradiction_and_refusal():
    supported = er.query('《多宝塔碑》的撰文者是不是岑勋？')
    assert supported['judgment'] == 'supported' and supported['claim']['recorded'] == '岑勋'
    assert supported['generation'] is None
    contradicted = er.query('《多宝塔碑》的撰文者是不是李白？')
    assert contradicted['judgment'] == 'contradicted'
    assert contradicted['claim']['recorded'] == '岑勋' and contradicted['claim']['proposed'] == '李白'
    assert contradicted['claim']['basis'] == 'catalogue_field_mismatch'
    assert '著录字段不一致' in contradicted['answer']
    assert '不是独立史料反证' in contradicted['answer']
    partial = er.query('《多宝塔碑》的书丹者是不是颜？')
    assert partial['judgment'] == 'contradicted' and partial['claim']['recorded'] == '颜真卿'
    assert partial['claim']['basis'] == 'catalogue_field_mismatch'
    exact = er.query('《多宝塔碑》的书丹者是不是颜真卿？')
    assert exact['judgment'] == 'supported' and exact['claim']['basis'] == 'catalogue_field_match'
    title_hand = er.query('《多宝塔碑》的篆额者是谁？')
    assert title_hand['judgment'] == 'supported' and title_hand['claim']['recorded']['篆额者'] == '徐浩'
    assert title_hand['claim']['basis'] == 'catalogue_field_match'
    disputed = er.query('书丹者是不是王羲之？', 'ming_04_tongdian')
    assert disputed['judgment'] == 'insufficient_evidence' and disputed['claim']['basis'] == 'insufficient_catalogue'
    assert '争议' in disputed['answer'] and disputed['claim']['recorded'] is None
    pending = er.query('撰文者是不是翁方纲？', 'qing_02_wushi_reerection')
    assert pending['judgment'] == 'insufficient_evidence' and '待复核' in pending['answer']
    not_author = er.query('撰文者是不是赵孟頫？', 'yuan_04_jingyuanchang')
    assert not_author['judgment'] == 'insufficient_evidence' and not_author['claim']['recorded'] is None
    unknown = er.query('《曹全碑》的撰文者是谁？')
    assert unknown['judgment'] == 'insufficient_evidence'
    assert '岑勋' not in unknown['answer']


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
