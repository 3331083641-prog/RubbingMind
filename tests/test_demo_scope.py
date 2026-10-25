"""C-16: synthetic demo samples stay out of ordinary retrieval unless explicitly selected."""
import pytest
from fastapi.testclient import TestClient

import evidence_retrieval as er
from main import app

LABEL = '合成测试文本（sample_generator 生成，非真实释文）'
UNRELATED = ['今天天气怎么样', '明天会下雨吗？天气预报', '你好', '请解释暗物质粒子', '今天吃什么', '帮我写一首诗', '2026年世界杯冠军是谁']
SAMPLE_WORDS = ['北魏建义元年演示样本是否已经确认真实文物身份？', '建义元年墓志的墓主是谁？', '昌黎人也', '夫人諱某', '演示样本有哪些']


@pytest.fixture(autouse=True)
def isolated_index(tmp_path, monkeypatch):
    monkeypatch.setattr(er, 'INDEX', tmp_path / 'evidence.sqlite')


def assert_no_synthetic(result):
    assert all(e['steleId'] != 'wei-jianyi' for e in result['evidence'])
    assert all(n['steleId'] != 'wei-jianyi' for n in result['entities'])
    assert result['contentWarnings'] == [] and LABEL not in result['answer']
    assert result['demoScope']['included'] is False and result['demoScope']['syntheticSamples'] == ['wei-jianyi']


@pytest.mark.parametrize('question', UNRELATED)
def test_unrelated_queries_never_surface_synthetic_text(question):
    result = er.query(question)
    assert result['status'] == 'insufficient_evidence'
    assert_no_synthetic(result)


@pytest.mark.parametrize('question', SAMPLE_WORDS)
def test_sample_words_alone_do_not_opt_in(question):
    assert_no_synthetic(er.query(question))


@pytest.mark.parametrize('kwargs,opt_in', [
    ({'include_demo': True}, 'include_demo'),
    ({'stele_id': 'wei-jianyi'}, 'demo_scope_id'),
    ({'stele_id': 'rm:demo:wei-jianyi'}, 'demo_scope_id'),
])
def test_explicit_selection_includes_labelled_sample(kwargs, opt_in):
    result = er.query('北魏建义元年演示样本是否已经确认真实文物身份？', **kwargs)
    assert result['demoScope'] == {**result['demoScope'], 'included': True, 'optIn': opt_in}
    assert result['evidence'] and all(e['steleId'] == 'wei-jianyi' for e in result['evidence'])
    assert all(e['text'].startswith('【' + LABEL + '】') for e in result['evidence'])
    assert result['contentWarnings'] == [LABEL]


def test_rm_demo_id_in_question_opts_in():
    result = er.query('rm:demo:wei-jianyi 是否已经确认真实文物身份？')
    assert result['demoScope']['optIn'] == 'rm_demo_id_in_question'
    assert any(e['steleId'] == 'wei-jianyi' for e in result['evidence'])


def test_real_works_unchanged_by_demo_flag():
    for question in ('多宝塔碑的撰文者与书丹者是谁？', '曹全碑原石现藏在哪里？'):
        default, demo = er.query(question), er.query(question, include_demo=True)
        assert default['status'] == demo['status'] and default['judgment'] == demo['judgment']
        assert [e['sourceId'] for e in default['evidence']] == [e['sourceId'] for e in demo['evidence']]


def test_api_default_excludes_and_demo_scope_includes():
    client = TestClient(app)
    plain = client.post('/api/research/query', json={'question': '北魏建义元年演示样本是否已经确认真实文物身份？'}).json()
    assert plain['demoScope']['included'] is False and plain['contentWarnings'] == []
    scoped = client.post('/api/research/query', json={'question': '北魏建义元年演示样本是否已经确认真实文物身份？', 'steleId': 'wei-jianyi'}).json()
    assert scoped['demoScope']['optIn'] == 'demo_scope_id' and scoped['contentWarnings'] == [LABEL]
    weather = client.post('/api/research/query', json={'question': '今天天气怎么样'}).json()
    assert weather['status'] == 'insufficient_evidence' and weather['contentWarnings'] == []
    assert all(e['steleId'] != 'wei-jianyi' for e in weather['evidence'])
